"""
Isolated Test Suite Execution Runner for Mutation-Sentinel.
Evaluates test vigilance against original code and adversarial AST mutants.
"""

import sys
import time
import traceback
import unittest
from typing import List, Dict, Any, Optional, Tuple
from .models import Mutant, MutantStatus


class MutationRunner:
    """Runs test suites against original and mutated target modules."""

    def __init__(self, target_module_name: str, target_source: str, test_source: str):
        self.target_module_name = target_module_name
        self.target_source = target_source
        self.test_source = test_source

    def _execute_test_suite_with_module(self, target_code: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Executes test suite with `target_code` injected into sys.modules.
        Returns (all_passed, killing_test_name, failure_message).
        """
        import types
        module_name = self.target_module_name

        # Create isolated module from code
        mod = types.ModuleType(module_name)
        mod.__file__ = f"<{module_name}>"
        saved_module = sys.modules.get(module_name)

        try:
            # 1. Compile and execute target module
            code_obj = compile(target_code, f"<{module_name}>", "exec")
            exec(code_obj, mod.__dict__)
            sys.modules[module_name] = mod

            # 2. Compile test code in isolated namespace
            test_ns = {"__name__": "__test_sandbox__", module_name: mod}
            test_code_obj = compile(self.test_source, "<test_suite>", "exec")
            exec(test_code_obj, test_ns)

            # 3. Discover TestCase subclasses in test_ns
            suite = unittest.TestSuite()
            loader = unittest.TestLoader()

            for item_name, item_val in test_ns.items():
                if isinstance(item_val, type) and issubclass(item_val, unittest.TestCase):
                    tests = loader.loadTestsFromTestCase(item_val)
                    suite.addTests(tests)

            if suite.countTestCases() == 0:
                # If no unittest.TestCase, check for simple test_ functions
                test_funcs = [v for k, v in test_ns.items() if k.startswith("test_") and callable(v)]
                if not test_funcs:
                    return False, None, "No unittest.TestCase or test_* functions found in test suite"
                
                # Execute standalone test functions
                for tf in test_funcs:
                    try:
                        tf()
                    except AssertionError as ae:
                        return False, tf.__name__, f"AssertionError: {ae}"
                    except Exception as ex:
                        return False, tf.__name__, f"Exception: {ex}"
                return True, None, None

            # Run with custom runner that captures results in memory
            result = unittest.TestResult()
            suite.run(result)

            if result.wasSuccessful():
                return True, None, None
            else:
                killing_test = None
                failure_msg = None
                if result.failures:
                    test_case, tb = result.failures[0]
                    killing_test = str(test_case)
                    failure_msg = tb.splitlines()[-1] if tb else "Assertion Failed"
                elif result.errors:
                    test_case, tb = result.errors[0]
                    killing_test = str(test_case)
                    failure_msg = tb.splitlines()[-1] if tb else "Runtime Error in Mutant"

                return False, killing_test, failure_msg

        except Exception as e:
            return False, "compile_failure", str(e)
        finally:
            if saved_module is not None:
                sys.modules[module_name] = saved_module
            elif module_name in sys.modules:
                del sys.modules[module_name]

    def verify_baseline(self) -> Tuple[bool, Optional[str]]:
        """Verify that the unmutated test suite passes cleanly."""
        passed, killing_test, failure_msg = self._execute_test_suite_with_module(self.target_source)
        if not passed:
            return False, f"Baseline test suite failed before mutation: {failure_msg} (Test: {killing_test})"
        return True, None

    def evaluate_mutants(self, mutants: List[Mutant]) -> List[Mutant]:
        """Test each mutant against the test suite."""
        for m in mutants:
            t0 = time.time()
            passed, killing_test, failure_msg = self._execute_test_suite_with_module(m.mutated_source)
            dur = (time.time() - t0) * 1000

            m.execution_time_ms = dur
            if not passed:
                if killing_test == "compile_failure":
                    m.status = MutantStatus.ERRORED
                    m.failure_message = failure_msg
                else:
                    m.status = MutantStatus.KILLED
                    m.killing_test = killing_test
                    m.failure_message = failure_msg
            else:
                # The mutant broke the code, but the test suite passed anyway!
                m.status = MutantStatus.SURVIVED

        return mutants

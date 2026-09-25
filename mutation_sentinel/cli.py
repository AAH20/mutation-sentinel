"""
Command Line Interface for Mutation-Sentinel.
Provides interactive demo comparing hollow AI tests vs hardened test suites.
"""

import argparse
import sys
import time
from .mutator import ASTMutator
from .runner import MutationRunner
from .scorer import MutationScorer


TARGET_CODE_SAMPLE = '''"""Banking Transaction and Risk Engine."""

def calculate_wire_fee(amount: float, is_international: bool) -> float:
    base_fee = 15.0
    if is_international:
        base_fee += amount * 0.03
    else:
        base_fee += amount * 0.005
    return round(base_fee, 2)

def authorize_withdrawal(balance: float, amount: float, max_overdraft: float = 500.0) -> bool:
    if amount <= 0.0:
        return False
    if balance - amount >= -max_overdraft:
        return True
    return False
'''

# 1. Hollow AI Test Suite (Looks like 100% coverage, but asserts almost nothing!)
HOLLOW_TEST_SUITE = '''import unittest
import banking_service

class TestBankingHollow(unittest.TestCase):
    def test_wire_fee(self):
        # AI generated: just checks it returns something without error
        res1 = banking_service.calculate_wire_fee(100.0, True)
        res2 = banking_service.calculate_wire_fee(100.0, False)
        self.assertIsNotNone(res1)
        self.assertIsNotNone(res2)

    def test_withdrawal(self):
        # AI generated: superficial call
        auth1 = banking_service.authorize_withdrawal(100.0, 50.0)
        auth2 = banking_service.authorize_withdrawal(-600.0, 100.0)
        self.assertTrue(auth1)
        self.assertFalse(auth2)
'''

# 2. Hardened Sentinel Test Suite (Strict mathematical invariants & boundary tests)
HARDENED_TEST_SUITE = '''import unittest
import banking_service

class TestBankingHardened(unittest.TestCase):
    def test_wire_fee_domestic(self):
        # Base 15 + 1000 * 0.005 = 20.0
        self.assertEqual(banking_service.calculate_wire_fee(1000.0, False), 20.0)

    def test_wire_fee_international(self):
        # Base 15 + 1000 * 0.03 = 45.0
        self.assertEqual(banking_service.calculate_wire_fee(1000.0, True), 45.0)

    def test_withdrawal_zero_or_negative(self):
        self.assertFalse(banking_service.authorize_withdrawal(100.0, 0.0))
        self.assertFalse(banking_service.authorize_withdrawal(100.0, -10.0))

    def test_withdrawal_exact_boundary(self):
        # Balance 0, amount 500, max_overdraft 500 -> 0 - 500 >= -500 is True
        self.assertTrue(banking_service.authorize_withdrawal(0.0, 500.0, 500.0))
        # Exceeds by 0.01 -> False
        self.assertFalse(banking_service.authorize_withdrawal(0.0, 500.01, 500.0))
'''


def run_demo() -> None:
    print("=" * 74)
    print("  🛡️ MUTATION-SENTINEL: ADVERSARIAL AST MUTATION ENGINE FOR AI CODE")
    print("=" * 74)
    print("Target Code: banking_service.py (wire fees & risk authorization)")
    print("Generating AST mutants across Arithmetic, Comparison, Constant, and Return...")

    mutator = ASTMutator(TARGET_CODE_SAMPLE)
    mutants = mutator.generate_mutants()
    print(f"✓ Discovered {len(mutants)} distinct adversarial mutation injection points.\n")

    # Round 1: Evaluate Hollow AI Test Suite
    print("-" * 74)
    print("ROUND 1: Auditing 'Hollow AI' Test Suite (Superficial Assertions)")
    print("-" * 74)
    runner_hollow = MutationRunner("banking_service", TARGET_CODE_SAMPLE, HOLLOW_TEST_SUITE)
    ok, err = runner_hollow.verify_baseline()
    if not ok:
        print(f"Baseline error: {err}")
        return

    t0 = time.time()
    evaluated_hollow = runner_hollow.evaluate_mutants([m for m in mutator.generate_mutants()])
    dur_hollow = (time.time() - t0) * 1000
    report_hollow = MutationScorer.calculate_report("banking_service", "test_banking_hollow.py", evaluated_hollow, dur_hollow)

    print(f"• Total Mutants Injected : {report_hollow.total_mutants}")
    print(f"• Mutants Killed         : {report_hollow.killed_mutants}")
    print(f"• Mutants SURVIVED       : {report_hollow.survived_mutants} 🚨")
    print(f"• Mutant Kill Rate (MKR) : {report_hollow.mutant_kill_rate * 100:.1f}%")
    print(f"• Resilience Score (MRS) : {report_hollow.mutation_resilience_score}% [{report_hollow.classification}]")

    # Round 2: Evaluate Hardened Sentinel Test Suite
    print("\n" + "-" * 74)
    print("ROUND 2: Auditing 'Hardened Sentinel' Test Suite (Strict Invariants)")
    print("-" * 74)
    runner_hardened = MutationRunner("banking_service", TARGET_CODE_SAMPLE, HARDENED_TEST_SUITE)
    ok, err = runner_hardened.verify_baseline()
    if not ok:
        print(f"Baseline error: {err}")
        return

    t1 = time.time()
    evaluated_hardened = runner_hardened.evaluate_mutants([m for m in mutator.generate_mutants()])
    dur_hardened = (time.time() - t1) * 1000
    report_hardened = MutationScorer.calculate_report("banking_service", "test_banking_hardened.py", evaluated_hardened, dur_hardened)

    print(f"• Total Mutants Injected : {report_hardened.total_mutants}")
    print(f"• Mutants Killed         : {report_hardened.killed_mutants} ✅")
    print(f"• Mutants SURVIVED       : {report_hardened.survived_mutants}")
    print(f"• Mutant Kill Rate (MKR) : {report_hardened.mutant_kill_rate * 100:.1f}%")
    print(f"• Resilience Score (MRS) : {report_hardened.mutation_resilience_score}% [{report_hardened.classification}]")

    print("\n" + "=" * 74)
    print("  VERDICT: HOLLOW AI TESTS FAIL REGRESSION DRIFT. SENTINEL ARMED.")
    print("=" * 74)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mutation-Sentinel AST Mutation Testing Engine")
    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser("demo", help="Run interactive demo")
    
    audit_parser = subparsers.add_parser("audit", help="Audit a python file against its test suite")
    audit_parser.add_argument("target", help="Path to target Python module")
    audit_parser.add_argument("tests", help="Path to Python test file")
    audit_parser.add_argument("--output", "-o", help="Optional markdown output path")

    args = parser.parse_args()

    if args.command == "demo" or len(sys.argv) == 1:
        run_demo()
    elif args.command == "audit":
        with open(args.target, "r") as f:
            target_src = f.read()
        with open(args.tests, "r") as f:
            test_src = f.read()

        import os
        mod_name = os.path.splitext(os.path.basename(args.target))[0]
        mutator = ASTMutator(target_src)
        mutants = mutator.generate_mutants()
        runner = MutationRunner(mod_name, target_src, test_src)
        
        ok, err = runner.verify_baseline()
        if not ok:
            print(f"Error: {err}")
            sys.exit(1)

        t0 = time.time()
        evaluated = runner.evaluate_mutants(mutants)
        dur = (time.time() - t0) * 1000
        report = MutationScorer.calculate_report(args.target, args.tests, evaluated, dur)
        md = MutationScorer.generate_markdown_report(report)

        if args.output:
            with open(args.output, "w") as f:
                f.write(md)
            print(f"Mutation report saved to {args.output}")
        else:
            print(md)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

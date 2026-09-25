"""
Comprehensive Unit Test Suite for Mutation-Sentinel.
"""

import unittest
from mutation_sentinel.models import MutationOperator, MutantStatus
from mutation_sentinel.mutator import ASTMutator
from mutation_sentinel.runner import MutationRunner
from mutation_sentinel.scorer import MutationScorer


SAMPLE_CODE = """
def add_bonus(salary: float, multiplier: float) -> float:
    if multiplier > 1.0:
        return salary * multiplier
    return salary + 100.0
"""

SAMPLE_VIGILANT_TEST = """
import unittest
import sample_mod

class TestBonus(unittest.TestCase):
    def test_high_mult(self):
        self.assertEqual(sample_mod.add_bonus(100.0, 2.0), 200.0)

    def test_low_mult(self):
        self.assertEqual(sample_mod.add_bonus(100.0, 0.5), 200.0)

    def test_boundary(self):
        self.assertEqual(sample_mod.add_bonus(100.0, 1.0), 200.0)
"""

SAMPLE_HOLLOW_TEST = """
import unittest
import sample_mod

class TestBonusHollow(unittest.TestCase):
    def test_bonus_runs(self):
        # AI superficial test
        res = sample_mod.add_bonus(100.0, 2.0)
        self.assertIsNotNone(res)
"""


class TestMutationSentinel(unittest.TestCase):

    def test_ast_mutator_discovery(self):
        """Test finding mutation points across operators."""
        mutator = ASTMutator(SAMPLE_CODE)
        points = mutator.discover_mutation_points()
        self.assertGreater(len(points), 0)

        # Check discovered operators
        ops = {p[0] for p in points}
        self.assertIn(MutationOperator.COMPARISON, ops)
        self.assertIn(MutationOperator.ARITHMETIC, ops)

        # Check mutant generation
        mutants = mutator.generate_mutants()
        self.assertEqual(len(mutants), len(points))
        for m in mutants:
            self.assertTrue(len(m.mutated_source) > 0)
            self.assertNotEqual(m.mutated_source, SAMPLE_CODE)

    def test_mutation_runner_vigilant_vs_hollow(self):
        """Test that vigilant tests kill mutants while hollow tests let them survive."""
        mutator = ASTMutator(SAMPLE_CODE)
        mutants = mutator.generate_mutants()

        # Run with vigilant test
        runner_vigilant = MutationRunner("sample_mod", SAMPLE_CODE, SAMPLE_VIGILANT_TEST)
        ok, err = runner_vigilant.verify_baseline()
        self.assertTrue(ok)

        evaluated_vigilant = runner_vigilant.evaluate_mutants([m for m in mutator.generate_mutants()])
        report_vigilant = MutationScorer.calculate_report("sample_mod", "vigilant", evaluated_vigilant)
        self.assertGreater(report_vigilant.killed_mutants, 0)
        self.assertGreater(report_vigilant.mutation_resilience_score, 50.0)

        # Run with hollow test
        runner_hollow = MutationRunner("sample_mod", SAMPLE_CODE, SAMPLE_HOLLOW_TEST)
        evaluated_hollow = runner_hollow.evaluate_mutants([m for m in mutator.generate_mutants()])
        report_hollow = MutationScorer.calculate_report("sample_mod", "hollow", evaluated_hollow)

        # Hollow test should have lower kill rate
        self.assertGreater(report_vigilant.mutant_kill_rate, report_hollow.mutant_kill_rate)
        self.assertEqual(report_hollow.classification, "HOLLOW_AI_SLOP")

    def test_scorer_and_markdown_generation(self):
        """Test score calculation and report rendering."""
        mutator = ASTMutator(SAMPLE_CODE)
        mutants = mutator.generate_mutants()
        runner = MutationRunner("sample_mod", SAMPLE_CODE, SAMPLE_VIGILANT_TEST)
        evaluated = runner.evaluate_mutants(mutants)
        report = MutationScorer.calculate_report("sample_mod", "vigilant", evaluated, 12.5)

        md = MutationScorer.generate_markdown_report(report)
        self.assertIn("# 🛡️ Mutation Sentinel Report", md)
        self.assertIn("Mutation Resilience Score", md)
        self.assertIn("Mutants Killed", md)


if __name__ == "__main__":
    unittest.main()

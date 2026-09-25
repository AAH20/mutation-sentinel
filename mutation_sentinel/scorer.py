"""
Scoring and Diagnostics Engine for Mutation-Sentinel.
Computes Mutant Kill Rate (MKR), Mutation Resilience Score (MRS), and generates audit reports.
"""

from typing import List, Dict, Any
from .models import Mutant, MutantStatus, MutationReport


class MutationScorer:
    """Evaluates mutant kill telemetry and issues quality ratings."""

    @staticmethod
    def calculate_report(
        target_name: str,
        test_name: str,
        mutants: List[Mutant],
        duration_ms: float = 0.0
    ) -> MutationReport:
        total = len(mutants)
        killed = sum(1 for m in mutants if m.status == MutantStatus.KILLED)
        survived = sum(1 for m in mutants if m.status == MutantStatus.SURVIVED)
        timed_out = sum(1 for m in mutants if m.status == MutantStatus.TIMED_OUT)
        errored = sum(1 for m in mutants if m.status == MutantStatus.ERRORED)

        effective_total = total - errored
        if effective_total > 0:
            kill_rate = (killed + timed_out) / effective_total
        else:
            kill_rate = 0.0

        mrs = round(kill_rate * 100.0, 2)

        if mrs >= 85.0:
            classification = "HIGH_ASSURANCE"
        elif mrs >= 70.0:
            classification = "MODERATE_RESILIENCE"
        else:
            classification = "HOLLOW_AI_SLOP"

        return MutationReport(
            target_module=target_name,
            test_module=test_name,
            total_mutants=total,
            killed_mutants=killed,
            survived_mutants=survived,
            timed_out_mutants=timed_out,
            errored_mutants=errored,
            mutant_kill_rate=round(kill_rate, 4),
            mutation_resilience_score=mrs,
            classification=classification,
            mutants=mutants,
            duration_ms=duration_ms
        )

    @staticmethod
    def generate_markdown_report(report: MutationReport) -> str:
        """Render high-fidelity markdown report with tables and diagnostics."""
        badge_color = "red" if report.classification == "HOLLOW_AI_SLOP" else ("yellow" if report.classification == "MODERATE_RESILIENCE" else "green")
        
        md = []
        md.append(f"# 🛡️ Mutation Sentinel Report: `{report.target_module}`\n")
        md.append(f"> **Evaluated against test suite**: `{report.test_module}`")
        md.append(f"> **Mutation Resilience Score (MRS)**: **{report.mutation_resilience_score}%** ({report.classification})\n")
        
        md.append("## 📊 Executive Summary\n")
        md.append("| Metric | Value | Meaning |")
        md.append("| :--- | :--- | :--- |")
        md.append(f"| **Total Mutants Generated** | `{report.total_mutants}` | Number of synthetic bugs injected |")
        md.append(f"| **Mutants Killed** | `{report.killed_mutants}` | Bugs caught by test suite assertions |")
        md.append(f"| **Mutants Survived** | `{report.survived_mutants}` | **Silent bugs that tests completely missed!** |")
        md.append(f"| **Mutant Kill Rate (MKR)** | `{report.mutant_kill_rate * 100:.1f}%` | Percentage of regressions detected |")
        md.append(f"| **Duration** | `{report.duration_ms:.2f}ms` | Total mutation test evaluation time |\n")

        if report.survived_mutants > 0:
            md.append("## 🚨 Survived Mutants (Hollow Test Vulnerabilities)\n")
            md.append("The following synthetic defects survived execution. The test suite passed despite the code being broken:\n")
            md.append("| Mutant ID | Operator | Line | Original Code | Mutated Bug | Risk |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for m in report.mutants:
                if m.status == MutantStatus.SURVIVED:
                    orig = m.original_code.replace("|", "\\|")
                    mut = m.mutated_code.replace("|", "\\|")
                    md.append(f"| `{m.mutant_id}` | `{m.operator.value}` | L{m.lineno} | `{orig}` | `{mut}` | **UNTESTED LOGIC** |")
            md.append("")

        if report.killed_mutants > 0:
            md.append("## ✅ Killed Mutants (Vigilant Assertions)\n")
            md.append("| Mutant ID | Operator | Line | Killing Test Case |")
            md.append("| :--- | :--- | :--- | :--- |")
            for m in report.mutants:
                if m.status == MutantStatus.KILLED:
                    killer = m.killing_test or "Unknown"
                    md.append(f"| `{m.mutant_id}` | `{m.operator.value}` | L{m.lineno} | `{killer}` |")
            md.append("")

        return "\n".join(md)

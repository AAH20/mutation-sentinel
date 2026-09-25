"""
Data models and mutation schemas for Mutation-Sentinel.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import time


class MutationOperator(str, Enum):
    ARITHMETIC = "AOR"       # Arithmetic Operator Replacement (+ -> -)
    COMPARISON = "COR"       # Comparison Operator Replacement (== -> !=, < -> >=)
    BOOLEAN = "BOR"          # Boolean Operator Replacement (and -> or, not)
    CONSTANT = "CR"          # Constant Replacement (True -> False, 0 -> 1)
    RETURN_VALUE = "RVR"     # Return Value Replacement (return x -> return None)
    STATEMENT_DELETE = "SDL" # Statement Deletion (pass)


class MutantStatus(str, Enum):
    KILLED = "KILLED"        # Test suite failed on broken code (GOOD: test is vigilant)
    SURVIVED = "SURVIVED"    # Test suite PASSED on broken code (BAD: test is hollow)
    TIMED_OUT = "TIMED_OUT"  # Caused infinite loop/timeout (treated as killed)
    ERRORED = "ERRORED"      # Syntax/runtime fatal error during mutation


@dataclass
class Mutant:
    mutant_id: str
    operator: MutationOperator
    lineno: int
    col_offset: int
    original_code: str
    mutated_code: str
    mutated_source: str
    status: MutantStatus = MutantStatus.SURVIVED
    killing_test: Optional[str] = None
    execution_time_ms: float = 0.0
    failure_message: Optional[str] = None


@dataclass
class MutationReport:
    target_module: str
    test_module: str
    total_mutants: int
    killed_mutants: int
    survived_mutants: int
    timed_out_mutants: int
    errored_mutants: int
    mutant_kill_rate: float        # 0.0 - 1.0 (Killed / (Total - Errored))
    mutation_resilience_score: float # 0.0 - 100.0%
    classification: str            # HIGH_ASSURANCE, MODERATE, HOLLOW_AI_SLOP
    mutants: List[Mutant] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0

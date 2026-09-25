"""
Mutation-Sentinel: Adversarial AST Mutation Testing Engine for AI Coding Agents.
"""

from .models import (
    MutationOperator,
    MutantStatus,
    Mutant,
    MutationReport,
)
from .mutator import ASTMutator, MutationTransformer
from .runner import MutationRunner
from .scorer import MutationScorer

__version__ = "1.0.0"
__all__ = [
    "MutationOperator",
    "MutantStatus",
    "Mutant",
    "MutationReport",
    "ASTMutator",
    "MutationTransformer",
    "MutationRunner",
    "MutationScorer",
]

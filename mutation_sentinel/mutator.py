"""
AST Mutation Generator for Mutation-Sentinel.
Traverses Python AST and systematically generates targeted adversarial mutants.
"""

import ast
import copy
from typing import List, Tuple, Optional
from .models import Mutant, MutationOperator, MutantStatus


class MutationTransformer(ast.NodeTransformer):
    """Applies a single designated mutation to an AST at a specified node coordinate."""

    def __init__(self, target_lineno: int, target_col: int, op_type: MutationOperator):
        self.target_lineno = target_lineno
        self.target_col = target_col
        self.op_type = op_type
        self.applied = False

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.generic_visit(node)
        if not self.applied and node.lineno == self.target_lineno and node.col_offset == self.target_col:
            if isinstance(node.op, ast.Add):
                node.op = ast.Sub()
                self.applied = True
            elif isinstance(node.op, ast.Sub):
                node.op = ast.Add()
                self.applied = True
            elif isinstance(node.op, ast.Mult):
                node.op = ast.FloorDiv()
                self.applied = True
            elif isinstance(node.op, ast.FloorDiv) or isinstance(node.op, ast.Div):
                node.op = ast.Mult()
                self.applied = True
        return node

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        self.generic_visit(node)
        if not self.applied and node.lineno == self.target_lineno and node.col_offset == self.target_col:
            if node.ops:
                op = node.ops[0]
                if isinstance(op, ast.Eq):
                    node.ops[0] = ast.NotEq()
                    self.applied = True
                elif isinstance(op, ast.NotEq):
                    node.ops[0] = ast.Eq()
                    self.applied = True
                elif isinstance(op, ast.Lt):
                    node.ops[0] = ast.GtE()
                    self.applied = True
                elif isinstance(op, ast.LtE):
                    node.ops[0] = ast.Gt()
                    self.applied = True
                elif isinstance(op, ast.Gt):
                    node.ops[0] = ast.LtE()
                    self.applied = True
                elif isinstance(op, ast.GtE):
                    node.ops[0] = ast.Lt()
                    self.applied = True
        return node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.generic_visit(node)
        if not self.applied and node.lineno == self.target_lineno and node.col_offset == self.target_col:
            if isinstance(node.op, ast.And):
                node.op = ast.Or()
                self.applied = True
            elif isinstance(node.op, ast.Or):
                node.op = ast.And()
                self.applied = True
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        self.generic_visit(node)
        if not self.applied and hasattr(node, "lineno") and node.lineno == self.target_lineno and node.col_offset == self.target_col:
            if isinstance(node.value, bool):
                node.value = not node.value
                self.applied = True
            elif isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                node.value = 0 if node.value != 0 else 1
                self.applied = True
        return node

    def visit_Return(self, node: ast.Return) -> ast.AST:
        self.generic_visit(node)
        if not self.applied and node.lineno == self.target_lineno and node.col_offset == self.target_col:
            if node.value is not None and not (isinstance(node.value, ast.Constant) and node.value.value is None):
                node.value = ast.Constant(value=None)
                self.applied = True
        return node


class ASTMutator:
    """Discovers mutation points and synthesizes mutant source codes."""

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.tree = ast.parse(source_code)
        self.source_lines = source_code.splitlines()

    def discover_mutation_points(self) -> List[Tuple[MutationOperator, int, int, str]]:
        """Scan AST for viable adversarial mutation sites."""
        points = []
        for node in ast.walk(self.tree):
            if not hasattr(node, "lineno") or not hasattr(node, "col_offset"):
                continue

            lineno = node.lineno
            col = node.col_offset
            orig_line = self.source_lines[lineno - 1] if 0 <= lineno - 1 < len(self.source_lines) else ""

            if isinstance(node, ast.BinOp):
                if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv)):
                    points.append((MutationOperator.ARITHMETIC, lineno, col, orig_line.strip()))

            elif isinstance(node, ast.Compare):
                if node.ops and isinstance(node.ops[0], (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                    points.append((MutationOperator.COMPARISON, lineno, col, orig_line.strip()))

            elif isinstance(node, ast.BoolOp):
                if isinstance(node.op, (ast.And, ast.Or)):
                    points.append((MutationOperator.BOOLEAN, lineno, col, orig_line.strip()))

            elif isinstance(node, ast.Constant):
                if isinstance(node.value, bool) or (isinstance(node.value, (int, float)) and not isinstance(node.value, bool)):
                    points.append((MutationOperator.CONSTANT, lineno, col, orig_line.strip()))

            elif isinstance(node, ast.Return):
                if node.value is not None:
                    points.append((MutationOperator.RETURN_VALUE, lineno, col, orig_line.strip()))

        return points

    def generate_mutants(self) -> List[Mutant]:
        """Generate distinct mutant programs."""
        points = self.discover_mutation_points()
        mutants = []

        for idx, (op_type, lineno, col, orig_line) in enumerate(points, start=1):
            mutant_id = f"MUT_{op_type.value}_{idx:03d}"
            # Clone AST
            cloned_tree = copy.deepcopy(self.tree)
            transformer = MutationTransformer(lineno, col, op_type)
            mutated_ast = transformer.visit(cloned_tree)
            ast.fix_missing_locations(mutated_ast)

            if transformer.applied:
                try:
                    mutated_source = ast.unparse(mutated_ast)
                    mut_lines = mutated_source.splitlines()
                    mut_line = mut_lines[lineno - 1] if 0 <= lineno - 1 < len(mut_lines) else "[altered]"
                    mutants.append(Mutant(
                        mutant_id=mutant_id,
                        operator=op_type,
                        lineno=lineno,
                        col_offset=col,
                        original_code=orig_line,
                        mutated_code=mut_line.strip(),
                        mutated_source=mutated_source,
                        status=MutantStatus.SURVIVED
                    ))
                except Exception:
                    pass

        return mutants

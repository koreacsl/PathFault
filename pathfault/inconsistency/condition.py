import ast
from z3 import *


class _ConditionType:
    def __init__(self, condition_str: str, not_condition: bool = False):
        self.condition_str = condition_str
        self.not_condition = not_condition

    def apply_with_not(self, condition: BoolRef) -> BoolRef:
        """Add Not() if NOT condition is True"""
        return Not(condition) if self.not_condition else condition

    def to_ast(self) -> ast.Call:
        """Convert Condition object to AST node"""
        return ast.Call(
            func=ast.Name(id=self.__class__.__name__, ctx=ast.Load()),
            args=[ast.Str(self.condition_str)],
            keywords=[ast.keyword(arg='not_condition', value=ast.NameConstant(self.not_condition))]
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.condition_str}, NOT={self.not_condition})"


# Equal condition type (exact match)
class EqualType(_ConditionType):
    def apply(self, expr: ExprRef) -> BoolRef:
        return self.apply_with_not(expr == StringVal(self.condition_str))


    def __repr__(self) -> str:
        return f"EqualType(condition_str='{self.condition_str}', NOT={self.not_condition})"


# Suffix condition type
class SuffixType(_ConditionType):
    def apply(self, expr: ExprRef) -> BoolRef:
        return self.apply_with_not(SuffixOf(StringVal(self.condition_str), expr))

    def __repr__(self) -> str:
        return f"SuffixType(condition_str='{self.condition_str}', NOT={self.not_condition})"


# Prefix condition type
class PrefixType(_ConditionType):
    def apply(self, expr: ExprRef) -> BoolRef:
        return self.apply_with_not(PrefixOf(StringVal(self.condition_str), expr))

    def __repr__(self) -> str:
        return f"PrefixType(condition_str='{self.condition_str}', NOT={self.not_condition})"


# Contains condition type
class ContainsType(_ConditionType):

    def apply(self, expr: ExprRef) -> BoolRef:
        # Handle escape characters
        condition_str = self.condition_str.encode('unicode_escape').decode('utf-8')
        condition = Contains(expr, StringVal(condition_str))
        return self.apply_with_not(condition)

    def __repr__(self) -> str:
        return f"ContainsType(condition_str='{self.condition_str}', NOT={self.not_condition})"


# Check for slash (`/`) after delimiter
class HasSlashAfterDelimiterType(_ConditionType):
    def apply(self, expr: ExprRef) -> BoolRef:
        iA = IndexOf(expr, StringVal(self.condition_str), IntVal(0))
        iSlash = IndexOf(expr, StringVal("/"), iA + 1)
        condition = iSlash != -1 # Return True if slash exists
        return self.apply_with_not(condition)

    def __repr__(self) -> str:
        return f"HasSlashAfterDelimiterType('{self.condition_str}', NOT={self.not_condition})"

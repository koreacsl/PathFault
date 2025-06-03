import ast
from typing import List, Tuple
from .condition import _ConditionType
from z3 import *

from .custom_z3_expression import ReplaceAll


class _TransformationType:
    def apply(self, expr: ExprRef) -> ExprRef:
        """Handle transformation logic with common interface"""
        raise NotImplementedError("Subclasses must implement 'apply' method")

    def apply_for_validation(self, expr: ExprRef) -> ExprRef:
        """Handle transformation logic with common interface"""
        raise NotImplementedError("Subclasses must implement 'apply_for_validation' method")

    def to_ast(self) -> ast.Call:
        raise NotImplementedError("Subclasses must implement 'to_ast' method")


# 변환 규칙 클래스
class Transformation:
    def __init__(self, name: str, transformation_type: _TransformationType, conditions: List[_ConditionType] = None):
        self.name: str = name
        self.transformation_type = transformation_type
        self.conditions = conditions if conditions else []

    def apply_transformation(self, expr: ExprRef) -> Tuple[ExprRef, BoolRef]:
        """
        - Return 1: Transformed ExprRef
        - Return 2: BoolRef condition that must be satisfied
        """
        transformed_output = self.transformation_type.apply(expr)

        if not self.conditions:
            return transformed_output, BoolVal(True)  # Return True if no conditions

        # Combine all conditions with AND if conditions exist
        condition_results = [condition.apply(expr) for condition in self.conditions]
        combined_conditions = And(*condition_results)

        return transformed_output, combined_conditions

    def apply_transformation_for_validation(self, expr: ExprRef) -> Tuple[ExprRef, BoolRef]:
        """
        - Return 1: Transformed ExprRef
        - Return 2: BoolRef condition that must be satisfied
        """
        transformed_output = self.transformation_type.apply_for_validation(expr)

        if not self.conditions:
            return transformed_output, BoolVal(True)  # Return True if no conditions

        # Combine all conditions with AND if conditions exist
        condition_results = [condition.apply(expr) for condition in self.conditions]
        combined_conditions = And(*condition_results)

        return transformed_output, combined_conditions

    def to_ast(self) -> ast.Call:
        return ast.Call(
            func=ast.Name(id='Transformation', ctx=ast.Load()),
            args=[
                ast.Str(self.name),
                self.transformation_type.to_ast(),
                ast.List(
                    elts=[
                        condition.to_ast()
                        for condition in self.conditions
                    ],
                    ctx=ast.Load()
                )
            ],
            keywords=[]
        )



class ReplaceTransformation(_TransformationType):
    def __init__(self, target_str: str, replace_str: str):
        self.target_str = target_str
        self.replace_str = replace_str

    def apply(self, expr: ExprRef) -> ExprRef:
        return Replace(expr, StringVal(self.target_str), StringVal(self.replace_str))

    def apply_for_validation(self, expr: ExprRef) -> ExprRef:
        return ReplaceAll(expr, StringVal(self.target_str), StringVal(self.replace_str))

    def to_ast(self) -> ast.Call:
        return ast.Call(
            func=ast.Name(id='ReplaceTransformation', ctx=ast.Load()),
            args=[ast.Str(self.target_str), ast.Str(self.replace_str)],
            keywords=[]
        )

    def __eq__(self, other):
        if isinstance(other, ReplaceTransformation):
            return self.target_str == other.target_str and self.replace_str == other.replace_str
        return False

    def __hash__(self):
        return hash((self.target_str, self.replace_str))

    def __repr__(self):
        return f"ReplaceTransformation('{self.target_str}' → '{self.replace_str}')"


class SubStringUntilTransformation(_TransformationType):
    """
    Extract substring from offset to the position of a specific delimiter
    - Assumes delimiter always exists
    """
    def __init__(self, offset: int, delimiter: str):
        self.offset = offset
        self.delimiter = delimiter

    def apply(self, expr: ExprRef) -> ExprRef:
        delimiter_index = IndexOf(expr, StringVal(self.delimiter))
        length_expr = delimiter_index - self.offset

        return SubString(expr, self.offset, length_expr)

    def apply_for_validation(self, expr: ExprRef) -> ExprRef:
        delimiter_index = IndexOf(expr, StringVal(self.delimiter))
        length_expr = delimiter_index - self.offset

        return SubString(expr, self.offset, length_expr)

    def to_ast(self) -> ast.Call:
        return ast.Call(
            func=ast.Name(id='SubStringUntilTransformation', ctx=ast.Load()),
            args=[ast.Num(self.offset), ast.Str(self.delimiter)],
            keywords=[]
        )

    def __eq__(self, other):
        return isinstance(other, SubStringUntilTransformation) and \
               self.offset == other.offset and self.delimiter == other.delimiter

    def __hash__(self):
        return hash((self.offset, self.delimiter))

    def __repr__(self):
        return f"SubStringUntilTransformation(offset={self.offset}, delimiter='{self.delimiter}')"


class SubStringOffsetTransformation(_TransformationType):
    """
    Perform SubString(expr, offset, Length(expr) - offset) with only offset provided
    """
    def __init__(self, offset: int):
        self.offset = offset

    def apply(self, expr: ExprRef) -> ExprRef:
        return SubString(expr, self.offset, Length(expr) - self.offset)

    def apply_for_validation(self, expr: ExprRef) -> ExprRef:
        return SubString(expr, self.offset, Length(expr) - self.offset)

    def to_ast(self) -> ast.Call:
        return ast.Call(
            func=ast.Name(id='SubStringOffsetTransformation', ctx=ast.Load()),
            args=[ast.Constant(self.offset)],
            keywords=[]
        )

    def __eq__(self, other):
        if isinstance(other, SubStringOffsetTransformation):
            return self.offset == other.offset
        return False

    def __hash__(self):
        return hash(self.offset)

    def __repr__(self):
        return f"SubStringOffsetTransformation(offset={self.offset})"


class NormalizationTransformation(_TransformationType):
    def __init__(self, normalization_str: str):
        """
        :param normalization_str: String to normalize (e.g., "/../", "./", "%2e")
        """
        self.normalization_str = normalization_str

    def apply(self, input_url) -> ExprRef:
        """
        Remove or transform normalization_str in the string
        - Supports both Z3 ExprRef and regular strings (no isinstance check)
        """
        norm_str = self.normalization_str

        # Z3 기반 변환 로직
        transformed_output = Concat(
            SubString(
                input_url,
                0,
                LastIndexOf(SubString(input_url, 0, IndexOf(input_url, norm_str)), "/") + 1
            ),
            SubString(
                input_url,
                IndexOf(input_url, norm_str) + len(norm_str),
                Length(input_url) - (IndexOf(input_url, norm_str) + len(norm_str))
            )
        )
        return transformed_output

    def apply_for_validation(self, input_url: ExprRef) -> ExprRef:
        """
        Remove or transform normalization_str in the string
        """
        norm_str = self.normalization_str

        transformed_output = Concat(
            SubString(
                input_url,
                0,
                LastIndexOf(SubString(input_url, 0, IndexOf(input_url, norm_str)), "/") + 1
            ),
            SubString(
                input_url,
                IndexOf(input_url, norm_str) + len(norm_str),
                Length(input_url) - (IndexOf(input_url, norm_str) + len(norm_str))
            )
        )
        return transformed_output


    def to_ast(self) -> ast.Call:
        return ast.Call(
            func=ast.Name(id='NormalizationTransformation', ctx=ast.Load()),
            args=[ast.Str(self.normalization_str)],
            keywords=[]
        )

    def __eq__(self, other):
        if isinstance(other, NormalizationTransformation):
            return self.normalization_str == other.normalization_str
        return False

    def __hash__(self):
        return hash(self.normalization_str)

    def __repr__(self):
        return f"NormalizationTransformation('{self.normalization_str}')"


class AddSuffixTransformation(_TransformationType):
    def __init__(self, suffix_str: str):
        self.suffix_str = suffix_str

    def apply(self, expr: ExprRef) -> ExprRef:
        return Concat(expr, StringVal(self.suffix_str))

    def apply_for_validation(self, expr: ExprRef) -> ExprRef:
        return Concat(expr, StringVal(self.suffix_str))

    def to_ast(self) -> ast.Call:
        return ast.Call(
            func=ast.Name(id='AddSuffixTransformation', ctx=ast.Load()),
            args=[ast.Str(self.suffix_str)],
            keywords=[]
        )

    def __eq__(self, other):
        return isinstance(other, AddSuffixTransformation) and self.suffix_str == other.suffix_str

    def __hash__(self):
        return hash(self.suffix_str)

    def __repr__(self):
        return f"AddSuffixTransformation('{self.suffix_str}')"


class AddPrefixTransformation(_TransformationType):
    def __init__(self, prefix_str: str):
        self.prefix_str = prefix_str

    def apply(self, expr: ExprRef) -> ExprRef:
        return Concat(StringVal(self.prefix_str), expr)

    def apply_for_validation(self, expr: ExprRef) -> ExprRef:
        return Concat(StringVal(self.prefix_str), expr)

    def to_ast(self) -> ast.Call:
        return ast.Call(
            func=ast.Name(id='AddPrefixTransformation', ctx=ast.Load()),
            args=[ast.Str(self.prefix_str)],
            keywords=[]
        )

    def __eq__(self, other):
        return isinstance(other, AddPrefixTransformation) and self.prefix_str == other.prefix_str

    def __hash__(self):
        return hash(self.prefix_str)

    def __repr__(self):
        return f"AddPrefixTransformation('{self.prefix_str}')"


class DelimiterSlashSplitTransformation(_TransformationType):
    def __init__(self, delimiter: str):
        self.delimiter = delimiter

    def apply(self, expr: ExprRef) -> ExprRef:
        iA = IndexOf(expr, StringVal(self.delimiter), IntVal(0))
        iSlash = IndexOf(expr, StringVal("/"), iA + 1)

        return Concat(
            SubString(expr, 0, iA),
            SubString(expr, iSlash + 1, Length(expr) - (iSlash + 1))
        )

    def apply_for_validation(self, expr: ExprRef) -> ExprRef:
        iA = IndexOf(expr, StringVal(self.delimiter), IntVal(0))
        iSlash = IndexOf(expr, StringVal("/"), iA + 1)

        return Concat(
            SubString(expr, 0, iA),
            SubString(expr, iSlash + 1, Length(expr) - (iSlash + 1))
        )

    def to_ast(self) -> ast.Call:
        return ast.Call(
            func=ast.Name(id='DelimiterSlashSplitTransformation', ctx=ast.Load()),
            args=[ast.Str(self.delimiter)],
            keywords=[]
        )

    def __eq__(self, other):
        return isinstance(other, DelimiterSlashSplitTransformation) and self.delimiter == other.delimiter

    def __hash__(self):
        return hash(self.delimiter)

    def __repr__(self):
        return f"DelimiterSlashSplitTransformation('{self.delimiter}')"


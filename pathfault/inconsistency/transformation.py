import ast
from typing import List, Tuple
from .condition import _ConditionType
from z3 import *

from .custom_z3_expression import ReplaceAll


class _TransformationType:
    def apply(self, expr: ExprRef) -> ExprRef:
        """공통 인터페이스로 변환 로직을 처리"""
        raise NotImplementedError("Subclasses must implement 'apply' method")

    def apply_for_validation(self, expr: ExprRef) -> ExprRef:
        """공통 인터페이스로 변환 로직을 처리"""
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
        - 반환값 1: 변환된 ExprRef
        - 반환값 2: 해당 변환이 만족해야 할 BoolRef (조건)
        """
        transformed_output = self.transformation_type.apply(expr)

        if not self.conditions:
            return transformed_output, BoolVal(True)  # 조건이 없는 경우 항상 True 반환

        # 조건이 있는 경우, 모든 조건을 AND로 묶기
        condition_results = [condition.apply(expr) for condition in self.conditions]
        combined_conditions = And(*condition_results)

        return transformed_output, combined_conditions

    def apply_transformation_for_validation(self, expr: ExprRef) -> Tuple[ExprRef, BoolRef]:
        """
        - 반환값 1: 변환된 ExprRef
        - 반환값 2: 해당 변환이 만족해야 할 BoolRef (조건)
        """
        transformed_output = self.transformation_type.apply_for_validation(expr)

        if not self.conditions:
            return transformed_output, BoolVal(True)  # 조건이 없는 경우 항상 True 반환

        # 조건이 있는 경우, 모든 조건을 AND로 묶기
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
                        condition.to_ast()  # ✅ 각 Condition이 to_ast() 호출하도록 수정
                        for condition in self.conditions
                    ],
                    ctx=ast.Load()
                )
            ],
            keywords=[]
        )



# T-시리즈 변환 타입 (상속 구조)
class ReplaceTransformation(_TransformationType):
    def __init__(self, target_str: str, replace_str: str):
        self.target_str = target_str
        self.replace_str = replace_str

    def apply(self, expr: ExprRef) -> ExprRef:
        """
        Z3의 Replace() 기반 Replace Transformation 로직
        """
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
    offset부터 특정 delimiter를 찾은 위치까지 substring을 추출
    - delimiter가 반드시 존재한다고 가정
    """
    def __init__(self, offset: int, delimiter: str):
        self.offset = offset
        self.delimiter = delimiter

    def apply(self, expr: ExprRef) -> ExprRef:
        """
        Z3에서 substring(expr, offset, length)
        - length = IndexOf(expr, delimiter, offset) - offset
        """
        delimiter_index = IndexOf(expr, StringVal(self.delimiter))
        length_expr = delimiter_index - self.offset

        return SubString(expr, self.offset, length_expr)

    def apply_for_validation(self, expr: ExprRef) -> ExprRef:
        """
        Z3에서 substring(expr, offset, length)
        - length = IndexOf(expr, delimiter, offset) - offset
        """
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
    offset만 입력받아 SubString(expr, offset, Length(expr) - offset)을 수행
    """
    def __init__(self, offset: int):
        self.offset = offset

    def apply(self, expr: ExprRef) -> ExprRef:
        """
        SubString(expr, offset, Length(expr) - offset) 을 수행.
        """
        return SubString(expr, self.offset, Length(expr) - self.offset)

    def apply_for_validation(self, expr: ExprRef) -> ExprRef:
        """
        SubString(expr, offset, Length(expr) - offset) 을 수행.
        """
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
        :param normalization_str: 정규화 대상 문자열 (예: "/../", "./", "%2e")
        """
        self.normalization_str = normalization_str

    def apply(self, input_url) -> ExprRef:
        """
        문자열 내에서 normalization_str을 제거 또는 특정 규칙으로 변환
        - Z3 ExprRef 및 일반 문자열을 모두 지원 (isinstance 검사 없이)
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
        문자열 내에서 normalization_str을 제거 또는 특정 규칙으로 변환
        - Z3 ExprRef 및 일반 문자열을 모두 지원 (isinstance 검사 없이)
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
# =========================
# 🔹 Transformation 1: 구분자 이후 슬래시가 있는 경우
# =========================
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


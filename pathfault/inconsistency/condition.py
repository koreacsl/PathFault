import ast
from z3 import *


# 공통 Condition Type 부모 클래스
class _ConditionType:
    def __init__(self, condition_str: str, not_condition: bool = False):
        self.condition_str = condition_str
        self.not_condition = not_condition

    def apply_with_not(self, condition: BoolRef) -> BoolRef:
        """NOT 조건이 True일 경우 Not()을 추가"""
        return Not(condition) if self.not_condition else condition

    def to_ast(self) -> ast.Call:
        """Condition 객체를 AST 노드로 변환"""
        return ast.Call(
            func=ast.Name(id=self.__class__.__name__, ctx=ast.Load()),
            args=[ast.Str(self.condition_str)],
            keywords=[ast.keyword(arg='not_condition', value=ast.NameConstant(self.not_condition))]
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.condition_str}, NOT={self.not_condition})"


# Equal 조건 타입 (완전 일치)
class EqualType(_ConditionType):
    def apply(self, expr: ExprRef) -> BoolRef:
        return self.apply_with_not(expr == StringVal(self.condition_str))


    def __repr__(self) -> str:
        return f"EqualType(condition_str='{self.condition_str}', NOT={self.not_condition})"


# Suffix 조건 타입
class SuffixType(_ConditionType):
    def apply(self, expr: ExprRef) -> BoolRef:
        return self.apply_with_not(SuffixOf(StringVal(self.condition_str), expr))

    def __repr__(self) -> str:
        return f"SuffixType(condition_str='{self.condition_str}', NOT={self.not_condition})"


# Prefix 조건 타입
class PrefixType(_ConditionType):
    def apply(self, expr: ExprRef) -> BoolRef:
        return self.apply_with_not(PrefixOf(StringVal(self.condition_str), expr))

    def __repr__(self) -> str:
        return f"PrefixType(condition_str='{self.condition_str}', NOT={self.not_condition})"


# Contains 조건 타입
class ContainsType(_ConditionType):

    def apply(self, expr: ExprRef) -> BoolRef:
        # 🔥 이스케이프 문자 처리 추가
        condition_str = self.condition_str.encode('unicode_escape').decode('utf-8')
        condition = Contains(expr, StringVal(condition_str))
        return self.apply_with_not(condition)

    def __repr__(self) -> str:
        return f"ContainsType(condition_str='{self.condition_str}', NOT={self.not_condition})"


# 🔹 Delimiter 이후 슬래시 (`/`) 존재 여부 확인
class HasSlashAfterDelimiterType(_ConditionType):
    def apply(self, expr: ExprRef) -> BoolRef:
        iA = IndexOf(expr, StringVal(self.condition_str), IntVal(0))
        iSlash = IndexOf(expr, StringVal("/"), iA + 1)
        condition = iSlash != -1  # 슬래시가 존재하는 경우 True 반환
        return self.apply_with_not(condition)

    def __repr__(self) -> str:
        return f"HasSlashAfterDelimiterType('{self.condition_str}', NOT={self.not_condition})"

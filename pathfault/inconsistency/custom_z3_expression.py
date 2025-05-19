from z3 import Solver, String, Int, StringVal, Length, SubString


def remove_shared_prefix(base_str_val, shared_val):
    s = Solver()
    base_s = String('base_s')
    s.add(base_s == StringVal(base_str_val))

    len_shared = len(shared_val)
    s.add(Length(base_s) >= len_shared)
    s.add(SubString(base_s, 0, len_shared) == StringVal(shared_val))

    diff = SubString(base_s, len_shared, Length(base_s) - len_shared)
    if s.check().r == 1:  # sat
        return s.model().eval(diff).as_string()
    return None


def remove_shared_suffix(base_str_val, shared_val):
    s = Solver()
    base_s = String('base_s')
    i = Int('i')
    s.add(base_s == StringVal(base_str_val))

    len_shared = len(shared_val)
    s.add(i + len_shared == Length(base_s))
    s.add(SubString(base_s, i, len_shared) == StringVal(shared_val))

    diff = SubString(base_s, 0, i)
    if s.check().r == 1:  # sat
        return s.model().eval(diff).as_string()
    return None


# 예시: /tmp1/Hello/tmp2 에서
#  1) /tmp1/ (prefix) 제거 -> Hello/tmp2
#  2) Hello/tmp2 에서 /tmp2 (suffix) 제거 -> Hello
def remove_prefix_then_suffix(base_str_val, prefix_val, suffix_val):
    # 1단계: 앞에서 prefix 제거
    after_prefix = remove_shared_prefix(base_str_val, prefix_val)
    if after_prefix is None:
        return None

    # 2단계: 위 결과에서 suffix 제거
    after_suffix = remove_shared_suffix(after_prefix, suffix_val)

    return after_suffix

from z3 import *

# ✅ 입력값이 문자열이면 StringVal로 변환하는 함수
def to_z3_string(val):
    return StringVal(val) if isinstance(val, str) else val

# ✅ 내부적으로 사용할 ReplaceRecursive 함수 (_ReplaceRecursive)
_ReplaceRecursive = RecFunction('_ReplaceRecursive', StringSort(), StringSort(), StringSort(), StringSort())

# 재귀 호출에 사용할 변수
s_ = Var(0, StringSort())  # 원본 문자열
src_ = Var(1, StringSort())  # 변경할 패턴
dst_ = Var(2, StringSort())  # 변경 후 문자열

# If 조건:
# s_ 안에 src_가 있으면 -> Replace() 실행 후 나머지에 대해 _ReplaceRecursive() 재귀 호출
# 없으면 -> s_ 그대로 반환
body = If(
    Contains(s_, src_),
    _ReplaceRecursive(Replace(s_, src_, dst_), src_, dst_),
    s_
)

# RecFunction 등록
RecAddDefinition(_ReplaceRecursive, (s_, src_, dst_), body)


# ✅ 최종 ReplaceRecursive: Python 문자열도 자동 변환
def ReplaceRecursive(s, src, dst):
    return _ReplaceRecursive(to_z3_string(s), to_z3_string(src), to_z3_string(dst))


# ✅ 모든 발생을 한 번에 변환하는 ReplaceAll (모든 매칭 처리)
def ReplaceAll(s, src, dst):
    """
    한 번에 모든 `src`를 `dst`로 변환하는 ReplaceAll.
    - 이미 변환된 문자가 추가적으로 변환되지 않도록 설계.
    """

    s, src, dst = to_z3_string(s), to_z3_string(src), to_z3_string(dst)

    # 1. src → '__TEMP__' (임시 치환)
    s = ReplaceRecursive(s, src, "__TEMP__")

    # 2. '__TEMP__' → dst (최종 변환)
    s = ReplaceRecursive(s, "__TEMP__", dst)

    return s

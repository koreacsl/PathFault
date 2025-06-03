from z3 import *


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


# Example: For /tmp1/Hello/tmp2
#  1) Remove /tmp1/ (prefix) -> Hello/tmp2
#  2) Remove /tmp2 (suffix) from Hello/tmp2 -> Hello
def remove_prefix_then_suffix(base_str_val, prefix_val, suffix_val):
    # Step 1: Remove prefix
    after_prefix = remove_shared_prefix(base_str_val, prefix_val)
    if after_prefix is None:
        return None

    # Step 2: Remove suffix from result
    after_suffix = remove_shared_suffix(after_prefix, suffix_val)

    return after_suffix


# Convert input to StringVal if string
def to_z3_string(val):
    return StringVal(val) if isinstance(val, str) else val

# Internal ReplaceRecursive function
_ReplaceRecursive = RecFunction('_ReplaceRecursive', StringSort(), StringSort(), StringSort(), StringSort())

# Variables for recursive call
s_ = Var(0, StringSort()) # Source string
src_ = Var(1, StringSort())  # Pattern to replace
dst_ = Var(2, StringSort())  # Replacement string

# If condition:
# If src_ is in s_, apply Replace() and recursively call _ReplaceRecursive() on remainder
# Otherwise, return s_ unchanged
body = If(
    Contains(s_, src_),
    _ReplaceRecursive(Replace(s_, src_, dst_), src_, dst_),
    s_
)

# Register RecFunction
RecAddDefinition(_ReplaceRecursive, (s_, src_, dst_), body)


# Final ReplaceRecursive: Auto-convert Python strings
def ReplaceRecursive(s, src, dst):
    return _ReplaceRecursive(to_z3_string(s), to_z3_string(src), to_z3_string(dst))


# Replace all occurrences at once (handles all matches)
def ReplaceAll(s, src, dst):
    """
    Replace all `src` with `dst` in one go.
    - Designed to prevent re-conversion of already replaced strings.
    """

    s, src, dst = to_z3_string(s), to_z3_string(src), to_z3_string(dst)

    # 1. Replace src with '__TEMP__' (temporary substitution)
    s = ReplaceRecursive(s, src, "__TEMP__")

    # 2. Replace '__TEMP__' with dst (final substitution)
    s = ReplaceRecursive(s, "__TEMP__", dst)

    return s

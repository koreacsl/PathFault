from typing import List, Iterable
from itertools import combinations

from .condition import ContainsType
from .transformation import NormalizationTransformation, Transformation

ENCODING_MAP = {
    "\x00": "%00", "\x01": "%01", "\x02": "%02", "\x03": "%03", "\x04": "%04", "\x05": "%05", "\x06": "%06", "\x07": "%07",
    "\x08": "%08", "\x09": "%09", "\x0A": "%0A", "\x0B": "%0B", "\x0C": "%0C", "\x0D": "%0D", "\x0E": "%0E", "\x0F": "%0F",
    "\x10": "%10", "\x11": "%11", "\x12": "%12", "\x13": "%13", "\x14": "%14", "\x15": "%15", "\x16": "%16", "\x17": "%17",
    "\x18": "%18", "\x19": "%19", "\x1A": "%1A", "\x1B": "%1B", "\x1C": "%1C", "\x1D": "%1D", "\x1E": "%1E", "\x1F": "%1F",
    " ": "%20", "!": "%21", "\"": "%22", "#": "%23", "$": "%24", "%": "%25", "&": "%26", "'": "%27",
    "(": "%28", ")": "%29", "*": "%2A", "+": "%2B", ",": "%2C", "-": "%2D", ".": "%2E", "/": "%2F",
    "0": "%30", "1": "%31", "2": "%32", "3": "%33", "4": "%34", "5": "%35", "6": "%36", "7": "%37",
    "8": "%38", "9": "%39", ":": "%3A", ";": "%3B", "<": "%3C", "=": "%3D", ">": "%3E", "?": "%3F",
    "@": "%40", "A": "%41", "B": "%42", "C": "%43", "D": "%44", "E": "%45", "F": "%46", "G": "%47",
    "H": "%48", "I": "%49", "J": "%4A", "K": "%4B", "L": "%4C", "M": "%4D", "N": "%4E", "O": "%4F",
    "P": "%50", "Q": "%51", "R": "%52", "S": "%53", "T": "%54", "U": "%55", "V": "%56", "W": "%57",
    "X": "%58", "Y": "%59", "Z": "%5A", "[": "%5B", "\\": "%5C", "]": "%5D", "^": "%5E", "_": "%5F",
    "`": "%60", "a": "%61", "b": "%62", "c": "%63", "d": "%64", "e": "%65", "f": "%66", "g": "%67",
    "h": "%68", "i": "%69", "j": "%6A", "k": "%6B", "l": "%6C", "m": "%6D", "n": "%6E", "o": "%6F",
    "p": "%70", "q": "%71", "r": "%72", "s": "%73", "t": "%74", "u": "%75", "v": "%76", "w": "%77",
    "x": "%78", "y": "%79", "z": "%7A", "{": "%7B", "|": "%7C", "}": "%7D", "~": "%7E", "\x7F": "%7F",
    "\x80": "%80", "\x81": "%81", "\x82": "%82", "\x83": "%83", "\x84": "%84", "\x85": "%85", "\x86": "%86", "\x87": "%87",
    "\x88": "%88", "\x89": "%89", "\x8A": "%8A", "\x8B": "%8B", "\x8C": "%8C", "\x8D": "%8D", "\x8E": "%8E", "\x8F": "%8F",
    "\x90": "%90", "\x91": "%91", "\x92": "%92", "\x93": "%93", "\x94": "%94", "\x95": "%95", "\x96": "%96", "\x97": "%97",
    "\x98": "%98", "\x99": "%99", "\x9A": "%9A", "\x9B": "%9B", "\x9C": "%9C", "\x9D": "%9D", "\x9E": "%9E", "\x9F": "%9F",
    "\xA0": "%A0", "\xA1": "%A1", "\xA2": "%A2", "\xA3": "%A3", "\xA4": "%A4", "\xA5": "%A5", "\xA6": "%A6", "\xA7": "%A7",
    "\xA8": "%A8", "\xA9": "%A9", "\xAA": "%AA", "\xAB": "%AB", "\xAC": "%AC", "\xAD": "%AD", "\xAE": "%AE", "\xAF": "%AF",
    "\xB0": "%B0", "\xB1": "%B1", "\xB2": "%B2", "\xB3": "%B3", "\xB4": "%B4", "\xB5": "%B5", "\xB6": "%B6", "\xB7": "%B7",
    "\xB8": "%B8", "\xB9": "%B9", "\xBA": "%BA", "\xBB": "%BB", "\xBC": "%BC", "\xBD": "%BD", "\xBE": "%BE", "\xBF": "%BF",
    "\xC0": "%C0", "\xC1": "%C1", "\xC2": "%C2", "\xC3": "%C3", "\xC4": "%C4", "\xC5": "%C5", "\xC6": "%C6", "\xC7": "%C7",
    "\xC8": "%C8", "\xC9": "%C9", "\xCA": "%CA", "\xCB": "%CB", "\xCC": "%CC", "\xCD": "%CD", "\xCE": "%CE", "\xCF": "%CF",
    "\xD0": "%D0", "\xD1": "%D1", "\xD2": "%D2", "\xD3": "%D3", "\xD4": "%D4", "\xD5": "%D5", "\xD6": "%D6", "\xD7": "%D7",
    "\xD8": "%D8", "\xD9": "%D9", "\xDA": "%DA", "\xDB": "%DB", "\xDC": "%DC", "\xDD": "%DD", "\xDE": "%DE", "\xDF": "%DF",
    "\xE0": "%E0", "\xE1": "%E1", "\xE2": "%E2", "\xE3": "%E3", "\xE4": "%E4", "\xE5": "%E5", "\xE6": "%E6", "\xE7": "%E7",
    "\xE8": "%E8", "\xE9": "%E9", "\xEA": "%EA", "\xEB": "%EB", "\xEC": "%EC", "\xED": "%ED", "\xEE": "%EE", "\xEF": "%EF",
    "\xF0": "%F0", "\xF1": "%F1", "\xF2": "%F2", "\xF3": "%F3", "\xF4": "%F4", "\xF5": "%F5", "\xF6": "%F6", "\xF7": "%F7",
    "\xF8": "%F8", "\xF9": "%F9", "\xFA": "%FA", "\xFB": "%FB", "\xFC": "%FC", "\xFD": "%FD", "\xFE": "%FE", "\xFF": "%FF"
}

DECODING_MAP = {
    "%00": "\x00", "%01": "\x01", "%02": "\x02", "%03": "\x03", "%04": "\x04", "%05": "\x05", "%06": "\x06", "%07": "\x07",
    "%08": "\x08", "%09": "\x09", "%0A": "\x0A", "%0B": "\x0B", "%0C": "\x0C", "%0D": "\x0D", "%0E": "\x0E", "%0F": "\x0F",
    "%10": "\x10", "%11": "\x11", "%12": "\x12", "%13": "\x13", "%14": "\x14", "%15": "\x15", "%16": "\x16", "%17": "\x17",
    "%18": "\x18", "%19": "\x19", "%1A": "\x1A", "%1B": "\x1B", "%1C": "\x1C", "%1D": "\x1D", "%1E": "\x1E", "%1F": "\x1F",
    "%20": " ", "%21": "!", "%22": "\"", "%23": "#", "%24": "$", "%25": "%", "%26": "&", "%27": "'",
    "%28": "(", "%29": ")", "%2A": "*", "%2B": "+", "%2C": ",", "%2D": "-", "%2E": ".", "%2F": "/",
    "%30": "0", "%31": "1", "%32": "2", "%33": "3", "%34": "4", "%35": "5", "%36": "6", "%37": "7",
    "%38": "8", "%39": "9", "%3A": ":", "%3B": ";", "%3C": "<", "%3D": "=", "%3E": ">", "%3F": "?",
    "%40": "@", "%41": "A", "%42": "B", "%43": "C", "%44": "D", "%45": "E", "%46": "F", "%47": "G",
    "%48": "H", "%49": "I", "%4A": "J", "%4B": "K", "%4C": "L", "%4D": "M", "%4E": "N", "%4F": "O",
    "%50": "P", "%51": "Q", "%52": "R", "%53": "S", "%54": "T", "%55": "U", "%56": "V", "%57": "W",
    "%58": "X", "%59": "Y", "%5A": "Z", "%5B": "[", "%5C": "\\", "%5D": "]", "%5E": "^", "%5F": "_",
    "%60": "`", "%61": "a", "%62": "b", "%63": "c", "%64": "d", "%65": "e", "%66": "f", "%67": "g",
    "%68": "h", "%69": "i", "%6A": "j", "%6B": "k", "%6C": "l", "%6D": "m", "%6E": "n", "%6F": "o",
    "%70": "p", "%71": "q", "%72": "r", "%73": "s", "%74": "t", "%75": "u", "%76": "v", "%77": "w",
    "%78": "x", "%79": "y", "%7A": "z", "%7B": "{", "%7C": "|", "%7D": "}", "%7E": "~", "%7F": "\x7F",
    "%80": "\x80", "%81": "\x81", "%82": "\x82", "%83": "\x83", "%84": "\x84", "%85": "\x85", "%86": "\x86", "%87": "\x87",
    "%88": "\x88", "%89": "\x89", "%8A": "\x8A", "%8B": "\x8B", "%8C": "\x8C", "%8D": "\x8D", "%8E": "\x8E", "%8F": "\x8F",
    "%90": "\x90", "%91": "\x91", "%92": "\x92", "%93": "\x93", "%94": "\x94", "%95": "\x95", "%96": "\x96", "%97": "\x97",
    "%98": "\x98", "%99": "\x99", "%9A": "\x9A", "%9B": "\x9B", "%9C": "\x9C", "%9D": "\x9D", "%9E": "\x9E", "%9F": "\x9F",
    "%A0": "\xA0", "%A1": "\xA1", "%A2": "\xA2", "%A3": "\xA3", "%A4": "\xA4", "%A5": "\xA5", "%A6": "\xA6", "%A7": "\xA7",
    "%A8": "\xA8", "%A9": "\xA9", "%AA": "\xAA", "%AB": "\xAB", "%AC": "\xAC", "%AD": "\xAD", "%AE": "\xAE", "%AF": "\xAF",
    "%B0": "\xB0", "%B1": "\xB1", "%B2": "\xB2", "%B3": "\xB3", "%B4": "\xB4", "%B5": "\xB5", "%B6": "\xB6", "%B7": "\xB7",
    "%B8": "\xB8", "%B9": "\xB9", "%BA": "\xBA", "%BB": "\xBB", "%BC": "\xBC", "%BD": "\xBD", "%BE": "\xBE", "%BF": "\xBF",
    "%C0": "\xC0", "%C1": "\xC1", "%C2": "\xC2", "%C3": "\xC3", "%C4": "\xC4", "%C5": "\xC5", "%C6": "\xC6", "%C7": "\xC7",
    "%C8": "\xC8", "%C9": "\xC9", "%CA": "\xCA", "%CB": "\xCB", "%CC": "\xCC", "%CD": "\xCD", "%CE": "\xCE", "%CF": "\xCF",
    "%D0": "\xD0", "%D1": "\xD1", "%D2": "\xD2", "%D3": "\xD3", "%D4": "\xD4", "%D5": "\xD5", "%D6": "\xD6", "%D7": "\xD7",
    "%D8": "\xD8", "%D9": "\xD9", "%DA": "\xDA", "%DB": "\xDB", "%DC": "\xDC", "%DD": "\xDD", "%DE": "\xDE", "%DF": "\xDF",
    "%E0": "\xE0", "%E1": "\xE1", "%E2": "\xE2", "%E3": "\xE3", "%E4": "\xE4", "%E5": "\xE5", "%E6": "\xE6", "%E7": "\xE7",
    "%E8": "\xE8", "%E9": "\xE9", "%EA": "\xEA", "%EB": "\xEB", "%EC": "\xEC", "%ED": "\xED", "%EE": "\xEE", "%EF": "\xEF",
    "%F0": "\xF0", "%F1": "\xF1", "%F2": "\xF2", "%F3": "\xF3", "%F4": "\xF4", "%F5": "\xF5", "%F6": "\xF6", "%F7": "\xF7",
    "%F8": "\xF8", "%F9": "\xF9", "%FA": "\xFA", "%FB": "\xFB", "%FC": "\xFC", "%FD": "\xFD", "%FE": "\xFE", "%FF": "\xFF"
}

BASE_NORMALIZATION = Transformation(
    name="BaseNormalization",
    transformation_type=NormalizationTransformation(normalization_str='/../'),
    conditions=[ContainsType('/../')]
)

# ─────────────────────────
# 유틸리티 함수
# ─────────────────────────
def partial_replace_all_combinations(original: str, old: str, new: str) -> List[str]:
    """
    original에서 old가 발견되는 모든 위치를 각기 new로 치환하는
    '모든 부분 치환 조합'을 반환.
    """
    results = set()
    idx_list = []

    start_idx = 0
    while True:
        found = original.find(old, start_idx)
        if found == -1:
            break
        idx_list.append(found)
        start_idx = found + len(old)

    # 부분 치환 (1개만, 2개만, ... 전부) 조합 생성
    for r in range(1, len(idx_list) + 1):
        for combo in combinations(idx_list, r):
            new_chars = list(original)
            offset = 0
            for pos in combo:
                actual_pos = pos + offset
                new_chars[actual_pos:actual_pos + len(old)] = list(new)
                offset += (len(new) - len(old))
            results.add("".join(new_chars))

    return list(results)


def encode_partial_combinations(original: str, target_char: str) -> List[str]:
    """
    original에서 target_char('/' 또는 '.')의 부분 치환 조합을 모두 생성하여
    ENCODING_MAP에 따라 인코딩한 문자열들을 반환.
    """
    results = set()
    idx_list = []

    start_idx = 0
    while True:
        found = original.find(target_char, start_idx)
        if found == -1:
            break
        idx_list.append(found)
        start_idx = found + len(target_char)

    for r in range(1, len(idx_list) + 1):
        for combo in combinations(idx_list, r):
            new_chars = list(original)
            offset = 0
            for pos in combo:
                actual_pos = pos + offset
                encoded_value = ENCODING_MAP.get(target_char, target_char)
                new_chars[actual_pos:actual_pos + 1] = list(encoded_value)
                offset += len(encoded_value) - 1
            replaced_str = "".join(new_chars)
            results.add(replaced_str)

    return list(results)


def add_percent_encoding_candidates(
    transformation_list: List[Transformation]  # 🔥 변경
) -> List[Transformation]:  # 🔥 반환도 Transformation으로 변경
    """모든 후보에 대해 '%' → '%25' 치환 후보 추가"""
    encoded_candidates = set()
    for norm in transformation_list:
        if '%' in norm.transformation_type.normalization_str:  # 🔥 수정
            new_str = norm.transformation_type.normalization_str.replace('%', '%25')
            encoded_candidates.add(Transformation(
                name=f"Normalization({new_str})",
                transformation_type=NormalizationTransformation(new_str),
                conditions=[ContainsType(new_str)]
            ))
    return list(encoded_candidates)

def remove_conflict_candidates(
    current_expanded: Iterable[Transformation],  # 🔥 변경
    pre_server_expanded: Iterable[Transformation]  # 🔥 변경
) -> List[Transformation]:  # 🔥 반환도 Transformation으로 변경
    """
    이전 서버의 normalization 후보 중
    pre_server_expanded에 포함되는 문자열을 가진 항목을 제거
    """
    final_expansion = set(current_expanded)

    # 포함 관계 기준 제거 로직
    for pre_norm in pre_server_expanded:
        final_expansion = {
            norm for norm in final_expansion
            if pre_norm.transformation_type.normalization_str
            not in norm.transformation_type.normalization_str  # 🔥 수정
        }

    return list(final_expansion)


def get_expanded_normalization_with_pre_server(
    normalization_list: List[NormalizationTransformation],
    pre_server_expanded: List[NormalizationTransformation],
    pre_server: "Server"
) -> List[NormalizationTransformation]:
    """
    이전 서버(pre_server)의 설정에 따라
    normalization_list를 기반으로 확장/제거한 결과만 return
    (normalization_list는 수정 X)

    --- 요구 사항 ---
    1) if (normalize=False, decode=True):
       => 모든 후보에 대해 '% -> %25' 치환한 신규 후보를 추가
    2) if (normalize=False, decode=False):
       => 아무것도 안 함
    3) if (normalize=True, decode=False):
       => pre_server_expanded의 후보와 '동일한 문자열'을 가진 current_expanded는 제거
    4) if (normalize=True, decode=True):
       => '% -> %25' 치환 후보를 추가, 그리고 pre_server_expanded와 동일한 후보 제거
    """
    final_expansion = set(normalization_list)

    if pre_server.is_normalize:
        if pre_server.is_decode:
            # 4) if (normalize=True, decode=True)
            final_expansion.update(add_percent_encoding_candidates(normalization_list))
            final_expansion = remove_conflict_candidates(final_expansion, pre_server_expanded)
        else:
            # 3) if (normalize=True, decode=False)
            final_expansion = remove_conflict_candidates(final_expansion, pre_server_expanded)
    elif not pre_server.is_normalize and pre_server.is_decode:
        # 1) if (normalize=False, decode=True)
        final_expansion.update(add_percent_encoding_candidates(normalization_list))

    # 2) if (normalize=False, decode=False) => 아무것도 안 함

    return list(final_expansion)

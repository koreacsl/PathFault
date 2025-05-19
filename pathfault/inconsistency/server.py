import itertools
import logging
import uuid
import ast
import random
from typing import Optional, Tuple, List
from z3 import BoolRef, And, BoolVal, String, If, ExprRef  # Z3의 문자열 및 조건 표현
from math import comb
from dataclasses import dataclass

from .custom_z3_expression import ReplaceAll
from .transformation import Transformation, NormalizationTransformation, ReplaceTransformation
from .condition import _ConditionType, ContainsType
from .tools import (
    partial_replace_all_combinations, encode_partial_combinations, ENCODING_MAP, BASE_NORMALIZATION, DECODING_MAP
)


@dataclass
class InconsistencyEntry:
    inconsistency_request_type: str
    inbound_url: str
    inbound_url_char: str
    outbound_url: str
    outbound_url_char: str

    def to_ast(self):
        return ast.Dict(
            keys=[
                ast.Constant("inconsistency_request_type"),
                ast.Constant("inbound_url"),
                ast.Constant("inbound_url_char"),
                ast.Constant("outbound_url"),
                ast.Constant("outbound_url_char")
            ],
            values=[
                ast.Constant(self.inconsistency_request_type),
                ast.Constant(self.inbound_url),
                ast.Constant(self.inbound_url_char),
                ast.Constant(self.outbound_url),
                ast.Constant(self.outbound_url_char)
            ]
        )

@dataclass
class InconsistencyInfo:
    hex_value: str
    char_value: str
    entries: List[InconsistencyEntry]

    def to_ast(self):
        return ast.Dict(
            keys=[
                ast.Constant("hex_value"),
                ast.Constant("char_value"),
                ast.Constant("entries")
            ],
            values=[
                ast.Constant(self.hex_value),
                ast.Constant(self.char_value),
                ast.List(elts=[entry.to_ast() for entry in self.entries], ctx=ast.Load())
            ]
        )


logger = logging.getLogger(__name__)


class Server:
    def __init__(self, name: str, condition_list: Optional[List[_ConditionType]] = None,
                 target_pre_condition_list: Optional[List[_ConditionType]] = None,
                 target_post_condition_list: Optional[List[_ConditionType]] = None,
                 transformation_list: Optional[List[Transformation]] = None,
                 essential_transformation_list: Optional[List[Transformation]] = None,
                 inconsistency_info: Optional[List[InconsistencyInfo]] = None,
                 omitted_inconsistency_info: Optional[List[InconsistencyInfo]] = None,
                 unprocessed_inconsistency_info: Optional[List[InconsistencyInfo]] = None, is_normalize: bool = False,
                 is_decode: bool = False):
        self.name: str = name

        self.condition_list: List[_ConditionType] = condition_list or []
        self.target_pre_condition_list: List[_ConditionType] = target_pre_condition_list or []
        self.target_post_condition_list: List[_ConditionType] = target_post_condition_list or []
        self.transformation_list: List[Transformation] = transformation_list or []
        self.essential_transformation_list: List[Transformation] = essential_transformation_list or []  # 🔥 빈 리스트 추가

        self.normalization_list: List[NormalizationTransformation] = []

        # 🔹 Discrepancy 정보 관련 (Optional 인자)
        self.inconsistency_info: List[InconsistencyInfo] = inconsistency_info or []
        self.omitted_inconsistency_info: List[InconsistencyInfo] = omitted_inconsistency_info or []
        self.unprocessed_inconsistency_info: List[InconsistencyInfo] = unprocessed_inconsistency_info or []

        # 초기 설정 (Setter 자동 호출)
        self.is_normalize = is_normalize
        self.is_decode = is_decode

    @property
    def is_normalize(self) -> bool:
        return hasattr(self, '_is_normalize') and self._is_normalize

    @is_normalize.setter
    def is_normalize(self, value: bool):
        if getattr(self, '_is_normalize', None) == value:
            return

        self._is_normalize = value

        if value:
            self.add_default_normalization()
            logger.debug(f"{self.name}: is_normalize -> True, called add_default_normalization()")
        else:
            self.normalization_list = []
            logger.debug(f"{self.name}: is_normalize -> False, set normalization_list=[]")

    @property
    def is_decode(self) -> bool:
        return hasattr(self, '_is_decode') and self._is_decode

    @is_decode.setter
    def is_decode(self, value: bool):
        if getattr(self, '_is_decode', None) == value:
            return

        self._is_decode = value
        logger.debug(f"{self.name}: is_decode -> {value}")

        if self.is_normalize:
            self.add_default_normalization()

    def add_default_normalization(self):
        """기본 Normalization 자동 추가 (확장 로직 없음)"""
        if BASE_NORMALIZATION not in self.normalization_list:
            self.normalization_list.append(BASE_NORMALIZATION)
            logger.debug(f"{self.name}: Added default normalization: '/../'")

    def get_expanded_normalization_with_decode(
            self,
            base_norm: Transformation  # 🔥 Transformation 객체로 인자 변경
    ) -> List[Transformation]:
        """
        base_norm을 기반으로 확장된 Normalization 후보를 리턴
        (self.normalization_list는 수정하지 않음)
        """

        if self.is_normalize:
            expansion_list = [Transformation(
                name=f"Normalization({base_norm.transformation_type.normalization_str})",  # 🔥 수정
                transformation_type=base_norm.transformation_type,  # 🔥 Transformation에서 타입 추출
                conditions=[ContainsType(base_norm.transformation_type.normalization_str)]  # 🔥 ContainsType 추가
            )]

            if self.is_decode:
                # '/' 인코딩 확장
                expanded_results = set(n.transformation_type.normalization_str for n in expansion_list)
                for original_str in expanded_results:
                    new_candidates = encode_partial_combinations(original_str, '/')
                    for enc in new_candidates:
                        expansion_list.append(Transformation(
                            name=f"Normalization({enc})",
                            transformation_type=NormalizationTransformation(enc),
                            conditions=[ContainsType(enc)]  # 🔥 ContainsType 추가
                        ))

                # '.' 인코딩 확장
                expanded_results = set(n.transformation_type.normalization_str for n in expansion_list)
                for original_str in expanded_results:
                    new_candidates = encode_partial_combinations(original_str, '.')
                    for enc in new_candidates:
                        expansion_list.append(Transformation(
                            name=f"Normalization({enc})",
                            transformation_type=NormalizationTransformation(enc),
                            conditions=[ContainsType(enc)]  # 🔥 ContainsType 추가
                        ))

            return expansion_list
        else:
            return []

    def get_expanded_normalization_with_replace(
            self,
            replace_transform: ReplaceTransformation
    ) -> List[Transformation]:
        """
        replace_transform을 기반으로 normalization 후보를 확장하는 메소드
        """

        result = set(Transformation(
            name=f"Normalization({norm.transformation_type.normalization_str})",
            transformation_type=norm.transformation_type,
            conditions=[ContainsType(norm.transformation_type.normalization_str)]  # 🔥 ContainsType 추가
        ) for norm in self.normalization_list)

        replace_expanded = set()

        # ReplaceTransformation을 통한 확장
        for norm in self.normalization_list:
            norm_str = norm.transformation_type.normalization_str
            if replace_transform.replace_str in norm_str:
                candidates = partial_replace_all_combinations(
                    norm_str,
                    replace_transform.replace_str,
                    replace_transform.target_str
                )
                for c in candidates:
                    replace_expanded.add(Transformation(
                        name=f"Normalization({c})",
                        transformation_type=NormalizationTransformation(c),
                        conditions=[ContainsType(c)]  # 🔥 ContainsType 추가
                    ))

        # Replace 확장 결과에 대해 추가 인코딩 후보 생성
        if self.is_decode:
            encoded_candidates = set()
            for candidate in replace_expanded:
                encoded_candidates.update(
                    encode_partial_combinations(candidate.transformation_type.normalization_str, '/'))
                encoded_candidates.update(
                    encode_partial_combinations(candidate.transformation_type.normalization_str, '.'))

            for encoded_str in encoded_candidates:
                replace_expanded.add(Transformation(
                    name=f"Normalization({encoded_str})",
                    transformation_type=NormalizationTransformation(encoded_str),
                    conditions=[ContainsType(encoded_str)]  # 🔥 ContainsType 추가
                ))

        if self.is_decode:
            # Replace의 target_str이 ENCODING_MAP에 존재하는 경우 인코딩된 값 추가
            if replace_transform.target_str in ENCODING_MAP:
                encoded_target = ENCODING_MAP[replace_transform.target_str]
                encoded_target_candidates = set()
                for candidate in replace_expanded:
                    encoded_target_candidates.update(
                        partial_replace_all_combinations(
                            candidate.transformation_type.normalization_str,
                            replace_transform.target_str,
                            encoded_target
                        )
                    )

                for encoded_str in encoded_target_candidates:
                    replace_expanded.add(Transformation(
                        name=f"Normalization({encoded_str})",
                        transformation_type=NormalizationTransformation(encoded_str),
                        conditions=[ContainsType(encoded_str)]  # 🔥 ContainsType 추가
                    ))

        # 기존 normalization_list와 확장 결과 합치기
        result.update(replace_expanded)

        return list(result)

    def apply_pre_conditions(self, input_url: ExprRef) -> BoolRef:
        # 새로운 변수 생성
        pre_var = String(f"pre_{uuid.uuid4().hex[:8]}")
        # 원본 input_url과 pre_var가 같음을 조건에 추가한 후,
        # pre_var에 대해 target_pre_condition_list의 모든 조건 적용
        condition_statements = [pre_var == input_url] + [
            condition.apply(pre_var) for condition in (self.target_pre_condition_list + self.condition_list)
        ]
        return And(*condition_statements) if condition_statements else BoolVal(True)

    def apply_post_conditions(self, input_url: ExprRef) -> BoolRef:
        # 새로운 변수 생성
        post_var = String(f"post_{uuid.uuid4().hex[:8]}")
        # 원본 input_url과 post_var가 같음을 조건에 추가한 후,
        # post_var에 대해 target_post_condition_list와 condition_list의 모든 조건 적용
        condition_statements = [post_var == input_url] + [
            condition.apply(post_var) for condition in (self.target_post_condition_list)
        ]
        return And(*condition_statements) if condition_statements else BoolVal(True)

    def apply_decoding(self, input_url: ExprRef) -> ExprRef:
        if self.is_decode:
            is_first = True
            # "%25"를 제외한 나머지 치환 수행
            for encoded, decoded in DECODING_MAP.items():
                if encoded == "%25":
                    continue
                if is_first:
                    next_decoded_output = ReplaceAll(input_url, encoded, decoded)
                    is_first = False
                else:
                    next_decoded_output = ReplaceAll(next_decoded_output, encoded, decoded)

            # 마지막에 "%25" 치환 수행
            next_decoded_output = ReplaceAll(next_decoded_output, "%25", DECODING_MAP["%25"])
            return next_decoded_output
        else:
            return input_url

    def apply_transformations(self, input_url: ExprRef) -> Tuple[ExprRef, BoolRef]:
        """
        선택된 Transformation을 순차적으로 input_url에 적용
        - 변환 결과 (ExprRef)
        - 모든 조건을 만족해야 하는 BoolRef 반환
        """
        # 🔥 초기 transformed_output을 UUID 기반으로 설정
        transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")
        condition_statements: List[BoolRef] = []

        # ✅ 최초 input_url과 첫 번째 transformed_output이 같아야 함
        condition_statements.append(input_url == transformed_output)

        for idx, transform in enumerate(self.transformation_list):
            # 🔥 각 변환 결과에 대해 고유한 변수 생성
            next_transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")

            new_transformed_output, condition = transform.apply_transformation_for_validation(transformed_output)

            # 조건이 True이면 new_transformed_output, 아니면 이전 transformed_output을 사용하도록 If로 처리
            condition_statements.append(
                next_transformed_output == If(condition, new_transformed_output, transformed_output)
            )

            # 🔹 다음 루프에서 사용할 변수 갱신
            transformed_output = next_transformed_output

        combined_conditions = And(*condition_statements) if condition_statements else BoolVal(True)

        return transformed_output, combined_conditions

    def apply_essential_tranformation(self, input_url: ExprRef) -> Tuple[ExprRef, BoolRef]:
        # 🔥 초기 transformed_output을 UUID 기반으로 설정
        transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")
        condition_statements: List[BoolRef] = []

        # ✅ 최초 input_url과 첫 번째 transformed_output이 같아야 함
        condition_statements.append(input_url == transformed_output)

        for idx, transform in enumerate(self.essential_transformation_list):
            # 🔥 각 변환 결과에 대해 고유한 변수 생성
            next_transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")

            new_transformed_output, condition = transform.apply_transformation(transformed_output)
            condition_statements.append(condition)

            # ✅ 이전 transformed_output과 새로운 transformed_output이 같아야 함
            condition_statements.append(new_transformed_output == next_transformed_output)

            # 🔹 다음 루프에서 사용할 변수 갱신
            transformed_output = next_transformed_output

        combined_conditions = And(*condition_statements) if condition_statements else BoolVal(True)

        return transformed_output, combined_conditions

    def apply_normalization(self, transformed_output: ExprRef) -> Tuple[ExprRef, BoolRef]:
        """
        🔥 Normalization 단계 추가
        - Normalize 플래그가 활성화된 경우 추가 수행
        - `custom_normalization` 인자가 없는 경우 → 기본적으로 BASE_NORMALIZATION 수행
        - `custom_normalization` 인자가 있는 경우 → 해당 Normalization만 수행
        """
        condition_statements: List[BoolRef] = []

        # 초기 normalized_expr는 transformed_output
        normalized_expr = transformed_output

        if self.is_normalize:
            # 각 단계에서 새로운 normalized_output 변수를 생성
            next_normalized_output = String(f"normalized_{uuid.uuid4().hex[:8]}")

            # norm.apply_transformation_for_validation은 (변환결과, 조건)을 반환
            new_normalized_output, normalize_condition = BASE_NORMALIZATION.apply_transformation(normalized_expr)

            # 조건이 만족되면 new_normalized_output, 아니면 이전 normalized_expr을 사용
            condition_statements.append(
                next_normalized_output == If(normalize_condition, new_normalized_output, normalized_expr)
            )

            # 다음 단계에 사용할 normalized_expr 업데이트
            normalized_expr = next_normalized_output
        else:
            # Normalize 플래그가 비활성화된 경우, 변환 없이 원래의 값 사용
            normalized_expr = transformed_output

        combined_conditions = And(*condition_statements) if condition_statements else BoolVal(True)

        return normalized_expr, combined_conditions


class ServerAction:
    def __init__(
            self,
            server: Server,  # 🔥 원본 Server 클래스 추가
            name: str,
            condition_list: Optional[List[_ConditionType]] = None,
            target_pre_condition_list: Optional[List[_ConditionType]] = None,
            target_post_condition_list: Optional[List[_ConditionType]] = None,
            transformation_list: Optional[List[Transformation]] = None,
            normalize: bool = False,
    ) -> None:
        self.server: Server = server  # 🔥 원본 Server 저장
        self.name: str = name
        self.condition_list: List[_ConditionType] = condition_list or []
        self.target_pre_condition_list: List[_ConditionType] = target_pre_condition_list or []
        self.target_post_condition_list: List[_ConditionType] = target_post_condition_list or []
        self.transformation_list: List[Transformation] = transformation_list or []
        self.normalize: bool = normalize

    def apply_pre_conditions(self, input_url: ExprRef) -> BoolRef:
        condition_statements: List[BoolRef] = [
            condition.apply(input_url) for condition in self.target_pre_condition_list
        ]
        return And(*condition_statements) if condition_statements else BoolVal(True)


    def apply_post_conditions(self, input_url: ExprRef) -> BoolRef:
        condition_statements: List[BoolRef] = [
            condition.apply(input_url) for condition in self.target_post_condition_list
        ]
        return And(*condition_statements) if condition_statements else BoolVal(True)


    def apply_transformations(self, input_url: ExprRef) -> Tuple[ExprRef, BoolRef]:
        """
        선택된 Transformation을 순차적으로 input_url에 적용
        - 변환 결과 (ExprRef)
        - 모든 조건을 만족해야 하는 BoolRef 반환
        """

        # 🔥 초기 transformed_output을 UUID 기반으로 설정
        transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")
        condition_statements: List[BoolRef] = []

        # ✅ 최초 input_url과 첫 번째 transformed_output이 같아야 함
        condition_statements.append(input_url == transformed_output)

        for idx, transform in enumerate(self.transformation_list):
            # 🔥 각 변환 결과에 대해 고유한 변수 생성
            next_transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")

            new_transformed_output, condition = transform.apply_transformation(transformed_output)
            condition_statements.append(condition)

            # ✅ 이전 transformed_output과 새로운 transformed_output이 같아야 함
            condition_statements.append(new_transformed_output == next_transformed_output)

            # 🔹 다음 루프에서 사용할 변수 갱신
            transformed_output = next_transformed_output

        combined_conditions = And(*condition_statements) if condition_statements else BoolVal(True)

        return transformed_output, combined_conditions


    def apply_normalization(self, transformed_output: ExprRef, custom_normalization: Optional[Transformation] = None) -> \
            Tuple[ExprRef, BoolRef]:
        """
        🔥 Normalization 단계 추가
        - Normalize 플래그가 활성화된 경우 추가 수행
        - `custom_normalization` 인자가 없는 경우 → 기본적으로 BASE_NORMALIZATION 수행
        - `custom_normalization` 인자가 있는 경우 → 해당 Normalization만 수행
        """

        condition_statements: List[BoolRef] = []

        # 🔹 Normalize가 True인 경우 Normalization 수행
        if self.normalize:
            # 🔥 첫 번째 normalized_output이 transformed_output과 동일하도록 조건 추가
            normalized_output = String(f"normalized_{uuid.uuid4().hex[:8]}")
            condition_statements.append(transformed_output == normalized_output)

            if custom_normalization:
                new_normalized_output, normalize_condition = custom_normalization.apply_transformation(
                    normalized_output)
            else:
                new_normalized_output, normalize_condition = BASE_NORMALIZATION.apply_transformation(normalized_output)

            condition_statements.append(normalize_condition)

            # 🔥 각 단계의 normalized_output이 다음 normalized_output과 같도록 조건 추가
            next_normalized_output = String(f"normalized_{uuid.uuid4().hex[:8]}")
            condition_statements.append(new_normalized_output == next_normalized_output)

            # 🔹 다음 단계에서 사용할 `normalized_output` 갱신
            normalized_output = next_normalized_output

        else:
            # 🔹 Normalize 플래그가 비활성화된 경우 → 기존 `transformed_output`을 반환
            normalized_output = transformed_output

        combined_conditions = And(*condition_statements) if condition_statements else BoolVal(True)

        return normalized_output, combined_conditions

    def __repr__(self) -> str:
        return (
            f"ServerAction(\n"
            f"  name={self.name},\n"
            f"  server={self.server.name},\n"  # 🔥 원본 서버 이름 출력
            f"  normalize={'On' if self.normalize else 'Off'},\n"
            f"  condition_list={[str(cond) for cond in self.condition_list]},\n"
            f"  target_pre_condition_list={[str(cond) for cond in self.target_pre_condition_list]},\n"
            f"  target_post_condition_list={[str(cond) for cond in self.target_post_condition_list]},\n"
            f"  transformation_list={[trans.name for trans in self.transformation_list]}\n"
            f")"
        )


def create_server_action(server: Server, selected_transforms: List[Transformation], normalize: bool) -> ServerAction:
    """
    단일 서버에 대한 ServerAction 객체 생성
    """
    return ServerAction(
        server=server,  # 🔥 원본 Server 추가
        name=server.name,
        condition_list=server.condition_list,
        target_pre_condition_list=server.target_pre_condition_list,
        target_post_condition_list=server.target_post_condition_list,
        transformation_list=selected_transforms,
        normalize=normalize
    )


def get_server_actions(servers: List[Server], selected_transforms: List[List[Transformation]], normalize_config: List[bool]) -> List[ServerAction]:
    """
    여러 서버에 대한 ServerAction 객체 리스트 생성
    """
    server_actions = [
        create_server_action(server, selected_transforms[idx], normalize_config[idx])
        for idx, server in enumerate(servers)
    ]
    return server_actions



# ---- 가능한 모든 조합 수 계산 ----
def calculate_combinations(servers, max_transformation_num=2):
    total_transformation_combinations = 1

    # Transformation 조합 계산
    for server in servers:
        combined_transformations = server.transformation_list + server.essential_transformation_list

        # 🔹 Transformation 조합: 0개 ~ max_transformation_num개 선택
        total_transformation_combinations *= sum(
            comb(len(combined_transformations), i)
            for i in range(0, max_transformation_num + 1)
        )

    # Normalize 조합 추가 (최대 1개만 True)
    normalize_candidates = sum(1 for server in servers if server.is_normalize)
    total_transformation_combinations *= comb(normalize_candidates, 1) + 1

    return total_transformation_combinations


# ---- 조합 기록을 위한 집합 ----
executed_combinations = set()


def get_server_transformation_combination(server, max_transforms=2):
    combined_transformations = server.transformation_list + server.essential_transformation_list

    # 🔥 가능한 모든 조합 생성 (0 ~ max_transforms까지)
    all_combinations = []
    for n in range(max_transforms + 1):
        all_combinations.extend([list(combination) for combination in itertools.combinations(combined_transformations, n)])

    return all_combinations


# 🔹 Normalize 조합 생성 함수 (개선 버전)
def get_normalize_combinations(servers):
    # 🔹 True로 설정 가능한 후보 (is_normalize=True인 서버만)
    normalize_candidates = [idx for idx, server in enumerate(servers) if server.is_normalize]

    # 🔥 가능한 Normalize 조합 생성
    normalize_combinations = []

    # 모든 False 조합 추가
    base_config = [False] * len(servers)
    normalize_combinations.append(base_config.copy())

    # 🔹 한 서버만 True인 조합 추가
    for idx in normalize_candidates:
        normalize_config = base_config.copy()
        normalize_config[idx] = True
        normalize_combinations.append(normalize_config)

    return normalize_combinations


# 🔹 Transformation + Normalize 조합 생성
def get_all_server_transformation_combinations(servers, max_transforms=2):
    total_combination_list = []

    for server in servers:
        combinations = get_server_transformation_combination(server, max_transforms)
        total_combination_list.append(combinations)

    # 🔥 Transformation 조합 생성
    all_combinations = [list(combination) for combination in itertools.product(*total_combination_list)]

    # 🔥 Normalize 조합 추가
    normalize_combinations = get_normalize_combinations(servers)

    # 🔥 최종 조합 생성
    final_combinations = [list(combination) for combination in itertools.product(all_combinations, normalize_combinations)]

    return final_combinations

# ---- 랜덤 Transformation + Normalize 선택 로직 ----
def get_random_combination(servers, max_transforms=2):
    total_combination_num = calculate_combinations(servers)

    if len(executed_combinations) == total_combination_num:
        print("[완료] 가능한 모든 조합을 탐색했습니다.")
        return None, None

    while True:
        selected_transforms = []
        normalize_config = [False] * len(servers)

        for idx, server in enumerate(servers):
            # 🔥 transformation_list + essential_transformation_list 포함
            combined_transformations = server.transformation_list + server.essential_transformation_list

            sample_size = random.randint(0, min(max_transforms, len(combined_transformations)))
            sampled_transforms = random.sample(
                combined_transformations,
                sample_size
            )
            print(f"[🔎 디버깅] 서버: {server.name} | random.sample 결과: {sampled_transforms}")

            selected_transforms.append(sorted(sampled_transforms, key=lambda x: x.name))

            # 🔍 디버깅: 최종 선택된 변환 목록 출력
            print(f"[🔎 디버깅] 서버: {server.name} | 최종 selected_transforms: {selected_transforms[-1]}")

        # Normalize 설정 추가 (최대 1개만 True)
        if any(server.is_normalize for server in servers):
            normalize_candidate_indices = [idx for idx, server in enumerate(servers) if server.is_normalize]
            selected_normalize_index = random.choice(normalize_candidate_indices + [-1])

            if selected_normalize_index != -1:
                normalize_config[selected_normalize_index] = True

        # 변환 결과의 이름을 튜플로 기록 (정렬 기준으로 동일한 조합 처리)
        combination = tuple(
            (tuple(sorted(trans.name for trans in selected_transforms[i])) or ("None",), normalize_config[i])
            for i in range(len(servers))
        )

        if combination in executed_combinations:
            continue

        # 새로운 조합이면 기록하고 반환
        executed_combinations.add(combination)
        return selected_transforms, normalize_config

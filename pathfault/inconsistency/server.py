import itertools
import logging
import uuid
import ast
import random
from typing import Optional, Tuple, List
from z3 import BoolRef, And, BoolVal, String, If, ExprRef
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

        self.inconsistency_info: List[InconsistencyInfo] = inconsistency_info or []
        self.omitted_inconsistency_info: List[InconsistencyInfo] = omitted_inconsistency_info or []
        self.unprocessed_inconsistency_info: List[InconsistencyInfo] = unprocessed_inconsistency_info or []

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
        """Add default normalization automatically (no extension logic)"""
        if BASE_NORMALIZATION not in self.normalization_list:
            self.normalization_list.append(BASE_NORMALIZATION)
            logger.debug(f"{self.name}: Added default normalization: '/../'")

    def get_expanded_normalization_with_decode(
            self,
            base_norm: Transformation
    ) -> List[Transformation]:
        """
        Return extended Normalization candidates based on base_norm
        (does not modify self.normalization_list)
        """

        if self.is_normalize:
            expansion_list = [Transformation(
                name=f"Normalization({base_norm.transformation_type.normalization_str})",
                transformation_type=base_norm.transformation_type,
                conditions=[ContainsType(base_norm.transformation_type.normalization_str)]
            )]

            if self.is_decode:
                # '/' encoding expansion
                expanded_results = set(n.transformation_type.normalization_str for n in expansion_list)
                for original_str in expanded_results:
                    new_candidates = encode_partial_combinations(original_str, '/')
                    for enc in new_candidates:
                        expansion_list.append(Transformation(
                            name=f"Normalization({enc})",
                            transformation_type=NormalizationTransformation(enc),
                            conditions=[ContainsType(enc)]
                        ))

                # '.' encoding expansion
                expanded_results = set(n.transformation_type.normalization_str for n in expansion_list)
                for original_str in expanded_results:
                    new_candidates = encode_partial_combinations(original_str, '.')
                    for enc in new_candidates:
                        expansion_list.append(Transformation(
                            name=f"Normalization({enc})",
                            transformation_type=NormalizationTransformation(enc),
                            conditions=[ContainsType(enc)]
                        ))

            return expansion_list
        else:
            return []

    def get_expanded_normalization_with_replace(
            self,
            replace_transform: ReplaceTransformation
    ) -> List[Transformation]:
        """
        Extend normalization candidates based on replace_transform
        """

        result = set(Transformation(
            name=f"Normalization({norm.transformation_type.normalization_str})",
            transformation_type=norm.transformation_type,
            conditions=[ContainsType(norm.transformation_type.normalization_str)]
        ) for norm in self.normalization_list)

        replace_expanded = set()

        # Expansion through ReplaceTransformation
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
                        conditions=[ContainsType(c)]
                    ))

        # Generate additional encoding candidate about Replace expansion results
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
                    conditions=[ContainsType(encoded_str)]
                ))

        if self.is_decode:
            # Add encoded value when the Replace.target_str is in ENCODING_MAP
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
                        conditions=[ContainsType(encoded_str)]
                    ))

        # merge with normalization_list
        result.update(replace_expanded)

        return list(result)

    def apply_pre_conditions(self, input_url: ExprRef) -> BoolRef:
        # Create new variable
        pre_var = String(f"pre_{uuid.uuid4().hex[:8]}")
        # Add condition that input_url equals pre_var, then apply all conditions from target_pre_condition_list and condition_list to pre_var
        condition_statements = [pre_var == input_url] + [
            condition.apply(pre_var) for condition in (self.target_pre_condition_list + self.condition_list)
        ]
        return And(*condition_statements) if condition_statements else BoolVal(True)

    def apply_post_conditions(self, input_url: ExprRef) -> BoolRef:
        # Create new variable
        post_var = String(f"post_{uuid.uuid4().hex[:8]}")
        # Add condition that input_url equals post_var, then apply all conditions from target_post_condition_list and condition_list to post_var
        condition_statements = [post_var == input_url] + [
            condition.apply(post_var) for condition in (self.target_post_condition_list)
        ]
        return And(*condition_statements) if condition_statements else BoolVal(True)

    def apply_decoding(self, input_url: ExprRef) -> ExprRef:
        if self.is_decode:
            is_first = True
            # Perform replacements except for "%25"
            for encoded, decoded in DECODING_MAP.items():
                if encoded == "%25":
                    continue
                if is_first:
                    next_decoded_output = ReplaceAll(input_url, encoded, decoded)
                    is_first = False
                else:
                    next_decoded_output = ReplaceAll(next_decoded_output, encoded, decoded)

            # Perform "%25" replacement last
            next_decoded_output = ReplaceAll(next_decoded_output, "%25", DECODING_MAP["%25"])
            return next_decoded_output
        else:
            return input_url

    def apply_transformations(self, input_url: ExprRef) -> Tuple[ExprRef, BoolRef]:
        """
        Apply selected transformations sequentially to input_url
        - Return transformed result (ExprRef)
        - Return BoolRef requiring all conditions to be satisfied
        """
        # Initialize transformed_output with UUID-based name
        transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")
        condition_statements: List[BoolRef] = []

        # Initial input_url must equal first transformed_output
        condition_statements.append(input_url == transformed_output)

        for idx, transform in enumerate(self.transformation_list):
            # Create unique variable for each transformation result
            next_transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")

            new_transformed_output, condition = transform.apply_transformation_for_validation(transformed_output)

            # Use If to select new_transformed_output if condition is True, else keep previous transformed_output
            condition_statements.append(
                next_transformed_output == If(condition, new_transformed_output, transformed_output)
            )

            # Update variable for next loop
            transformed_output = next_transformed_output

        combined_conditions = And(*condition_statements) if condition_statements else BoolVal(True)

        return transformed_output, combined_conditions

    def apply_essential_tranformation(self, input_url: ExprRef) -> Tuple[ExprRef, BoolRef]:
        # Initialize transformed_output with UUID-based name
        transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")
        condition_statements: List[BoolRef] = []

        # Initial input_url must equal first transformed_output
        condition_statements.append(input_url == transformed_output)

        for idx, transform in enumerate(self.essential_transformation_list):
            # Create unique variable for each transformation result
            next_transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")

            new_transformed_output, condition = transform.apply_transformation(transformed_output)
            condition_statements.append(condition)

            # Previous transformed_output must equal new transformed_output
            condition_statements.append(new_transformed_output == next_transformed_output)

            # Update variable for next loop
            transformed_output = next_transformed_output

        combined_conditions = And(*condition_statements) if condition_statements else BoolVal(True)

        return transformed_output, combined_conditions

    def apply_normalization(self, transformed_output: ExprRef) -> Tuple[ExprRef, BoolRef]:
        """
        Add normalization step
        - Performed if normalize flag is enabled
        - Without custom_normalization, defaults to BASE_NORMALIZATION
        - With custom_normalization, performs only specified normalization
        """
        condition_statements: List[BoolRef] = []

        # Initial normalized_expr is transformed_output
        normalized_expr = transformed_output

        if self.is_normalize:
            # Create new normalized_output variable for each step
            next_normalized_output = String(f"normalized_{uuid.uuid4().hex[:8]}")

            # norm.apply_transformation_for_validation returns (transformed result, condition)
            new_normalized_output, normalize_condition = BASE_NORMALIZATION.apply_transformation(normalized_expr)

            # Use new_normalized_output if condition is satisfied, else keep previous normalized_expr
            condition_statements.append(
                next_normalized_output == If(normalize_condition, new_normalized_output, normalized_expr)
            )

            # Update normalized_expr for next step
            normalized_expr = next_normalized_output
        else:
            # If normalize flag is disabled, use original value without transformation
            normalized_expr = transformed_output

        combined_conditions = And(*condition_statements) if condition_statements else BoolVal(True)

        return normalized_expr, combined_conditions

class ServerAction:
    def __init__(
            self,
            server: Server,
            name: str,
            condition_list: Optional[List[_ConditionType]] = None,
            target_pre_condition_list: Optional[List[_ConditionType]] = None,
            target_post_condition_list: Optional[List[_ConditionType]] = None,
            transformation_list: Optional[List[Transformation]] = None,
            normalize: bool = False,
    ) -> None:
        self.server: Server = server
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
        Apply selected transformations sequentially to input_url
        - Return transformed result (ExprRef)
        - Return BoolRef requiring all conditions to be satisfied
        """

        # Initialize transformed_output with UUID-based name
        transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")
        condition_statements: List[BoolRef] = []

        # Initial input_url must equal first transformed_output
        condition_statements.append(input_url == transformed_output)

        for idx, transform in enumerate(self.transformation_list):
            # Create unique variable for each transformation result
            next_transformed_output = String(f"transformed_{uuid.uuid4().hex[:8]}")

            new_transformed_output, condition = transform.apply_transformation(transformed_output)
            condition_statements.append(condition)

            # Previous transformed_output must equal new transformed_output
            condition_statements.append(new_transformed_output == next_transformed_output)

            # Update variable for next loop
            transformed_output = next_transformed_output

        combined_conditions = And(*condition_statements) if condition_statements else BoolVal(True)

        return transformed_output, combined_conditions

    def apply_normalization(self, transformed_output: ExprRef,
                            custom_normalization: Optional[Transformation] = None) -> \
            Tuple[ExprRef, BoolRef]:
        """
        - Perform normalization if normalize flag is enabled
        - Without custom_normalization, defaults to BASE_NORMALIZATION
        - With custom_normalization, performs only specified normalization
        """

        condition_statements: List[BoolRef] = []

        # Perform normalization if normalize is True
        if self.normalize:
            normalized_output = String(f"normalized_{uuid.uuid4().hex[:8]}")
            condition_statements.append(transformed_output == normalized_output)

            if custom_normalization:
                new_normalized_output, normalize_condition = custom_normalization.apply_transformation(
                    normalized_output)
            else:
                new_normalized_output, normalize_condition = BASE_NORMALIZATION.apply_transformation(
                    normalized_output)

            condition_statements.append(normalize_condition)

            next_normalized_output = String(f"normalized_{uuid.uuid4().hex[:8]}")
            condition_statements.append(new_normalized_output == next_normalized_output)

            # Update normalized_output for next step
            normalized_output = next_normalized_output

        else:
            # If normalize flag is disabled, return original transformed_output
            normalized_output = transformed_output

        combined_conditions = And(*condition_statements) if condition_statements else BoolVal(True)

        return normalized_output, combined_conditions

    def __repr__(self) -> str:
        return (
            f"ServerAction(\n"
            f"  name={self.name},\n"
            f"  server={self.server.name},\n"
            f"  normalize={'On' if self.normalize else 'Off'},\n"
            f"  condition_list={[str(cond) for cond in self.condition_list]},\n"
            f"  target_pre_condition_list={[str(cond) for cond in self.target_pre_condition_list]},\n"
            f"  target_post_condition_list={[str(cond) for cond in self.target_post_condition_list]},\n"
            f"  transformation_list={[trans.name for trans in self.transformation_list]}\n"
            f")"
        )

def create_server_action(server: Server, selected_transforms: List[Transformation],
                         normalize: bool) -> ServerAction:
    return ServerAction(
        server=server,
        name=server.name,
        condition_list=server.condition_list,
        target_pre_condition_list=server.target_pre_condition_list,
        target_post_condition_list=server.target_post_condition_list,
        transformation_list=selected_transforms,
        normalize=normalize
    )

def get_server_actions(servers: List[Server], selected_transforms: List[List[Transformation]],
                       normalize_config: List[bool]) -> List[ServerAction]:
    server_actions = [
        create_server_action(server, selected_transforms[idx], normalize_config[idx])
        for idx, server in enumerate(servers)
    ]
    return server_actions

# ---- Calculate total possible combinations ----
def calculate_combinations(servers, max_transformation_num=2):
    total_transformation_combinations = 1

    # Calculate transformation combinations
    for server in servers:
        combined_transformations = server.transformation_list + server.essential_transformation_list

        # Transformation combinations: select 0 to max_transformation_num
        total_transformation_combinations *= sum(
            comb(len(combined_transformations), i)
            for i in range(0, max_transformation_num + 1)
        )

    # Add normalize combinations (at most one True)
    normalize_candidates = sum(1 for server in servers if server.is_normalize)
    total_transformation_combinations *= comb(normalize_candidates, 1) + 1

    return total_transformation_combinations

# ---- Set for tracking combinations ----
executed_combinations = set()

def get_server_transformation_combination(server, max_transforms=2):
    combined_transformations = server.transformation_list + server.essential_transformation_list

    # Generate all possible combinations (0 to max_transforms)
    all_combinations = []
    for n in range(max_transforms + 1):
        all_combinations.extend(
            [list(combination) for combination in itertools.combinations(combined_transformations, n)])

    return all_combinations

# Generate normalize combinations
def get_normalize_combinations(servers):
    # Candidates that can be set to True (servers with is_normalize=True)
    normalize_candidates = [idx for idx, server in enumerate(servers) if server.is_normalize]

    # Generate possible normalize combinations
    normalize_combinations = []

    # Add all False combination
    base_config = [False] * len(servers)
    normalize_combinations.append(base_config.copy())

    # Add combinations with one server set to True
    for idx in normalize_candidates:
        normalize_config = base_config.copy()
        normalize_config[idx] = True
        normalize_combinations.append(normalize_config)

    return normalize_combinations

# Generate Transformation + Normalize combinations
def get_all_server_transformation_combinations(servers, max_transforms=2):
    total_combination_list = []

    for server in servers:
        combinations = get_server_transformation_combination(server, max_transforms)
        total_combination_list.append(combinations)

    # Generate transformation combinations
    all_combinations = [list(combination) for combination in itertools.product(*total_combination_list)]

    # Add normalize combinations
    normalize_combinations = get_normalize_combinations(servers)

    # Generate final combinations
    final_combinations = [list(combination) for combination in
                          itertools.product(all_combinations, normalize_combinations)]

    return final_combinations

# ---- Random Transformation + Normalize selection logic ----
def get_random_combination(servers, max_transforms=2):
    total_combination_num = calculate_combinations(servers)

    if len(executed_combinations) == total_combination_num:
        print("[Completed] All possible combinations explored.")
        return None, None

    while True:
        selected_transforms = []
        normalize_config = [False] * len(servers)

        for idx, server in enumerate(servers):
            # Include transformation_list + essential_transformation_list
            combined_transformations = server.transformation_list + server.essential_transformation_list

            sample_size = random.randint(0, min(max_transforms, len(combined_transformations)))
            sampled_transforms = random.sample(
                combined_transformations,
                sample_size
            )
            print(f"[Debug] Server: {server.name} | random.sample result: {sampled_transforms}")

            selected_transforms.append(sorted(sampled_transforms, key=lambda x: x.name))

            # Debug: Print final selected transforms
            print(f"[Debug] Server: {server.name} | Final selected_transforms: {selected_transforms[-1]}")

        # Add normalize setting (at most one True)
        if any(server.is_normalize for server in servers):
            normalize_candidate_indices = [idx for idx, server in enumerate(servers) if server.is_normalize]
            selected_normalize_index = random.choice(normalize_candidate_indices + [-1])

            if selected_normalize_index != -1:
                normalize_config[selected_normalize_index] = True

        # Record combination as tuple of sorted transform names for consistent handling
        combination = tuple(
            (tuple(sorted(trans.name for trans in selected_transforms[i])) or ("None",), normalize_config[i])
            for i in range(len(servers))
        )

        if combination in executed_combinations:
            continue

        # Record and return new combination
        executed_combinations.add(combination)
        return selected_transforms, normalize_config

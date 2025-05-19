import os
import sys
import json
import urllib.parse
from pathlib import Path

import astor
import ast
import subprocess
from typing import List, Dict, Tuple

import black
import click
from pathfault.logger import setup_logger

from pathfault.inconsistency.server import Server, InconsistencyInfo, InconsistencyEntry
from pathfault.inconsistency.condition import ContainsType, _ConditionType, HasSlashAfterDelimiterType
from pathfault.inconsistency.transformation import (
    ReplaceTransformation,
    Transformation,
    SubStringUntilTransformation,
    DelimiterSlashSplitTransformation,
)

logger = setup_logger(__name__)


def load_json(json_path: str) -> dict:
    """Load and return JSON data; exit on failure."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load JSON file '{json_path}': {e}")
        sys.exit(1)


def print_json_keys(json_keys: List[str]) -> None:
    """Log the top-level keys found in the JSON file."""
    logger.info("Available JSON top‐level keys:")
    for idx, key in enumerate(json_keys, 1):
        logger.info(f"  {idx}. {key}")


def print_server_list(server_list: List[str]) -> None:
    """Log the list of servers to be processed."""
    logger.info("Server list to process:")
    for idx, srv in enumerate(server_list, 1):
        logger.info(f"  {idx}. {srv}")


def check_server_inclusion(json_keys: List[str], server_list: List[str]) -> None:
    """Verify that each requested server exists in the JSON data."""
    missing = []
    for srv in server_list:
        if srv in json_keys:
            logger.info(f"Server '{srv}' found in JSON ✅")
        else:
            logger.error(f"Server '{srv}' missing from JSON ❌")
            missing.append(srv)
    if missing:
        logger.error(f"The following servers are not present: {', '.join(missing)}")
        sys.exit(1)


def hex_to_char(hex_value: str) -> str:
    """
    Convert a hex string to its character representation.
    - 'empty' maps to empty string
    - tries UTF-8 then Latin-1 decoding
    """
    if hex_value.lower() == "empty" or not hex_value:
        return ""
    try:
        return bytes.fromhex(hex_value).decode("utf-8", errors="replace")
    except Exception:
        try:
            return bytes.fromhex(hex_value).decode("latin-1", errors="replace")
        except Exception:
            logger.warning(f"Ignoring invalid hex value '{hex_value}'")
            return ""


def process_inconsistency(
    inconsistency_data: dict,
) -> Tuple[List[InconsistencyInfo], List[InconsistencyInfo]]:
    """
    Parse inconsistency_data into two lists:
    - inconsistency_info: genuine mismatches
    - excluded_info: those matching percent-encoding exactly
    """
    inconsistency_map: Dict[str, InconsistencyInfo] = {}
    excluded_map: Dict[str, InconsistencyInfo] = {}

    for hex_value, details in inconsistency_data.items():
        char_value = hex_to_char(hex_value)
        if char_value == "":
            logger.info(f"Hex '{hex_value}' interpreted as empty, continuing comparison")
        elif not char_value:
            continue

        # build percent‐encoded hex
        encoded_str = urllib.parse.quote(char_value)
        encoded_hex = "".join(f"{ord(c):02X}" for c in encoded_str)

        for req_type, content in details.items():
            inbound = content.get("inbound_url", "")
            outbound = content.get("outbound_url", "")

            # replace occurrences of hex_value in inbound_url with encoded_hex
            modified = ""
            i = 0
            while i < len(inbound):
                if inbound[i : i + len(hex_value)] == hex_value:
                    modified += encoded_hex
                    i += len(hex_value)
                else:
                    modified += inbound[i : i + 2]
                    i += 2

            # also derive human chars
            inbound_char = "".join(hex_to_char(inbound[i : i + 2]) or "" for i in range(0, len(inbound), 2))
            outbound_char = "".join(hex_to_char(outbound[i : i + 2]) or "" for i in range(0, len(outbound), 2))

            entry = InconsistencyEntry(
                inconsistency_request_type=req_type,
                inbound_url=inbound,
                inbound_url_char=inbound_char,
                outbound_url=outbound,
                outbound_url_char=outbound_char,
            )

            # decide map
            target_map = excluded_map if modified == outbound else inconsistency_map
            if hex_value not in target_map:
                target_map[hex_value] = InconsistencyInfo(
                    hex_value=hex_value, char_value=char_value, entries=[]
                )
            target_map[hex_value].entries.append(entry)

    return list(inconsistency_map.values()), list(excluded_map.values())


def add_transformations_from_inconsistency_info(server: Server) -> None:
    """
    From server.inconsistency_info, append the correct Transformation objects:
    - look for composite_middle_without_slash first
    - then for composite_middle
    - otherwise record as unprocessed
    """
    for d in server.inconsistency_info:
        no_slash = next(
            (e for e in d.entries if e.inconsistency_request_type == "transformation_composite_middle_without_slash"),
            None,
        )
        middle = next(
            (e for e in d.entries if e.inconsistency_request_type == "transformation_composite_middle"), None
        )

        # Case 1: composite without slash
        if no_slash:
            out_char = no_slash.outbound_url_char
            A = d.char_value

            if out_char == "/tmp1/tmp2":
                name = f"Inconsistency_transformation_composite_middle_without_slash({A})"
                server.transformation_list.append(
                    Transformation(
                        name=name,
                        transformation_type=SubStringUntilTransformation(offset=0, delimiter=A),
                        conditions=[ContainsType(A)],
                    )
                )
            elif out_char == "/tmp1/tmp2/tmp4":
                name = f"Inconsistency_transformation_composite_middle_with_slash({A})"
                # external slash split
                server.transformation_list.append(
                    Transformation(
                        name=name,
                        transformation_type=DelimiterSlashSplitTransformation(delimiter=A),
                        conditions=[ContainsType(A), HasSlashAfterDelimiterType(A)],
                    )
                )
                # substring until
                server.transformation_list.append(
                    Transformation(
                        name=name,
                        transformation_type=SubStringUntilTransformation(offset=0, delimiter=A),
                        conditions=[ContainsType(A), HasSlashAfterDelimiterType(A, not_condition=True)],
                    )
                )
            else:
                server.unprocessed_inconsistency_info.append(
                    InconsistencyInfo(
                        hex_value=d.hex_value,
                        char_value=d.char_value,
                        entries=[
                            InconsistencyEntry(
                                inconsistency_request_type=f"transformation_composite_middle_without_slash({A})",
                                inbound_url=no_slash.inbound_url_char,
                                inbound_url_char=no_slash.inbound_url_char,
                                outbound_url=out_char,
                                outbound_url_char=out_char,
                            )
                        ],
                    )
                )

        # Case 2: composite middle
        elif middle:
            in_char = middle.inbound_url_char
            out_char = middle.outbound_url_char
            target = in_char.replace("/tmp1", "").replace("tmp2", "")
            replace = out_char.replace("/tmp1", "").replace("tmp2", "")

            if target and replace:
                name = f"Inconsistency_transformation_composite_middle({target} -> {replace})"
                server.transformation_list.append(
                    Transformation(
                        name=name,
                        transformation_type=ReplaceTransformation(target_str=target, replace_str=replace),
                        conditions=[ContainsType(target)],
                    )
                )
            else:
                server.unprocessed_inconsistency_info.append(
                    InconsistencyInfo(
                        hex_value=d.hex_value,
                        char_value=d.char_value,
                        entries=[
                            InconsistencyEntry(
                                inconsistency_request_type=f"transformation_composite_middle({d.char_value})",
                                inbound_url=in_char,
                                inbound_url_char=in_char,
                                outbound_url=out_char,
                                outbound_url_char=out_char,
                            )
                        ],
                    )
                )


def create_condition_list_from_bad_data(bad_data: dict) -> List[_ConditionType]:
    """
    Build a list of negative ContainsType conditions for each bad‐hex.
    Skips invalid or '%' results.
    """
    conds: List[_ConditionType] = []
    for hx in bad_data.keys():
        try:
            ch = bytes.fromhex(hx).decode("utf-8", errors="ignore")
        except Exception:
            logger.warning(f"Ignoring invalid hex '{hx}'")
            continue
        if ch == "%":
            logger.warning(f"Skipping '%' from hex '{hx}'")
            continue
        if ch:
            conds.append(ContainsType(condition_str=ch, not_condition=True))
    return conds


def create_servers(data: dict, server_list: List[str]) -> List[Server]:
    """
    From JSON data and server_list, build Server objects:
    1. generate conditions
    2. parse inconsistencies
    3. instantiate Server
    4. add transformations
    """
    servers: List[Server] = []
    for name in server_list:
        sd = data[name]
        is_norm = sd.get("is_normalize", False)
        is_dec = sd.get("is_decode", False)

        trans = sd.get("transformation", {})
        bad = trans.get("bad", {})
        conds = create_condition_list_from_bad_data(bad)

        disc, excl = process_inconsistency(trans.get("inconsistency", {}))

        srv = Server(name=name, condition_list=conds, is_normalize=is_norm, is_decode=is_dec)
        srv.inconsistency_info = disc
        srv.omitted_inconsistency_info = excl

        add_transformations_from_inconsistency_info(srv)
        servers.append(srv)
    return servers


def print_created_servers(servers: List[Server]) -> None:
    """Log out each created Server and its details (debug-level logging)."""
    for srv in servers:
        logger.debug(
            f"Server(name={srv.name}, is_normalize={srv.is_normalize}, "
            f"is_decode={srv.is_decode})"
        )
        if srv.condition_list:
            logger.debug("  Conditions:")
            for c in srv.condition_list:
                s = "".join(c if 32 <= ord(c) <= 126 else f"\\x{ord(c):02x}" for c in c.condition_str)
                logger.debug(f"    - {c.__class__.__name__}(str='{s}', NOT={c.not_condition})")
        else:
            logger.debug("  No conditions")

        if srv.inconsistency_info:
            logger.debug("  Inconsistency:")
            for info in srv.inconsistency_info:
                logger.debug(f"    - HEX {info.hex_value} -> '{info.char_value}'")
                for e in info.entries:
                    logger.debug(f"      * [{e.inconsistency_request_type}] in='{e.inbound_url_char}' out='{e.outbound_url_char}'")
        else:
            logger.debug("  No inconsistencies")

        if srv.omitted_inconsistency_info:
            logger.debug("  Excluded Inconsistency:")
            for info in srv.omitted_inconsistency_info:
                logger.debug(f"    - HEX {info.hex_value} -> '{info.char_value}'")
        else:
            logger.debug("  No excluded inconsistencies")

        if srv.transformation_list:
            logger.debug("  Transformations:")
            for t in srv.transformation_list:
                logger.debug(f"    - {t.name} ({t.transformation_type.__class__.__name__})")
        else:
            logger.debug("  No transformations")
        logger.debug("")


def print_unprocessed_inconsistency_info(servers: List[Server]) -> None:
    """Log any inconsistency infos that were not processed into transformations."""
    count = 0
    for srv in servers:
        for info in srv.unprocessed_inconsistency_info:
            count += 1
            logger.warning(
                f"Unprocessed HEX {info.hex_value} -> '{info.char_value}', entries: "
                + ", ".join(e.inconsistency_request_type for e in info.entries)
            )
    if count == 0:
        logger.info("All inconsistencies processed successfully.")
    else:
        logger.warning(f"{count} inconsistencies remain unprocessed.")


def server_to_ast_node(server: Server, include_omitted_inconsistency: bool = False) -> ast.Assign:
    """
    Convert a Server object into an AST node for code generation.
    """
    keywords = [
        ast.keyword(arg="name", value=ast.Constant(server.name)),
        ast.keyword(
            arg="condition_list",
            value=ast.List(
                elts=[c.to_ast() for c in server.condition_list], ctx=ast.Load()
            ),
        ),
        ast.keyword(
            arg="target_pre_condition_list",
            value=ast.List(
                elts=[c.to_ast() for c in server.target_pre_condition_list], ctx=ast.Load()
            ),
        ),
        ast.keyword(
            arg="target_post_condition_list",
            value=ast.List(
                elts=[c.to_ast() for c in server.target_post_condition_list], ctx=ast.Load()
            ),
        ),
        ast.keyword(
            arg="transformation_list",
            value=ast.List(
                elts=[t.to_ast() for t in server.transformation_list], ctx=ast.Load()
            ),
        ),
        ast.keyword(
            arg="essential_transformation_list",
            value=ast.List(
                elts=[t.to_ast() for t in server.essential_transformation_list],
                ctx=ast.Load(),
            ),
        ),
        ast.keyword(arg="is_normalize", value=ast.Constant(server.is_normalize)),
        ast.keyword(arg="is_decode", value=ast.Constant(server.is_decode)),
    ]
    if include_omitted_inconsistency:
        keywords += [
            ast.keyword(
                arg="inconsistency_info",
                value=ast.List(elts=[i.to_ast() for i in server.inconsistency_info], ctx=ast.Load()),
            ),
            ast.keyword(
                arg="omitted_inconsistency_info",
                value=ast.List(
                    elts=[i.to_ast() for i in server.omitted_inconsistency_info],
                    ctx=ast.Load(),
                ),
            ),
            ast.keyword(
                arg="unprocessed_inconsistency_info",
                value=ast.List(
                    elts=[i.to_ast() for i in server.unprocessed_inconsistency_info], ctx=ast.Load()
                ),
            ),
        ]
    return ast.Assign(
        targets=[ast.Name(id=server.name, ctx=ast.Store())],
        value=ast.Call(func=ast.Name(id="Server", ctx=ast.Load()), args=[], keywords=keywords),
    )


def generate_output_file(
    servers: List[Server], output_path: str = "surrogate_model.py", include_omitted_inconsistency: bool = False
) -> None:
    """
    Emit a Python module containing get_surrogate_model() that returns our Server list.
    """
    module_body = [
        ast.ImportFrom(module="z3", names=[ast.alias(name="*")], level=0),
        ast.ImportFrom(module="pathfault.inconsistency.server", names=[ast.alias(name="Server")], level=0),
        ast.ImportFrom(module="pathfault.inconsistency.transformation", names=[ast.alias(name="*")], level=0),
        ast.ImportFrom(module="pathfault.inconsistency.condition", names=[ast.alias(name="*")], level=0),
        ast.FunctionDef(
            name="get_surrogate_model",
            args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
            body=[*[
                server_to_ast_node(srv, include_omitted_inconsistency) for srv in servers
            ], ast.Return(value=ast.List(elts=[ast.Name(id=srv.name, ctx=ast.Load()) for srv in servers], ctx=ast.Load()))],
            decorator_list=[],
        ),
    ]
    module = ast.fix_missing_locations(ast.Module(body=module_body, type_ignores=[]))
    code = ast.unparse(module)

    # ✅ Apply Black formatting in memory
    try:
        formatted_code = black.format_str(code, mode=black.FileMode())
    except Exception as e:
        logger.warning(f"Black formatting failed: {e}")
        formatted_code = code

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(formatted_code)

    logger.info(f"Surrogate model written to {output_path}")


@click.command("build-surrogate-model")
@click.option("--json", "json_path", required=True, help="Path to input JSON data.")
@click.option(
    "--server-list",
    callback=lambda ctx, param, value: sum((s.split(",") for s in value), []),
    multiple=True,
    help="List of servers (space or comma separated).",
    required=True,
)
@click.option("--output", default="./pathfault/results/surrogate_model_builder/surrogate_model.py", show_default=True, help="Output Python model file.")
@click.option(
    "--include-omitted-inconsistency",
    is_flag=True,
    default=False,
    help="If set, include omitted inconsistency info from the generated model.",
)
def cli_build_surrogate_model(json_path, server_list, output, include_omitted_inconsistency):
    """
    Build a surrogate-model Python file from JSON inconsistency data.
    """
    logger.info("Starting surrogate-model build…")
    data = load_json(json_path)
    keys = list(data.keys())
    print_json_keys(keys)

    # choose servers
    slist = list(server_list) if server_list else keys
    print_server_list(slist)
    check_server_inclusion(keys, slist)

    servers = create_servers(data, slist)
    print_created_servers(servers)
    print_unprocessed_inconsistency_info(servers)

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    generate_output_file(servers, output, include_omitted_inconsistency)
    logger.info(f"Surrogate model successfully written to: {Path(output).resolve()}")
    logger.info("Surrogate-model build complete.")


__all__ = ["cli_build_surrogate_model"]
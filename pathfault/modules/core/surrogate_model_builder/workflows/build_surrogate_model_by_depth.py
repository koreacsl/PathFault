import json
import itertools
import os
import sys
from pathlib import Path
from typing import List

import click
from pathfault.logger import setup_logger
from pathfault.modules.core.surrogate_model_builder.services.build_surrogate_model import (
    cli_build_surrogate_model,
)

logger = setup_logger(__name__)

def load_json_keys(json_path: str) -> List[str]:
    """Load the top-level keys from the specified JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return list(json.load(f).keys())
    except Exception as e:
        logger.error(f"Failed to load JSON file: {e}")
        sys.exit(1)

def generate_combinations(keys: List[str], depth: int) -> List[tuple]:
    """Generate all permutations of keys with the specified depth."""
    return list(itertools.permutations(keys, depth))

@click.command("build-surrogate-model-by-depth")
@click.option("--json", "json_path", required=True, help="Path to the JSON input file of anlysis_results.")
@click.option("--depth", required=True, type=int, help="Depth of server combinations to generate.")
@click.option(
    "--output-dir",
    default="./pathfault/results/surrogate_model_builder",
    show_default=True,
    type=click.Path(),
    help="Base directory where output models will be saved.",
)
@click.option(
    "--include-omitted-inconsistency",
    is_flag=True,
    default=False,
    help="If set, include omitted inconsistency info in model output.",
)
def cli_build_surrogate_model_by_depth(json_path: str, depth: int, output_dir: str, include_omitted_inconsistency: bool):
    """
    Automatically generate surrogate model Python files for all server combinations
    of the specified depth using the given JSON file. Each generated model will be
    stored under a subdirectory named 'surrogate_model_depth_{depth}' inside output-dir.
    """
    logger.info(f"Generating surrogate models from: {json_path} with depth={depth}")
    keys = load_json_keys(json_path)
    combinations = generate_combinations(keys, depth)

    base_output = Path(output_dir).resolve()
    target_output_dir = base_output / f"surrogate_model_depth_{depth}"
    target_output_dir.mkdir(parents=True, exist_ok=True)

    for combo in combinations:
        filename = f"surrogate_model_{'_'.join(combo)}.py"
        output_path = target_output_dir / filename

        try:
            ctx = click.Context(cli_build_surrogate_model)
            ctx.invoke(
                cli_build_surrogate_model,
                json_path=json_path,
                server_list=list(combo),
                output=str(output_path),
                include_omitted_inconsistency=include_omitted_inconsistency,
            )
            logger.info(f"✅ Generated: {output_path}")
        except Exception as e:
            logger.warning(f"❌ Failed to generate {output_path}: {e}")

__all__ = ["cli_build_surrogate_model_by_depth"]
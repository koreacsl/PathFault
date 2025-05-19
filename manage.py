import sys
import click
import logging

from pathfault.logger import setup_logger

# Core service command for inconsistency detection
# Core module for inconsistency detection (same style as mimic_environment)
from pathfault.modules.core.inconsistency_detector.detector import inconsistency_detector_command

# Core modules for other components
from pathfault.modules.core.exploit_payload_generator.generator import exploit_generator_command
from pathfault.modules.core.surrogate_model_builder.builder import surrogate_model_builder_command

# Utility module for mimic environment generation
from pathfault.modules.utilities.mimic_environment_creator.creator import create_mimic_environment_command

logger = setup_logger(__name__)

# Global logging level setup
logging.root.setLevel(logging.INFO)
for handler in logging.root.handlers:
    handler.setLevel(logging.INFO)

# Enable debug mode if specified in CLI arguments
debug_mode = '--debug' in sys.argv
if debug_mode:
    sys.argv.remove('--debug')
    logging.root.setLevel(logging.DEBUG)
    for handler in logging.root.handlers:
        handler.setLevel(logging.DEBUG)
    logger.debug("Debug mode activated.")


@click.group(invoke_without_command=True)
@click.option('--debug', is_flag=True, default=False, help="Enable debug output.")
@click.pass_context
def cli(ctx, debug):
    """
    PathFault CLI entry point.
    Provides access to core analysis tools, utility modules, and high-level workflows.
    """
    if debug:
        logging.root.setLevel(logging.DEBUG)
        for handler in logging.root.handlers:
            handler.setLevel(logging.DEBUG)
        logger.debug("Debug mode activated.")

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()

    logger.info("Starting PathFault CLI...")


@click.group()
def core():
    """
    Core commands for inconsistency detection, surrogate modeling, and exploit generation.
    """
    pass

core.add_command(inconsistency_detector_command)
core.add_command(surrogate_model_builder_command)
core.add_command(exploit_generator_command)


@click.group()
def utilities():
    """
    Utility commands for environment setup and tool scaffolding.
    """
    pass

utilities.add_command(create_mimic_environment_command)


# Attach groups to root CLI
cli.add_command(core)
cli.add_command(utilities)


if __name__ == "__main__":
    cli()
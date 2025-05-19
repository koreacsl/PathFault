import click
from pathfault.logger import setup_logger
from pathfault.modules.core.surrogate_model_builder.services.build_surrogate_model import cli_build_surrogate_model
from pathfault.modules.core.surrogate_model_builder.workflows.build_surrogate_model_by_depth import \
    cli_build_surrogate_model_by_depth

logger = setup_logger(__name__)

@click.group("surrogate-model-builder")
def surrogate_model_builder_command():
    """
    Commands for building surrogate models for HTTP component behavior.
    Divided into service-level commands and workflow-level pipelines.
    """
    logger.info("Entered 'surrogate-model-builder' command group.")

@click.group("services")
def services_group():
    """Service-level commands related to surrogate model construction."""
    pass

@click.group("workflows")
def workflows_group():
    """Workflow-level commands to orchestrate surrogate model generation and usage."""
    pass


# Register future commands here
services_group.add_command(cli_build_surrogate_model)
workflows_group.add_command(cli_build_surrogate_model_by_depth)

surrogate_model_builder_command.add_command(services_group)
surrogate_model_builder_command.add_command(workflows_group)

__all__ = ["surrogate_model_builder_command"]
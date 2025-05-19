import click
from pathfault.logger import setup_logger

# Import service-level commands
from pathfault.modules.utilities.mimic_environment_creator.services.create_entrypoint_script import create_entrypoint_script
from pathfault.modules.utilities.mimic_environment_creator.services.create_dockerfile import create_dockerfile
from pathfault.modules.utilities.mimic_environment_creator.services.create_port_map import create_port_map_command
from pathfault.modules.utilities.mimic_environment_creator.services.create_docker_compose_file import create_docker_compose

# Import workflow-level commands
from pathfault.modules.utilities.mimic_environment_creator.workflows.create_mimic_environment import create_mimic_environment

logger = setup_logger(__name__)

@click.group("mimic-environment-creator")
def create_mimic_environment_command():
    """
    Create a mimic environment by composing multiple service modules and workflows.
    - Services: Basic building blocks like Dockerfile generation, port map creation, etc.
    - Workflows: High-level commands that orchestrate multiple services together.
    """
    logger.info("Entered 'create-mimic-environment' group.")

# Create a subgroup for services
@click.group("services")
def services_group():
    """Basic service commands for mimic environment creation."""
    pass

# Create a subgroup for workflows
@click.group("workflows")
def workflows_group():
    """Workflow commands that compose multiple services."""
    pass

# Register service commands under 'services' group
services_group.add_command(create_entrypoint_script)
services_group.add_command(create_dockerfile)
services_group.add_command(create_port_map_command)
services_group.add_command(create_docker_compose)

# ✅ Register workflow command under 'workflows' group
workflows_group.add_command(create_mimic_environment)

# Register both groups under the top-level 'create-mimic-environment' group
create_mimic_environment_command.add_command(services_group)
create_mimic_environment_command.add_command(workflows_group)

# Export for manage.py
__all__ = ["create_mimic_environment_command"]
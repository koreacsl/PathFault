import os
import click
from pathfault.logger import setup_logger

# Import service functions
from pathfault.modules.utilities.mimic_environment_creator.services.create_entrypoint_script import create_entrypoint_script
from pathfault.modules.utilities.mimic_environment_creator.services.create_dockerfile import create_dockerfile
from pathfault.modules.utilities.mimic_environment_creator.services.create_port_map import create_port_map_command
from pathfault.modules.utilities.mimic_environment_creator.services.create_docker_compose_file import create_docker_compose

logger = setup_logger(__name__)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

@click.command("create-mimic-environment")
@click.option("--web-app-config-path", required=True, help="Path to web_app_components config.json file.")
@click.option(
    "--web-app-result-dir",
    required=False,
    default="./pathfault/results/mimic_environment_creator/web_app_components",
    show_default=True,
    help="Directory to output generated Dockerfiles and scripts."
)
@click.option(
    "--port-map-path",
    required=False,
    default="./pathfault/results/mimic_environment_creator/port_map.json",
    show_default=True,
    help="Path to output generated port_map.json."
)
@click.option(
    "--docker-compose-path",
    required=False,
    default="./pathfault/results/mimic_environment_creator/docker-compose.yml",
    show_default=True,
    help="Path to output generated docker-compose.yml."
)
def create_mimic_environment(web_app_config_path, web_app_result_dir, port_map_path, docker_compose_path):
    """
    Full workflow to create a complete mimic environment:
    - Generate entrypoint.sh scripts
    - Generate Dockerfiles
    - Generate port_map.json
    - Generate docker-compose.yml
    """

    logger.info("🚀 Starting full mimic environment creation workflow...")

    ctx = click.get_current_context()

    logger.info("Step 1: Generating entrypoint.sh scripts...")
    ctx.invoke(create_entrypoint_script, web_app_config_path=web_app_config_path)

    logger.info("Step 2: Generating Dockerfiles...")
    ctx.invoke(create_dockerfile, web_app_config_path=web_app_config_path)

    logger.info("Step 3: Generating port_map.json...")
    ctx.invoke(create_port_map_command, web_app_result_dir=web_app_result_dir, output_path=port_map_path)

    logger.info("Step 4: Generating docker-compose.yml...")
    ctx.invoke(create_docker_compose, web_app_result_dir=web_app_result_dir, port_map_path=port_map_path, output_path=docker_compose_path)

    logger.info("🎉 Full mimic environment setup has been successfully completed!")

    # Convert to PROJECT_ROOT-relative paths
    def to_relative(path):
        return os.path.relpath(os.path.abspath(path), PROJECT_ROOT)

    logger.info("📦 Final Output Summary (relative to PROJECT_ROOT):")
    logger.info(f"  - Entrypoint scripts directory : {to_relative(web_app_result_dir)}/*/entrypoint.sh")
    logger.info(f"  - Dockerfiles directory        : {to_relative(web_app_result_dir)}/*/Dockerfile")
    logger.info(f"  - Port map JSON                : {to_relative(port_map_path)}")
    logger.info(f"  - Docker Compose file          : {to_relative(docker_compose_path)}")

# Exportable for import into the workflows group
__all__ = ["create_mimic_environment"]

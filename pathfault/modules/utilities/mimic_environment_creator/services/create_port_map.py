import os
import json
import click
from pathfault.logger import setup_logger

logger = setup_logger(__name__)

def extract_exposed_port(dockerfile_path):
    """
    Extract the exposed port number from a Dockerfile.
    """
    try:
        with open(dockerfile_path, "r") as dockerfile:
            for line in dockerfile:
                if line.strip().startswith("EXPOSE"):
                    parts = line.strip().split()
                    if len(parts) > 1 and parts[1].isdigit():
                        return int(parts[1])
    except FileNotFoundError:
        logger.warning(f"Dockerfile not found: {dockerfile_path}")
    return None

def process_web_app_components(web_app_result_dir, port_map):
    """
    Process each web_app_component directory to extract EXPOSE port and populate the port map.
    """
    if not os.path.exists(web_app_result_dir):
        logger.error(f"Directory not found: {web_app_result_dir}")
        raise click.ClickException("web_app_component result directory does not exist.")

    for name in os.listdir(web_app_result_dir):
        component_path = os.path.join(web_app_result_dir, name)
        if not os.path.isdir(component_path):
            continue

        dockerfile_path = os.path.join(component_path, "Dockerfile")
        exposed_port = extract_exposed_port(dockerfile_path)

        if exposed_port is None:
            logger.warning(f"No EXPOSE directive found in: {dockerfile_path}")
            continue

        port_map[name] = exposed_port
        logger.info(f"Mapped {name} to port {exposed_port}")

@click.command("create-port-map")
@click.option(
    "--web-app-result-dir",
    required=True,
    help="Path to the directory containing built web_app_component Dockerfiles."
)
@click.option(
    "--output-path",
    required=True,
    help="Path to save the resulting port_map.json (e.g. ./results/port_map.json)"
)
def create_port_map_command(web_app_result_dir, output_path):
    """
    Generate a port_map.json mapping each web_app_component directory to its exposed port.
    """
    logger.info("Starting port map creation for web_app_components...")

    port_map = {}
    process_web_app_components(web_app_result_dir, port_map)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as file:
        json.dump(port_map, file, indent=4)

    logger.info(f"Port map saved to: {output_path}")
    logger.info(f"Total components mapped: {len(port_map)}")

import os
import json
import yaml
import click
from pathfault.logger import setup_logger

logger = setup_logger(__name__)

def extract_exposed_port(dockerfile_path):
    """Extract the exposed port from a Dockerfile."""
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

def ensure_dot_slash(path):
    """Ensure that a path starts with './'."""
    if not (path.startswith("./") or path.startswith("/")):
        return f"./{path}"
    return path

def process_components(result_dir, port_map_path, compose_output_path, services):
    """Process all web_app_component directories to construct Docker Compose service definitions."""
    if not os.path.exists(result_dir):
        logger.error(f"Result directory does not exist: {result_dir}")
        raise click.ClickException("Result directory missing.")

    compose_base_dir = os.path.dirname(compose_output_path)
    relative_port_map_path = os.path.relpath(port_map_path, compose_base_dir)
    relative_port_map_path = ensure_dot_slash(relative_port_map_path)

    for component in os.listdir(result_dir):
        component_path = os.path.join(result_dir, component)
        if not os.path.isdir(component_path):
            continue

        dockerfile_path = os.path.join(component_path, "Dockerfile")
        exposed_port = extract_exposed_port(dockerfile_path)
        if exposed_port is None:
            logger.warning(f"No EXPOSE directive found in: {dockerfile_path}. Skipping {component}.")
            continue

        relative_context = os.path.relpath(component_path, compose_base_dir)
        relative_context = ensure_dot_slash(relative_context)

        services[component] = {
            "container_name": component,
            "build": {
                "context": relative_context,
                "dockerfile": "Dockerfile",
            },
            "ports": [f"{exposed_port}:{exposed_port}"],
            "volumes": [
                "./logs:/app/logs",
                f"{relative_port_map_path}:/app/port_map.json"
            ],
            "environment": {
                "PORT": str(exposed_port),
                "PORT_MAP_PATH": "/app/port_map.json"
            },
            "cap_add": ["NET_ADMIN"]
        }
        logger.info(f"Configured service '{component}' on port {exposed_port}")

@click.command("create-docker-compose-file")
@click.option("--web-app-result-dir", required=True, help="Path to the directory containing built web_app_component Dockerfiles.")
@click.option("--port-map-path", required=True, help="Path to the port_map.json file.")
@click.option("--output-path", required=True, help="Path to output docker-compose.yml file.")
def create_docker_compose(web_app_result_dir, port_map_path, output_path):
    """Generate a docker-compose.yml file for all web_app_components."""
    logger.info("Starting docker-compose.yml generation...")
    logger.info(f"Reading from: {web_app_result_dir}")
    logger.info(f"Using port map: {port_map_path}")
    logger.info(f"Output will be saved to: {output_path}")

    if not os.path.exists(port_map_path):
        logger.error(f"Port map file not found: {port_map_path}")
        raise click.ClickException("Missing port_map.json file.")

    services = {}
    process_components(web_app_result_dir, port_map_path, output_path, services)

    docker_compose = {
        "version": "3.9",
        "services": services
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as file:
        yaml.dump(docker_compose, file, default_flow_style=False, sort_keys=False)

    logger.info(f"docker-compose.yml has been successfully written to: {output_path}")
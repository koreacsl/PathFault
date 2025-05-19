import os
import json
import click
from pathfault.logger import setup_logger

logger = setup_logger(__name__)


def extract_ports(port_map):
    return list({v for k, v in port_map.items() if k != "tmpserver"})


def generate_urls(ports):
    return [f"http://127.0.0.1:{port}" for port in ports]


@click.command("create-inconsistency-detector-config")
@click.option("--port-map-path", required=True, help="Path to port_map.json file.")
@click.option(
    "--output-path",
    default="./pathfault/results/inconsistency_detector/inconsistency_detector_config",
    show_default=True,
    help="Output config file path.",
)
def create_inconsistency_detector_config(port_map_path, output_path):
    """Generate configuration file for inconsistency detector."""
    logger.info("Starting generation of inconsistency_detector_config...")

    if not os.path.exists(port_map_path):
        raise click.ClickException(f"Port map file not found: {port_map_path}")

    with open(port_map_path, "r") as f:
        port_map = json.load(f)

    ports = extract_ports(port_map)
    urls = generate_urls(ports)
    headers = ["127.0.0.1"] * len(urls)

    config_lines = [
        f"config.target_urls = {urls}\n",
        f"config.target_host_headers = {headers}\n",
        "config.grammar = {\n",
        "    '<start>': ['<request>'],\n",
        "    '<request>': ['<method-name><space><request-line><base>'],\n",
        "    '<request-line>': ['<uri><space><protocol><separator><version><newline>'],\n",
        "    '<method-name>': ['GET'],\n",
        "    '<space>': [' '],\n",
        "    '<uri>': ['_URI_'],\n",
        "    '<protocol>': ['HTTP'],\n",
        "    '<separator>': ['/'],\n",
        "    '<version>': ['1.0'],\n",
        "    '<newline>': ['\\r\\n'],\n",
        "    '<base>': ['Host: _HOST_\\r\\nConnection:close\\r\\nX-Request-Type: _REQUEST_TYPE_\\r\\nX-Request-ID: _REQUEST_ID_\\r\\nX-Request-Seed: _REQUEST_SEED_\\r\\nContent-Length: _CONTENT_LENGTH_\\r\\n\\r\\n'],\n",
        "}\n"
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.writelines(config_lines)

    logger.info(f"Successfully wrote inconsistency detector config to: {output_path}")
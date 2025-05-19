import os
import json
import shutil
import click
from pathfault.logger import setup_logger

logger = setup_logger(__name__)

# Default paths
DEFAULT_WEB_APP_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "presets", "create_mimic_environment_config.json")
DEFAULT_WEB_APP_DIR = os.path.join(os.path.dirname(__file__), "..", "web_app_components")
DEFAULT_RESULT_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "results", "mimic_environment_creator"))
DEFAULT_RESULT_DIR = os.path.join(DEFAULT_RESULT_BASE_DIR, "web_app_components")
DEFAULT_PORT_MAP_PATH = os.path.join(DEFAULT_RESULT_BASE_DIR, "port_map.json")

def load_web_app_config(config_path):
    """Load the web application configuration JSON file."""
    try:
        with open(config_path, "r") as file:
            config = json.load(file)
            logger.debug(f"Loaded configuration: {config}")
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise click.ClickException("Missing configuration file.")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in configuration file: {config_path}")
        raise click.ClickException("Invalid JSON format.")

def extract_container_name(name):
    """Convert the service name into a lowercase container-friendly name."""
    return name.lower()

def create_entrypoint_script_for_component(output_dir, container_name, frag_path):
    """Generate the entrypoint.sh script for a given component."""
    entrypoint_path = os.path.join(output_dir, "entrypoint.sh")

    try:
        with open(entrypoint_path, "w") as entrypoint_file:
            entrypoint_file.write(
                "#!/bin/bash\n\n"
                f"export LOG_DIR=\"/app/logs/{container_name}\"\n"
                "mkdir -p $LOG_DIR\n\n"
                "EXTERNAL_INTERFACE=$(ip -o -4 addr show | awk '{print $2}' | grep -v lo)\n"
                "if [ -z \"$EXTERNAL_INTERFACE\" ]; then\n"
                "  echo \"Error: Unable to detect network interface.\"\n"
                "  exit 1\n"
                "fi\n"
                "echo \"Using interface: $EXTERNAL_INTERFACE\"\n\n"
                "if [ -z \"$PORT\" ]; then\n"
                "  echo \"Error: The environment variable 'PORT' is not set.\"\n"
                "  exit 1\n"
                "fi\n"
                "echo \"Using port: $PORT\"\n\n"
                "SERVER_IP=$(ip -o -4 addr list \"$EXTERNAL_INTERFACE\" | awk '{print $4}' | cut -d/ -f1)\n"
                "if [ -z \"$SERVER_IP\" ]; then\n"
                "  echo \"Error: Unable to determine server IP address.\"\n"
                "  exit 1\n"
                "fi\n"
                "echo \"Server IP: $SERVER_IP\"\n\n"
                "tshark -i \"$EXTERNAL_INTERFACE\" "
                "-f \"tcp dst port $PORT and tcp[13] & 24 == 24\" "
                "-w \"$LOG_DIR/capture_inbound.pcap\" "
                "-b packets:10 &\n"
                "echo \"Started capturing inbound HTTP requests.\"\n\n"
                "tshark -i \"$EXTERNAL_INTERFACE\" "
                "-f \"tcp[13] & 24 == 24 and not tcp src port $PORT and ip src $SERVER_IP\" "
                "-w \"$LOG_DIR/capture_outbound.pcap\" "
                "-b packets:10 &\n"
                "echo \"Started capturing outbound HTTP responses.\"\n\n"
            )

            if os.path.exists(frag_path):
                with open(frag_path, "r") as frag_file:
                    entrypoint_file.write(frag_file.read())
            else:
                logger.warning(f"Fragment file missing for {container_name}: {frag_path}")

        logger.debug(f"Created entrypoint.sh for '{container_name}' at {entrypoint_path}")

    except Exception as e:
        logger.error(f"Failed to create entrypoint.sh for '{container_name}': {e}")

@click.command("create-entrypoint-script")
@click.option("--web-app-config-path", required=True, help="Path to web_app_components config.json file.")
def create_entrypoint_script(web_app_config_path):
    """
    Generate entrypoint.sh scripts for all web application components based on the given configuration.
    This will also clean any existing port_map.json in the result directory.
    """
    logger.info("Starting entrypoint.sh generation...")

    config = load_web_app_config(web_app_config_path)
    components = config.get("web_app_components", {})
    if not components:
        logger.error("No 'web_app_components' found in the configuration.")
        return

    # Step 1: Clear previous generated web_app_components
    if os.path.exists(DEFAULT_RESULT_DIR):
        for item in os.listdir(DEFAULT_RESULT_DIR):
            item_path = os.path.join(DEFAULT_RESULT_DIR, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        logger.info(f"Cleared contents under: {DEFAULT_RESULT_DIR}")
    else:
        os.makedirs(DEFAULT_RESULT_DIR, exist_ok=True)

    # Step 2: Remove existing port_map.json if exists
    if os.path.exists(DEFAULT_PORT_MAP_PATH):
        os.remove(DEFAULT_PORT_MAP_PATH)
        logger.info(f"Removed old port_map.json: {DEFAULT_PORT_MAP_PATH}")

    # Step 3: Generate entrypoint.sh per component
    created_files = []
    for name in components.keys():
        source_dir = os.path.join(DEFAULT_WEB_APP_DIR, name)
        frag_path = os.path.join(source_dir, "entrypoint.sh.frag")
        output_dir = os.path.join(DEFAULT_RESULT_DIR, name)

        os.makedirs(output_dir, exist_ok=True)

        container_name = extract_container_name(name)
        create_entrypoint_script_for_component(output_dir, container_name, frag_path)

        created_files.append(os.path.join(output_dir, "entrypoint.sh"))

    # Step 4: Log generated paths
    logger.info("Generated the following entrypoint.sh files:")
    for path in created_files:
        logger.info(f" - {os.path.relpath(path, os.getcwd())}")
    logger.info(f"Total scripts created: {len(created_files)}")

    logger.info("Entrypoint script generation completed.")

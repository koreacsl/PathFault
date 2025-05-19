import os
import json
import shutil
import click
from pathfault.logger import setup_logger

logger = setup_logger(__name__)

# Constants
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DEFAULT_RESULT_DIR = os.path.join(PROJECT_ROOT, "results", "mimic_environment_creator", "web_app_components")
DEFAULT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "_templates", "DefaultDockerfile.frag")
DEFAULT_WEB_APP_DIR = os.path.join(os.path.dirname(__file__), "..", "web_app_components")
DEFAULT_PORT = 8000


def load_config(config_path):
    """Load the web app configuration JSON file."""
    try:
        with open(config_path, "r") as file:
            config = json.load(file)
            logger.debug(f"Loaded configuration: {config}")
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise click.ClickException("Missing configuration file.")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in config file: {config_path}")
        raise click.ClickException("Invalid JSON format.")

def copy_dependencies(dockerfile_frag_path, source_dir, target_dir):
    """Copy files or directories referenced by COPY commands in a Dockerfile fragment."""
    try:
        with open(dockerfile_frag_path, "r") as dockerfile:
            for line in dockerfile:
                if line.strip().startswith("COPY"):
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        rel_path = parts[1]
                        src_path = os.path.join(source_dir, rel_path)
                        dest_path = os.path.join(target_dir, os.path.basename(rel_path))
                        if os.path.isdir(src_path):
                            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                            logger.debug(f"Copied directory {src_path} → {dest_path}")
                        elif os.path.isfile(src_path):
                            shutil.copy(src_path, dest_path)
                            logger.debug(f"Copied file {src_path} → {dest_path}")
                        else:
                            logger.warning(f"MISSING for COPY: {src_path}")
    except Exception as e:
        logger.error(f"Failed to copy dependencies from {dockerfile_frag_path}: {e}")

@click.command("create-dockerfile")
@click.option("--web-app-config-path", required=True, help="Path to the web_app_components config.json file.")
def create_dockerfile(web_app_config_path):
    """
    Generate Dockerfiles for each web application component using its Dockerfile fragment.
    Each fragment is merged with the default base Dockerfile, and ports start from 8000.
    """
    logger.info("Starting Dockerfile creation for web app components.")
    logger.info(f"All Dockerfiles will be written to: {os.path.relpath(DEFAULT_RESULT_DIR, os.getcwd())}")

    config = load_config(web_app_config_path)
    components = config.get("web_app_components", {})
    if not components:
        logger.error("No 'web_app_components' found in the configuration.")
        return

    os.makedirs(DEFAULT_RESULT_DIR, exist_ok=True)

    current_port = DEFAULT_PORT
    generated_files = []

    for name, info in components.items():
        component_dir = os.path.join(DEFAULT_WEB_APP_DIR, name)
        frag_path = os.path.join(component_dir, "Dockerfile.frag")
        result_dir = os.path.join(DEFAULT_RESULT_DIR, name)
        result_dockerfile = os.path.join(result_dir, "Dockerfile")

        os.makedirs(result_dir, exist_ok=True)
        logger.debug(f"Preparing Dockerfile for '{name}' at port {current_port}")

        try:
            with open(result_dockerfile, "w") as dockerfile:
                if os.path.exists(frag_path):
                    with open(frag_path, "r") as frag:
                        dockerfile.write(frag.read() + "\n")
                    copy_dependencies(frag_path, component_dir, result_dir)
                else:
                    logger.warning(f"Dockerfile.frag not found for component '{name}'")

                dockerfile.write(f"ENV PORT={current_port}\n")
                dockerfile.write(f"EXPOSE {current_port}\n")

                if os.path.exists(DEFAULT_TEMPLATE_PATH):
                    with open(DEFAULT_TEMPLATE_PATH, "r") as default_frag:
                        dockerfile.write(default_frag.read() + "\n")
                else:
                    logger.warning("Default Dockerfile fragment is missing.")

            logger.info(f"Created Dockerfile for '{name}' at port {current_port}")
            generated_files.append(os.path.relpath(result_dockerfile, os.getcwd()))
            current_port += 1

        except Exception as e:
            logger.error(f"Failed to create Dockerfile for '{name}': {e}")

    if generated_files:
        logger.info("Generated the following Dockerfiles:")
        for path in generated_files:
            logger.info(f" - {path}")
        logger.info(f"Total Dockerfiles generated: {len(generated_files)}")
    else:
        logger.warning("No Dockerfiles were generated.")

    logger.info(f"Dockerfile creation completed at: {os.path.relpath(DEFAULT_RESULT_DIR, os.getcwd())}")

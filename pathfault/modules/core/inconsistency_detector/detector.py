import click
from pathfault.logger import setup_logger
from pathfault.modules.core.inconsistency_detector.services.analysis_inconsistency_result import \
    cli_analysis_inconsistency
from pathfault.modules.core.inconsistency_detector.services.convert_logs_to_csv import convert_logs_to_csv

from pathfault.modules.core.inconsistency_detector.services.create_inconsistency_detector_config import (
    create_inconsistency_detector_config,
)
from pathfault.modules.core.inconsistency_detector.services.send_confusable_uri import (
    send_confusable_uri,
)
from pathfault.modules.core.inconsistency_detector.workflows.detect_inconsistency import detect_inconsistency_workflow
from pathfault.modules.core.inconsistency_detector.workflows.get_csv_with_sending_exploit_payloads import \
    get_csv_with_sending_exploit_payloads_workflow

logger = setup_logger(__name__)

@click.group("inconsistency-detector")
def inconsistency_detector_command():
    """
    Commands for detecting inconsistencies in HTTP message parsing.
    Divided into service modules and high-level workflows.
    """
    logger.info("Entered 'inconsistency-detector' command group.")

@click.group("services")
def services_group():
    """Service-level commands for parser inconsistency detection."""
    pass

@click.group("workflows")
def workflows_group():
    """Workflow-level commands for orchestrating multi-step detection."""
    pass

# Register service-level commands
services_group.add_command(create_inconsistency_detector_config)
services_group.add_command(send_confusable_uri)
services_group.add_command(convert_logs_to_csv)
services_group.add_command(cli_analysis_inconsistency)

workflows_group.add_command(detect_inconsistency_workflow)
workflows_group.add_command(get_csv_with_sending_exploit_payloads_workflow)

# Register groups under the top-level group
inconsistency_detector_command.add_command(services_group)
inconsistency_detector_command.add_command(workflows_group)

__all__ = ["inconsistency_detector_command"]

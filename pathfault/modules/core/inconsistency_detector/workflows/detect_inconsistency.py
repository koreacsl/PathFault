import os
import time
import click
from pathfault.logger import setup_logger

# Import service commands to invoke in sequence
from pathfault.modules.core.inconsistency_detector.services.create_inconsistency_detector_config import create_inconsistency_detector_config
from pathfault.modules.core.inconsistency_detector.services.send_confusable_uri import send_confusable_uri
from pathfault.modules.core.inconsistency_detector.services.convert_logs_to_csv import convert_logs_to_csv
from pathfault.modules.core.inconsistency_detector.services.analysis_inconsistency_result import cli_analysis_inconsistency

logger = setup_logger(__name__)

@click.command("detect-inconsistency")
@click.option(
    "--port-map-path",
    required=True,
    help="Path to the port_map.json used to generate config and target URLs."
)
@click.option(
    "--result-root-dir",
    default="./pathfault/results/inconsistency_detector",
    show_default=True,
    help="Base directory for output files."
)
@click.option(
    "--num-procs",
    default=64,
    show_default=True,
    help="Number of parallel processes to use for request sending."
)
def detect_inconsistency_workflow(port_map_path, result_root_dir, num_procs):
    """
    Run the full inconsistency detection workflow:
    1. Generate config
    2. Send confusable URI requests
    3. Convert logs to CSV
    4. Analyze inconsistencies
    """
    ctx = click.get_current_context()

    config_path = os.path.join(result_root_dir, "inconsistency_detector_config")
    logs_dir = os.path.join(os.path.dirname(port_map_path), "logs")
    converted_csv = os.path.join(result_root_dir, "converted_logs.csv")
    analysis_output = os.path.join(result_root_dir, "inconsistency_analysis_result.json")

    logger.info("Step 1: Creating inconsistency detector config...")
    ctx.invoke(create_inconsistency_detector_config, port_map_path=port_map_path, output_path=config_path)

    logger.info("Step 2: Sending confusable URI requests...")
    ctx.invoke(send_confusable_uri, config=config_path, num_procs=num_procs)

    logger.info("Waiting briefly before parsing logs to ensure all data is flushed...")
    time.sleep(5)

    logger.info("Step 3: Converting PCAP logs to CSV...")
    ctx.invoke(convert_logs_to_csv, logs_dir=logs_dir, output_path=converted_csv)

    logger.info("Step 4: Analyzing inconsistencies from CSV logs...")
    ctx.invoke(cli_analysis_inconsistency, csv_file=converted_csv, output=analysis_output)

    logger.info("🎯 Inconsistency detection workflow completed.")
    logger.info(f"📝 Config         : {config_path}")
    logger.info(f"📁 Logs directory : {logs_dir}")
    logger.info(f"📊 CSV output     : {converted_csv}")
    logger.info(f"📈 Final JSON     : {analysis_output}")

__all__ = ["detect_inconsistency_workflow"]

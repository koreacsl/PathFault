import time
import click
import multiprocessing

from pathfault.logger import setup_logger
from pathfault.modules.core.inconsistency_detector.services.request_sender.request_sender import RequestSender

logger = setup_logger(__name__)

@click.command("send-confusable-uri")
@click.option(
    "--config",
    required=True,
    type=click.Path(exists=True),
    help="Path to the configuration file used for request generation."
)
@click.option(
    "--exploit",
    is_flag=True,
    default=False,
    help="Enable exploit payload sending mode. Requires --exploit-options-file."
)
@click.option(
    "--exploit-option-file",
    required=False,
    type=click.Path(exists=True),
    help="Exploit options file (required if --exploit is set)."
)
@click.option(
    "--num-procs",
    default=64,
    show_default=True,
    type=int,
    help="Number of parallel processes to use."
)
def send_confusable_uri(config, exploit, exploit_option_file, num_procs):
    """
    Send HTTP requests with confusable URIs to test parser inconsistencies,
    or validate exploit payloads in exploit mode.
    """
    logger.info("Starting request sender")
    logger.info(f"Config: {config}")
    multiprocessing.set_start_method("fork", force=True)

    # Validate exploit requirements
    if exploit and not exploit_option_file:
        logger.error("--exploit is set but --exploit-option-file is not provided.")
        raise click.ClickException("Exploit mode requires --exploit-option-file.")

    start = time.time()
    sender = RequestSender(
        config_file_path=config,
        num_procs=num_procs,
    )

    if exploit:
        logger.info(f"Running in exploit mode with: {exploit_option_file}")
        sender.send_exploit_payload_for_experiment(exploit_option_file)
    else:
        logger.info("Running in confusable URI send mode.")
        sender.send_confusable_uri()

    logger.info(f"Request sending completed in {time.time() - start:.2f}s")

__all__ = ["send_confusable_uri"]
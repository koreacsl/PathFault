import logging
import os
import shutil
import zipfile
from typing import List

import pyshark
import pandas as pd
import re
import traceback
import tempfile
import subprocess
import click

from pathfault.logger import setup_logger
logger = setup_logger(__name__)

def extract_logs(source_path, extract_path):
    """
    If source_path is a directory, return it directly.
    Otherwise, assume it's a zip file and extract it into extract_path.
    """
    # If logs directory already provided, use it as-is
    if os.path.isdir(source_path):
        return source_path

    # Remove existing extract_path if present
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    try:
        with zipfile.ZipFile(source_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        logger.info(f"Unzipped logs to {extract_path}")
    except Exception as e:
        logger.error(f"Error extracting zip: {e}")
        return None

    # If nested 'logs' directories exist, descend into the deepest one
    while os.path.exists(os.path.join(extract_path, "logs")):
        extract_path = os.path.join(extract_path, "logs")
        logger.info(f"Adjusted extract path to {extract_path}")
    return extract_path


def find_pcap_files(base_dir, server_name, direction):
    """
    Search under base_dir/server_name/ for files containing direction ('inbound' or 'outbound')
    and ending with .pcap. Return a list of matching file paths.
    """
    server_path = os.path.join(base_dir, server_name)
    if not os.path.exists(server_path):
        logger.warning(f"Server directory not found: {server_path}")
        return []

    pcap_files = []
    for root, _, files in os.walk(server_path):
        for file in files:
            if direction in file and file.endswith(".pcap"):
                pcap_files.append(os.path.join(root, file))

    logger.info(f"Searching in: {server_path}")
    logger.info(f"Found {len(pcap_files)} '{direction}' pcap files for {server_name}")
    return pcap_files


MAX_FILES_PER_BATCH = 500  # Safe upper limit; can be adjusted depending on the system

def merge_pcap(input_files: List[str]) -> str | None:
    """
    Merge multiple pcap files into a single file using mergecap.
    If there are too many files, they are merged in batches.
    Returns the path to the merged pcap file, or None on failure.
    """
    if not input_files:
        logger.warning("No pcap files to merge.")
        return None

    # Temporary list of intermediate merged files
    intermediate_files = []

    # 1. Batch merge if input exceeds the maximum file limit
    for i in range(0, len(input_files), MAX_FILES_PER_BATCH):
        batch = input_files[i:i + MAX_FILES_PER_BATCH]
        fd, tmpfile = tempfile.mkstemp(suffix=".pcap")
        os.close(fd)
        os.remove(tmpfile)  # Ensure mergecap can write to the file

        merge_cmd = ["sudo", "mergecap", "-F", "pcap", "-w", tmpfile] + batch
        result = subprocess.run(merge_cmd)

        if result.returncode != 0:
            logger.error(f"Failed to merge batch starting at index {i}")
            return None

        intermediate_files.append(tmpfile)

    # 2. Final merge of intermediate files
    fd, final_merged = tempfile.mkstemp(suffix=".pcap")
    os.close(fd)
    os.remove(final_merged)

    final_merge_cmd = ["sudo", "mergecap", "-F", "pcap", "-w", final_merged] + intermediate_files
    result = subprocess.run(final_merge_cmd)

    # Clean up intermediate temporary files
    for tmp in intermediate_files:
        try:
            os.remove(tmp)
        except OSError:
            pass

    if result.returncode == 0:
        logger.info(f"Merged {len(input_files)} files into {final_merged}")
        return final_merged
    else:
        logger.error("Final merge failed.")
        return None

#
# def merge_pcap(input_files):
#     """
#     Merge multiple pcap files into one temporary pcap using mergecap.
#     Return the path to the merged file or None on failure.
#     """
#     if not input_files:
#         logger.warning("No pcap files to merge.")
#         return None
#
#     # Generate a temp file path but don't create the file yet
#     fd, tmpfile_path = tempfile.mkstemp(suffix=".pcap")
#     os.close(fd)  # Close file descriptor
#     os.remove(tmpfile_path)  # Remove the file so mergecap (as root) can create it
#
#     merge_command = f"sudo mergecap -F pcap -w {tmpfile_path} " + " ".join(input_files)
#     result = subprocess.run(merge_command, shell=True)
#
#     if result.returncode == 0:
#         logger.info(f"Merged {len(input_files)} files into {tmpfile_path}")
#         return tmpfile_path
#     else:
#         logger.error("Failed to merge files with mergecap.")
#         return None


def extract_http_from_tcp_payload(pcap_file):
    """
    Use pyshark to extract HTTP messages and metadata from a pcap file.

    Returns a list of tuples:
      (url, decoded_http, x_request_id, x_request_type, x_request_seed, raw_tcp_payload_hex)
    """
    if not pcap_file or not os.path.exists(pcap_file):
        logger.warning(f"Pcap file not found: {pcap_file}")
        return []

    http_messages = []
    tcp_streams_decoded = {}
    tcp_streams_hex = {}

    try:
        with pyshark.FileCapture(pcap_file, display_filter="tcp") as capture:
            for packet in capture:
                try:
                    if hasattr(packet, 'tcp'):
                        tcp_layer = packet.tcp
                        stream_id = getattr(tcp_layer, 'stream', 'unknown')
                        if stream_id not in tcp_streams_decoded:
                            tcp_streams_decoded[stream_id] = ""
                            tcp_streams_hex[stream_id] = ""

                        if hasattr(tcp_layer, 'payload'):
                            raw_hex = tcp_layer.payload.replace(':', '')
                            tcp_streams_hex[stream_id] += raw_hex
                            try:
                                payload_bytes = bytes.fromhex(raw_hex)
                                decoded = payload_bytes.decode('utf-8', errors='ignore')
                                tcp_streams_decoded[stream_id] += decoded
                            except Exception as e:
                                logger.warning(f"Failed to decode payload in stream {stream_id}: {e}")

                        if "\r\n\r\n" in tcp_streams_decoded[stream_id]:
                            message = tcp_streams_decoded[stream_id]
                            lines = message.split("\r\n")
                            url = ""
                            if lines:
                                match = re.match(r"(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH) (.*?) HTTP", lines[0])
                                if match:
                                    url = match.group(2)

                            headers = {}
                            for line in lines[1:]:
                                if ": " in line:
                                    key, value = line.split(": ", 1)
                                    headers[key.lower()] = value

                            http_messages.append((
                                url,
                                message,
                                headers.get('x-request-id', '').upper(),
                                headers.get('x-request-type', '').upper(),
                                headers.get('x-request-seed', '').upper(),
                                tcp_streams_hex[stream_id]
                            ))
                            del tcp_streams_decoded[stream_id]
                            del tcp_streams_hex[stream_id]
                except Exception as e:
                    logger.error(f"Error processing packet: {e}\n{traceback.format_exc()}")
    except Exception as e:
        logger.error(f"Failed to read {pcap_file}: {e}\n{traceback.format_exc()}")

    return http_messages


def parse_http_requests(messages, server_name, direction):
    """
    Convert extracted HTTP tuples into dicts for DataFrame ingestion.
    """
    data = []
    for url, decoded, req_id, req_type, req_seed, tcp_hex in messages:
        data.append({
            'webserver': server_name,
            'direction': direction,
            'URL': url,
            'request': decoded.strip(),
            'X-Request-ID': req_id,
            'X-Request-Type': req_type,
            'X-Request-Seed': req_seed,
            'tcp_payload': tcp_hex
        })
    return data


def pcap_to_csv(logs_dir: str, output_path: str):
    """
    Full pipeline:
      1) use provided logs directory
      2) find and merge pcaps per server, per direction
      3) extract HTTP data
      4) save as a CSV file
    """
    extract_path = extract_logs(logs_dir, 'extracted_logs')
    if not extract_path or not os.path.isdir(extract_path):
        logger.error(f"Extract path is not valid: {extract_path}")
        return None

    servers = [d for d in os.listdir(extract_path) if os.path.isdir(os.path.join(extract_path, d))]
    data_entries = []
    for srv in servers:
        inbound = merge_pcap(find_pcap_files(extract_path, srv, 'inbound'))
        outbound = merge_pcap(find_pcap_files(extract_path, srv, 'outbound'))
        if inbound:
            msgs = extract_http_from_tcp_payload(inbound)
            logger.info(f"Extracted {len(msgs)} inbound messages from {srv}")
            data_entries.extend(parse_http_requests(msgs, srv, 'inbound'))
        if outbound:
            msgs = extract_http_from_tcp_payload(outbound)
            logger.info(f"Extracted {len(msgs)} outbound messages from {srv}")
            data_entries.extend(parse_http_requests(msgs, srv, 'outbound'))

    df = pd.DataFrame(data_entries, columns=[
        'webserver','direction','URL','request',
        'X-Request-ID','X-Request-Type','X-Request-Seed','tcp_payload'
    ])
    df.to_csv(output_path, index=False)
    logger.info(f"CSV file saved: {output_path}")

@click.command('convert-logs-to-csv')
@click.option(
    '--logs-dir',
    required=True,
    help='Path to the logs directory (located alongside docker-compose.yml).'
)
@click.option(
    '--output-path',
    default='./pathfault/results/inconsistency_detector/converted_logs.csv',
    show_default=True,
    help='Output CSV file path.'
)
def convert_logs_to_csv(logs_dir, output_path):
    """
    Convert PCAP logs into a CSV summary for analysis.

    - Expects a directory containing structured log folders (not a zip file).
    - This directory should be at the same level as docker-compose.yml.
    """
    logger.info("Starting conversion of logs to CSV...")
    pcap_to_csv(logs_dir, output_path)
    logger.info(f"Conversion completed. CSV written to: {output_path}")


# Export for manage.py registration
__all__ = ['convert_logs_to_csv']

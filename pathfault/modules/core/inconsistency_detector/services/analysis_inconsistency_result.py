import json
import os
import click
import pandas as pd

from pathfault.logger import setup_logger
logger = setup_logger(__name__)

def parse_get_url_hex(tcp_payload_hex: str) -> str:
    """
    Extract the URL path in hex form between the HTTP method and version markers.
    Returns an empty string if markers are not found.
    """
    if not tcp_payload_hex:
        return ""
    start_marker = "47455420"   # Hex for 'GET '
    end_marker = "20485454502f"  # Hex for ' HTTP/'

    start_idx = tcp_payload_hex.find(start_marker)
    if start_idx == -1:
        return ""
    search_from = start_idx + len(start_marker)
    end_idx = tcp_payload_hex.find(end_marker, search_from)
    if end_idx == -1:
        return ""
    return tcp_payload_hex[search_from:end_idx]


def evaluate_flags(reqtype_in: str, inbound_url: str, outbound_url: str) -> dict:
    """
    Determine whether the observed URLs correspond to normalization or decoding behavior.
    Returns:
      {
        'is_normalize': bool,
        'is_decode': bool
      }
    """
    result = {
        "is_normalize": False,
        "is_decode": False
    }

    rt = reqtype_in.lower()
    in_lc = inbound_url.lower()
    out_lc = outbound_url.lower()

    # Check for normalization: request type contains 'normalization' and inbound path matches
    if "normalization" in rt and in_lc == "/tmp1/../tmp2":
        if "tmp2" in out_lc and "tmp1" not in out_lc:
            result["is_normalize"] = True

    # Check for decoding: request type contains 'decoding_in_range' and inbound/outbound patterns
    if "decoding_in_range" in rt and in_lc == "/%21":
        if out_lc == "/!":
            result["is_decode"] = True

    return result


def process_bad_rows(bad_inbound_rows: pd.DataFrame, transform_bad: dict) -> None:
    """
    Populate transform_bad with entries for requests that never received responses.
    Skips types validated by flag checks.
    """
    for _, row in bad_inbound_rows.iterrows():
        reqtype_in = str(row.get("X-Request-Type", "")).lower().zfill(2)
        # Skip known flag-based types
        if any(k in reqtype_in for k in ["normalization", "decoding_in_range"]):
            continue

        seed_hex = str(row.get("X-Request-Seed", "")).lower()
        if len(seed_hex) == 1:
            seed_hex = f"0{seed_hex}"

        if seed_hex not in transform_bad:
            transform_bad[seed_hex] = {}

        inbound_payload = row.get("tcp_payload", "")
        xreq_id = row.get("X-Request-ID", "")
        inbound_url_hex = parse_get_url_hex(inbound_payload)

        transform_bad[seed_hex][reqtype_in] = {
            "inbound_payload": inbound_payload,
            "inbound_url": inbound_url_hex,
            "x_request_id": xreq_id
        }


def process_inconsistency_rows(disc_data: pd.DataFrame, transform_disc: dict) -> None:
    """
    Populate transform_disc with entries for requests whose inbound and outbound URLs differ.
    Skips types validated by flag checks.
    """
    for _, row in disc_data.iterrows():
        reqtype_in = str(row.get("X-Request-Type_in", "")).lower()
        # Skip known flag-based types
        if any(k in reqtype_in for k in ["normalization", "decoding_in_range"]):
            continue

        seed_in = str(row.get("X-Request-Seed_in", "")).lower()
        if len(seed_in) == 1:
            seed_in = f"0{seed_in}"

        # Convert single-byte seed to UTF-8 hex
        try:
            seed_in = "".join(f"{b:02x}" for b in chr(int(seed_in, 16)).encode('utf-8'))
        except Exception:
            logger.warning(f"Invalid hex seed '{seed_in}', using as-is.")

        if seed_in not in transform_disc:
            transform_disc[seed_in] = {}

        inbound_payload = row.get("tcp_payload_in", "")
        outbound_payload = row.get("tcp_payload_out", "")
        xreq_id_merged = row.get("X-Request-ID", "")
        inbound_url_hex = parse_get_url_hex(inbound_payload)
        outbound_url_hex = parse_get_url_hex(outbound_payload)

        transform_disc[seed_in][reqtype_in] = {
            "inbound_payload": inbound_payload,
            "inbound_url": inbound_url_hex,
            "outbound_payload": outbound_payload,
            "outbound_url": outbound_url_hex,
            "x_request_id": xreq_id_merged
        }


def analyze_server(server_data: pd.DataFrame) -> dict:
    """
    Analyze a single server's inbound/outbound pairs:
      - Count total, missing, and mismatched requests
      - Determine normalization and decoding flags
      - Collect details for bad and inconsistency cases
    Returns a JSON-serializable dict.
    """
    inbound_data = server_data[server_data["direction"] == "inbound"]
    outbound_data = server_data[server_data["direction"] == "outbound"]

    total_count = len(inbound_data)
    inbound_ids = set(inbound_data["X-Request-ID"].dropna())
    outbound_ids = set(outbound_data["X-Request-ID"].dropna())

    missing_ids = inbound_ids - outbound_ids
    bad_count = len(missing_ids)
    valid_count = max(0, total_count - bad_count)

    merged = inbound_data.merge(
        outbound_data,
        on="X-Request-ID",
        suffixes=("_in", "_out"),
        how="inner"
    )
    inconsistency_mask = merged["URL_in"] != merged["URL_out"]
    inconsistency_count = int(inconsistency_mask.sum())

    def safe_ratio(n, d): return float(round(n / d, 4)) if d > 0 else 0.0
    bad_ratio = safe_ratio(bad_count, total_count)
    valid_ratio = safe_ratio(valid_count, total_count)
    disc_ratio = safe_ratio(inconsistency_count, total_count)
    disc_ratio_to_valid = safe_ratio(inconsistency_count, valid_count)

    # Initialize flags
    is_normalize = False
    is_decode = False

    for _, row in merged.iterrows():
        reqtype_in = str(row.get("X-Request-Type_in", "")).lower()
        inbound_url = str(row.get("URL_in", ""))
        outbound_url = str(row.get("URL_out", ""))

        flags = evaluate_flags(reqtype_in, inbound_url, outbound_url)
        is_normalize |= flags["is_normalize"]
        is_decode |= flags["is_decode"]

    # Build transform mappings
    transform_bad = {}
    process_bad_rows(inbound_data[inbound_data["X-Request-ID"].isin(missing_ids)], transform_bad)

    transform_disc = {}
    process_inconsistency_rows(merged[inconsistency_mask], transform_disc)

    return {
        "statistic": {
            "total": {"count": total_count},
            "valid": {"count": valid_count, "ratio": valid_ratio},
            "bad": {"count": bad_count, "ratio": bad_ratio},
            "inconsistency": {"count": inconsistency_count, "ratio": disc_ratio, "ratio_to_valid": disc_ratio_to_valid}
        },
        "is_normalize": is_normalize,
        "is_decode": is_decode,
        "transformation": {
            "bad": transform_bad,
            "inconsistency": transform_disc
        }
    }


def analysis_inconsistency(csv_file: str, output: str) -> None:
    """
    Read a CSV of HTTP request data, analyze each server, and write a JSON report.
    """
    logger.info(f"Loading CSV data from: {csv_file}")
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        logger.error(f"Unable to read CSV: {e}")
        return

    # Filter out rows with invalid X-Request-Type
    non_str_mask = ~df["X-Request-Type"].apply(lambda x: isinstance(x, str))
    if non_str_mask.any():
        error_rows = df[non_str_mask]
        error_path = "error.csv"
        error_rows.to_csv(error_path, index=False)
        logger.warning(f"Exported {len(error_rows)} invalid rows to {error_path}")
        df = df[~non_str_mask]

    if df.empty:
        logger.warning("No valid records to analyze after cleanup.")
        return

    result = {}
    # Skip 'tmpserver' entirely
    for server in df["webserver"].unique():
        if server.lower() == "tmpserver":
            continue
        server_data = df[df["webserver"] == server]
        result[server] = analyze_server(server_data)

    # Write JSON output
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    logger.info(f"Analysis results saved to: {output}")


@click.command("analysis-inconsistency-results")
@click.option(
    "--csv-file",
    required=True,
    help="Path to the CSV file produced by convert-logs-to-csv."
)
@click.option(
    "--output",
    default="./pathfault/results/inconsistency_detector/inconsistency_analysis_result.json",
    show_default=True,
    help="Path where the JSON analysis result will be written."
)
def cli_analysis_inconsistency(csv_file, output):
    """
    CLI entrypoint: analyze HTTP request discrepancies and output JSON report.
    """
    analysis_inconsistency(csv_file, output)


__all__ = ["cli_analysis_inconsistency"]

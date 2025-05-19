#!/usr/bin/env python3
import csv
import sys
from collections import defaultdict

# Constants for future analysis
LAST_W_URI = '/profile'
FIRST_W_CONDITION_SUFFIX = 'not_a_file.css'

def load_csv_grouped_by_type(csv_path):
    """
    Load the CSV and group data into the following structure:
    {
        X-Request-Type: {
            webserver: {
                direction: {
                    X-Request-ID: URL,
                    ...
                }
            }
        }
    }

    Collect all duplicate X-Request-ID entries and report them at the end.
    """
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    duplicates = []  # Collect all duplicates

    try:
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                req_type = row.get('X-Request-Type', '').strip()
                webserver = row.get('webserver', '').strip()
                direction = row.get('direction', '').strip().lower()
                request_id = row.get('X-Request-ID', '').strip()
                url = row.get('URL', '').strip()

                # Skip empty or invalid rows
                if not (req_type and webserver and direction and request_id and url):
                    continue

                group = result[req_type][webserver][direction]
                if request_id in group:
                    duplicates.append({
                        'X-Request-ID': request_id,
                        'X-Request-Type': req_type,
                        'webserver': webserver,
                        'direction': direction,
                        'existing_url': group[request_id],
                        'new_url': url
                    })
                    continue

                group[request_id] = url

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        sys.exit(1)

    # If duplicates found, print and exit
    if duplicates:
        print("\n❌ Duplicate X-Request-ID(s) found:")
        print("────────────────────────────────────────────")
        for dup in duplicates:
            print(f"🆔 {dup['X-Request-ID']}")
            print(f"   → type={dup['X-Request-Type']}, server={dup['webserver']}, direction={dup['direction']}")
            print(f"   → Existing URL: {dup['existing_url']}")
            print(f"   → New URL     : {dup['new_url']}")
            print()
        print(f"🚫 Total {len(duplicates)} duplicate(s) found. Aborting.")
        sys.exit(1)

    return result

def analyze_matching_requests(grouped_data):
    print("\n📊 Matched X-Request-IDs based on suffix and endpoint criteria:")

    match_summary = {}
    inbound_url_summary = {}  # per request-type
    all_matched_inbound_urls = set()  # ✅ global set for all matched inbound URLs

    for req_type_raw, server_map in grouped_data.items():
        req_type = req_type_raw.strip().lower()
        server_sequence = req_type.split("_")

        match_summary[req_type_raw] = 0
        inbound_url_summary[req_type_raw] = set()

        if not server_sequence:
            continue

        first = server_sequence[0]
        last = server_sequence[-1]

        if first not in server_map or last not in server_map:
            continue

        first_outbound = server_map[first].get('outbound', {})
        first_inbound = server_map[first].get('inbound', {})
        last_outbound = server_map[last].get('outbound', {})

        candidate_ids = {
            rid for rid, url in first_outbound.items()
            if url.endswith(FIRST_W_CONDITION_SUFFIX)
        }

        matched_ids = [
            rid for rid in candidate_ids
            if rid in last_outbound and last_outbound[rid] == LAST_W_URI
        ]

        match_summary[req_type_raw] = len(matched_ids)

        # ✅ Add to both local and global sets, with server-name prefix stripped
        for mid in matched_ids:
            if mid in first_inbound:
                inbound_url = first_inbound[mid]
                normalized_url = inbound_url

                # ✅ 지금 시퀀스에 있는 서버 이름 전부 제거 (/server 또는 /server/)
                for server in server_sequence:
                    for pattern in [f"/{server}", f"/{server}/"]:
                        normalized_url = normalized_url.replace(pattern, "")

                # ✅ 시작이 / 아니면 붙여줌 (예: profile → /profile)

                inbound_url_summary[req_type_raw].add(normalized_url)
                all_matched_inbound_urls.add(normalized_url)
        if matched_ids:
            print(f"\n🧩 X-Request-Type: {req_type_raw}")
            for mid in matched_ids:
                print(f"  ✅ Matched ID: {mid}")
                print(f"     ↳ {first} outbound URL: {first_outbound.get(mid)}")
                print(f"     ↳ {last} outbound URL : {last_outbound.get(mid)}")
                print(f"     📦 Full Request Trace:")
                for srv in server_sequence:
                    inbound_url = server_map.get(srv, {}).get('inbound', {}).get(mid)
                    outbound_url = server_map.get(srv, {}).get('outbound', {}).get(mid)
                    if inbound_url or outbound_url:
                        print(f"        🔸 {srv}:")
                        if inbound_url:
                            print(f"           ↳ inbound  URL: {inbound_url}")
                        if outbound_url:
                            print(f"           ↳ outbound URL: {outbound_url}")

    # Print per-type summary
    print("\n📌 Summary: Matched ID Count per X-Request-Type")
    print("────────────────────────────────────────────────────────────────────────────")
    max_key_len = max((len(k) for k in match_summary), default=0)
    col_width = max(max_key_len + 2, 50)

    for req_type in sorted(match_summary):
        count = match_summary[req_type]
        unique_urls = len(inbound_url_summary.get(req_type, set()))
        print(f"{req_type.ljust(col_width)}→ {count} matched ID(s) "
              f"(from {unique_urls} unique inbound URL(s))")

    # Overall counts
    total_matches = sum(match_summary.values())
    total_combinations = len(match_summary)
    vulnerable_combos = sum(1 for c in match_summary.values() if c > 0)
    total_unique_payloads = len(all_matched_inbound_urls)

    # Print totals
    print(f"\n🏷️ Total Matched IDs Across All Types: {total_matches}")
    print(f"\n🌐 Total Unique Inbound URLs from All Matched IDs: {total_unique_payloads}")
    if all_matched_inbound_urls:
        for url in sorted(all_matched_inbound_urls):
            print(f"   - {url}")

    total_combinations    = len(match_summary)
    vulnerable_combos     = sum(1 for c in match_summary.values() if c > 0)
    total_matches         = sum(match_summary.values())
    total_unique_payloads = len(all_matched_inbound_urls)

    print("\n📊 Summary")
    print(f"Unique Payloads: {total_unique_payloads}")
    print(f"Vulnerable Pairs: {vulnerable_combos}/{total_combinations}")
    print(f"TP: {total_matches}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python experiment_do_analysis_wcde_tp.py <csv_file_path>")
        sys.exit(1)

    csv_path = sys.argv[1]
    grouped_data = load_csv_grouped_by_type(csv_path)

    # Debug print
    for req_type, servers in grouped_data.items():
        print(f"\nX-Request-Type: {req_type}")
        for webserver, directions in servers.items():
            print(f"  Webserver: {webserver}")
            for direction, entries in directions.items():
                print(f"    Direction: {direction}")
                for req_id, url in entries.items():
                    print(f"      {req_id} -> {url}")

    # New analysis
    analyze_matching_requests(grouped_data)

if __name__ == '__main__':
    main()
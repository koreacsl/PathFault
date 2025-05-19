# Inconsistency Detector

This module provides core functionality for generating configuration files and performing analysis  
to detect inconsistencies in how different components parse HTTP messages.

---

## 📁 Module Structure

```
inconsistency_detector/
├── detector.py                        # CLI group definition for services and workflows
├── services/                          # Independent commands (e.g., config generation, request sending)
│   ├── create_inconsistency_detector_config.py
│   ├── send_confusable_uri.py
│   ├── convert_logs_to_csv.py
│   └── request_sender/                # Internal modules for crafting and sending raw requests
│       ├── input_tree.py
│       ├── input_tree_node.py
│       ├── helper_functions.py
│       └── request_sender.py
├── workflows/                         # Placeholder for future composed pipelines
│   └── __init__.py
└── README.md                          # This file
```

---

## ⚙️ Generating Configuration for Detection

To prepare for inconsistency detection, you first need to generate a configuration file that defines:

- The target URLs (based on ports defined in `port_map.json`)
- The corresponding `Host` headers
- A base HTTP request structure to be used in analysis

### ✅ Command

```
python manage.py core inconsistency-detector services create-inconsistency-detector-config \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json
```

This will create a file at:

```
./pathfault/results/inconsistency_detector/inconsistency_detector_config
```

If the output directory does not exist, it will be created automatically.

---

## 📤 Sending Requests with Confusable URIs

Once the configuration file is ready, you can launch the confusable URI request sequence  
to test how different servers and intermediaries handle ambiguous input formats.

### ✅ Command

```
python manage.py core inconsistency-detector services send-confusable-uri \
  --config pathfault/results/inconsistency_detector/inconsistency_detector_config \
  --num-procs 32
```

### 🔁 What This Command Performs

- **Non-standard inconsistency** detection:
  - Tests transformation behavior using crafted characters at path junctions.
- **Standard inconsistency** detection:
  - Checks for path normalization behavior (`..`, `.` segments).
  - Verifies decoding behavior of percent-encoded bytes (e.g., `%2e`, `%21`).

---

## 📄 Converting Logs to CSV

After request sending, you can convert the resulting packet capture logs  
into a structured CSV for further analysis. This includes decoded HTTP messages and raw TCP payloads.

### ✅ Command

```
python manage.py core inconsistency-detector services convert-logs-to-csv \
  --logs-dir ./pathfault/results/mimic_environment_creator/logs
```

This command:

- Scans the given `logs` directory for `inbound` and `outbound` `.pcap` files.
- Merges and extracts HTTP traffic using `pyshark`.
- Produces a CSV file at:

```
./pathfault/results/inconsistency_detector/converted_logs.csv
```

### 🗂 Directory Requirement

- The `--logs-dir` should point to the `logs` directory generated during request execution.
- This directory must be at the same level as your `docker-compose.yml`.

---

## 🧪 Analyzing Inconsistency Results

To analyze inconsistencies across web servers, run the following:

### ✅ Command

```
python manage.py core inconsistency-detector services analysis-inconsistency-results \
  --csv-file ./pathfault/results/inconsistency_detector/converted_logs.csv
```

This will generate a detailed report at:

```
./pathfault/results/inconsistency_detector/inconsistency_analysis_result.json
```

Each server’s entry in the result JSON includes:

- **bad**: Requests that were sent but never received a response from the server.
- **discrepancy**: Requests where the server returned a different path than expected.
- **is_normalize**: Whether the server performed normalization (e.g., resolving `/../`).
- **is_decode**: Whether the server decoded percent-encoded characters (e.g., `%21` to `!`).

### 🔍 Example Output Snippet

```json
"apachehttpserver": {
  "statistic": {
    "total": { "count": 516 },
    "valid": { "count": 444, "ratio": 0.8605 },
    "bad": { "count": 72, "ratio": 0.1395 },
    "discrepancy": {
      "count": 283,
      "ratio": 0.5484,
      "ratio_to_valid": 0.6374
    }
  },
  "is_normalize": true,
  "is_decode": true,
  "transformation": {
    "bad": { ... },
    "discrepancy": { ... }
  }
}
```

---

## 📌 Notes

- `tmpserver` is excluded from analysis and report generation.
- All analysis is performed per server based on `X-Request-ID` matching.
- Flags (`is_normalize`, `is_decode`) are derived from specific transformation behavior.

---

## 🧵 Unified Workflow: Detecting Inconsistencies from Start to Finish

To execute the **entire pipeline in one step**, you can use the `detect-inconsistency` workflow.  
This combines configuration creation, request dispatch, log conversion, and inconsistency analysis.

### ✅ Command

```
python manage.py core inconsistency-detector workflows detect-inconsistency \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json
```

---

### ⚠️ Important: Clean Logs Before Execution

Before running this command, you **must delete** any previously generated `logs` directory.  
This prevents contamination from outdated `inbound` or `outbound` PCAP files:

```
rm -rf ./pathfault/results/mimic_environment_creator/logs
```

---

### 📋 What This Workflow Performs

1. **Create Configuration**  
   Generates a configuration file for the inconsistency detector using the given `port_map.json`.

2. **Send Requests**  
   Issues raw HTTP requests designed to test URI parsing inconsistencies.

3. **Wait for Logs to Settle**  
   Waits 5 seconds after requests are sent to allow all network traffic to be flushed to disk.

4. **Convert PCAP Logs to CSV**  
   Reads `inbound` and `outbound` capture logs and extracts HTTP-level information.

5. **Analyze CSV for Inconsistencies**  
   Matches requests and responses per server to detect:
   - **bad** requests (no response received)
   - **discrepancy** (URL mismatch after transformation)
   - normalization/decoding flags

---

### 📦 Final Output Files

Upon completion, you will find:

- Configuration file:  
  `./pathfault/results/inconsistency_detector/inconsistency_detector_config`

- Converted CSV of all captured HTTP requests/responses:  
  `./pathfault/results/inconsistency_detector/converted_logs.csv`

- JSON analysis result:  
  `./pathfault/results/inconsistency_detector/inconsistency_analysis_result.json`

This result shows per-server statistics, transformation results, and behavioral flags.

```json
"apachehttpserver": {
  "statistic": {
    "total": { "count": 516 },
    "valid": { "count": 444, "ratio": 0.8605 },
    "bad": { "count": 72, "ratio": 0.1395 },
    "discrepancy": {
      "count": 283,
      "ratio": 0.5484,
      "ratio_to_valid": 0.6374
    }
  },
  "is_normalize": true,
  "is_decode": true,
  "transformation": {
    "bad": { ... },
    "discrepancy": { ... }
  }
}
```
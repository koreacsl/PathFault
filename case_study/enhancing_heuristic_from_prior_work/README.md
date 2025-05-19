# Generating Real-World Exploit Payloads - Enhancing Heuristic from Prior Work

This document provides a step-by-step guide for modeling and validating exploit payloads related to **Enhancing Heuristic from Prior Work** using the PathFault framework.

## About Enhancing Heuristic from Prior Work

This case study addresses vulnerabilities arising from inconsistent URL parsing behaviors across multiple web components, leveraging insights and heuristics derived from previous research. Although specific server types or infrastructure details might not be explicitly disclosed, the scenario typically involves a frontend component that handles certain path prefixes such as `/share/` without proper normalization, while backend components perform normalization and consequently expose sensitive information.

PathFault constructs surrogate models capturing assumed behaviors of these components. By systematically modeling realistic combinations of web components—each with distinct parsing semantics—PathFault deterministically estimates how crafted requests may traverse and transform across an entire web stack.

This case study leverages the insight that incorporating additional known parsing behaviors and heuristics into surrogate models significantly improves their fidelity, enhancing their ability to accurately reflect real-world web application vulnerabilities.

## Create Mimic Environment

The vulnerable configuration involves `nginx`, `apachehttpserver`, `apachetrafficserver`, and `apachetomcat`. Therefore, a **mimic environment** needs to be set up using these components.

> **⚠️ Important Note:** If you previously completed the case study for **ChatGPT Account Takeover**, the necessary log files (`logs`) might already exist at `./pathfault/results/mimic_environment_creator/`. If these logs are present, you can skip creating a new mimic environment and directly proceed to the "Build Surrogate Model" step.
>
> This flexibility is possible due to PathFault's methodological approach, which retains only essential analysis data and discards supplementary details. It highlights PathFault's powerful scalability and efficient reuse of previously generated data.

### Step 1: Copy Preset Files

To use the provided preset files, copy them into the tool’s `web_app_components` directory:

```bash
cp -r ./presets/web_app_components/apachehttpserver ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/apachetrafficserver ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/apachetomcat ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/nginx ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
```

### Step 2: Generate Docker Compose Configuration

Generate the `docker-compose.yml` configuration using:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config.json
```

### Step 3: Launch the Mimic Environment

If the `logs` file is already exists, delete it.
```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

Start the mimic environment with Docker Compose:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

---


## Detect Inconsistency

This step analyzes how different web application components (e.g., nginx, apachehttpserver) interpret identical HTTP requests. This discrepancy can cause unintended path resolutions, making it critical to identify such behaviors before building a surrogate model.

Run the following command to initiate inconsistency detection based on the active mimic environment:

```bash
python manage.py core inconsistency-detector workflows detect-inconsistency \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json
```

This will automatically send crafted payloads to each containerized server, capture and replay PCAP traffic, and detect discrepancies in URL interpretations.

The following files are generated:

* 🧾 `inconsistency_detector_config`: Auto-generated configuration for consistency testing.
* 📁 `logs/`: Captured PCAP traces of all HTTP interactions.
* 📊 `converted_logs.csv`: Parsed summary of request/response behavior per server.
* 📈 `inconsistency_analysis_result.json`: A structured JSON result containing identified inconsistencies between components.

> 💡 **Tip**: If you have already completed the full `chatgpt_account_takeover` case study, this `logs/` directory and `inconsistency_analysis_result.json` should already exist in `./pathfault/results/mimic_environment_creator/`.  
> In such a case, **you may skip the mimic environment creation and inconsistency detection steps**, and proceed directly to surrogate model construction.  
> This is possible because **PathFault isolates only the essential discrepancy data**, discarding unrelated traffic and transient state. This design ensures scalability and reuse across different research scenarios.

---

## Build Surrogate Models by Depth

Once inconsistencies are detected, surrogate models are constructed to simulate the full transformation path of HTTP requests through multiple layers. To evaluate heuristic robustness, we generate surrogate models of increasing depth (2 to 4):

```bash
python manage.py core surrogate-model-builder workflows build-surrogate-model-by-depth \
  --json ./pathfault/results/inconsistency_detector/inconsistency_analysis_result.json \
  --depth 2 \
  --output-dir ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets

python manage.py core surrogate-model-builder workflows build-surrogate-model-by-depth \
  --json ./pathfault/results/inconsistency_detector/inconsistency_analysis_result.json \
  --depth 3 \
  --output-dir ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets

python manage.py core surrogate-model-builder workflows build-surrogate-model-by-depth \
  --json ./pathfault/results/inconsistency_detector/inconsistency_analysis_result.json \
  --depth 4 \
  --output-dir ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets
```
Each generated surrogate model file simulates the chain of parsing transformations across multiple web components.

After generating surrogate models for each depth, move the model files into their corresponding experiment directories.  
⚠️ Avoid using `cp -r` with wildcards across depths, as this will mix models from different depths.

Instead, for each depth level, execute:

```bash
# For depth 2
mkdir ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/surrogate_model_for_experiment/
cp ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/surrogate_model_depth_2/surrogate_model_* \
   ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/surrogate_model_for_experiment/

# For depth 3
mkdir ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/surrogate_model_for_experiment/
cp ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/surrogate_model_depth_3/surrogate_model_* \
   ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/surrogate_model_for_experiment/

# For depth 4
mkdir ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/surrogate_model_for_experiment/
cp ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/surrogate_model_depth_4/surrogate_model_* \
   ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/surrogate_model_for_experiment/
```

> 🔧 **Configuration Note**:  
> In every surrogate model file, update the first component's conditions to focus the analysis on requests targeting stylesheets with the suffix `not_a_file.css`.  
> This ensures that only payloads ending with this sensitive suffix are considered valid targets during both generation and validation phases.

```python
target_pre_condition_list=[
    SuffixType("not_a_file.css")
],
target_post_condition_list=[
    SuffixType("not_a_file.css")
],
```

---
## Generate and Validate Exploit Payloads by Depth

For each surrogate model depth (`depth2`, `depth3`, `depth4`), we perform a two-stage process:

1. **Payload Generation** – An SMT-based algorithm explores transformation sequences that could allow a payload to bypass intermediate filtering.
2. **Payload Validation** – Each generated payload is validated to ensure that it meets the attacker’s objective when passed through all modeled components.

Below are the specific commands to execute for each depth.

### Depth 2

```bash
python case_study/tools/generate_validated_exploit_payloads_for_experiment.py \
  --rules ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/experiment_config_prior_work_depth2.json \
  --iterations 10 \
  --timeout 10 \
  --max-transformation 1 \
  --max-workers 6
```

### Depth 3

```bash
python case_study/tools/generate_validated_exploit_payloads_for_experiment.py \
  --rules ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/experiment_config_prior_work_depth3.json \
  --iterations 10 \
  --timeout 10 \
  --max-transformation 1 \
  --max-workers 6
```

### Depth 4

```bash
python case_study/tools/generate_validated_exploit_payloads_for_experiment.py \
  --rules ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/experiment_config_prior_work_depth4.json \
  --iterations 10 \
  --timeout 10 \
  --max-transformation 1 \
  --max-workers 6
```

Each execution produces:

- 📁 `./case_study/generation_results/` – Raw SMT solving output for each surrogate model
- 📁 `./case_study/validation_results/` – Validated payloads and associated metrics

These outputs are essential for assessing the effectiveness of depth-based modeling and for comparing against prior heuristic methods.

---

## Analyze and Summarize Results by Depth

To quantify performance and validation effectiveness, we analyze the outputs for each depth and generate a CSV summary.

### Depth 2

```bash
 python case_study/tools/analysis_generation_and_validation_results_for_experiment.py \
  --config ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/analysis_config_prior_work_depth2.json \
  --depth 2 \
  --output ./case_study/analysis_results/enhancing_heuristic_depth2.csv
```

### Depth 3

```bash
 python case_study/tools/analysis_generation_and_validation_results_for_experiment.py \
  --config ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/analysis_config_prior_work_depth3.json \
  --depth 3 \
  --output ./case_study/analysis_results/enhancing_heuristic_depth3.csv
```

### Depth 4

```bash
 python case_study/tools/analysis_generation_and_validation_results_for_experiment.py \
  --config ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/analysis_config_prior_work_depth4.json \
  --depth 4 \
  --output ./case_study/analysis_results/enhancing_heuristic_depth4.csv
```

Each resulting CSV provides comprehensive metrics for every surrogate model tested, including:

- ✔️ **Payload Generation**:
  - Total SMT solving time per model
  - Average number of successful exploit paths
  - Per-step execution time and system resource usage

- 🔍 **Payload Validation**:
  - Validation success rate per model
  - Ratio of payloads reaching target path
  - Frequency of exact target match

This depth-specific analysis enables empirical comparison of **transformation-based payload discovery** against traditional heuristics under increasing system complexity.

---
## Extract Unique Exploit Payloads by Depth

After validating exploit payloads for each surrogate model, we extract unique payloads per depth level to assess diversity, overlap, and novelty of attack vectors.

This step helps in understanding how increasing the depth of surrogate models affects payload complexity and discovery rate.

Run the following commands for each depth:

### Depth 2

```bash
python case_study/tools/get_unique_exploit_payloads_for_experiment.py \
  ./case_study/validation_results/enhancing_heuristic_from_prior_work/prior_work_depth2 \
  --output ./case_study/unique_payloads/unique_payloads_enhancing_heuristic_depth2.json
```

### Depth 3

```bash
python case_study/tools/get_unique_exploit_payloads_for_experiment.py \
  ./case_study/validation_results/enhancing_heuristic_from_prior_work/prior_work_depth3 \
  --output ./case_study/unique_payloads/unique_payloads_enhancing_heuristic_depth3.json
```

### Depth 4

```bash
python case_study/tools/get_unique_exploit_payloads_for_experiment.py \
  ./case_study/validation_results/enhancing_heuristic_from_prior_work/prior_work_depth4 \
  --output ./case_study/unique_payloads/unique_payloads_enhancing_heuristic_depth4.json
```

Each output JSON contains the deduplicated list of payloads that successfully bypassed intermediate filters and reached the target destination under the specified surrogate model.

These payload sets allow researchers to:

- Assess the **semantic variety** of generated exploits.
- Compare **cross-depth differences** in attack surface coverage.
- Measure **heuristic effectiveness** against a controlled payload universe.

All extracted payloads are saved under:

```bash
./case_study/unique_payloads/
```

This provides a clean, reproducible base for downstream analyses such as clustering, real-world replay testing, or manual triage.

---
## Reproducing Results from the Paper

Each subfolder under `prior_work_depth2/`, `prior_work_depth3/`, and `prior_work_depth4/` includes:

- `data/`: Archived payloads and logs  
- `presets/`: Final surrogate models used in the experiment  
- `experiment_config_*.json`: Configuration inputs for the experiment script

```bash
case_study/enhancing_heuristic_from_prior_work/prior_work_depth*/data/
```

To validate true positives (TPs) of generated exploit payloads, PathFault provides a mechanism to replay payloads through a real HTTP request chain. This requires setting up a mimic environment in which each component forwards requests to the next component based on the URL prefix.

For example, when `apachehttpserver` is listening on port 8001 and `apachetomcat` is on 8002, a request to:

```
http://127.0.0.1:8001/apachetomcat/payload
```

will be parsed by `apachehttpserver`, which recognizes the prefix and forwards it to:

```
http://apachetomcat:8002/payload
```

The preset configuration files already implement such behavior, except for `apachetrafficserver (ATS)`, which acts as the entry point in this reproduction setting.  
Therefore, to fully validate the results of the paper, we reproduce the evaluation by chaining ATS to the following backend targets:

- `apachehttpserver`
- `apachetomcat`
- `nginx`
- `tmpserver`

Each test should be conducted independently and results can be filtered/merged afterward. Below is the procedure for `depth2`. The same steps apply to other depths using their respective directories and configuration files.

---

### Step 1: Copy Preset Web Component Configurations

```bash
cp -r ./presets/web_app_components/apachehttpserver ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/apachetrafficserver ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/apachetrafficserver2apachehttpserver ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/apachetrafficserver2apachetomcat ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/apachetrafficserver2nginx ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/apachetomcat ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/nginx ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
```

---

### Step 2: Execute Prior Work (tmp, httpd, tomcat, nginx)

For each backend target, follow these steps:

#### (A) ATS → tmpserver

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tmp.json

docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_ats2tmp.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/prior_work_exploit_option_file_depth2.json
```

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (B) ATS → apachehttpserver

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2httpd.json

docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_ats2httpd.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/prior_work_exploit_option_file_depth2.json
```

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (C) ATS → apachetomcat

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tomcat.json

docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_ats2tomcat.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/prior_work_exploit_option_file_depth2.json
```

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (D) ATS → nginx

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2nginx.json

docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_ats2nginx.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/prior_work_exploit_option_file_depth2.json
```

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### 🔄 Combining and Analyzing Log Results


After executing all ATS chain validations, the generated logs need to be merged into a single file for consolidated analysis.  
The following script performs selective row filtering from each CSV and stores the result in a unified output file:

- From `logs_ats2tmp.csv`: keep all rows where the `X-Request-Type` does **not** contain `APACHETRAFFICSERVER_`
- From `logs_ats2httpd.csv`: keep rows where the field **contains** `APACHETRAFFICSERVER2APACHEHTTPSERVER_APACHEHTTPSERVER`
- From `logs_ats2tomcat.csv`: keep rows where the field **contains** `APACHETRAFFICSERVER2APACHETOMCAT_APACHETOMCAT`
- From `logs_ats2nginx.csv`: keep rows where the field **contains** `APACHETRAFFICSERVER2NGINX_NGINX`

The merged result is written to the output CSV file.

```bash
python ./case_study/tools/get_combined_logs_csv.py \
  --tmp    ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_ats2tmp.csv \
  --httpd  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_ats2httpd.csv \
  --tomcat ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_ats2tomcat.csv \
  --nginx  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_ats2nginx.csv \
  --output ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/combined_logs.csv
```

You can now analyze the fully merged log using:

```bash
python ./case_study/tools/analysis_combined_logs_csv.py \
  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/combined_logs.csv
```

Expected output:

```
📌 Summary: Matched ID Count per X-Request-Type
────────────────────────────────────────────────────────────────────────────
APACHEHTTPSERVER_APACHETOMCAT                          → 2 matched ID(s) (from 2 unique inbound URL(s))
APACHEHTTPSERVER_APACHETRAFFICSERVER                   → 0 matched ID(s) (from 0 unique inbound URL(s))
APACHEHTTPSERVER_NGINX                                 → 0 matched ID(s) (from 0 unique inbound URL(s))
APACHETOMCAT_APACHEHTTPSERVER                          → 0 matched ID(s) (from 0 unique inbound URL(s))
APACHETOMCAT_APACHETRAFFICSERVER                       → 0 matched ID(s) (from 0 unique inbound URL(s))
APACHETOMCAT_NGINX                                     → 0 matched ID(s) (from 0 unique inbound URL(s))
APACHETRAFFICSERVER2APACHEHTTPSERVER_APACHEHTTPSERVER  → 0 matched ID(s) (from 0 unique inbound URL(s))
APACHETRAFFICSERVER2APACHETOMCAT_APACHETOMCAT          → 1 matched ID(s) (from 1 unique inbound URL(s))
APACHETRAFFICSERVER2NGINX_NGINX                        → 0 matched ID(s) (from 0 unique inbound URL(s))
NGINX_APACHEHTTPSERVER                                 → 0 matched ID(s) (from 0 unique inbound URL(s))
NGINX_APACHETOMCAT                                     → 1 matched ID(s) (from 1 unique inbound URL(s))
NGINX_APACHETRAFFICSERVER                              → 0 matched ID(s) (from 0 unique inbound URL(s))

🏷️ Total Matched IDs Across All Types: 4

🌐 Total Unique Inbound URLs from All Matched IDs: 2  
   - /profile%23not_a_file.css  
   - /profile%3Bnot_a_file.css

📊 Summary  
Unique Payloads: 2  
Vulnerable Pairs: 3/12  
TP: 4  
```

In summary, for **depth-2**, among 12 possible server combinations:  
- **2 unique exploit payloads** were confirmed,  
- **3 combinations were vulnerable**,
- **and 4 true positives (TPs)** were identified,

### Step 3: Execute PathFault Variant (tmp, httpd, tomcat, nginx)

#### Prepare Exploit Payloads

Insert the previously generated payloads placed in `case_study/unique_payloads/unique_payloads_enhancing_heuristic_depth2.json` into the following JSON file `./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/pathfault_exploit_option_file_depth2.json` in proper depth :

```json
{
  "port_map_path": "./pathfault/results/mimic_environment_creator/port_map.json",
  "depth": 2,
  "exploit_payloads": [
    // add the generated exploit payloads here
  ]
}
```



And then, to reproduce the experiment using **PathFault-generated payloads**, replace the `--exploit-option-file` path with:

```bash
./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/pathfault_exploit_option_file_depth2.json
```

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (A) ATS → tmpserver

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tmp.json

docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_pathfault_ats2tmp.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/pathfault_exploit_option_file_depth2.json
```

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (B) ATS → apachehttpserver

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2httpd.json

docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_pathfault_ats2httpd.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/pathfault_exploit_option_file_depth2.json
```

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (C) ATS → apachetomcat

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tomcat.json

docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_pathfault_ats2tomcat.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/pathfault_exploit_option_file_depth2.json
```

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (D) ATS → nginx

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2nginx.json

docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_pathfault_ats2nginx.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/pathfault_exploit_option_file_depth2.json
```

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

---

After executing all PathFault evaluations, you can merge the log results using:

```bash
python ./case_study/tools/get_combined_logs_csv.py \
  --tmp    ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_pathfault_ats2tmp.csv \
  --httpd  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_pathfault_ats2httpd.csv \
  --tomcat ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_pathfault_ats2tomcat.csv \
  --nginx  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/logs_pathfault_ats2nginx.csv \
  --output ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/combined_logs_pathfault.csv
```

Then run the analysis:

```bash
python ./case_study/tools/analysis_combined_logs_csv.py \
  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth2/presets/combined_logs_pathfault.csv
```

---

Repeat this entire process for `depth3` and `depth4` by adjusting all paths and filenames accordingly.

## Depth 3

### Prior Work

For each backend target, follow these steps to create a mimic environment, generate CSV logs with exploit payloads, and clean up logs.

#### (A) ATS → tmpserver

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tmp.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_ats2tmp.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/prior_work_exploit_option_file_depth3.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (B) ATS → apachehttpserver

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2httpd.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_ats2httpd.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/prior_work_exploit_option_file_depth3.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (C) ATS → apachetomcat

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tomcat.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_ats2tomcat.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/prior_work_exploit_option_file_depth3.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (D) ATS → nginx

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2nginx.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_ats2nginx.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/prior_work_exploit_option_file_depth3.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### Combining and Analyzing Log Results

After executing all ATS chain validations, the generated logs need to be merged into a single file for consolidated analysis. The following script performs selective row filtering from each CSV and stores the result in a unified output file:

- From `logs_ats2tmp.csv`: keep all rows where the `X-Request-Type` does **not** contain `APACHETRAFFICSERVER_`
- From `logs_ats2httpd.csv`: keep rows where the field **contains** `APACHETRAFFICSERVER2APACHEHTTPSERVER_APACHEHTTPSERVER`
- From `logs_ats2tomcat.csv`: keep rows where the field **contains** `APACHETRAFFICSERVER2APACHETOMCAT_APACHETOMCAT`
- From `logs_ats2nginx.csv`: keep rows where the field **contains** `APACHETRAFFICSERVER2NGINX_NGINX`

The merged result is written to the output CSV file.

```bash
python ./case_study/tools/get_combined_logs_csv.py \
  --tmp    ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_ats2tmp.csv \
  --httpd  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_ats2httpd.csv \
  --tomcat ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_ats2tomcat.csv \
  --nginx  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_ats2nginx.csv \
  --output ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/combined_logs.csv
```

Analyze the combined logs to obtain a summary of matched IDs, unique payloads, and vulnerable pairs:

```bash
python ./case_study/tools/analysis_combined_logs_csv.py \
  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/combined_logs.csv
```

### PathFault Variant

First, prepare the exploit payloads by inserting the generated payloads from `case_study/unique_payloads/unique_payloads_enhancing_heuristic_depth3.json` into `./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/pathfault_exploit_option_file_depth3.json` in the proper depth format:

```json
{
  "port_map_path": "./pathfault/results/mimic_environment_creator/port_map.json",
  "depth": 3,
  "exploit_payloads": [
    // add the generated exploit payloads here
  ]
}
```

Then, for each backend target, follow these steps:

#### (A) ATS → tmpserver

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tmp.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_pathfault_ats2tmp.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/pathfault_exploit_option_file_depth3.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (B) ATS → apachehttpserver

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2httpd.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_pathfault_ats2httpd.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/pathfault_exploit_option_file_depth3.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (C) ATS → apachetomcat

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tomcat.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_pathfault_ats2tomcat.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/pathfault_exploit_option_file_depth3.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (D) ATS → nginx

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2nginx.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_pathfault_ats2nginx.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/pathfault_exploit_option_file_depth3.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### Combining and Analyzing Log Results

Merge the logs using the same filtering logic as described in Prior Work:

```bash
python ./case_study/tools/get_combined_logs_csv.py \
  --tmp    ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_pathfault_ats2tmp.csv \
  --httpd  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_pathfault_ats2httpd.csv \
  --tomcat ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_pathfault_ats2tomcat.csv \
  --nginx  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/logs_pathfault_ats2nginx.csv \
  --output ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/combined_logs_pathfault.csv
```

Analyze the combined logs:

```bash
python ./case_study/tools/analysis_combined_logs_csv.py \
  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth3/presets/combined_logs_pathfault.csv
```

## Depth 4

### Prior Work

For each backend target, follow these steps:

#### (A) ATS → tmpserver

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tmp.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_ats2tmp.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/prior_work_exploit_option_file_depth4.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (B) ATS → apachehttpserver

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2httpd.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_ats2httpd.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/prior_work_exploit_option_file_depth4.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (C) ATS → apachetomcat

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tomcat.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_ats2tomcat.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/prior_work_exploit_option_file_depth4.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (D) ATS → nginx

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2nginx.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_ats2nginx.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/prior_work_exploit_option_file_depth4.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### Combining and Analyzing Log Results

Merge the logs using the same filtering logic as described in Depth 3 Prior Work:

```bash
python ./case_study/tools/get_combined_logs_csv.py \
  --tmp    ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_ats2tmp.csv \
  --httpd  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_ats2httpd.csv \
  --tomcat ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_ats2tomcat.csv \
  --nginx  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_ats2nginx.csv \
  --output ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/combined_logs.csv
```

Analyze the combined logs:

```bash
python ./case_study/tools/analysis_combined_logs_csv.py \
  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/combined_logs.csv
```

### PathFault Variant

First, prepare the exploit payloads by inserting the generated payloads from `case_study/unique_payloads/unique_payloads_enhancing_heuristic_depth4.json` into `./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/pathfault_exploit_option_file_depth4.json` in the proper depth format:

```json
{
  "port_map_path": "./pathfault/results/mimic_environment_creator/port_map.json",
  "depth": 4,
  "exploit_payloads": [
    // add the generated exploit payloads here
  ]
}
```

Then, for each backend target:

#### (A) ATS → tmpserver

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tmp.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_pathfault_ats2tmp.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/pathfault_exploit_option_file_depth4.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (B) ATS → apachehttpserver

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2httpd.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_pathfault_ats2httpd.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/pathfault_exploit_option_file_depth4.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (C) ATS → apachetomcat

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2tomcat.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_pathfault_ats2tomcat.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/pathfault_exploit_option_file_depth4.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### (D) ATS → nginx

1. **Create mimic environment**:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/enhancing_heuristic_from_prior_work/create_mimic_environment_config_ats2nginx.json
```

2. **Manage docker containers**:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml down
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

3. **Generate CSV logs**:

```bash
python manage.py core inconsistency-detector workflows get-csv-with-sending-exploit-payloads \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --csv-output-path ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_pathfault_ats2nginx.csv \
  --exploit-option-file ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/pathfault_exploit_option_file_depth4.json
```

4. **Clean up logs**:

```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

#### Combining and Analyzing Log Results

Merge the logs using the same filtering logic as described in Depth 4:

```bash
python ./case_study/tools/get_combined_logs_csv.py \
  --tmp    ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_pathfault_ats2tmp.csv \
  --httpd  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_pathfault_ats2httpd.csv \
  --tomcat ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_pathfault_ats2tomcat.csv \
  --nginx  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/logs_pathfault_ats2nginx.csv \
  --output ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/combined_logs_pathfault.csv
```

Analyze the combined logs:

```bash
python ./case_study/tools/analysis_combined_logs_csv.py \
  ./case_study/enhancing_heuristic_from_prior_work/prior_work_depth4/presets/combined_logs_pathfault.csv
```
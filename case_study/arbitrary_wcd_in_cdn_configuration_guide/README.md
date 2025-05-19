# Generating Real-World Exploit Payloads - Arbitrary Web Cache Deception in the CDN Configuration Guide

This document provides a step-by-step guide for modeling and validating exploit payloads related to **Arbitrary Web Cache Deception (WCD)** in CDN configurations using the PathFault.

## About Arbitrary WCD in CDN Configuration Guide

This case study focuses on a vulnerability that arises when Content Delivery Networks (CDNs) inconsistently handle cacheable resources, particularly under certain path prefixes. In this scenario, some frontend caching layers (e.g., CDN edges) cache resources under paths like `/images/*.jpg` without normalization, while the backend may interpret the path differently or enforce normalization rules that expose unintended files.

The PathFault allows for systematic modeling of such inconsistencies by constructing surrogate models representing chains of URL-parsing behaviors across realistic component sequences. Importantly, this case demonstrates that **multiple domain-specific conditions** can be applied simultaneously (e.g., path prefix and suffix), showcasing PathFault's ability to incorporate **compound pentester knowledge**, not just single heuristics.

## Create Mimic Environment

The experiment uses components such as `nginx`, `apachehttpserver`, `apachetrafficserver`, and `apachetomcat`. These are replicated using container presets.

### Step 1: Copy Preset Files

```bash
cp -r ./presets/web_app_components/apachehttpserver ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/apachetrafficserver ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/apachetomcat ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/nginx ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
````

### Step 2: Generate Docker Compose Configuration

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/arbitrary_wcd_in_cdn_configuration_guide/create_mimic_environment_config.json
```

### Step 3: Launch the Mimic Environment

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

---

## Detect Inconsistency

```bash
python manage.py core inconsistency-detector workflows detect-inconsistency \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json
```

Outputs include:

* `inconsistency_detector_config/`
* `logs/`
* `converted_logs.csv`
* `inconsistency_analysis_result.json`

---

## Build Surrogate Models (Depth 3)

```bash
python manage.py core surrogate-model-builder workflows build-surrogate-model-by-depth \
  --json ./pathfault/results/inconsistency_detector/inconsistency_analysis_result.json \
  --depth 3 \
  --output-dir ./case_study/arbitrary_wcd_in_cdn_configuration_guide/presets
```

Manually copy relevant models to the experimental directory:

```bash
mkdir ./case_study/arbitrary_wcd_in_cdn_configuration_guide/presets/surrogate_model_for_experiment/
cp -r ./case_study/arbitrary_wcd_in_cdn_configuration_guide/presets/surrogate_model_depth_3/* \
  ./case_study/arbitrary_wcd_in_cdn_configuration_guide/presets/surrogate_model_for_experiment/
```

In each surrogate model, update the first component as follows:

```python
target_pre_condition_list = [
    PrefixType("/images/"),
    SuffixType(".jpg")
],
target_post_condition_list = [
    PrefixType("/images/"),
    SuffixType(".jpg")
],
```

> ✅ This demonstrates PathFault's ability to reflect **multi-factored constraints**, enabling compound pentester insights within the model.

---

## Generate and Validate Exploit Payloads

```bash
python case_study/tools/generate_validated_exploit_payloads_for_experiment.py \
  --rules ./case_study/arbitrary_wcd_in_cdn_configuration_guide/experiment_config_cdn.json \
  --iterations 5 \
  --timeout 10 \
  --max-transformation 1 \
  --max-workers 6
```

Payload generation and validation outputs are written to:

* `./case_study/generation_results/`
* `./case_study/validation_results/`

---

## Reproducing Results from the Paper
To analyze and summarize the results, the tool produces a CSV file containing detailed metrics for each surrogate model tested.
```bash
python ./case_study/tools/analysis_generation_and_validation_results_for_experiment.py \
  --config ./case_study/arbitrary_wcd_in_cdn_configuration_guide/analysis_config_cdn.json \
  --depth 3 \
  --output ./case_study/analysis_results/arbitrary_wcd_in_cdn_configuration_guide.csv
```

To extract all unique exploit payloads observed across validation results:

```bash
python case_study/tools/get_unique_exploit_payloads_for_experiment.py \
  ./case_study/validation_results/arbitrary_wcd_in_cdn_configuration_guide \
  --output ./case_study/unique_payloads/unique_payloads_arbitrary_wcd_in_cdn_configuration_guide.json
```

All validated payloads and data files that support the paper's findings are available at:

```text
./case_study/arbitrary_wcd_in_cdn_configuration_guide/data/
```


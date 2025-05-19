# Generating Real-World Exploit Payloads - Account Takeover in ChatGPT

This document provides a step-by-step guide for modeling and validating exploit payloads related to **ChatGPT Account Takeover** using the PathFault framework.

## About ChatGPT Account Takeover

This case study addresses an account takeover vulnerability caused by inconsistent URL parsing behaviors across multiple web components. While specific server types are not disclosed in public incident reports, the vulnerability centers around scenarios in which a frontend component caches certain path prefixes like `/share/` without normalization, while the final backend performs normalization and exposes sensitive information.

PathFault is used here to construct surrogate models that capture the assumed behavior of such systems. By modeling multiple realistic combinations of web components—each with distinct parsing semantics—we can deterministically estimate how a crafted request may traverse and transform across the entire stack.

This case study is thus designed under the insight that increasing the number of known components involved in the surrogate model leads to a higher fidelity in approximating real-world web application behavior, particularly in complex setups like ChatGPT's multi-layered infrastructure.

## Create Mimic Environment

The vulnerable configuration involves `nginx`, `apachehttpserver`, `apachetrafficserver`, and `apachetomcat`. Therefore, a **mimic environment** needs to be set up using these components.

### Step 1: Copy Preset Files

To use the provided preset files, copy them into the tool’s `web_app_components` directory:

```bash
cp -r ./presets/web_app_components/apachehttpserver ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/apachetrafficserver ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/apachetomcat ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/nginx ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
cp -r ./presets/web_app_components/tmpserver ./pathfault/modules/utilities/mimic_environment_creator/web_app_components
```

### Step 2: Generate Docker Compose Configuration

Generate the `docker-compose.yml` configuration using:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./case_study/chatgpt_account_takeover/create_mimic_environment_config.json
```

### Step 3: Launch the Mimic Environment

Start the mimic environment with Docker Compose:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

Also, if the `logs` file is already exists, delete it.
```bash
sudo rm -r ./pathfault/results/mimic_environment_creator/logs
```

---

## Detect Inconsistency

After launching the mimic environment, run the inconsistency detection workflow:

```bash
python manage.py core inconsistency-detector workflows detect-inconsistency \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json
```

This workflow outputs the following artifacts:

* 🧾 `inconsistency_detector_config`: Configuration files for testing.
* 📁 `logs/`: PCAP traffic logs.
* 📊 `converted_logs.csv`: Structured summary of requests and responses.
* 📈 `inconsistency_analysis_result.json`: JSON summary of identified discrepancies.

## Build Surrogate Model

Use the inconsistency detection results to build surrogate models representing URL parsing behaviors. The following command generates surrogate models for all possible combinations up to depth 2:

```bash
python manage.py core surrogate-model-builder workflows build-surrogate-model-by-depth \
  --json ./pathfault/results/inconsistency_detector/inconsistency_analysis_result.json \
  --depth 2 \
  --output-dir ./case_study/chatgpt_account_takeover/presets
```

The generated surrogate models are initially stored under:

[`./case_study/chatgpt_account_takeover/presets/surrogate_model_depth_2/`](./case_study/chatgpt_account_takeover/presets/surrogate_model_depth_2/)

To prepare for experiments, copy the relevant surrogate models into:

[`./case_study/chatgpt_account_takeover/presets/surrogate_model_for_experiment/`](./case_study/chatgpt_account_takeover/presets/surrogate_model_for_experiment/)

```shell
cp -r ./case_study/chatgpt_account_takeover/presets/surrogate_model_depth_2/* ./case_study/chatgpt_account_takeover/presets/surrogate_model_for_experiment/
```

Each surrogate model includes specific pre-conditions and post-conditions targeting the `/share/` prefix in the first component:

```python
target_pre_condition_list=[
    PrefixType("/share/"),
],
target_post_condition_list=[
    PrefixType("/share/"),
],
```


## Generate Exploit Payload

### Step 1: Setting the Pentester's Objective

Adjust the surrogate model (as required) to reflect realistic exploitation objectives such as accessing sensitive internal resources.

### Step 2: Generating Validated Exploit Payloads

Generate and validate exploit payloads using:

```bash
python case_study/tools/generate_validated_exploit_payloads_for_experiment.py \
  --rules ./case_study/chatgpt_account_takeover/experiment_config_chatgpt.json \
  --iterations 10 \
  --timeout 10 \
  --max-transformation 1 \
  --max-workers 6
```

Each option controls:

* `--rules`: JSON config file specifying surrogate models.
* `--iterations`: Number of execution iterations.
* `--timeout`: SMT solver timeout per payload.
* `--max-transformation`: Max transformations per request.
* `--max-workers`: Parallel SMT solver processes.

Generated and validated payloads are written to:

* `./case_study/generation_results/`
* `./case_study/validation_results/`

## Reproducing Results from the Paper

To analyze and summarize the results, the tool produces a CSV file containing detailed metrics for each surrogate model tested.
```bash
python ./case_study/tools/analysis_generation_and_validation_results_for_experiment.py \
  --config ./case_study/chatgpt_account_takeover/analysis_config_chatgpt.json \
  --depth 2 \
  --output ./case_study/analysis_results/chatgpt_account_takeover.csv
```


> ⚠️ **Important Notes on Analysis Scope**
>
> The `--config` argument is used to specify the *target payload* for each case study, allowing the tool to perform enhanced analysis such as checking whether the desired exploit payload was successfully generated and validated.
>
> However, the tool will analyze **all files** under the following directories:
>
> - `./case_study/generation_results/`
> - `./case_study/validation_results/`
>
> Therefore, to ensure that the CSV includes only metrics relevant to the current case study (e.g., ChatGPT Account Takeover), you **must manually remove** or relocate unrelated experiment results from these directories **before** running the analysis.
>
> This design supports bulk analysis but places responsibility on the user to manage directory contents appropriately for scoped evaluation.

Each row corresponds to a specific surrogate model and includes the following fields:

* **project**: The name of the case study.
* **surrogate**: The surrogate model filename.
* **target\_payload**: The attacker-specified target path.
* **gen\_component1**, **gen\_component2**, ...: The sequence of components (e.g., nginx → apachehttpserver).
* **gen\_file\_count**: Number of generation trials.
* **gen\_total\_avg**: Average total generation time per trial.
* **gen\_smt\_solving\_info\_count**: Total number of SMT solving attempts.
* **gen\_avg\_success** / **gen\_avg\_failed**: Average count of successful or failed SMT attempts.
* **gen\_avg\_final\_transformed\_urls**: Average number of final URLs generated.
* **gen\_stepX**: Average duration for each internal step in the generation pipeline.
* **gen\_max\_memory\_MB**, **gen\_cpu\_user\_time\_sec**, etc.: Average resource usage during generation.
* **val\_file\_count**: Number of validation attempts.
* **val\_avg\_execution\_time**: Average time taken per validation.
* **val\_avg\_successful** / **val\_avg\_removed**: Average number of valid vs. filtered payloads.
* **val\_max\_successful**, etc.: Maximum counts observed during validation.
* **val\_contain\_payload\_success\_ratio**: Ratio of validations where the exact target payload appeared.
* **val\_payload\_exist\_success\_ratio**: Ratio of validations that produced at least one valid payload.
* **total\_avg\_combined**: Combined generation + validation duration.
* **combined\_cpu\_user\_time\_sec**, etc.: Aggregate resource usage across both phases.

All quantitative results reported in the paper were derived from this workflow. The final processed artifacts can be accessed at:

[`./case_study/chatgpt_account_takeover/data/`](./case_study/chatgpt_account_takeover/data/)

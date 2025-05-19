# Mimic Environment Creator

This module provides utilities to help users create a mimic environment simulating various web infrastructure setups.  
It generates necessary files such as customized `entrypoint.sh`, `Dockerfile`s, a `port_map.json`, and `docker-compose.yml` based on user-defined configurations.

---

## Getting Started

To construct the mimic environment, run the following commands in **order**.

---

### Step 1: Generate `entrypoint.sh` Scripts

This step creates the `entrypoint.sh` script for each web app component based on its `entrypoint.sh.frag`.

```bash
python manage.py utilities mimic-environment-creator services create-entrypoint-script \
  --web-app-config-path ./presets/create_mimic_environment_config.json
```

---

### Step 2: Generate `Dockerfile`s

This step generates full `Dockerfile`s by combining:
- The component-specific `Dockerfile.frag`
- The default Dockerfile fragment
- Port assignments starting from 8000

```bash
python manage.py utilities mimic-environment-creator services create-dockerfile \
  --web-app-config-path ./presets/create_mimic_environment_config.json
```

---

### Step 3: Generate `port_map.json`

This step analyzes the generated `Dockerfile`s to extract the assigned ports and saves them in `port_map.json`.

```bash
python manage.py utilities mimic-environment-creator services create-port-map \
  --web-app-result-dir ./pathfault/results/mimic_environment_creator/web_app_components \
  --output-path ./pathfault/results/mimic_environment_creator/port_map.json
```

---

### Step 4: Generate `docker-compose.yml`

This step uses the generated `Dockerfile`s and `port_map.json` to build a full `docker-compose.yml` file.

```bash
python manage.py utilities mimic-environment-creator services create-docker-compose-file \
  --web-app-result-dir ./pathfault/results/mimic_environment_creator/web_app_components \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --output-path ./pathfault/results/mimic_environment_creator/docker-compose.yml
```

---

## Shortcut: Using Workflow (One-Shot)

You can run the full process above using a single command via the `workflows` shortcut:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./presets/create_mimic_environment_config.json
```

This workflow internally invokes all the service commands in the correct order:
1. `create-entrypoint-script`
2. `create-dockerfile`
3. `create-port-map`
4. `create-docker-compose-file`

---

## Running the Mimic Environment

Once all files have been generated, launch the mimic environment using Docker Compose:

```bash
docker compose -f ./pathfault/results/mimic_environment_creator/docker-compose.yml up
```

- This command will build and start all web application containers defined in `docker-compose.yml`.
- **To stop the environment**, simply press `Ctrl + C` in the terminal.

---

### Command Arguments

| Argument                 | Description                                                          |
|--------------------------|----------------------------------------------------------------------|
| `--web-app-config-path`  | Path to the JSON configuration file specifying web components.       |
| `--web-app-result-dir`   | Directory where generated Dockerfiles are stored.                    |
| `--output-path`          | Path to store the generated `port_map.json` or `docker-compose.yml`. |
| `--port-map-path`        | Path to the `port_map.json` used by `docker-compose.yml`.            |

---

### Notes

- All generated artifacts are saved to:

```
pathfault/results/mimic_environment_creator/
```

- Each component is assigned a sequential port starting from `8000`.
- The input JSON file must define a `web_app_components` key.
- `entrypoint.sh` must be created **before** the Dockerfiles.
- `port_map.json` must be created **after** Dockerfiles.
- `docker-compose.yml` must be created last.

---

## Example

Given the preset config file at:

```
./presets/create_mimic_environment_config.json
```

Run the full sequence manually:

```bash
python manage.py utilities mimic-environment-creator services create-entrypoint-script \
  --web-app-config-path ./presets/create_mimic_environment_config.json

python manage.py utilities mimic-environment-creator services create-dockerfile \
  --web-app-config-path ./presets/create_mimic_environment_config.json

python manage.py utilities mimic-environment-creator services create-port-map \
  --web-app-result-dir ./pathfault/results/mimic_environment_creator/web_app_components \
  --output-path ./pathfault/results/mimic_environment_creator/port_map.json

python manage.py utilities mimic-environment-creator services create-docker-compose-file \
  --web-app-result-dir ./pathfault/results/mimic_environment_creator/web_app_components \
  --port-map-path ./pathfault/results/mimic_environment_creator/port_map.json \
  --output-path ./pathfault/results/mimic_environment_creator/docker-compose.yml
```

Or simply use the workflow shortcut:

```bash
python manage.py utilities mimic-environment-creator workflows create-mimic-environment \
  --web-app-config-path ./presets/create_mimic_environment_config.json
```

---

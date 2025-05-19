# Surrogate Model Builder

This utility generates a Python-based surrogate model for web server behaviors by translating inconsistency analysis results into symbolic transformation rules and predicate conditions.

---

## 🛠️ Usage: Single Surrogate Model

To build a surrogate model for the core server configurations evaluated in our study (`nginx`, `apachehttpserver`, `apachetrafficserver`, `apachetomcat`), run the following command:

```bash
python manage.py core surrogate-model-builder services build-surrogate-model \
--json ./pathfault/results/inconsistency_detector/inconsistency_analysis_result.json \
--server-list apachehttpserver,apachetomcat
```

This command will generate a Python module named `surrogate_model.py` in the working directory.

---

## 🔁 Usage: Build All Server Combinations by Depth

To automatically build surrogate models for **all permutations of server combinations** of a specified depth (e.g., 2), use the following workflow command:

```bash
python manage.py core surrogate-model-builder workflows build-surrogate-model-by-depth \
--json ./pathfault/results/inconsistency_detector/inconsistency_analysis_result.json \
--depth 2
```

This will generate surrogate models for all length-2 permutations (e.g., `nginx→apachetomcat`, `apachehttpserver→nginx`, etc.) and save them in:

```
./pathfault/results/surrogate_model_builder/surrogate_model_depth_2/
```

Each generated model is named:

```
surrogate_model_<server1>_<server2>.py
```

---

## 📄 Command-line Options

| Option                             | Description                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| `--json` (required)               | Path to the inconsistency JSON result file                                 |
| `--server-list` (repeatable)     | Names of servers to include in the model (e.g., `nginx`, `apachehttpserver`) |
| `--output`                        | Output Python file name (default: `surrogate_model.py`)                    |
| `--include-omitted-inconsistency`| If specified, includes inconsistencies omitted due to percent-encoding equivalence |
| `--depth` (for workflow)          | Depth of server permutations to generate                                   |
| `--output-dir` (for workflow)     | Output directory for generated models (default: `./pathfault/results/surrogate_model_builder`) |

---

## ✅ Output

The generated `surrogate_model.py` defines a `get_surrogate_model()` function that returns a list of `Server` objects, each containing symbolic transformation rules and predicate logic conditions derived from the inconsistency data.

```python
def get_surrogate_model():
    ...
    return [apachehttpserver, apachetomcat]
```

This surrogate model is consumed by downstream components (e.g., the exploit payload generator) to synthesize and validate candidate attack vectors under inconsistent parsing behaviors.

---

## 📦 Assumptions

This model builder assumes that the input JSON file contains structured results for the following servers:

- `nginx`
- `apachehttpserver`
- `apachetrafficserver`
- `apachetomcat`

If any of these servers are missing from the file, the script will terminate with an error message.

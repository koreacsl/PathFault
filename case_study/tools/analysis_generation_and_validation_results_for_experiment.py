#!/usr/bin/env python3
"""
Aggregate PathFault *generation* and *validation* JSON logs into a single CSV.

• generation-results default:  ./case_study/generation_results
• validation-results default:  ./case_study/validation_results
• --config (required) : maps each <project> → its expected payload
"""

from __future__ import annotations
import os, json, csv, glob
import click

# ───────────────────────── helper functions (logic unchanged) ───────────────
def _safe_add(acc: dict, key: str, value):
    """add value to acc[key] treating None as 0."""
    acc[key] = acc.get(key, 0) + (value or 0)

def process_generation_json_files(json_files):
    aggregated, total_sum, count = {}, 0.0, 0
    smt_solving_info_count = None
    total_success = total_failed = total_final_urls = 0
    resource_sum = dict.fromkeys(
        ("max_memory_MB", "cpu_user_time_sec", "cpu_system_time_sec", "wall_clock_time_sec"), 0
    )
    resource_count = 0

    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as fp:
                data = json.load(fp)

            # steps
            if "steps" not in data:
                continue
            file_total = 0.0
            for step, info in data["steps"].items():
                dur = info.get("duration") or 0
                aggregated[step] = aggregated.get(step, 0) + dur
                file_total += dur
            total_sum += file_total

            # SMT list
            if isinstance(data.get("smt_solving_info"), list):
                if smt_solving_info_count is None:
                    smt_solving_info_count = len(data["smt_solving_info"])
                total_success += sum(1 for i in data["smt_solving_info"] if i.get("status") == "success")
                total_failed  += sum(1 for i in data["smt_solving_info"] if i.get("status") == "failed")

            # final urls
            if isinstance(data.get("final_transformed_urls"), list):
                total_final_urls += len(data["final_transformed_urls"])

            # resources
            if isinstance(data.get("resource_usage"), dict):
                ru = data["resource_usage"]
                for k in resource_sum:
                    resource_sum[k] += ru.get(k) or 0
                resource_count += 1

            count += 1
        except Exception as e:
            print(f"[warn] generation file {jf}: {e}")

    resource_avg = {k: (resource_sum[k] / resource_count if resource_count else None) for k in resource_sum}
    return (
        aggregated, total_sum, count, smt_solving_info_count,
        total_success, total_failed, total_final_urls, resource_avg
    )

def process_validation_json_files(json_files, expected_payload=None):
    total_exec_time = total_successful = total_removed = 0
    max_successful = max_removed = max_total = None
    contain_payload_success = contain_payload_failure = 0
    payload_exist_success = payload_exist_failure = 0
    count = 0
    resource_sum = dict.fromkeys(
        ("max_memory_MB", "cpu_user_time_sec", "cpu_system_time_sec", "wall_clock_time_sec"), 0
    )
    resource_count = 0

    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as fp:
                data = json.load(fp)

            exec_time = data.get("execution_time") or 0
            total_exec_time += exec_time

            cand = data.get("candidate_summary", {})
            counts = cand.get("counts", {})
            successful = counts.get("successful") or 0
            removed    = counts.get("removed")    or 0
            total      = successful + removed
            total_successful += successful
            total_removed    += removed
            max_successful = successful if max_successful is None else max(max_successful, successful)
            max_removed    = removed    if max_removed    is None else max(max_removed, removed)
            max_total      = total      if max_total      is None else max(max_total, total)

            succ_cands = cand.get("successful_candidates", [])

            if expected_payload is not None:
                if expected_payload in succ_cands:
                    contain_payload_success += 1
                else:
                    contain_payload_failure += 1

            if succ_cands:
                payload_exist_success += 1
            else:
                payload_exist_failure += 1

            if isinstance(data.get("resource_usage"), dict):
                ru = data["resource_usage"]
                for k in resource_sum:
                    resource_sum[k] += ru.get(k) or 0
                resource_count += 1

            count += 1
        except Exception as e:
            print(f"[warn] validation file {jf}: {e}")

    avg_exec_time = total_exec_time / count if count else 0
    avg_successful = total_successful / count if count else 0
    avg_removed    = total_removed    / count if count else 0

    cps = contain_payload_success + contain_payload_failure
    pes = payload_exist_success + payload_exist_failure
    contain_ratio = contain_payload_success / cps if cps else 0
    exist_ratio   = payload_exist_success / pes if pes else 0

    avg_resource_usage = {k: (resource_sum[k] / resource_count if resource_count else None) for k in resource_sum}

    return {
        "file_count": count,
        "avg_execution_time": avg_exec_time,
        "avg_successful": avg_successful,
        "avg_removed": avg_removed,
        "max_successful": max_successful or 0,
        "max_removed": max_removed or 0,
        "max_total": max_total or 0,
        "contain_payload_success": contain_payload_success,
        "contain_payload_failure": contain_payload_failure,
        "contain_payload_success_ratio": contain_ratio,
        "payload_exist_success": payload_exist_success,
        "payload_exist_failure": payload_exist_failure,
        "payload_exist_success_ratio": exist_ratio,
        "avg_resource_usage": avg_resource_usage,
    }

# ─────────────────────────────────────────── CLI ────────────────────────────
@click.command()
@click.option("--gen-dir", default="./case_study/generation_results", show_default=True,
              help="Root of generation_results/<project>/…")
@click.option("--val-dir", default="./case_study/validation_results", show_default=True,
              help="Root of validation_results/<project>/…")
@click.option("--output", default="./case_study/analysis_results.csv", show_default=True,
              help="CSV file path")
@click.option("--depth",  default=2, type=int, show_default=True,
              help="Tokens to keep from surrogate_model_<component1>_<component2>_…")
@click.option("--config", required=True,
              help="JSON mapping each project → expected payload string")
def cli(gen_dir: str, val_dir: str, output: str, depth: int, config: str):
    """Aggregate generation / validation metrics and write a CSV."""
    try:
        target_cfg = json.load(open(config, encoding="utf-8"))
    except Exception as e:
        raise click.ClickException(f"Cannot load config {config}: {e}")

    combined: dict[tuple[str, str], dict] = {}

    # --------------------- scan generation ----------------------------------
    # Only process projects listed in the config
    for project in target_cfg.keys():
        proj_path = os.path.join(gen_dir, project)
        if not os.path.isdir(proj_path):
            continue
        for subdir in os.listdir(proj_path):
            if not subdir.startswith("surrogate_model_"):
                continue
            model_dir = os.path.join(proj_path, subdir)
            json_files = glob.glob(os.path.join(model_dir, "*.json"))
            if not json_files:
                continue

            (agg, tot_sum, cnt,
             smt_cnt, tot_succ, tot_fail,
             tot_urls, res_avg) = process_generation_json_files(json_files)
            if not cnt:
                continue

            avg_steps = {s: agg[s]/cnt for s in agg}
            components = subdir[len("surrogate_model_"):].split("_")[:depth]

            combined.setdefault((project, subdir), {})["gen"] = {
                "components": components,
                "file_count": cnt,
                "steps": avg_steps,
                "total_avg": tot_sum / cnt,
                "smt_solving_info_count": smt_cnt,
                "avg_success": tot_succ / cnt,
                "avg_failed":  tot_fail / cnt,
                "avg_final_transformed_urls": tot_urls / cnt,
                "avg_resource_usage": res_avg,
            }

    # ---------------------- scan validation ---------------------------------
    # Again, only the projects in the config
    for project in target_cfg.keys():
        proj_path = os.path.join(val_dir, project)
        if not os.path.isdir(proj_path):
            continue
        expected_payload = target_cfg.get(project)
        for subdir in os.listdir(proj_path):
            if not subdir.startswith("surrogate_model_"):
                continue
            model_dir = os.path.join(proj_path, subdir)
            json_files = glob.glob(os.path.join(model_dir, "*.json"))
            if not json_files:
                continue
            val_data = process_validation_json_files(json_files, expected_payload)
            combined.setdefault((project, subdir), {})["val"] = val_data

    # ------------- collect dynamic step names & field lists -----------------
    all_gen_steps = sorted({s for v in combined.values() if "gen" in v for s in v["gen"]["steps"]})
    res_keys = ["max_memory_MB","cpu_user_time_sec","cpu_system_time_sec","wall_clock_time_sec"]
    gen_base_fields = ["file_count","total_avg","smt_solving_info_count","avg_success",
                       "avg_failed","avg_final_transformed_urls"]
    val_base_fields = ["file_count","avg_execution_time","avg_successful","avg_removed",
                       "max_successful","max_removed","max_total",
                       "contain_payload_success","contain_payload_failure",
                       "contain_payload_success_ratio",
                       "payload_exist_success","payload_exist_failure",
                       "payload_exist_success_ratio"]
    comb_res_keys = ["cpu_user_time_sec","cpu_system_time_sec","wall_clock_time_sec"]

    comp_cols = [f"gen_component{i}" for i in range(1, depth+1)]
    header = ["project","surrogate","target_payload"] + comp_cols
    header += [f"gen_{f}" for f in gen_base_fields + all_gen_steps + res_keys]
    header += [f"val_{f}" for f in val_base_fields + res_keys]
    header += ["total_avg_combined"] + [f"combined_{k}" for k in comb_res_keys]

    # ----------------------------- CSV write --------------------------------
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", newline="", encoding="utf-8") as csvf:
        w = csv.DictWriter(csvf, fieldnames=header)
        w.writeheader()

        for (project, surrogate), data in combined.items():
            row = {
                "project": project,
                "surrogate": surrogate,
                "target_payload": target_cfg.get(project, "")
            }

            gen = data.get("gen")
            if gen:
                for idx, c in enumerate(gen["components"], 1):
                    row[f"gen_component{idx}"] = c
                for f in gen_base_fields:
                    row[f"gen_{f}"] = gen.get(f, "")
                for step in all_gen_steps:
                    row[f"gen_{step}"] = gen["steps"].get(step, "")
                for rk in res_keys:
                    row[f"gen_{rk}"] = gen["avg_resource_usage"].get(rk, "")
            else:
                for col in comp_cols + [f"gen_{f}" for f in gen_base_fields + all_gen_steps + res_keys]:
                    row[col] = ""

            val = data.get("val")
            if val:
                for f in val_base_fields:
                    row[f"val_{f}"] = val.get(f, "")
                for rk in res_keys:
                    row[f"val_{rk}"] = val["avg_resource_usage"].get(rk, "")
            else:
                for col in [f"val_{f}" for f in val_base_fields + res_keys]:
                    row[col] = ""

            # combined timings / CPU
            gen_tot = (gen or {}).get("total_avg") or 0
            val_time = (val or {}).get("avg_execution_time") or 0
            row["total_avg_combined"] = gen_tot + val_time
            for k in comb_res_keys:
                g = ((gen or {}).get("avg_resource_usage", {}).get(k)) or 0
                v = ((val or {}).get("avg_resource_usage", {}).get(k)) or 0
                row[f"combined_{k}"] = g + v

            w.writerow(row)

    click.echo(f"CSV report written to {output}")

# entry-point
if __name__ == "__main__":
    cli()
import os
import json
import csv

RESULTS_DIR = "results"
CSV_OUTPUT = "benchmark_results.csv"


def collect_json_files(results_dir):
    for root, _, files in os.walk(results_dir):
        for fname in files:
            if fname.endswith(".json"):
                yield os.path.join(root, fname)


def flatten_result(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    rows = []
    for resp in data.get("responses", []):
        row = {
            "model": data.get("model"),
            "timestamp": data.get("timestamp"),
            "run_index": data.get("run_index"),
            "system_platform": data.get("system_metadata", {}).get("platform"),
            "system_release": data.get("system_metadata", {}).get("platform_release"),
            "system_machine": data.get("system_metadata", {}).get("machine"),
            "system_processor": data.get("system_metadata", {}).get("processor"),
            "python_version": data.get("system_metadata", {}).get("python_version"),
            "ollama_version": data.get("system_metadata", {}).get("ollama_version"),
            "category": resp.get("category"),
            "question": resp.get("question"),
            "response": resp.get("response"),
            "score": resp.get("score"),
            "score_reason": resp.get("score_reason"),
            "total_score": data.get("total_score"),
            "inference_threads": data.get("inference_params", {}).get("threads"),
            "run_wall_time_sec": data.get("resource_usage", {}).get("wall_time_sec"),
            "run_peak_ram_mb": data.get("resource_usage", {}).get("peak_ram_mb"),
            "run_avg_cpu_percent": data.get("resource_usage", {}).get("avg_cpu_percent"),
            "response_peak_ram_mb": resp.get("resource_usage", {}).get("peak_ram_mb"),
            "response_avg_cpu_percent": resp.get("resource_usage", {}).get("avg_cpu_percent")
        }
        rows.append(row)
    return rows


def main():
    all_rows = []
    for json_path in collect_json_files(RESULTS_DIR):
        all_rows.extend(flatten_result(json_path))
    if not all_rows:
        print("No results found.")
        return
    fieldnames = list(all_rows[0].keys())
    with open(CSV_OUTPUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Exported {len(all_rows)} rows to {CSV_OUTPUT}")


if __name__ == "__main__":
    main()

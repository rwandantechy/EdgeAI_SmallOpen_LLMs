

import os
import json
import subprocess
import time
from datetime import datetime
import platform
import psutil
import argparse
import threading
import shutil
import re
from typing import Tuple

# Constants
BENCHMARK_DATA = "benchmark_data/questions.json"
RESULTS_DIR = "results"
OLLAMA_MODELS = [
    "deepseek-r1:1.5b",
    "llama3.2:1b",
    "gemma2:2b",
    "phi3:3.8b"
]
INFERENCE_PARAMS = {
    "temperature": 0,
    "top_p": 1.0,
    "max_tokens": 256,
    "seed": 42,
    "threads": 1
}

def load_questions():
    with open(BENCHMARK_DATA, "r") as f:
        return json.load(f)


def prepare_output_dir(model_name: str) -> Tuple[str, str]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_root = os.path.join(RESULTS_DIR, model_name)
    os.makedirs(model_root, exist_ok=True)
    timestamp_dir = os.path.join(model_root, timestamp)
    os.makedirs(timestamp_dir, exist_ok=True)
    return timestamp_dir, timestamp


def purge_results_dir(model_name: str) -> None:
    model_root = os.path.join(RESULTS_DIR, model_name)
    if os.path.isdir(model_root):
        try:
            print(f"Removing existing results at {model_root}...")
            shutil.rmtree(model_root)
        except Exception as exc:
            print(f"Warning: could not remove {model_root}: {exc}")
    else:
        print(f"No previous results found at {model_root}.")

def clean_ollama_blobs():
    subprocess.run(["ollama", "rm", "--all"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def restart_ollama():
    subprocess.run(["ollama", "serve", "--restart"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)  # Give time for restart

def get_ollama_version() -> str:
    try:
        proc = subprocess.run(["ollama", "--version"], capture_output=True, check=False, text=True, timeout=5)
        raw_output = (proc.stdout or proc.stderr).strip()
        if not raw_output:
            return "unknown"
        last_line = raw_output.splitlines()[-1]
        match = re.search(r"\d+\.\d+\.\d+", last_line)
        if match:
            return match.group(0)
        tokens = last_line.split()
        for token in tokens:
            if any(ch.isdigit() for ch in token):
                return token
        return "unknown"
    except Exception:
        return "unavailable"


def get_system_metadata():
    cpu_freq = psutil.cpu_freq()
    release = platform.release() or None
    release_major = release.split(".")[0] if release and "." in release else release
    python_version = platform.python_version() or None
    python_major_minor = ".".join(python_version.split(".")[:2]) if python_version else None

    def sanitize(value, default="unknown"):
        if value is None:
            return default
        if isinstance(value, str) and not value.strip():
            return default
        return value

    def partial_value(raw: str, keep: int = 12) -> str:
        if not raw:
            return ""
        trimmed = raw.strip()
        if not trimmed:
            return ""
        if len(trimmed) <= keep:
            return trimmed
        return f"{trimmed[:keep]}…"

    raw_processor = platform.processor()
    if not raw_processor or not raw_processor.strip():
        raw_processor = platform.uname().processor
    if not raw_processor or not raw_processor.strip():
        raw_processor = platform.machine()

    return {
        "platform": platform.system(),
        "platform_release": sanitize(release_major),
        "platform_version": sanitize(partial_value(platform.version(), 16)),
        "machine": sanitize(platform.machine()),
        "processor": sanitize(partial_value(raw_processor, 16)),
        "python_version": sanitize(python_major_minor),
        "ollama_version": get_ollama_version(),
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_physical": psutil.cpu_count(logical=False),
        "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "cpu_freq_mhz": cpu_freq.current if cpu_freq else 0,
        "cpu_percent": psutil.cpu_percent(interval=1),
        "threading_info": {
            "num_threads": len(psutil.Process().threads())
        }
    }


def parse_version_tuple(version: str) -> Tuple[int, int, int] | None:
    if not version or version in {"unknown", "unavailable"}:
        return None
    try:
        parts = version.split(".")
        numbers = []
        for part in parts[:3]:
            digits = ''.join(ch for ch in part if ch.isdigit())
            if digits:
                numbers.append(int(digits))
        while len(numbers) < 3:
            numbers.append(0)
        return tuple(numbers[:3])
    except Exception:
        return None


def cli_supports_options(version: Tuple[int, int, int] | None) -> bool:
    if version is None:
        return True
    return version >= (0, 16, 0)


def build_cli_options(params: dict) -> list[str]:
    return [
        "--temperature", str(params["temperature"]),
        "--top-p", str(params["top_p"]),
        "--seed", str(params["seed"]),
        "--num-predict", str(params["max_tokens"]),
        "--threads", str(params["threads"])
    ]


def score_response(q, response):
    # Logical Reasoning & Deductive Reasoning: exact match (case-insensitive, strip)
    if q["category"] in ["Logical Reasoning", "Deductive Reasoning"]:
        corrects = [a.lower().strip() for a in q.get("answer", [])]
        if response.lower().strip() in corrects:
            return q["scoring"]["correct"], "correct"
        else:
            return q["scoring"]["incorrect"], "incorrect"
    # Knowledge Comparison: must contain a key phrase
    elif q["category"] == "Knowledge Comparison":
        for ans in q.get("acceptable_answers", []):
            for phrase in ans.lower().split("/"):
                if phrase.strip() in response.lower():
                    return q["scoring"]["correct"], "correct"
        return q["scoring"]["incorrect"], "incorrect"
    # Summarization: check for required ideas
    elif q["category"].startswith("Text Understanding"):
        ideas = q.get("required_ideas", [])
        found = 0
        resp = response.lower()
        if "solar" in resp and "panel" in resp and "electric" in resp:
            found += 1
        if "renewable" in resp or "reduce" in resp or "pollution" in resp:
            found += 1
        if "weather" in resp or "cost" in resp:
            found += 1
        if found == 3:
            return q["scoring"]["all_key_ideas"], "all_key_ideas"
        elif found >= 2:
            return q["scoring"]["partial"], "partial"
        else:
            return q["scoring"]["incorrect"], "incorrect"
    return 0, "ungraded"


def monitor_resources(proc, stats):
    p = psutil.Process(proc.pid)
    peak_mem = 0
    cpu_samples = []
    while proc.poll() is None:
        try:
            mem = p.memory_info().rss / (1024 ** 2)  # MB
            peak_mem = max(peak_mem, mem)
            cpu = p.cpu_percent(interval=0.1)
            cpu_samples.append(cpu)
        except Exception:
            break
    stats["peak_ram_mb"] = peak_mem
    stats["avg_cpu_percent"] = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0

def run_model(model: str, questions: list, timestamp_dir: str, timestamp: str, run_idx: int = 1):
    clean_ollama_blobs()
    restart_ollama()
    os.environ["OLLAMA_NUM_PARALLEL"] = "1"

    results = {
        "model": model,
        "timestamp": datetime.now().isoformat(),
        "run_index": run_idx,
        "system_metadata": get_system_metadata(),
        "inference_params": INFERENCE_PARAMS,
        "responses": [],
        "scores": [],
        "total_score": 0,
        "resource_usage": {},
        "run_status": "in_progress"
    }

    start_time = time.time()
    run_peak_ram = 0.0
    run_cpu_samples = []
    version_tuple = parse_version_tuple(results["system_metadata"].get("ollama_version"))
    use_cli_options = cli_supports_options(version_tuple)
    results.setdefault("metadata", {})["cli_options_supported"] = use_cli_options

    for q in questions:
        prompt = q["question"]
        attempt = 0
        while True:
            attempt += 1
            attempt_used_cli = use_cli_options and attempt == 1
            ollama_cmd = ["ollama", "run", model]
            if attempt_used_cli:
                ollama_cmd.extend(build_cli_options(INFERENCE_PARAMS))
            try:
                proc = subprocess.Popen(
                    ollama_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stats = {}
                monitor_thread = threading.Thread(target=monitor_resources, args=(proc, stats))
                monitor_thread.start()
                out, err = proc.communicate(input=prompt.encode(), timeout=180)
                monitor_thread.join()
                response = out.decode(errors="replace").strip()
                if proc.returncode != 0:
                    error_text = err.decode(errors="replace").strip() or response or "ollama run exited with a non-zero status"
                    if "unknown flag" in error_text.lower() and attempt_used_cli:
                        use_cli_options = False
                        results["metadata"]["cli_options_supported"] = False
                        if attempt < 2:
                            continue
                    response = f"ERROR: {error_text}"
            except Exception as e:
                response = f"ERROR: {e}"
                stats = {"peak_ram_mb": None, "avg_cpu_percent": None}
            break
        if stats.get("peak_ram_mb"):
            run_peak_ram = max(run_peak_ram, stats["peak_ram_mb"])
        if stats.get("avg_cpu_percent") is not None:
            run_cpu_samples.append(stats["avg_cpu_percent"])
        score, reason = score_response(q, response)
        if response.startswith("ERROR:"):
            reason = "error"
            score = 0
        results["responses"].append({
            "category": q["category"],
            "question": prompt,
            "response": response,
            "score": score,
            "score_reason": reason,
            "resource_usage": stats
        })
        results["scores"].append(score)
    results["total_score"] = sum(results["scores"])
    run_avg_cpu = sum(run_cpu_samples) / len(run_cpu_samples) if run_cpu_samples else 0
    results["resource_usage"].update({
        "wall_time_sec": round(time.time() - start_time, 2),
        "peak_ram_mb": round(run_peak_ram, 2) if run_peak_ram else None,
        "avg_cpu_percent": round(run_avg_cpu, 2)
    })
    if any(resp["response"].startswith("ERROR:") for resp in results["responses"]):
        results["run_status"] = "error"
    else:
        results["run_status"] = "completed"

    out_path = os.path.join(timestamp_dir, f"run_{run_idx:02d}.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results for {model} run {run_idx} to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark LLMs on edge devices.")
    parser.add_argument("--model", type=str, default=None, help="Model to run (default: all)")
    parser.add_argument("--purge-results", action="store_true", help="Remove existing results/<model> directory before running")
    args = parser.parse_args()

    questions = load_questions()["questions"]
    models = [args.model] if args.model else OLLAMA_MODELS
    if args.purge_results:
        for model in models:
            purge_results_dir(model)
    for model in models:
        timestamp_dir, timestamp = prepare_output_dir(model)
        run_model(model, questions, timestamp_dir, timestamp, 1)

if __name__ == "__main__":
    main()

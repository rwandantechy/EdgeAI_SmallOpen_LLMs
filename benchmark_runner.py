
import os
import json
import subprocess
import time
from datetime import datetime
import platform
import psutil

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
    "seed": 42
}

def load_questions():
    with open(BENCHMARK_DATA, "r") as f:
        return json.load(f)

def prepare_output_dir(model_name: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(RESULTS_DIR, model_name)
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, f"{timestamp}.json")

def clean_ollama_blobs():
    subprocess.run(["ollama", "rm", "--all"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def restart_ollama():
    subprocess.run(["ollama", "serve", "--restart"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)  # Give time for restart

def get_system_metadata():
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_physical": psutil.cpu_count(logical=False),
        "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
        "cpu_percent": psutil.cpu_percent(interval=1),
        "threading_info": {
            "num_threads": len(psutil.Process().threads())
        }
    }

def run_model(model: str, questions: list, output_path: str):
    # Clean blobs and restart Ollama for determinism
    clean_ollama_blobs()
    restart_ollama()
    os.environ["OLLAMA_NUM_PARALLEL"] = "1"

    results = {
        "model": model,
        "timestamp": datetime.now().isoformat(),
        "system_metadata": get_system_metadata(),
        "inference_params": INFERENCE_PARAMS,
        "responses": []
    }

    for q in questions:
        prompt = q["question"]
        # Run Ollama model with fixed params
        ollama_cmd = [
            "ollama", "run", model,
            "--temperature", str(INFERENCE_PARAMS["temperature"]),
            "--top-p", str(INFERENCE_PARAMS["top_p"]),
            "--seed", str(INFERENCE_PARAMS["seed"]),
            "--num-predict", str(INFERENCE_PARAMS["max_tokens"])
        ]
        try:
            proc = subprocess.run(
                ollama_cmd,
                input=prompt.encode(),
                capture_output=True,
                timeout=120
            )
            response = proc.stdout.decode(errors="replace").strip()
        except Exception as e:
            response = f"ERROR: {e}"
        results["responses"].append({
            "category": q["category"],
            "question": prompt,
            "response": response
        })

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results for {model} to {output_path}")

def main():
    questions = load_questions()["questions"]
    for model in OLLAMA_MODELS:
        output_path = prepare_output_dir(model)
        run_model(model, questions, output_path)

if __name__ == "__main__":
    main()

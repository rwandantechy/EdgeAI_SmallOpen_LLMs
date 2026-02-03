import os
import json
from datetime import datetime

# Constants
BENCHMARK_DATA = "benchmark_data/questions.json"
RESULTS_DIR = "results"


def load_questions():
    with open(BENCHMARK_DATA, "r") as f:
        return json.load(f)


def prepare_output_dir(model_name: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(RESULTS_DIR, model_name)
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, f"{timestamp}.json")


def main():
    # Example usage: load questions and prepare output path for a model
    questions = load_questions()
    print(f"Loaded {len(questions['questions'])} benchmark questions.")
    # Example: prepare output file for a model (placeholder name)
    output_path = prepare_output_dir("MODEL_NAME_PLACEHOLDER")
    print(f"Results will be saved to: {output_path}")


if __name__ == "__main__":
    main()

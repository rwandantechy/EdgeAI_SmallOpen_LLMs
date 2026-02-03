import os
import json
import matplotlib.pyplot as plt

RESULTS_DIR = "results"
IMG_OUTPUT = os.path.join(RESULTS_DIR, "benchmark_scores.png")


def collect_total_scores(results_dir):
    scores = {}
    for model_dir in os.listdir(results_dir):
        model_path = os.path.join(results_dir, model_dir)
        if os.path.isdir(model_path):
            for fname in os.listdir(model_path):
                if fname.endswith(".json"):
                    with open(os.path.join(model_path, fname), "r") as f:
                        data = json.load(f)
                        model = data.get("model")
                        score = data.get("total_score")
                        if model and score is not None:
                            scores.setdefault(model, []).append(score)
    # Use average if multiple runs per model
    avg_scores = {m: sum(v)/len(v) for m, v in scores.items()}
    return avg_scores


def plot_scores(scores, output_path):
    models = list(scores.keys())
    values = [scores[m] for m in models]
    plt.figure(figsize=(8, 5))
    bars = plt.bar(models, values, color="skyblue")
    plt.ylabel("Total Score")
    plt.title("LLM Benchmark Scores (Higher is Better)")
    plt.ylim(0, 5)
    plt.grid(axis="y", linestyle=":", alpha=0.5)
    for bar, value in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, f"{value:.2f}", ha="center", va="bottom")
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Saved bar chart to {output_path}")


def main():
    scores = collect_total_scores(RESULTS_DIR)
    if not scores:
        print("No scores found.")
        return
    plot_scores(scores, IMG_OUTPUT)


if __name__ == "__main__":
    main()

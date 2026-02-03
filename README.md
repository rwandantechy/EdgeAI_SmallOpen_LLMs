# EdgeAI Small Open LLMs Benchmark

This project is a friendly, reproducible home for testing small open-source LLMs on edge hardware. Every run is scripted so teammates (or reviewers) can see exactly what happened, compare notes, and feel confident repeating the experiment on their own machines.

## What’s included
- A ready-to-run suite covering deepseek-r1:1.5b, llama3.2:1b, gemma2:2b, phi3:3.8b (feel free to extend the list)
- Deterministic inference settings baked in (temperature=0, top_p=1.0, max_tokens=256, fixed seed)
- Automatic cache clears and Ollama restarts so tests start fresh
- Single-thread runs to keep CPU usage consistent across devices
- Auto-grading with clear scoring plus light-weight system metadata for context
- Export and plotting scripts so you can move smoothly from raw JSON to spreadsheets or visuals

## Folder Structure
```
EdgeAI_SmallOpen_LLMs/
├── benchmark_data/questions.json         # Benchmark questions and scoring rules
├── benchmark_runner.py                  # Main benchmarking script
├── export_results_csv.py                # Export all results to CSV
├── plot_benchmark_scores.py             # Visualize model scores
├── requirements.txt                     # Python dependencies
├── results/                             # Model outputs and plots
│   └── <model_name>/
│       └── <timestamp>/                 # One benchmark session
│           ├── run_01.json              # Individual run (status, scores, resources)
│           └── run_02.json              # Additional runs share same timestamp
└── README.md                            # Project documentation
```

## Quick start
1. **Set up the Python environment**
   ```sh
   pip install -r requirements.txt
   ```
   - Installs psutil, matplotlib, and any other helper libraries the scripts expect.
2. **Pull the models you plan to test (one time per model)**
   ```sh
   ollama pull llama3.2:1b
   ```
   - Repeat with deepseek-r1:1.5b, gemma2:2b, phi3:3.8b, or any other identifiers you want in the mix.
3. **Run a basic benchmark pass**
   ```sh
   python benchmark_runner.py
   ```
   - Add `--model llama3.2:1b` to focus on that model only.
   - Add `--runs 5` when you want repeated passes to average results manually.
   - Add `--purge-results` if you want to delete the existing `results/llama3.2:1b` folder before this run.
   - Each run saves to `results/<model>/<timestamp>/run_<index>.json` with scores, metadata, and resource stats.
4. **Automate a reproducible cold start (optional)**
   ```sh
   python scripts/full_repro_benchmark.py --model llama3.2:1b --runs 3 --output llama_runs.log
   ```
   - Stops Ollama, clears its caches, enforces single-thread inference, and then calls `benchmark_runner.py`.
   - Use `--no-cache-clear` to skip wiping caches or `--purge-results` to remove earlier outputs for that model.
   - The helper stores JSON results in the same `results/<model>/<timestamp>/run_<index>.json` structure and tees stdout into the optional log.
5. **Export cumulative results to a spreadsheet-friendly format**
   ```sh
   python export_results_csv.py
   ```
   - Produces `results/benchmark_results.csv` with one row per run plus metadata columns.
6. **Generate a quick scoreboard plot**
   ```sh
   python plot_benchmark_scores.py
   ```
   - Reads every JSON result, averages total scores per model, and writes `results/benchmark_scores.png`.
7. **Clean up before a new experiment (optional)**
   ```sh
   rm -rf results/<model>
   ```
   - Handy if you want to archive old results elsewhere and start fresh without touching the scripts.

### Quick reproducibility helper
- When you want a fresh, cold-cache run without thinking about the prep steps, use the helper:
   ```sh
   python scripts/full_repro_benchmark.py --model llama3.2:1b --runs 3 --output llama_runs.log
   ```
   The script stops Ollama, clears cached weights, enforces single-thread inference, and nudges you to close heavy apps before running `benchmark_runner.py`. Prefer to keep the cache? Pass `--no-cache-clear`. Want a clean slate for that model’s outputs? Add `--purge-results` to clear `results/<model>` before the run, or delete the folder manually afterward. Drop the `--runs` flag if you’re happy with the default single pass, or set it to any number when you want repeats—there’s no automatic counter under the hood. The helper works the same on macOS and Raspberry Pi OS as long as Ollama and Python are installed.
   The helper writes each run to `results/<model>/<timestamp>/run_<index>.json` and streams a copy of stdout to the optional log file so you can revisit the transcript later.

Every `run_<index>.json` includes a short snapshot of the host (OS, machine type, processor string, Python version, Ollama version, CPU and RAM capacity) so collaborators can see where the run happened without revealing anything sensitive.

## Requirements
- Python 3.8+
- Ollama installed and models pulled (see https://ollama.com/)
- macOS or Linux recommended

## Contributing
- Keep the code modular, readable, and kind to the next person who opens it
- Suggest new tasks, models, or visualizations through issues or PRs
- Stick to objective, reproducible methods so results stay comparable across machines

## License
MIT

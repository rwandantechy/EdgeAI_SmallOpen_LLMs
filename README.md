# EdgeAI Small Open LLMs Benchmark

This project is a friendly, reproducible home for testing small open-source LLMs on edge hardware. Every run is scripted so teammates (or reviewers) can see exactly what happened, compare notes, and feel confident repeating the experiment on their own machines.

## What’s included
- A ready-to-run suite covering deepseek-r1:1.5b, llama3.2:1b, gemma2:2b, phi3:3.8b (feel free to extend the list)
- Deterministic inference settings baked in (temperature=0, top_p=1.0, max_tokens=256, fixed seed)
- Automatic cache clears and Ollama restarts so tests start fresh
- Single-thread runs to keep CPU usage consistent across devices
- Auto-grading with clear scoring plus light-weight system metadata for context
- Export and plotting scripts so you can move smoothly from raw JSON to spreadsheets or visuals

### Model snapshots
- deepseek-r1:1.5b — 1.5B-parameter reasoning model tuned for concise step-by-step answers on modest hardware.
- llama3.2:1b — Meta’s 1B-parameter general model optimized for low-latency edge inference with balanced quality.
- gemma2:2b — Google’s 2B successor to Gemma with stronger multilingual coverage and stable generation at small scale.
- phi3:3.8b — Microsoft’s 3.8B compact transformer focused on code and reasoning tasks while staying edge-friendly.

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
1. **Install the tools**
   ```sh
   pip install -r requirements.txt
   ```
   Installs everything the scripts need (psutil, matplotlib, etc.).
2. **Grab at least one model**
   ```sh
   ollama pull llama3.2:1b
   ```
   Repeat for deepseek-r1:1.5b, gemma2:2b, phi3:3.8b, or any other Ollama model you want to test.
3. **Run the benchmark**
   ```sh
   python benchmark_runner.py --model llama3.2:1b
   ```
   Results land under `results/llama3.2:1b/<timestamp>/run_01.json` with scores, responses, and system metadata. Rerun the command as many times as you like—each pass creates a new timestamped folder.
4. **Look at the outputs**
   - Open the JSON from step 3 to inspect a single run.
   - `python export_results_csv.py` collects every run into `results/benchmark_results.csv`.
   - `python plot_benchmark_scores.py` creates `results/benchmark_scores.png` for a quick comparison chart.

### Helpful extras (optional)
- Reproducible cold start and log capture:
  ```sh
   python scripts/full_repro_benchmark.py --model llama3.2:1b --output run.log
  ```
   Stops Ollama, clears caches, enforces single-thread inference, and writes outputs to the same results folder.
- Fresh slate before a rerun:
  ```sh
  python benchmark_runner.py --model llama3.2:1b --purge-results
  ```
  Removes the existing `results/llama3.2:1b` directory before writing new data.

### Quick reproducibility helper
- When you want a fresh, cold-cache run without thinking about the prep steps, use the helper:
   ```sh
   python scripts/full_repro_benchmark.py --model llama3.2:1b --output llama_runs.log
   ```
   The script stops Ollama, clears cached weights, enforces single-thread inference, and then runs `benchmark_runner.py` for you. Prefer to keep the cache? Pass `--no-cache-clear`. Want a clean slate for that model’s outputs? Add `--purge-results` to clear `results/<model>` before the run, or delete the folder manually afterward. Re-run the helper whenever you need another pass. The helper works the same on macOS and Raspberry Pi OS as long as Ollama and Python are installed.
   Each invocation writes outputs to `results/<model>/<timestamp>/run_<index>.json` and streams a copy of stdout to the optional log file so you can revisit the transcript later.

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

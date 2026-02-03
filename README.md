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
1. **Install the Python bits**
   ```sh
   pip install -r requirements.txt
   ```
2. **Kick off a full benchmark run**
   ```sh
   python benchmark_runner.py
   ```
   - Add `--model llama3.2:1b` to focus on a single model
   - Add `--runs 5` to repeat the run and capture resource stats for each pass
   - You’ll find the results at `results/<model>/<timestamp>/run_<index>.json`, each tagged with `run_status: completed`
3. **Export everything to CSV**
   ```sh
   python export_results_csv.py
   ```
4. **Plot the scores for a quick glance**
   ```sh
   python plot_benchmark_scores.py
   ```

### Quick reproducibility helper
- When you want a fresh, cold-cache run without thinking about the prep steps, use the helper:
   ```sh
   python scripts/full_repro_benchmark.py --model llama3.2:1b --runs 3 --output llama_runs.log
   ```
   The script stops Ollama, clears cached weights, enforces single-thread inference, and nudges you to close heavy apps before running `benchmark_runner.py`. Prefer to keep the cache? Pass `--no-cache-clear`. The helper works the same on macOS and Raspberry Pi OS as long as Ollama and Python are installed.

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

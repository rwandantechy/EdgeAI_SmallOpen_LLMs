# EdgeAI Small Open LLMs Benchmark

A standardized, reproducible benchmarking framework for evaluating small, open-source LLMs on edge-capable devices. The framework measures performance, accuracy, and resource usage in a transparent, interpretable, and peer-review-friendly way.

## Features
- Runs multiple LLMs (e.g., deepseek-r1:1.5b, llama3.2:1b, gemma2:2b, phi3:3.8b) on objective, standardized questions
- Enforces deterministic inference (temperature=0, top_p=1.0, max_tokens=256, fixed seed)
- Cleans model blobs and restarts Ollama for each run
- Controls CPU concurrency for reproducibility
- Auto-grades responses and saves results with system metadata
- Exports results to CSV and visualizes scores with matplotlib

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

## Quick Start
1. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
2. **Run the benchmark**
   ```sh
   python benchmark_runner.py
   ```
   - Use `--model llama3.2:1b` to benchmark a single model
   - Use `--runs 5` to repeat the same model run multiple times (resource usage tracked per run)
   - Each run is saved under `results/<model>/<timestamp>/run_<index>.json` with a `run_status` flag set to `completed`
3. **Export results to CSV**
   ```sh
   python export_results_csv.py
   ```
4. **Visualize scores**
   ```sh
   python plot_benchmark_scores.py
   ```

### Fully reproducible run helper
- Use the helper script to automate cold-cache preparation and run a benchmark in one step:
   ```sh
   ./scripts/full_repro_benchmark.sh --model llama3.2:1b --runs 3 --output llama_runs.log
   ```
   This stops Ollama, clears cached models/blobs, enforces single-thread inference, reminds you to close heavy background apps, and then calls `benchmark_runner.py`.

## Requirements
- Python 3.8+
- Ollama installed and models pulled (see https://ollama.com/)
- macOS or Linux recommended

## Contribution
- Keep code modular, readable, and well-documented
- Submit PRs for new features or improvements
- Use objective, reproducible methods for all benchmarks

## License
MIT

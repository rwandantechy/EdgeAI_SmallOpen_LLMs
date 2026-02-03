#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/full_repro_benchmark.sh --model <name> [--runs N] [--output file]

Prepares a cold-cache, single-threaded environment and runs benchmark_runner.py
for the specified model. Requires Ollama and Python dependencies to be installed.

Options:
  --model <name>      Ollama model identifier (e.g., llama3.2:1b). Required.
  --runs <N>          Number of repeated runs (default: 1).
  --output <file>     Tee benchmark_runner output to <file> for later review.
  --help              Show this help and exit.
EOF
}

MODEL=""
RUNS=1
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="${2:-}"
      shift 2
      ;;
    --runs)
      RUNS="${2:-1}"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="${2:-}"
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$MODEL" ]]; then
  echo "Error: --model is required." >&2
  usage
  exit 1
fi

if ! [[ "$RUNS" =~ ^[0-9]+$ ]]; then
  echo "Error: --runs must be a positive integer." >&2
  exit 1
fi

if ! command -v ollama >/dev/null 2>&1; then
  echo "Error: ollama command not found. Install Ollama first." >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "Stopping any running Ollama server..."
pkill -f "ollama serve" >/dev/null 2>&1 || true

OLLAMA_DIR="${OLLAMA_HOME:-$HOME/.ollama}"
MODELS_DIR="$OLLAMA_DIR/models"
BLOBS_DIR="$OLLAMA_DIR/blobs"

if [[ -d "$MODELS_DIR" ]]; then
  echo "Clearing Ollama models cache ($MODELS_DIR)..."
  rm -rf "$MODELS_DIR"/*
fi

if [[ -d "$BLOBS_DIR" ]]; then
  echo "Clearing Ollama blobs cache ($BLOBS_DIR)..."
  rm -rf "$BLOBS_DIR"/*
fi

export OLLAMA_NUM_PARALLEL=1

echo "OLLAMA_NUM_PARALLEL set to $OLLAMA_NUM_PARALLEL"

echo "Active user processes (non-system) for review:"
ps -u "$(whoami)" -o pid,%cpu,%mem,comm | grep -vE '^ *PID|/System/Library|/usr/libexec|/usr/sbin'

echo
echo "Reminder: manually close heavy background apps (Docker, browsers, etc.) for cleaner measurements."
echo

echo
PYTHON_BIN="${PYTHON_BIN:-$(command -v python)}"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "Error: python executable not found." >&2
  exit 1
fi

CMD=("$PYTHON_BIN" benchmark_runner.py --model "$MODEL" --runs "$RUNS")

echo "Running benchmark_runner with model=$MODEL runs=$RUNS"
if [[ -n "$OUTPUT_FILE" ]]; then
  echo "Output will be tee'd to $OUTPUT_FILE"
  "${CMD[@]}" | tee "$OUTPUT_FILE"
else
  "${CMD[@]}"
fi

echo "Benchmark completed for $MODEL. Results stored under results/$MODEL/<timestamp>/"

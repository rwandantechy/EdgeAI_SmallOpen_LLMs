#!/usr/bin/env python3
"""Automate reproducible benchmark runs across macOS and Linux edge devices."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from getpass import getuser
from pathlib import Path
from typing import Iterable, Optional
import shutil

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OLLAMA_HOME = Path(os.environ.get("OLLAMA_HOME", Path.home() / ".ollama"))


def run_command(command: Iterable[str], *, check: bool = False, capture_output: bool = False, text: bool = True, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    """Run a subprocess with sensible defaults for this automation."""
    return subprocess.run(
        list(command),
        check=check,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
    )


def stop_ollama() -> None:
    """Stop any existing Ollama server; ignore failures."""
    pkill = shutil.which("pkill")
    if pkill:
        print("Stopping any running Ollama server...")
        run_command([pkill, "-f", "ollama serve"], check=False, capture_output=True)
    else:
        print("pkill not available; ensure Ollama server is stopped manually if running.")


def clear_cache() -> None:
    """Clear Ollama model and blob caches for a cold start."""
    models_dir = DEFAULT_OLLAMA_HOME / "models"
    blobs_dir = DEFAULT_OLLAMA_HOME / "blobs"
    for path in (models_dir, blobs_dir):
        if path.exists():
            print(f"Clearing Ollama cache at {path}...")
            for child in path.iterdir():
                if child.is_dir():
                    try:
                        shutil.rmtree(child)
                    except Exception as exc:
                        print(f"  Warning: could not remove {child}: {exc}")
                else:
                    try:
                        child.unlink(missing_ok=True)
                    except Exception as exc:
                        print(f"  Warning: could not remove {child}: {exc}")


def purge_previous_results(model: str) -> None:
    """Optionally remove prior benchmark outputs for the selected model."""
    target_dir = REPO_ROOT / "results" / model
    if target_dir.exists():
        try:
            print(f"Removing existing results at {target_dir}...")
            shutil.rmtree(target_dir)
        except Exception as exc:
            print(f"  Warning: could not purge {target_dir}: {exc}")
    else:
        print(f"No previous results found at {target_dir}.")


def show_user_processes() -> None:
    """Display user processes minus obvious system daemons to help manual cleanup."""
    try:
        result = run_command(
            [
                "ps",
                "-u",
                getuser(),
                "-o",
                "pid,%cpu,%mem,comm",
            ],
            capture_output=True,
        )
        lines = result.stdout.strip().splitlines()
        filtered = [lines[0]] if lines else []
        for line in lines[1:]:
            command = line.split(maxsplit=3)[-1] if line.split(maxsplit=3) else ""
            if not (command.startswith("/System/Library") or command.startswith("/usr/libexec") or command.startswith("/usr/sbin")):
                filtered.append(line)
        if filtered:
            print("Active user processes (non-system) for review:")
            for line in filtered:
                print(line)
    except Exception as exc:  # pragma: no cover - purely informative
        print(f"Could not list processes: {exc}")


def ensure_python_interpreter(env_value: Optional[str]) -> str:
    """Resolve the Python interpreter to use for benchmark_runner."""
    if env_value:
        return env_value
    for candidate in ("python3", "python"):
        path = shutil.which(candidate)
        if path:
            return path
    raise RuntimeError("python3 or python executable not found on PATH")


def run_benchmark(model: str, runs: int, python_bin: str, output_file: Optional[Path]) -> None:
    """Invoke benchmark_runner with optional tee to a log file."""
    cmd = [python_bin, "benchmark_runner.py", "--model", model, "--runs", str(runs)]
    print(f"Running benchmark_runner with model={model} runs={runs}")
    process = subprocess.Popen(
        cmd,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
    log_handle = output_file.open("w", encoding="utf-8") if output_file else None
    assert process.stdout is not None
    try:
        for line in process.stdout:
            print(line, end="")
            if log_handle:
                log_handle.write(line)
        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, cmd)
    finally:
        if log_handle:
            log_handle.flush()
            log_handle.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare and run reproducible LLM benchmarks")
    parser.add_argument("--model", required=True, help="Ollama model identifier (e.g., llama3.2:1b)")
    parser.add_argument("--runs", type=int, default=1, help="Number of repeated runs (default: 1)")
    parser.add_argument("--output", type=Path, default=None, help="Optional log file to capture runner output")
    parser.add_argument("--no-cache-clear", action="store_true", help="Skip clearing Ollama caches (not reproducible)")
    parser.add_argument("--purge-results", action="store_true", help="Remove existing results/<model> directory before running")
    args = parser.parse_args()

    if args.runs < 1:
        parser.error("--runs must be at least 1")

    python_bin = os.environ.get("PYTHON_BIN")
    try:
        import shutil  # local import to avoid module-level dependency

        python_bin = ensure_python_interpreter(python_bin)
    except RuntimeError as exc:
        parser.error(str(exc))

    os.environ["OLLAMA_NUM_PARALLEL"] = "1"
    print(f"OLLAMA_NUM_PARALLEL set to {os.environ['OLLAMA_NUM_PARALLEL']}")

    stop_ollama()
    if args.purge_results:
        purge_previous_results(args.model)
    if not args.no_cache_clear:
        clear_cache()
    else:
        print("Skipping cache clear as requested; results may be non-reproducible.")

    show_user_processes()
    print("Reminder: manually close heavy background apps (Docker, browsers, etc.) for cleaner measurements.\n")

    run_benchmark(args.model, args.runs, python_bin, args.output)
    print(f"Benchmark completed for {args.model}. Results stored under results/{args.model}/<timestamp>/")


if __name__ == "__main__":
    main()

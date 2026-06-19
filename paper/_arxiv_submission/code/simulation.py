#!/usr/bin/env python3
"""
DSECS Paper Experiments — runs the real kernel experiments.

Usage:
    python simulation.py                          # single 3-node simulation
    python simulation.py --full-benchmark         # all validation experiments
    python simulation.py --results               # print current benchmark results
"""
import argparse
import json
import os
import subprocess
import sys
import time

KERNEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "../results")
os.makedirs(RESULTS_DIR, exist_ok=True)

PYTHON = sys.executable
ENV = {**os.environ, "PYTHONPATH": KERNEL_DIR}


def run_kernel_experiment(script: str, args: list = None) -> dict:
    """Run a kernel experiment script and return parsed output."""
    cmd = [PYTHON, os.path.join(KERNEL_DIR, "experiments", script)]
    if args:
        cmd.extend(args)
    
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    elapsed = time.time() - t0
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    
    return {
        "script": script,
        "exit_code": result.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "elapsed_s": round(elapsed, 2),
        "passed": result.returncode == 0,
    }


def run_benchmark():
    """Run all 3 kernel experiments."""
    results = {
        "simulation": run_kernel_experiment("simulate.py", ["--steps", "50", "--nodes", "3"]),
        "deterministic": run_kernel_experiment("deterministic_test.py"),
        "byzantine": run_kernel_experiment("byzantine_test.py", ["--byzantine-ratio", "0.33"]),
    }
    return results


def main():
    parser = argparse.ArgumentParser("DSECS Paper Experiments")
    parser.add_argument("--full-benchmark", action="store_true")
    args = parser.parse_args()

    if args.full_benchmark:
        print("DSECS Paper Benchmark — running kernel experiments...\n")
        results = run_benchmark()
        
        path = os.path.join(RESULTS_DIR, "benchmark_results.json")
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
        
        for name, r in results.items():
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            print(f"  {name}: {status} ({r['exit_code']}) [{r['elapsed_s']:.1f}s]")
            # Print first/last non-empty lines of stdout
            lines = [l for l in r["stdout"].split("\n") if l.strip()]
            if lines:
                print(f"    → {lines[0]}")
                if len(lines) > 1:
                    print(f"    → {lines[-1]}")
        
        print(f"\n  Results saved: {path}")
        return results
    
    # Single run
    result = run_kernel_experiment("simulate.py", ["--steps", "20", "--nodes", "3"])
    print(result["stdout"])


if __name__ == "__main__":
    main()

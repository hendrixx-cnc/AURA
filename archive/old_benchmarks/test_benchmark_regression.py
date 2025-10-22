#!/usr/bin/env python3
"""
Lightweight regression guard for benchmark performance.

Runs the quick benchmark suite (small + medium datasets) and compares results
to the checked-in baseline to detect significant compression regressions.
"""
import json
from pathlib import Path

from benchmarks.benchmark_suite import run_benchmarks

BASELINE_PATH = Path("benchmarks/baseline_quick.json")
RATIO_TOLERANCE = 0.90  # Allow up to 10% degradation relative to baseline


def load_baseline() -> dict:
    if not BASELINE_PATH.is_file():
        raise FileNotFoundError(
            f"Baseline file {BASELINE_PATH} is missing. Re-run benchmark_suite.py to generate it."
        )
    with BASELINE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_quick_benchmark_regression():
    baseline = load_baseline()
    baseline_index = {entry["dataset"]: entry for entry in baseline["results"]}

    current = run_benchmarks(quick=True, include_large=False)
    current_index = {entry["dataset"]: entry for entry in current["results"]}

    assert current_index, "Benchmark suite returned no results."

    for dataset, result in current_index.items():
        aura_ratio = result["aura_ratio"]
        assert aura_ratio > 0.8, f"AURA compression ratio unexpectedly low for {dataset}: {aura_ratio}"

        if dataset not in baseline_index:
            continue

        baseline_ratio = baseline_index[dataset]["aura_ratio"]
        allowed_drop = baseline_ratio * RATIO_TOLERANCE
        assert aura_ratio >= allowed_drop, (
            f"AURA ratio for {dataset} degraded below threshold: {aura_ratio:.3f} "
            f"(baseline {baseline_ratio:.3f})"
        )

#!/usr/bin/env python3
"""
Comprehensive benchmarking harness for the AURA protocol.

Features:
- Evaluates AURA against gzip, Brotli, and Zstandard (if available)
- Covers multiple dataset sizes (small / medium / large)
- Uses representative content profiles (AI text, natural language, code)
- Emits structured JSON for regression tracking
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import statistics
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple, TypeVar

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "aura-compressor-py" / "src"))

from aura_compressor.streamer import AuraTransceiver  # type: ignore  # noqa: E402

try:
    import brotli  # type: ignore

    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False

try:
    import zstandard as zstd  # type: ignore

    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False


AI_TEXT_BASE = (
    "The large language model considered the query carefully before responding with a richly detailed"
    " explanation, referencing previous context and adapting tone to the user's intent. "
)
NATURAL_TEXT_BASE = (
    "In a calm forest clearing, sunlight filtered through the trees, illuminating a carpet of wildflowers."
    " A gentle breeze carried the scent of pine and damp soil, mingling with distant birdsong. "
)
CODE_BASE = (
    "def compute_checksum(payload: bytes) -> int:\n"
    "    checksum = 0\n"
    "    for index, value in enumerate(payload):\n"
    "        checksum = (checksum + (value * (index + 1))) % 0xFFFFFFFF\n"
    "    return checksum\n\n"
)


CONTENT_PROFILES = {
    "ai_text": AI_TEXT_BASE,
    "natural_text": NATURAL_TEXT_BASE,
    "code": CODE_BASE,
}

SIZE_PROFILES = {
    "small": [64, 256, 512, 1024],
    "medium": [2048, 8192, 65536],
    "large": [262144, 1048576, 5242880],
}


def build_payload(base: str, target_size: int) -> str:
    """Repeat and trim a base string to approximate the requested byte size."""
    if target_size <= 0:
        raise ValueError("target_size must be positive")
    repetitions = math.ceil(target_size / len(base.encode("utf-8")))
    text = (base * repetitions)[:target_size]
    # Ensure UTF-8 slicing integrity by trimming to code-point boundary
    encoded = text.encode("utf-8")
    if len(encoded) > target_size:
        encoded = encoded[:target_size]
        while True:
            try:
                text = encoded.decode("utf-8")
                break
            except UnicodeDecodeError:
                encoded = encoded[:-1]
    return text


T = TypeVar("T")


def time_operation(func: Callable[[], T]) -> Tuple[T, float]:
    start = time.perf_counter()
    result = func()
    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, elapsed_ms


@dataclass
class BenchmarkResult:
    dataset: str
    category: str
    size_bytes: int
    aura_ratio: float
    aura_compress_ms: float
    aura_decompress_ms: float
    aura_packet_count: int
    aura_handshake_ms: float
    gzip_ratio: Optional[float] = None
    gzip_compress_ms: Optional[float] = None
    gzip_decompress_ms: Optional[float] = None
    brotli_ratio: Optional[float] = None
    brotli_compress_ms: Optional[float] = None
    brotli_decompress_ms: Optional[float] = None
    zstd_ratio: Optional[float] = None
    zstd_compress_ms: Optional[float] = None
    zstd_decompress_ms: Optional[float] = None


def run_aura_benchmark(text: str) -> Tuple[float, float, float, int, float]:
    text_bytes = text.encode("utf-8")

    server = AuraTransceiver(load_env=False)
    client = AuraTransceiver(load_env=False)

    handshake_start = time.perf_counter()
    handshake_packet = server.perform_handshake()
    client.receive_handshake(handshake_packet)
    handshake_ms = (time.perf_counter() - handshake_start) * 1000

    packets, compress_ms = time_operation(lambda: server.compress(text, adaptive=False))
    compressed_payload = b"".join(packets)

    def _decompress_all() -> str:
        output: List[str] = []
        for packet in packets:
            decoded = client.decompress(packet)
            if decoded:
                output.append(decoded)
        return "".join(output)

    reconstructed, decompress_ms = time_operation(_decompress_all)
    assert reconstructed == text, "AURA decompression mismatch"

    ratio = len(text_bytes) / len(compressed_payload) if compressed_payload else 0.0
    return ratio, compress_ms, decompress_ms, len(packets), handshake_ms


def run_gzip_benchmark(text: str) -> Tuple[float, float, float]:
    text_bytes = text.encode("utf-8")
    compressed, compress_ms = time_operation(lambda: gzip.compress(text_bytes, compresslevel=6))
    decompressed, decompress_ms = time_operation(lambda: gzip.decompress(compressed))
    assert decompressed == text_bytes
    ratio = len(text_bytes) / len(compressed) if compressed else 0.0
    return ratio, compress_ms, decompress_ms


def run_brotli_benchmark(text: str) -> Tuple[float, float, float]:
    if not BROTLI_AVAILABLE:
        raise RuntimeError("Brotli not available")
    text_bytes = text.encode("utf-8")
    compressed, compress_ms = time_operation(lambda: brotli.compress(text_bytes))
    decompressed, decompress_ms = time_operation(lambda: brotli.decompress(compressed))
    assert decompressed == text_bytes
    ratio = len(text_bytes) / len(compressed) if compressed else 0.0
    return ratio, compress_ms, decompress_ms


def run_zstd_benchmark(text: str) -> Tuple[float, float, float]:
    if not ZSTD_AVAILABLE:
        raise RuntimeError("Zstandard not available")
    text_bytes = text.encode("utf-8")
    compressor = zstd.ZstdCompressor(level=3)
    compressed, compress_ms = time_operation(lambda: compressor.compress(text_bytes))
    decompressor = zstd.ZstdDecompressor()
    decompressed, decompress_ms = time_operation(lambda: decompressor.decompress(compressed))
    assert decompressed == text_bytes
    ratio = len(text_bytes) / len(compressed) if compressed else 0.0
    return ratio, compress_ms, decompress_ms


def generate_datasets(
    quick: bool = False,
    include_large: bool = True,
) -> Iterable[Tuple[str, str, int, str]]:
    for profile_name, base_text in CONTENT_PROFILES.items():
        for category, sizes in SIZE_PROFILES.items():
            if category == "large" and not include_large:
                continue
            target_sizes = sizes[:1] if quick else sizes
            for size in target_sizes:
                dataset_name = f"{profile_name}_{category}_{size}"
                text = build_payload(base_text, size)
                yield dataset_name, category, size, text


def summarize_results(results: List[BenchmarkResult]) -> Dict[str, Dict[str, float]]:
    summary: Dict[str, Dict[str, float]] = {}
    for category in SIZE_PROFILES.keys():
        category_results = [r for r in results if r.category == category]
        if not category_results:
            continue
        summary[category] = {
            "aura_ratio_avg": statistics.mean(r.aura_ratio for r in category_results),
            "aura_compress_ms_avg": statistics.mean(r.aura_compress_ms for r in category_results),
        }
        if any(r.gzip_ratio for r in category_results):
            summary[category]["gzip_ratio_avg"] = statistics.mean(
                r.gzip_ratio for r in category_results if r.gzip_ratio
            )
        if any(r.brotli_ratio for r in category_results):
            summary[category]["brotli_ratio_avg"] = statistics.mean(
                r.brotli_ratio for r in category_results if r.brotli_ratio
            )
        if any(r.zstd_ratio for r in category_results):
            summary[category]["zstd_ratio_avg"] = statistics.mean(
                r.zstd_ratio for r in category_results if r.zstd_ratio
            )
    return summary


def run_benchmarks(quick: bool = False, include_large: bool = True) -> Dict[str, object]:
    results: List[BenchmarkResult] = []

    for dataset_name, category, size, text in generate_datasets(quick=quick, include_large=include_large):
        print(f"▶ Benchmarking {dataset_name} ({size} bytes)...")
        aura_ratio, aura_compress_ms, aura_decompress_ms, packet_count, handshake_ms = run_aura_benchmark(text)

        gzip_ratio = gzip_compress_ms = gzip_decompress_ms = None
        brotli_ratio = brotli_compress_ms = brotli_decompress_ms = None
        zstd_ratio = zstd_compress_ms = zstd_decompress_ms = None

        try:
            gzip_ratio, gzip_compress_ms, gzip_decompress_ms = run_gzip_benchmark(text)
        except Exception as exc:  # pragma: no cover - extremely unlikely
            print(f"   ⚠️  Gzip benchmark failed: {exc}")

        if BROTLI_AVAILABLE:
            try:
                brotli_ratio, brotli_compress_ms, brotli_decompress_ms = run_brotli_benchmark(text)
            except Exception as exc:
                print(f"   ⚠️  Brotli benchmark failed: {exc}")
        else:
            print("   ℹ️  Brotli not available; skipping.")

        if ZSTD_AVAILABLE:
            try:
                zstd_ratio, zstd_compress_ms, zstd_decompress_ms = run_zstd_benchmark(text)
            except Exception as exc:
                print(f"   ⚠️  Zstandard benchmark failed: {exc}")
        else:
            print("   ℹ️  Zstandard not available; skipping.")

        results.append(
            BenchmarkResult(
                dataset=dataset_name,
                category=category,
                size_bytes=size,
                aura_ratio=aura_ratio,
                aura_compress_ms=aura_compress_ms,
                aura_decompress_ms=aura_decompress_ms,
                aura_packet_count=packet_count,
                aura_handshake_ms=handshake_ms,
                gzip_ratio=gzip_ratio,
                gzip_compress_ms=gzip_compress_ms,
                gzip_decompress_ms=gzip_decompress_ms,
                brotli_ratio=brotli_ratio,
                brotli_compress_ms=brotli_compress_ms,
                brotli_decompress_ms=brotli_decompress_ms,
                zstd_ratio=zstd_ratio,
                zstd_compress_ms=zstd_compress_ms,
                zstd_decompress_ms=zstd_decompress_ms,
            )
        )

    summary = summarize_results(results)
    return {
        "metadata": {
            "quick": quick,
            "include_large": include_large,
            "brotli_available": BROTLI_AVAILABLE,
            "zstd_available": ZSTD_AVAILABLE,
            "timestamp": time.time(),
        },
        "results": [asdict(r) for r in results],
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(description="Run AURA benchmark suite.")
    parser.add_argument("--output", type=Path, help="Output JSON file.")
    parser.add_argument("--quick", action="store_true", help="Run quick mode (small sample only).")
    parser.add_argument("--no-large", action="store_true", help="Skip large payload benchmarks.")
    args = parser.parse_args()

    payload = run_benchmarks(quick=args.quick, include_large=not args.no_large)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"\n✅ Benchmark results written to {args.output}")

    print("\n=== Summary ===")
    for category, metrics in payload["summary"].items():
        aura_ratio = metrics["aura_ratio_avg"]
        gzip_ratio = metrics.get("gzip_ratio_avg")
        print(f"- {category.title():<8} | AURA ratio avg: {aura_ratio:5.2f}:1", end="")
        if gzip_ratio:
            print(f" | Gzip ratio avg: {gzip_ratio:5.2f}:1", end="")
        print()


if __name__ == "__main__":
    main()

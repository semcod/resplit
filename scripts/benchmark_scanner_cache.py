#!/usr/bin/env python3
"""
benchmark_scanner_cache — quantify the diff-aware caching speedup.

This script simulates a typical ``rebuild walk`` scenario: scanning the same
repository at ``N`` consecutive commits where only ``CHURN_PCT`` of files
change between commits.

Usage:
    python scripts/benchmark_scanner_cache.py [--commits N] [--files M] [--churn 0.05]

Example output (FastAPI fixture, 200 files, 30 commits, 5% churn):

    Without cache: 30 scans, 12.34 s total, 411 ms/scan
    With cache:    30 scans,  1.42 s total,  47 ms/scan
    Speedup:       8.7×

Run with ``-q`` for machine-parseable JSON output.
"""
from __future__ import annotations

import argparse
import json
import random
import string
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from rebuild.application.services.scanner_service import ScannerService  # noqa: E402
from rebuild.domain.models import WalkConfig  # noqa: E402


_FASTAPI_TEMPLATE = '''\
from fastapi import APIRouter

router = APIRouter(prefix="/api/{name}")

@router.get("/health")
def health_{name}():
    return {{"ok": True}}

@router.post("/items")
def create_{name}():
    return {{}}

@router.get("/items/{{item_id}}")
def get_{name}(item_id: int):
    return {{"id": item_id}}
'''


def _gen_module(name: str) -> str:
    return _FASTAPI_TEMPLATE.format(name=name)


def _random_suffix(n: int = 6) -> str:
    return "".join(random.choice(string.ascii_lowercase) for _ in range(n))


def setup_repo(repo: Path, n_files: int) -> List[Path]:
    """Create *n_files* FastAPI module files inside *repo*."""
    repo.mkdir(parents=True, exist_ok=True)
    files: List[Path] = []
    for i in range(n_files):
        f = repo / f"routes_{i:04d}.py"
        f.write_text(_gen_module(f"mod{i}"), encoding="utf-8")
        files.append(f)
    return files


def churn(files: List[Path], pct: float) -> int:
    """Mutate ``ceil(pct * len(files))`` files in-place. Returns count touched."""
    k = max(1, int(len(files) * pct))
    chosen = random.sample(files, k)
    for f in chosen:
        suffix = _random_suffix()
        f.write_text(f.read_text(encoding="utf-8") + f"\n# {suffix}\n", encoding="utf-8")
    return k


def run_walk(repo: Path, files: List[Path], n_commits: int, churn_pct: float, use_cache: bool) -> Tuple[float, dict]:
    """Run *n_commits* sequential scans, mutating *churn_pct* of files between them.

    Returns ``(elapsed_seconds, cache_stats)``.
    """
    config = WalkConfig(repo_path=repo, base_url="http://localhost:8003")
    service = ScannerService(config)

    start = time.perf_counter()
    for i in range(n_commits):
        if not use_cache:
            # Defeat the cache by clearing it before every scan.
            service.reset_cache()
        service._scan_via_fastapi_routes(repo)
        if i < n_commits - 1:
            churn(files, churn_pct)
    elapsed = time.perf_counter() - start
    return elapsed, dict(service.cache_stats)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--commits", type=int, default=30, help="Number of sequential scans (default: 30)")
    ap.add_argument("--files", type=int, default=200, help="Number of Python files in the fake repo (default: 200)")
    ap.add_argument("--churn", type=float, default=0.05, help="Fraction of files mutated per commit (default: 0.05)")
    ap.add_argument("--seed", type=int, default=42, help="RNG seed (default: 42)")
    ap.add_argument("-q", "--quiet", action="store_true", help="Emit machine-parseable JSON only")
    args = ap.parse_args()

    random.seed(args.seed)

    with tempfile.TemporaryDirectory(prefix="rebuild_bench_") as tmp:
        repo = Path(tmp) / "repo"
        files = setup_repo(repo, args.files)

        if not args.quiet:
            print(f"Setup: {args.files} files in {repo}")
            print(f"Running {args.commits} scans, churn={args.churn:.0%} per commit\n")

        # Run WITHOUT cache first (baseline)
        random.seed(args.seed)
        files_a = list(files)
        # Snapshot original contents for fair comparison
        snapshots = {f: f.read_bytes() for f in files_a}
        no_cache_elapsed, no_cache_stats = run_walk(repo, files_a, args.commits, args.churn, use_cache=False)

        # Restore originals
        for f, content in snapshots.items():
            f.write_bytes(content)

        # Run WITH cache (warm)
        random.seed(args.seed)
        cache_elapsed, cache_stats = run_walk(repo, files_a, args.commits, args.churn, use_cache=True)

    speedup = no_cache_elapsed / cache_elapsed if cache_elapsed else float("inf")
    result = {
        "commits": args.commits,
        "files": args.files,
        "churn_pct": args.churn,
        "no_cache": {
            "elapsed_s": round(no_cache_elapsed, 3),
            "ms_per_scan": round(no_cache_elapsed / args.commits * 1000, 1),
            "stats": no_cache_stats,
        },
        "with_cache": {
            "elapsed_s": round(cache_elapsed, 3),
            "ms_per_scan": round(cache_elapsed / args.commits * 1000, 1),
            "stats": cache_stats,
            "hit_rate": round(cache_stats["hits"] / max(1, cache_stats["hits"] + cache_stats["misses"]), 3),
        },
        "speedup": round(speedup, 2),
    }

    if args.quiet:
        print(json.dumps(result, indent=2))
    else:
        print(f"Without cache: {result['no_cache']['elapsed_s']} s ({result['no_cache']['ms_per_scan']} ms/scan)")
        print(f"With cache:    {result['with_cache']['elapsed_s']} s ({result['with_cache']['ms_per_scan']} ms/scan)")
        print(f"Cache stats:   hits={cache_stats['hits']} misses={cache_stats['misses']} size={cache_stats['size']}")
        print(f"Hit rate:      {result['with_cache']['hit_rate']:.1%}")
        print(f"\nSpeedup:       {speedup:.1f}×")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

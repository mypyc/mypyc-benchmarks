"""Utility to collect new baselines for all benchmarks.

Run this to collect baselines after a Python version, operating system
or hardware upgrade.

Usage:

  python3 -m reporting.collect_all_baselines <data-repo-dir>
"""

import argparse
import subprocess
import sys

from benchmarking import benchmarks
from runbench import import_all


def main() -> None:
    import_all()

    parser = argparse.ArgumentParser(
        description="Collect baselines for all benchmarks; store results in <data_repo>/data"
    )
    parser.add_argument(
        "data_repo",
        help="target data repository where output will be written (this will be modified!)")
    args = parser.parse_args()
    data_repo: str = args.data_repo

    for benchmark in benchmarks:
        print(f"== Collecting baseline for {benchmark.name} ==\n")
        cmd = [
            sys.executable,
            "-m",
            "reporting.collect_baseline",
            benchmark.name,
            data_repo,
        ]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()

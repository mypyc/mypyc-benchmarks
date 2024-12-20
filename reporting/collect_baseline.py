"""Utility that collects interpreted benchmark timings for a commit.

Run "python3 -m reporting.collect_baseline --help" for more information.
"""

from typing import Tuple
from datetime import datetime, UTC
import argparse

from reporting.common import get_csv_path
from reporting.gitutil import get_current_commit
from reporting.collect import write_csv_line, run_bench


def parse_args() -> Tuple[str, str]:
    parser = argparse.ArgumentParser(
        description="""Run an interpreted benchmark, and append result to the
                       file <data_repo>/data/<benchmark>-cpython.csv.""")
    parser.add_argument(
        "benchmark",
        help="""benchmark name, such as 'richards' (use 'runbench.py --list' to show valid
                values)""")
    parser.add_argument(
        "data_repo",
        help="target data repository where output will be written (this will be modified!)")
    args = parser.parse_args()
    return args.benchmark, args.data_repo


def main() -> None:
    benchmark, data_repo = parse_args()
    now = datetime.now(UTC)
    benchmark_commit = get_current_commit(".")
    runtime, stddev = run_bench(benchmark, None, compiled=False)
    fnam = get_csv_path(data_repo, benchmark, cpython=True)
    write_csv_line(fnam, benchmark, now, runtime, stddev, "", benchmark_commit)


if __name__ == "__main__":
    main()

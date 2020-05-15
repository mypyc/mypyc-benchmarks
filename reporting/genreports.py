"""Generate benchmark reports."""

from typing import Tuple, Dict, NamedTuple, List
import glob
import os
import argparse

from reporting.gitutil import get_mypy_commit_sort_order, get_mypy_commit_dates
from reporting.data import (
    BenchmarkData,
    load_data,
    sort_data_items,
)
from reporting.report_runs import gen_reports_for_benchmarks
from reporting.report_summary import gen_summary_reports
from reporting.common import REPORTS_DIR, BENCHMARKS_DIR


def parse_args() -> Tuple[str, str]:
    parser = argparse.ArgumentParser(
        description="""Generate benchmark markdown reports based on available data.""")
    parser.add_argument("mypy_repo",
                        help="target mypy repository (used to look up information on commits)")
    parser.add_argument(
        "data_repo",
        help="""target repository where input data resides and output will be written
                (this will be modified!)""")
    args = parser.parse_args()
    return args.mypy_repo, args.data_repo


def main() -> None:
    mypy_repo, data_repo = parse_args()
    commit_order = get_mypy_commit_sort_order(mypy_repo)
    commit_times = get_mypy_commit_dates(mypy_repo)
    data = load_data(mypy_repo, data_repo)
    per_benchmark_report_dir = os.path.join(data_repo, REPORTS_DIR, BENCHMARKS_DIR)
    gen_reports_for_benchmarks(data, per_benchmark_report_dir, commit_order, commit_times)
    summary_report_dir = os.path.join(data_repo, REPORTS_DIR)
    gen_summary_reports(data, summary_report_dir, commit_order, commit_times)


if __name__ == '__main__':
    main()

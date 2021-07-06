"""Generate mypyc benchmark reports in markdown.

We generate one detailed report per benchmark, and also summary
reports that include information about multiple benchmarks.
"""

from typing import Tuple, Dict, NamedTuple, List
import glob
import os
import argparse

from reporting.gitutil import get_mypy_commit_sort_order, get_mypy_commit_dates
from reporting.data import (
    BenchmarkData,
    load_data,
    normalize_data,
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

    # Prepare input data.
    commit_order = get_mypy_commit_sort_order(mypy_repo)
    commit_times = get_mypy_commit_dates(mypy_repo)
    data = load_data(data_repo)

    recent_item = sort_data_items(data.runs['richards'], commit_order)[0]
    python_version = recent_item.python_version
    os_version = recent_item.os_version
    hardware_id = recent_item.hardware_id
    environment_summary = "Environment: CPython %s, %s and %s." % (
        python_version,
        os_version,
        hardware_id,
    )

    normalize_data(data, python_version, hardware_id)

    # Generate reports about individual benchmarks.
    per_benchmark_report_dir = os.path.join(data_repo, REPORTS_DIR, BENCHMARKS_DIR)
    gen_reports_for_benchmarks(data, per_benchmark_report_dir, commit_order, commit_times)

    # Generate benchmark summary reports.
    summary_report_dir = os.path.join(data_repo, REPORTS_DIR)
    gen_summary_reports(data, summary_report_dir, commit_order, commit_times,
                        environment_summary)


if __name__ == '__main__':
    main()

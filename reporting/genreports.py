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
from reporting.report_runs import gen_data_for_benchmark, gen_benchmark_table


# Base directory for all reports
REPORTS_DIR = 'reports'
# Subdirectory for per-benchmark reports
BENCHMARKS_DIR = 'benchmarks'


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


def gen_reports_for_benchmarks(data: BenchmarkData,
                               output_dir: str,
                               commit_order: Dict[str, int],
                               commit_dates: Dict[str, Tuple[str, str]]) -> None:
    for benchmark in data.baselines:
        runs = data.runs[benchmark]
        runs = sort_data_items(runs, commit_order)
        items = gen_data_for_benchmark(data.baselines[benchmark], runs, commit_dates)
        table = gen_benchmark_table(items)
        fnam = os.path.join(output_dir, '%s.md' % benchmark)
        lines = []
        lines.append('# Benchmark results for "%s"' % benchmark)
        lines.append('')
        lines.extend(table)
        os.makedirs(output_dir, exist_ok=True)
        print('writing %s' % fnam)
        with open(fnam, 'w') as f:
            f.write('\n'.join(lines))


def main() -> None:
    mypy_repo, data_repo = parse_args()
    commit_order = get_mypy_commit_sort_order(mypy_repo)
    commit_times = get_mypy_commit_dates(mypy_repo)
    data = load_data(mypy_repo, data_repo)
    report_dir = os.path.join(data_repo, REPORTS_DIR, BENCHMARKS_DIR)
    gen_reports_for_benchmarks(data, report_dir, commit_order, commit_times)


if __name__ == '__main__':
    main()

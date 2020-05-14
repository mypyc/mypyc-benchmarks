"""Generate benchmark reports."""

from typing import Tuple, Dict, NamedTuple, List
import glob
import os
import argparse

from reporting.csv import read_csv, DataItem
from reporting.common import DATA_DIR


# Base directory for all reports
REPORTS_DIR = 'reports'
# Subdirectory for per-benchmark reports
BENCHMARKS_DIR = 'benchmarks'


class BenchmarkData(NamedTuple):
    # Data about interpreted baseline runs (benchmark name as key)
    baselines: Dict[str, List[DataItem]]
    # Data about each compiled benchmark run (benchmark name as key)
    runs: Dict[str, List[DataItem]]


def load_data(mypy_repo: str, data_repo: str) -> BenchmarkData:
    baselines = {}
    runs = {}
    files = glob.glob(os.path.join(data_repo, DATA_DIR, '*.csv'))
    for fnam in files:
        benchmark, suffix, _ = fnam.partition('-cpython')
        items = read_csv(fnam)
        if suffix:
            baselines[benchmark] = items
        else:
            runs[benchmark] = items
    return BenchmarkData(baselines, runs)


class BenchmarkItem(NamedTuple):
    date: str
    relative_perf: float
    mypy_commit: str


def find_baseline(baselines: List[DataItem], run: DataItem) -> DataItem:
    for item in baselines:
        if (item.python_version == run.python_version
                and item.hardware_id == run.hardware_id
                and item.os_version == run.os_version):
            return item
    assert False, "No baseline found for %r" % (run,)


def gen_data_for_benchmark(baselines: List[DataItem],
                           runs: List[DataItem]) -> List[BenchmarkItem]:
    out = []
    for item in runs:
        baseline = find_baseline(baselines, item)
        new_item = BenchmarkItem(
            date="TODO",
            relative_perf=baseline.runtime / item.runtime,
            mypy_commit=item.mypy_commit,
        )
        out.append(new_item)
    return out


def gen_benchmark_table(data: List[BenchmarkItem]) -> List[str]:
    out = []
    out.append('| Date | Performance | Mypy commit |')
    out.append('| -- | -- | -- |')
    for item in data:
        out.append('| %s | %.2fx | %s |' % (item.date, item.relative_perf, item.mypy_commit))
    return out


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


def gen_reports_for_benchmarks(data: BenchmarkData, output_dir: str) -> None:
    for benchmark in data.baselines:
        items = gen_data_for_benchmark(data.baselines[benchmark], data.runs[benchmark])
        table = gen_benchmark_table(items)
        fnam = os.path.join(output_dir, '%s.md' % benchmark)
        lines = []
        lines.append('# Benchmark results for "%s"' % benchmark)
        lines.append('')
        lines.extend(table)
        with open(fnam, 'w') as f:
            f.write('\n'.join(lines))


def main() -> None:
    mypy_repo, data_repo = parse_args()
    data = load_data(mypy_repo, data_repo)
    report_dir = os.path.join(data_repo, REPORTS_DIR, BENCHMARKS_DIR)
    gen_reports_for_benchmarks(data, report_dir)


if __name__ == '__main__':
    main()

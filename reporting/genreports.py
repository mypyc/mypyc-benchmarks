"""Generate benchmark reports."""

from typing import Tuple, Dict, NamedTuple, List
import glob
import os
import argparse

from reporting.csv import read_csv, DataItem
from reporting.common import DATA_DIR
from reporting.gitutil import get_commit_range, get_commit_times


# Base directory for all reports
REPORTS_DIR = 'reports'
# Subdirectory for per-benchmark reports
BENCHMARKS_DIR = 'benchmarks'


OLDEST_COMMIT = '07ca355c547b062f252df491819dbe08693ecbb4'


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
        benchmark = os.path.basename(fnam)
        benchmark, _, _ = benchmark.partition('.csv')
        benchmark, suffix, _ = benchmark.partition('-cpython')
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


def all_relevant_commits(mypy_repo: str) -> List[str]:
    return get_commit_range(mypy_repo, OLDEST_COMMIT, 'master')


def get_commit_sort_order(mypy_repo: str) -> Dict[str, int]:
    commits = all_relevant_commits(mypy_repo)
    result = {}
    for i, commit in enumerate(commits):
        result[commit] = i
    return result


def get_commit_dates(mypy_repo: str) -> Dict[str, Tuple[str, str]]:
    commits = all_relevant_commits(mypy_repo)
    return get_commit_times(mypy_repo, commits)


def sort_data_items(items: List[DataItem], commit_order: Dict[str, int]) -> List[DataItem]:
    """Sort data items by age of mypy commit, from recent to old."""
    return sorted(items, key=lambda x: commit_order[x.mypy_commit])


def find_baseline(baselines: List[DataItem], run: DataItem) -> DataItem:
    for item in baselines:
        if (item.python_version == run.python_version
                and item.hardware_id == run.hardware_id
                and item.os_version == run.os_version):
            return item
    assert False, "No baseline found for %r" % (run,)


def gen_data_for_benchmark(baselines: List[DataItem],
                           runs: List[DataItem],
                           commit_dates: Dict[str, Tuple[str, str]]) -> List[BenchmarkItem]:
    out = []
    for item in runs:
        baseline = find_baseline(baselines, item)
        new_item = BenchmarkItem(
            date=commit_dates.get(item.mypy_commit, ("???", "???"))[0],
            relative_perf=baseline.runtime / item.runtime,
            mypy_commit=item.mypy_commit,
        )
        out.append(new_item)
    return out


def mypy_commit_link(commit: str) -> str:
    url = 'https://github.com/python/mypy/commit/%s' % commit
    return '[%s](%s)' % (commit[:12], url)


def gen_benchmark_table(data: List[BenchmarkItem]) -> List[str]:
    out = []
    out.append('| Date | Performance | Mypy commit |')
    out.append('| --- | --- | --- |')
    for item in data:
        out.append('| %s | %.2fx | %s |' % (
            item.date,
            item.relative_perf,
            mypy_commit_link(item.mypy_commit),
        ))
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
    commit_order = get_commit_sort_order(mypy_repo)
    commit_times = get_commit_dates(mypy_repo)
    data = load_data(mypy_repo, data_repo)
    report_dir = os.path.join(data_repo, REPORTS_DIR, BENCHMARKS_DIR)
    gen_reports_for_benchmarks(data, report_dir, commit_order, commit_times)


if __name__ == '__main__':
    main()

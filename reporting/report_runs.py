"""Generate reports, each containing data about the runs of a single benchmark."""

from typing import Dict, List, NamedTuple, Tuple
import os

from reporting.markdown import bold, mypy_commit_link
from reporting.data import (
    DataItem, find_baseline, BenchmarkData, sort_data_items, is_significant_percent_change
)


class BenchmarkItem(NamedTuple):
    date: str
    relative_perf: float
    perf_change: str
    mypy_commit: str


def gen_data_for_benchmark(baselines: List[DataItem],
                           runs: List[DataItem],
                           commit_dates: Dict[str, Tuple[str, str]],
                           is_microbenchmark: bool) -> List[BenchmarkItem]:
    """Generate data for each run of a single benchmark."""
    result = []
    prev_runtime = 0.0
    for item in reversed(runs):
        baseline = find_baseline(baselines, item)
        perf_change = ''
        if prev_runtime:
            change = 100.0 * (prev_runtime / item.runtime - 1.0)
            if is_significant_percent_change(item.benchmark, change, is_microbenchmark):
                perf_change = '%+.1f%%' % change
        new_item = BenchmarkItem(
            date=commit_dates.get(item.mypy_commit, ("???", "???"))[0],
            relative_perf=baseline.runtime / item.runtime,
            perf_change=perf_change,
            mypy_commit=item.mypy_commit,
        )
        result.append(new_item)
        prev_runtime = item.runtime
    return list(reversed(result))


def gen_benchmark_table(data: List[BenchmarkItem]) -> List[str]:
    """Generate markdown table for the runs of a single benchmark."""
    lines = []
    lines.append('| Date | Performance | Change | Mypy commit |')
    lines.append('| --- | :---: | :---: | --- |')
    for i, item in enumerate(data):
        relative_perf = '%.2fx' % item.relative_perf
        if i == 0 or item.perf_change:
            relative_perf = bold(relative_perf)
        date = item.date
        if i == 0:
            date = bold(date)
        lines.append('| %s | %s | %s | %s |' % (
            date,
            relative_perf,
            bold(item.perf_change),
            mypy_commit_link(item.mypy_commit),
        ))
    return lines


def gen_reports_for_benchmarks(data: BenchmarkData,
                               output_dir: str,
                               commit_order: Dict[str, int],
                               commit_dates: Dict[str, Tuple[str, str]]) -> None:
    """Generate separate reports for each benchmark about their runs."""
    for benchmark in data.baselines:
        runs = data.runs[benchmark]
        runs = sort_data_items(runs, commit_order)
        items = gen_data_for_benchmark(
            data.baselines[benchmark],
            runs,
            commit_dates,
            benchmark in data.microbenchmarks,
        )
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

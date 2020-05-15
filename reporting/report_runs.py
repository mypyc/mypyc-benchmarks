"""Report containing all runs of a single benchmark."""

from typing import Dict, List, NamedTuple, Tuple

from reporting.markdown import bold, mypy_commit_link
from reporting.data import DataItem, find_baseline


class BenchmarkItem(NamedTuple):
    date: str
    relative_perf: float
    perf_change: str
    mypy_commit: str


def gen_data_for_benchmark(baselines: List[DataItem],
                           runs: List[DataItem],
                           commit_dates: Dict[str, Tuple[str, str]]) -> List[BenchmarkItem]:
    """Generate data for each run of a single benchmark."""
    out = []
    prev_runtime = 0.0
    for item in reversed(runs):
        baseline = find_baseline(baselines, item)
        perf_change = ''
        if prev_runtime:
            change = max(item.runtime, prev_runtime) / min(item.runtime, prev_runtime)
            if change > 1.03:
                perf_change = '%+.1f%%' % ((prev_runtime / item.runtime - 1.0) * 100.0)
        new_item = BenchmarkItem(
            date=commit_dates.get(item.mypy_commit, ("???", "???"))[0],
            relative_perf=baseline.runtime / item.runtime,
            perf_change=perf_change,
            mypy_commit=item.mypy_commit,
        )
        out.append(new_item)
        prev_runtime = item.runtime
    return list(reversed(out))


def gen_benchmark_table(data: List[BenchmarkItem]) -> List[str]:
    """Generate markdown table for the runs of a single benchmark."""
    out = []
    out.append('| Date | Performance | Change | Mypy commit |')
    out.append('| --- | :---: | :---: | --- |')
    for i, item in enumerate(data):
        relative_perf = '%.2fx' % item.relative_perf
        if i == 0 or item.perf_change:
            relative_perf = bold(relative_perf)
        date = item.date
        if i == 0:
            date = bold(date)
        out.append('| %s | %s | %s | %s |' % (
            date,
            relative_perf,
            bold(item.perf_change),
            mypy_commit_link(item.mypy_commit),
        ))
    return out

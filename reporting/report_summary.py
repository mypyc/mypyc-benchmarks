"""Generate report containing summary of multiple benchmarks."""

from typing import Dict, List, Tuple, NamedTuple
from datetime import datetime, timedelta
import os

from reporting.data import DataItem, find_baseline, BenchmarkData, is_significant_percent_change
from reporting.markdown import benchmark_link
from reporting.common import split_datetime


class SummaryItem(NamedTuple):
    benchmark: str
    relative_perf: float
    delta_three_months: str


def gen_summary_data(benchmarks: List[str],
                     baselines: Dict[str, List[DataItem]],
                     runs: Dict[str, List[DataItem]],
                     commit_order: Dict[str, int],
                     commit_times: Dict[str, Tuple[str, str]]) -> List[SummaryItem]:
    result = []
    for benchmark in benchmarks:
        newest_item = min(runs[benchmark], key=lambda x: commit_order[x.mypy_commit])
        baseline = find_baseline(baselines[benchmark], newest_item)
        three_months_ago = datetime.utcnow() - timedelta(days=30 * 3)
        old_item = find_item_at_time(runs[benchmark], three_months_ago, commit_times)
        percentage_3m = 100.0 * (old_item.runtime / newest_item.runtime - 1.0)
        delta_3m = ''
        if is_significant_percent_change(benchmark, percentage_3m):
            delta_3m = '%+.1f%%' % percentage_3m
        summary_item = SummaryItem(
            benchmark=benchmark,
            relative_perf=baseline.runtime / newest_item.runtime,
            delta_three_months=delta_3m,
        )
        result.append(summary_item)
    result = sorted(result, key=lambda x: -x.relative_perf)
    return result


def find_item_at_time(runs: List[DataItem],
                      when: datetime,
                      commit_times: Dict[str, Tuple[str, str]]) -> DataItem:
    dt = split_datetime(when)
    candidates = [run
                  for run in runs
                  if commit_times[run.mypy_commit] >= dt]
    return min(candidates, key=lambda x: commit_times[x.mypy_commit])


def gen_summary_table(data: List[SummaryItem]) -> List[str]:
    lines = []
    lines.append('| Benchmark | Current perf | Change in 3 months |')
    lines.append('| --- | :---: | :---: |')
    for i, item in enumerate(data):
        relative_perf = '%.2fx' % item.relative_perf
        lines.append('| %s | %s | %s |' % (
            benchmark_link(item.benchmark),
            relative_perf,
            item.delta_three_months,
        ))
    return lines


def gen_summary_report(benchmarks: List[str],
                       title: str,
                       fnam: str,
                       data: BenchmarkData,
                       commit_order: Dict[str, int],
                       commit_times: Dict[str, Tuple[str, str]]) -> None:
    items = gen_summary_data(benchmarks, data.baselines, data.runs, commit_order, commit_times)
    table = gen_summary_table(items)
    lines = []
    lines.append('# %s' % title) # Mypyc benchmark summary')
    lines.append('')
    lines.append('Performance is relative to interpreted CPython.')
    lines.append('')
    lines.extend(table)
    print('writing %s' % fnam)
    with open(fnam, 'w') as f:
        f.write('\n'.join(lines) + '\n')


def gen_summary_reports(data: BenchmarkData,
                        output_dir: str,
                        commit_order: Dict[str, int],
                        commit_times: Dict[str, Tuple[str, str]]) -> None:
    benchmarks = set(data.runs)
    os.makedirs(output_dir, exist_ok=True)

    fnam = os.path.join(output_dir, 'summary-main.md')
    gen_summary_report(
        list(benchmarks - data.microbenchmarks),
        'Mypyc benchmark summary',
        fnam,
        data,
        commit_order,
        commit_times,
    )

    fnam = os.path.join(output_dir, 'summary-microbenchmarks.md')
    gen_summary_report(
        list(benchmarks & data.microbenchmarks),
        'Mypyc benchmark summary (microbenchmarks)',
        fnam,
        data,
        commit_order,
        commit_times,
    )

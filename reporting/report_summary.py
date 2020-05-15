"""Generate report containing summary of multiple benchmarks."""

from typing import Dict, List, Tuple, NamedTuple
import os

from reporting.data import DataItem, find_baseline, BenchmarkData


class SummaryItem(NamedTuple):
    benchmark: str
    relative_perf: float


def gen_summary_data(benchmarks: List[str],
                     baselines: Dict[str, List[DataItem]],
                     runs: Dict[str, List[DataItem]],
                     commit_order: Dict[str, int]) -> List[SummaryItem]:
    result = []
    for benchmark in benchmarks:
        newest_item = min(runs[benchmark], key=lambda x: commit_order[x.mypy_commit])
        baseline = find_baseline(baselines[benchmark], newest_item)
        summary_item = SummaryItem(benchmark=benchmark,
                                   relative_perf=baseline.runtime / newest_item.runtime)
        result.append(summary_item)
    result = sorted(result, key=lambda x: -x.relative_perf)
    return result


def gen_summary_table(data: List[SummaryItem]) -> List[str]:
    lines = []
    lines.append('| Benchmark | Mypyc vs. interpreted |')
    lines.append('| --- | | ---: |')
    for i, item in enumerate(data):
        relative_perf = '%.2fx' % item.relative_perf
        lines.append('| %s | %s |' % (item.benchmark, relative_perf))
    return lines


def gen_summary_reports(data: BenchmarkData,
                        output_dir: str,
                        commit_order: Dict[str, int]) -> None:
    benchmarks = sorted(data.runs)
    items = gen_summary_data(benchmarks, data.baselines, data.runs, commit_order)
    table = gen_summary_table(items)
    lines = []
    lines.append('# Benchmark summary')
    lines.append('')
    lines.extend(table)
    os.makedirs(output_dir, exist_ok=True)
    fnam = os.path.join(output_dir, 'summary.md')
    print('writing %s' % fnam)
    with open(fnam, 'w') as f:
        f.write('\n'.join(lines))

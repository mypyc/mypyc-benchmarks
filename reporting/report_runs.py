"""Generate reports, each containing data about the runs of a single benchmark."""

from typing import Dict, List, NamedTuple, Tuple
import os

from reporting.markdown import bold, mypy_commit_link
from reporting.data import (
    DataItem, find_baseline, BenchmarkData, sort_data_items, is_significant_percent_change,
    significant_percent_change, get_benchmark_names
)


class BenchmarkItem(NamedTuple):
    date: str
    perf: str
    perf_change: str
    mypy_commit: str


def gen_data_for_benchmark(baselines: List[DataItem],
                           runs: List[DataItem],
                           commit_order: Dict[str, int],
                           commit_dates: Dict[str, Tuple[str, str]],
                           is_microbenchmark: bool) -> List[BenchmarkItem]:
    """Generate data for each run of a single benchmark."""
    result = []
    prev_adjusted_runtime = 0.0

    newest_item = min(runs, key=lambda x: commit_order[x.mypy_commit])
    new_baseline = find_baseline(baselines, newest_item)

    for item in reversed(runs):
        baseline = find_baseline(baselines, item)
        perf_change = ''
        change = 0.0
        if baseline and new_baseline:
            adjusted_runtime = item.runtime * (new_baseline.runtime / baseline.runtime)
            if prev_adjusted_runtime != 0.0 and adjusted_runtime != 0.0:
                change = 100.0 * (prev_adjusted_runtime / adjusted_runtime - 1.0)
            if adjusted_runtime != 0.0:
                relative = new_baseline.runtime / adjusted_runtime
                perf = '%.2fx' % relative
            else:
                perf = '**error**'
        else:
            adjusted_runtime = item.runtime
            if adjusted_runtime != 0.0:
                change = 100.0 * (prev_adjusted_runtime / adjusted_runtime - 1.0)
                perf = '%.2fs' % adjusted_runtime
            else:
                perf = '**error**'
        if (
            is_significant_percent_change(item.benchmark, change, is_microbenchmark)
            and change != -100.0
        ):
            perf_change = '%+.1f%%' % change
        new_item = BenchmarkItem(
            date=commit_dates.get(item.mypy_commit, ("???", "???"))[0],
            perf=perf,
            perf_change=perf_change,
            mypy_commit=item.mypy_commit,
        )
        result.append(new_item)
        prev_adjusted_runtime = adjusted_runtime
    return list(reversed(result))


def gen_benchmark_table(data: List[BenchmarkItem]) -> List[str]:
    """Generate markdown table for the runs of a single benchmark."""
    lines = []
    lines.append('| Date | Performance | Change | Mypy commit |')
    lines.append('| --- | :---: | :---: | --- |')
    for i, item in enumerate(data):
        perf = item.perf
        if i == 0 or item.perf_change:
            perf = bold(perf)
        date = item.date
        if i == 0:
            date = bold(date)
        lines.append('| %s | %s | %s | %s |' % (
            date,
            perf,
            bold(item.perf_change),
            mypy_commit_link(item.mypy_commit),
        ))
    return lines


def gen_reports_for_benchmarks(data: BenchmarkData,
                               output_dir: str,
                               commit_order: Dict[str, int],
                               commit_dates: Dict[str, Tuple[str, str]]) -> None:
    """Generate separate reports for each benchmark about their runs."""
    benchmarks = list(data.baselines) + sorted(data.compiled_only_benchmarks)

    for benchmark in benchmarks:
        runs = data.runs.get(benchmark, [])
        runs = sort_data_items(runs, commit_order)
        is_microbenchmark = benchmark in data.microbenchmarks
        items = gen_data_for_benchmark(
            data.baselines.get(benchmark, []),
            runs,
            commit_order,
            commit_dates,
            is_microbenchmark,
        )
        table = gen_benchmark_table(items)
        fnam = os.path.join(output_dir, '%s.md' % benchmark)
        lines = []
        lines.append('# Benchmark results for "%s"' % benchmark)
        lines.append('')
        if benchmark in data.source_locations:
            path, line = data.source_locations[benchmark]
            url = 'https://github.com/mypyc/mypyc-benchmarks/blob/master/%s#L%d' % (
                path, line
            )
            lines.append('[Benchmark implementation](%s)' % url)
            lines.append('')
        if is_microbenchmark:
            threshold = significant_percent_change(benchmark, is_microbenchmark)
            lines.append("**Note:** This is a microbenchmark. Results can be noisy.")
            lines.append(
                "A change of less than **%.1f%%** is considered insignificant." % threshold
            )
            lines.append("")
        lines.extend(table)
        os.makedirs(output_dir, exist_ok=True)
        print('writing %s' % fnam)
        with open(fnam, 'w') as f:
            f.write('\n'.join(lines))

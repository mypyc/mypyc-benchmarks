from typing import NamedTuple, List, Dict, Set, Tuple
from datetime import datetime
import os
import re
import sys
import glob
import subprocess

from reporting.common import (
    get_hardware_id, get_os_version, get_c_compiler_version, CC, DATA_DIR, SOURCE_DIRS
)


def write_csv_header(fnam: str) -> None:
    with open(fnam, "w") as f:
        f.write("Timestamp,Runtime (s),Runtime (stddev),Mypy commit," +
                "Benchmark commit,Python version,Hardware,OS,C compiler\n")


def write_csv_line(fnam: str,
                   benchmark: str,
                   timestamp: datetime,
                   runtime: float,
                   stdev: float,
                   mypy_commit: str,
                   benchmark_commit: str) -> None:
    if not os.path.exists(fnam):
        write_csv_header(fnam)
    with open(fnam, "a") as f:
        f.write("%s,%.6f,%.6f,%s,%s,%s,%s,%s,%s\n" % (
            timestamp,
            runtime,
            stdev,
            mypy_commit,
            benchmark_commit,
            sys.version.split()[0],
            get_hardware_id(),
            get_os_version(),
            '%s %s' % (CC, get_c_compiler_version(CC)),
        ))


class DataItem(NamedTuple):
    benchmark: str
    timestamp: datetime
    runtime: float
    stdev_percent: float
    mypy_commit: str
    benchmark_commit: str
    python_version: str
    hardware_id: str
    os_version: str


def read_csv(fnam: str) -> List[DataItem]:
    benchmark = os.path.basename(fnam)
    benchmark = benchmark.partition('.csv')[0]
    benchmark = benchmark.partition('-cpython')[0]
    with open(fnam) as f:
        lines = f.readlines()
    lines = lines[1:]
    result = []
    for line in lines:
        fields = line.split(',')
        item = DataItem(
            benchmark=benchmark,
            timestamp=datetime.fromisoformat(fields[0]),
            runtime=float(fields[1]),
            stdev_percent=float(fields[2]),
            mypy_commit=fields[3],
            benchmark_commit=fields[4],
            python_version=fields[5],
            hardware_id=fields[6],
            os_version=fields[7],
        )
        result.append(item)
    return result


class BenchmarkData(NamedTuple):
    # Data about interpreted baseline runs (benchmark name as key)
    baselines: Dict[str, List[DataItem]]
    # Data about each compiled benchmark run (benchmark name as key)
    runs: Dict[str, List[DataItem]]
    # These benchmarks are microbenchmarks
    microbenchmarks: Set[str]
    # Dict from benchmark name to (source .py file path, line number)
    source_locations: Dict[str, Tuple[str, int]]


def load_data(mypy_repo: str, data_repo: str) -> BenchmarkData:
    """Load all benchmark data from csv files."""
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
    microbenchmarks = get_microbenchmark_names()
    source_locations = get_source_locations()
    return BenchmarkData(baselines, runs, microbenchmarks, source_locations)


def get_benchmark_names() -> Set[str]:
    """Get names of all benchmarks (normal and microbenchmarks)."""
    result = set()
    data = subprocess.check_output(['python', 'runbench.py', '--list']).decode('ascii')
    for line in data.splitlines():
        result.add(line.split()[0])
    return result


def get_microbenchmark_names() -> Set[str]:
    result = set()
    data = subprocess.check_output(['python', 'runbench.py', '--list']).decode('ascii')
    for line in data.splitlines():
        if '(micro)' in line:
            result.add(line.split()[0])
    return result


def get_source_locations() -> Dict[str, Tuple[str, int]]:
    result = {}
    for src_dir in SOURCE_DIRS:
        for fnam in glob.glob('%s/*.py' % src_dir):
            with open(fnam) as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if line.strip().startswith('@benchmark'):
                    for j, line2 in enumerate(lines[i + 1 : i + 10]):
                        line2 = line2.strip()
                        m = re.match('def +([a-zA-Z_0-9]+)', line2)
                        if m:
                            result[m.group(1)] = (fnam, i + 2 + j)
    return result


def sort_data_items(items: List[DataItem], commit_order: Dict[str, int]) -> List[DataItem]:
    """Sort data items by age of mypy commit, from recent to old."""
    return sorted(items, key=lambda x: commit_order[x.mypy_commit])


def find_baseline(baselines: List[DataItem], run: DataItem) -> DataItem:
    """Find the corresponding baseline measurement for a benchmark run."""
    for item in baselines:
        if (item.python_version == run.python_version
                and item.hardware_id == run.hardware_id
                and item.os_version == run.os_version):
            return item
    assert False, "No baseline found for %r" % (run,)


# Override the default significance levels for benchmarks that aren't very noisy.
significant_percent_change_overrides = {
    'sieve': 3.0,
    'str_methods_2': 3.0,
    'str_format': 10.0,
    'str_methods': 10.0,
    'matrix_multiply': 10.0,
}


def significant_percent_change(benchmark: str, is_microbenchmark: bool) -> float:
    if benchmark in significant_percent_change_overrides:
        return significant_percent_change_overrides[benchmark]
    elif is_microbenchmark:
        # Microbenchmark measurements are noisy. By default, only
        # consider 15% change as significant.
        return 15.0
    else:
        # Other benchmarks are less noisy.
        return 3.0


def is_significant_percent_change(benchmark: str,
                                  delta_percentage: float,
                                  is_microbenchmark: bool) -> bool:
    return abs(delta_percentage) >= significant_percent_change(benchmark, is_microbenchmark)

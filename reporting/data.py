from typing import NamedTuple, List, Dict, Set, Tuple, Optional
from datetime import datetime
import os
import re
import sys
import glob
import subprocess

from reporting.common import (
    get_hardware_id, get_os_version, get_c_compiler_version, CC, DATA_DIR, SOURCE_DIRS,
    SCALING_FNAM
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


class ScalingItem(NamedTuple):
    # Scale old results by this factor to get an estimate of the corresponding
    # result on the new configuration (1.0 == identical)
    factor: float
    old_hardware_id: str
    old_python_version: str  # X.Y (e.g. 3.8)
    new_hardware_id: str
    new_python_version: str  # X.Y (e.g. 3.8)


class BenchmarkData(NamedTuple):
    # Data about interpreted baseline runs (benchmark name as key)
    baselines: Dict[str, List[DataItem]]
    # Data about each compiled benchmark run (benchmark name as key)
    runs: Dict[str, List[DataItem]]
    # These benchmarks are microbenchmarks
    microbenchmarks: Set[str]
    # Dict from benchmark name to (source .py file path, line number)
    source_locations: Dict[str, Tuple[str, int]]
    compiled_only_benchmarks: Set[str]
    # Scaling information for benchmark results between different hardware and
    # python versions (benchmark name as key)
    scaling: Dict[str, List[ScalingItem]]


def load_data(data_repo: str) -> BenchmarkData:
    """Load all benchmark data from csv files.

    Call normalize_data() afterwards to normalize data collected from different
    hardware/Python configurations.
    """
    baselines = {}
    runs = {}
    files = glob.glob(os.path.join(data_repo, DATA_DIR, '*.csv'))
    for fnam in files:
        if os.path.basename(fnam) == SCALING_FNAM:
            continue
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
    compiled_only = {name for name, compiled_only
                     in get_benchmark_names().items()
                     if compiled_only}
    scaling = load_scaling_data(data_repo)
    return BenchmarkData(baselines, runs, microbenchmarks, source_locations, compiled_only,
                         scaling)


def load_scaling_data(data_repo: str) -> Dict[str, List[ScalingItem]]:
    """Load data about how to scale benchmark results between different configurations."""
    fnam = os.path.join(data_repo, DATA_DIR, SCALING_FNAM)
    with open(fnam) as f:
        lines = f.readlines()
    result: Dict[str, List[ScalingItem]] = {}
    for line in lines:
        benchmark, factor, old_hw, old_py, new_hw, new_py = line.strip().split(',')
        item = ScalingItem(float(factor), old_hw, old_py, new_hw, new_py)
        result.setdefault(benchmark, []).append(item)
    return result


def get_benchmark_names() -> Dict[str, bool]:
    """Get names of all benchmarks (normal and microbenchmarks).

    The value in the dict is True for compiled-only benchmarks (i.e. no
    baseline to compare to).
    """
    result = {}
    data = subprocess.check_output(['python', 'runbench.py', '--list']).decode('ascii')
    for line in data.splitlines():
        compiled_only = 'compiled only' in line
        result[line.split()[0]] = compiled_only
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


def find_baseline(baselines: List[DataItem], run: DataItem) -> Optional[DataItem]:
    """Find the corresponding baseline measurement for a benchmark run."""
    for item in baselines:
        if (item.python_version == run.python_version
                and item.hardware_id == run.hardware_id
                and item.os_version == run.os_version):
            return item
    return None


# Override the default significance levels for benchmarks that aren't very noisy.
significant_percent_change_overrides = {
    'sieve': 3.0,
    'str_methods_2': 3.0,
    'str_format': 10.0,
    'str_methods': 10.0,
    'matrix_multiply': 10.0,
    'mypy_self_check': 1.5,
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


def normalize_data(data: BenchmarkData, current_py: str, current_hw: str) -> None:
    """Normalize results collected on old configuration to the current config.

    Also remove duplicate items.

    This changes data in-place!
    """
    # TODO: If there are scaling items from C1 to C2 and C2 to C3, support calculating
    #       scaling item from C1 to C3.
    current_py = '.'.join(current_py.split('.')[:2])
    for bm, runs in data.runs.items():
        scaling = data.scaling.get(bm)
        if scaling is None:
            # No scaling information available
            continue
        scaling = add_inferred_scaling_items(scaling)
        seen_commits = set()
        new_runs = []
        for run in runs:
            if run.mypy_commit in seen_commits:
                continue
            seen_commits.add(run.mypy_commit)
            for scale_item in scaling:
                if (run.hardware_id == scale_item.old_hardware_id
                        and run.python_version.startswith(scale_item.old_python_version)
                        and scale_item.new_hardware_id == current_hw
                        and scale_item.new_python_version == current_py):
                    run = DataItem(benchmark=run.benchmark,
                                   timestamp=run.timestamp,
                                   runtime=run.runtime / scale_item.factor,
                                   stdev_percent=run.stdev_percent,
                                   mypy_commit=run.mypy_commit,
                                   benchmark_commit=run.benchmark_commit,
                                   python_version=run.python_version,
                                   hardware_id=run.hardware_id,
                                   os_version=run.os_version)
                    break
            new_runs.append(run)
        runs[:] = new_runs


def add_inferred_scaling_items(items: List[ScalingItem]) -> List[ScalingItem]:
    pairs = set()
    for item in items:
        pairs.add((item.old_hardware_id, item.old_python_version,
                   item.new_hardware_id, item.new_python_version))
    old_configs = []
    for item in items:
        old = (item.old_hardware_id, item.old_python_version)
        if old not in old_configs:
            old_configs.append(old)

    new_config = None
    for item in items:
        new = (item.new_hardware_id, item.new_python_version)
        if new not in old_configs:
            assert new_config is None, "couldn't determine unique newest config"
            new_config = new

    assert new_config is not None, "couldn't determine newest config"
    inferred_items = []
    for item in items:
        t = (item.old_hardware_id, item.old_python_version,
             new_config[0], new_config[1])
        if t not in pairs:
            inferred_item = infer_scaling_item(
                items, item.old_hardware_id, item.old_python_version,
                new_config[0], new_config[1],
            )
            inferred_items.append(inferred_item)
            pairs.add(t)

    return items + inferred_items


def infer_scaling_item(items: List[ScalingItem],
                       old_hw: str,
                       old_py: str,
                       new_hw: str,
                       new_py: str) -> ScalingItem:
    for item in items:
        if item.old_hardware_id == old_hw and item.old_python_version == old_py:
            if item.new_hardware_id == new_hw and item.new_python_version == new_py:
                return item
            first = infer_scaling_item(items, old_hw, old_py,
                                       item.new_hardware_id, item.new_python_version)
            second = infer_scaling_item(items, item.new_hardware_id, item.new_python_version,
                                        new_hw, new_py)
            return ScalingItem(first.factor * second.factor, old_hw, old_py, new_hw, new_py)
    raise RuntimeError("could not find scaling from {old_hw}/{old_py} to {new_hw}/{new_py}")

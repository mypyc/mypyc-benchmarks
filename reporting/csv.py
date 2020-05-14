from typing import NamedTuple, List
from datetime import datetime
import os
import sys

from reporting.common import get_hardware_id, get_os_version, get_c_compiler_version, CC


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
    benchmark = fnam.split('.')[0]
    benchmark = os.path.basename(benchmark)
    benchmark, _, _ = benchmark.partition('-cpython')
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

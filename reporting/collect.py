from typing import Tuple
from datetime import datetime
import argparse
import os
import subprocess
import sys

from reporting.gitutil import get_commit_range, checkout_commit, get_current_commit
from reporting.common import get_csv_path, get_hardware_id, get_os_version, get_c_compiler_version


# Use clang since it tends to generate faster code.
CC = "clang"


def write_csv_header(fnam: str) -> None:
    with open(fnam, "w") as f:
        f.write("Timestamp,Runtime (s),Runtime (stddev),Mypy commit," +
                "Benchmark commit,Python version,Hardware,OS,C compiler\n")


def write_csv_line(fnam: str,
                   benchmark: str,
                   timestamp: datetime,
                   runtime: float,
                   stddev: float,
                   mypy_commit: str,
                   benchmark_commit: str) -> None:
    if not os.path.exists(fnam):
        write_csv_header(fnam)
    with open(fnam, "a") as f:
        f.write("%s,%.6f,%.6f,%s,%s,%s,%s,%s,%s\n" % (
            timestamp,
            runtime,
            stddev,
            mypy_commit,
            benchmark_commit,
            sys.version.split()[0],
            get_hardware_id(),
            get_os_version(),
            '%s %s' % (CC, get_c_compiler_version(CC)),
        ))


def run_bench(benchmark: str, mypy_repo: str) -> Tuple[float, float]:
    """Run benchmark in compiled and interpreted modes.

    Return (relative speed of compiled, % standard deviation of compiled runtimes).
    """
    env = os.environ.copy()
    env['PYTHONPATH'] = mypy_repo
    env['CC'] = CC
    output = subprocess.check_output(
        ['python', 'runbench.py', '--raw', benchmark], env=env).decode("ascii")
    last_line = output.rstrip().splitlines()[-1]
    fields = last_line.split()
    return float(fields[0]), 100.0 * float(fields[5]) / float(fields[4])


def sync_typeshed(mypy_repo: str) -> None:
    subprocess.check_call(['git', 'submodule', 'update'], cwd=mypy_repo)


def install_mypy_deps(mypy_repo: str) -> None:
    subprocess.check_call(
        ['pip', 'install', '--quiet', '--disable-pip-version-check',
         '-r', 'mypy-requirements.txt'], cwd=mypy_repo)


def parse_args() -> Tuple[str, str, str, str, str]:
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark")
    parser.add_argument("mypy_repo")
    parser.add_argument("data_repo")
    parser.add_argument("start_commit")
    parser.add_argument("end_commit")
    args = parser.parse_args()
    return args.benchmark, args.mypy_repo, args.data_repo, args.start_commit, args.end_commit


def main() -> None:
    benchmark, mypy_repo, data_repo, start_commit, end_commit = parse_args()
    mypy_commits = get_commit_range(mypy_repo, start_commit, end_commit)
    if not mypy_commits:
        sys.exit("Could not find any commits")
    benchmark_commit = get_current_commit(".")
    for mypy_commit in mypy_commits:
        now = datetime.utcnow()
        checkout_commit(mypy_repo, mypy_commit)
        sync_typeshed(mypy_repo)
        install_mypy_deps(mypy_repo)
        runtime, stddev = run_bench(benchmark, mypy_repo)
        fnam = get_csv_path(data_repo, benchmark)
        write_csv_line(fnam, benchmark, now, runtime, stddev, mypy_commit, benchmark_commit)


if __name__ == "__main__":
    main()

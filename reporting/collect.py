"""Utility that collects mypyc benchmark results for a range of commits.

Run "python3 -m reporting.collect --help" for more information.
"""

from typing import Optional, Tuple
from datetime import datetime
import argparse
import os
import subprocess
import sys

from reporting.gitutil import get_commit_range, checkout_commit, get_current_commit
from reporting.common import get_csv_path, get_hardware_id, get_os_version, get_c_compiler_version


# Use clang since it tends to generate faster code.
CC = "clang"

# Minimum number of iterations for an interpreted benchmark (this needs to be high,
# since interpreted measurements are noisier than compiled)
MIN_INTERPRETED_ITER = 200


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


def run_bench(benchmark: str,
              mypy_repo: Optional[str],
              compiled: bool = True) -> Tuple[float, float]:
    """Run benchmark (in compiled or interpreted mode).

    Return (time per iteration, % standard deviation).
    """
    env = os.environ.copy()
    if mypy_repo:
        env['PYTHONPATH'] = mypy_repo
    if compiled:
        env['CC'] = CC
    cmd = ['python', 'runbench.py', '--raw']
    if compiled:
        cmd.append('-c')
    else:
        cmd.extend(['-i', '--min-iter', str(MIN_INTERPRETED_ITER)])
    cmd.append(benchmark)
    output = subprocess.check_output(cmd, env=env).decode("ascii")
    last_line = output.rstrip().splitlines()[-1]
    fields = last_line.split()
    if compiled:
        return float(fields[3]), 100.0 * float(fields[4]) / float(fields[3])
    else:
        return float(fields[1]), 100.0 * float(fields[2]) / float(fields[1])


def sync_typeshed(mypy_repo: str) -> None:
    subprocess.check_call(['git', 'submodule', 'update'], cwd=mypy_repo)


def install_mypy_deps(mypy_repo: str) -> None:
    subprocess.check_call(
        ['pip', 'install', '--quiet', '--disable-pip-version-check',
         '-r', 'mypy-requirements.txt'], cwd=mypy_repo)


def parse_args() -> Tuple[str, str, str, str, str]:
    parser = argparse.ArgumentParser(
        description="""Run a mypyc benchmark for a range of commits, and append results to a .csv
                       file at the path '<data_repo>/data/<benchmark>.csv'. Note that this
                       will check out the commits in the target mypy repository, and this
                       will also install mypy dependencies in the current virtualenv!""")
    parser.add_argument(
        "benchmark",
        help="""benchmark name, such as 'richards' (use 'runbench.py --list' to show valid
                values)""")
    parser.add_argument("mypy_repo", help="target mypy repository (this will be modified!)")
    parser.add_argument(
        "data_repo",
        help="target data repository where output will be written (this will be modified!)")
    parser.add_argument("start_commit", help="commits reachable from here are skipped")
    parser.add_argument("end_commit", help="final commit to include")
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

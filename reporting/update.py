"""Update benchmark data and reports.

Run like this:

  $ python3 -m reporting.update <mypy_repo> <results_repo>

This does several things:

* Pull repos.
* Collect interpreted baselines for any new benchmarks.
* Run compiled benchmarks against any new commits.
* Generate reports.
* Commit new data and reports.
* Push repos.
"""

from typing import List, Tuple
from datetime import datetime
import argparse
import os
import subprocess
import sys

from reporting.common import DATA_DIR, REPORTS_DIR
from reporting.gitutil import pull_repo, push_repo, git_commit, get_commit_range
from reporting.data import get_benchmark_names, load_data


benchmarks_repo = os.path.dirname(os.path.dirname(__file__))

# If True, don't modify file system
dry_run = False


def log(*args: object) -> None:
    print('[%s]' % datetime.utcnow(), *args)
    sys.stdout.flush()


def heading(*args: object) -> None:
    log()
    log('====', *args, '====')
    log()


def run(cmd: List[str], cwd: str) -> int:
    if not dry_run:
        return subprocess.check_call(cmd, cwd=cwd)
    else:
        if os.path.abspath(cwd) != os.getcwd():
            print('> cd %s' % cwd)
        print('> ' + ' '.join(cmd))
        sys.stdout.flush()
        return 0


def pull_repos(repos: List[str]) -> None:
    for repo in repos:
        heading('Pulling %s' % repo)
        if not dry_run:
            pull_repo(repo)


def baseline_csv_path(data_repo: str, benchmark: str) -> str:
    return os.path.join(data_repo, DATA_DIR, '%s-cpython.csv' % benchmark)


def compiled_csv_path(data_repo: str, benchmark: str) -> str:
    return os.path.join(data_repo, DATA_DIR, '%s.csv' % benchmark)


def collect_new_baselines(data_repo: str) -> List[str]:
    """Collect interpreted baseline measurements for all new benchmarks.

    Return list of new benchmark names
    """
    result = []
    heading('Looking for new benchmarks')
    benchmarks = get_benchmark_names()
    if not benchmarks:
        log('No new benchmarks found')
    else:
        log('Found %d new benchmarks without baseline data:' % len(benchmarks))
        for benchmark in benchmarks:
            log(' * %s' % benchmark)
    for benchmark in benchmarks:
        baseline_fnam = baseline_csv_path(data_repo, benchmark)
        if not os.path.isfile(baseline_fnam):
            heading('Collecting baseline for new benchmark "%s"' % benchmark)
            cmd = ['python', '-m', 'reporting.collect_baseline', benchmark, data_repo]
            run(cmd, cwd=benchmarks_repo)
            if not dry_run:
                assert os.path.isfile(baseline_fnam)
            result.append(benchmark)
    return result


def run_compiled_benchmarks(mypy_repo: str, data_repo: str) -> None:
    benchmarks = get_benchmark_names()
    heading('Determining new commits')
    commits = get_commits_without_results(mypy_repo, data_repo)
    log('Found %d commits without results:' % len(commits))
    for commit in commits:
        log(' * %s' % commit)
    for commit in commits:
        heading('Running benchmarks against mypy commit %s' % commit)
        for benchmark in benchmarks:
            run_benchmark(commit, benchmark, mypy_repo, data_repo)


def get_commits_without_results(mypy_repo: str, data_repo: str) -> List[str]:
    commits = get_commit_range(mypy_repo, 'HEAD~30', 'HEAD')
    data = load_data(mypy_repo, data_repo)
    seen = set()
    for items in data.runs.values():
        for item in items:
            seen.add(item.mypy_commit)
    return sorted(set(commits) - seen)


def run_benchmark(commit: str, benchmark: str, mypy_repo: str, data_repo: str) -> None:
    log('Running benchmark "%s" against mypy commit %s' % (benchmark, commit))
    cmd = ['python', '-m', 'reporting.collect',
           benchmark, mypy_repo, data_repo, '%s~1' % commit, commit]
    run(cmd, cwd=benchmarks_repo)


def generate_reports(mypy_repo: str, data_repo: str) -> None:
    heading('Generating reports')
    run(['python', '-m', 'reporting.genreports', mypy_repo, data_repo], cwd=benchmarks_repo)


def commit(data_repo: str, new_benchmarks: List[str]) -> None:
    heading('Committing changes to data and reports')
    for benchmark in new_benchmarks:
        log('Git add csv data files for "%s"' % benchmark)
        run(['git', 'add', baseline_csv_path(data_repo, benchmark)], cwd=data_repo)
        run(['git', 'add', compiled_csv_path(data_repo, benchmark)], cwd=data_repo)
    log('Committing changes to repository')
    if not dry_run:
        git_commit(data_repo, [DATA_DIR, REPORTS_DIR], 'Update benchmark data and reports')


def push_repos(repos: List[str]) -> None:
    for repo in repos:
        if not dry_run:
            push_repo(repo)


def parse_args() -> Tuple[str, str, bool, bool]:
    parser = argparse.ArgumentParser(
        description="""Update mypyc benchmark data and reports based on recent commits.
                       Collect benchmark timings for new mypy commits. Collect baselines
                       for new benchmarks. Also pull and push repositories by default.""")
    parser.add_argument("mypy_repo",
                        help="target mypy repository (used to look up information on commits)")
    parser.add_argument(
        "data_repo",
        help="""target repository where input data resides and output will be written
                (this will be modified!)""")
    parser.add_argument(
        "--dry-run", action='store_true',
        help="simulate a run without changing the file system or running benchmarks")
    parser.add_argument(
        "--no-git", action='store_true',
        help="don't pull git repos or commit changed or created files")
    args = parser.parse_args()
    return args.mypy_repo, args.data_repo, args.dry_run, args.no_git


def main() -> None:
    global dry_run
    mypy_repo, data_repo, dry_run, no_git = parse_args()

    if not no_git:
        # Pull latest mypyc, benchmarks and benchmark scripts.
        pull_repos([mypy_repo, benchmarks_repo])

    # Collect baseline interpreted measurements for any new benchmarks.
    new_benchmarks = collect_new_baselines(data_repo)

    run_compiled_benchmarks(mypy_repo, data_repo)

    generate_reports(mypy_repo, data_repo)

    if not no_git:
        commit(data_repo, new_benchmarks )

        heading('Pushing %s' % data_repo)
        if not dry_run:
            push_repo(data_repo)


if __name__ == '__main__':
    main()

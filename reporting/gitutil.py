from typing import List, Dict, Tuple
import subprocess
from datetime import datetime


def checkout_commit(repo_dir: str, commit: str) -> None:
    subprocess.check_call(['git', 'checkout', commit], cwd=repo_dir)


def get_commit_range(repo_dir: str, start_commit: str, end_commit: str) -> List[str]:
    """Return commits reachable from end_commit but not from start_commit."""
    output = subprocess.check_output(
        ['git', 'log', '%s..%s' % (start_commit, end_commit)], cwd=repo_dir).decode("utf-8")
    commits = []
    for line in output.splitlines():
        if line.startswith('commit '):
            commits.append(line.split()[1])
    return commits


def get_current_commit(repo_dir: str) -> str:
    output = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir)
    return output.decode("ascii").strip()


def commit_changed_paths(repo_dir: str, commit: str) -> List[str]:
    # --numstat: show per-file statistics in machine-readable format
    # --oneline: show summary in one line (easy to skip)
    cmd = ['git', 'show', '--numstat', '--oneline', commit]
    output = subprocess.check_output(cmd, cwd=repo_dir).decode("ascii")
    lines = output.splitlines()[1:]
    lines = [line for line in lines if line]
    return [line.split()[2] for line in lines]


def filter_commits_by_path(repo_dir: str, commits: List[str], prefix: str) -> List[str]:
    result = []
    for commit in commits:
        paths = commit_changed_paths(repo_dir, commit)
        if any(path.startswith(prefix) for path in paths):
            result.append(commit)
    return result


def get_commit_times(repo_dir: str, commits: List[str]) -> Dict[str, Tuple[str, str]]:
    cmd = ['git', 'show', '--numstat', '--date=unix'] + commits
    output = subprocess.check_output(cmd, cwd=repo_dir).decode("ascii")
    result = {}
    for line in output.splitlines():
        if line.startswith('commit '):
            commit = line.split()[1]
        if line.startswith('Date: '):
            timestamp = int(line.split()[1])
            dt = datetime.utcfromtimestamp(timestamp)
            d, t = dt.isoformat().split('T')
            result[commit] = (d, t)
    return result

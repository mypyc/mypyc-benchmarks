from typing import List
import re
import subprocess


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

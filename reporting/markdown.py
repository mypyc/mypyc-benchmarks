"""Utilities for generation markdown."""


def mypy_commit_link(commit: str) -> str:
    url = 'https://github.com/python/mypy/commit/%s' % commit
    return '[%s](%s)' % (commit[:12], url)


def bold(s: str) -> str:
    if not s:
        return s
    return '**%s**' % s

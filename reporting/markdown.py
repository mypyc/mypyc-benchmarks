"""Utilities for generation markdown."""

from reporting.common import BENCHMARKS_DIR


def mypy_commit_link(commit: str) -> str:
    url = 'https://github.com/python/mypy/commit/%s' % commit
    return '[%s](%s)' % (commit[:12], url)


def benchmark_link(benchmark: str, link_name: str = '') -> str:
    link_name = link_name or benchmark
    return '[%s](%s/%s.md)' % (link_name, BENCHMARKS_DIR, benchmark)


def bold(s: str) -> str:
    if not s:
        return s
    return '**%s**' % s

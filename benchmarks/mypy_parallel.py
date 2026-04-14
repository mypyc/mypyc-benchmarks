"""Mypy parallel benchmark.

Run mypy with --num-workers=4 on a synthetic 5000-file codebase with
a cold cache. The codebase is split into 100 packages of 50 files each.
Every group of 10 files forms a linear import chain; groups are otherwise
independent, so there is a lot of room for parallelism.

Each file is relatively small, so the impact of per-file overhead,
including synchronization overhead, is emphasized.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from benchmarking import benchmark
from benchmarks.mypy_self_check import VENV_DIR, prepare

TMPDIR = 'mypy-parallel.tmpdir'
MYPY_BIN = os.path.abspath(os.path.join(VENV_DIR, 'bin', 'mypy'))
SRC_DIR = os.path.join(TMPDIR, 'src')

NUM_PACKAGES = 100
NUM_FILES_PER_PACKAGE = 50
CHAIN_LENGTH = 10

STDLIB_IMPORTS = [
    'os',
    'sys',
    'collections',
    'typing',
    'io',
    'pathlib',
    'json',
    're',
    'functools',
    'itertools',
]


def log(s: str) -> None:
    sys.stderr.write(f'{s}\n')
    sys.stderr.flush()


def get_clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.pop('MYPYPATH', None)
    return env


def generate_module_source(pkg_index: int, file_index: int) -> str:
    """Generate realistic-looking source for one module."""
    pkg = f'pkg_{pkg_index:03d}'
    lines: list[str] = ['from __future__ import annotations\n']

    # 3 stdlib imports, varied per file
    for i in range(3):
        mod = STDLIB_IMPORTS[(pkg_index + file_index + i) % len(STDLIB_IMPORTS)]
        lines.append(f'import {mod}')

    # Import predecessor in the chain (groups of CHAIN_LENGTH form a chain)
    chain_pos = file_index % CHAIN_LENGTH
    if chain_pos > 0:
        prev = f'mod_{file_index - 1:03d}'
        lines.append(f'from {pkg} import {prev}')

    lines.append('')
    lines.append('')

    # A constant
    lines.append(f'VERSION = {pkg_index * 1000 + file_index}')
    lines.append('')
    lines.append('')

    # A data class-like class
    cls_name = f'Record_{file_index:03d}'
    lines.append(f'class {cls_name}:')
    lines.append(f'    label: str')
    lines.append(f'    value: int')
    lines.append(f'    active: bool')
    lines.append('')
    lines.append(f'    def __init__(self, label: str, value: int, active: bool = True) -> None:')
    lines.append(f'        self.label = label')
    lines.append(f'        self.value = value')
    lines.append(f'        self.active = active')
    lines.append('')
    lines.append(f'    def summarize(self) -> str:')
    lines.append(f'        status = "on" if self.active else "off"')
    lines.append(f'        return f"{{self.label}}: {{self.value}} ({{status}})"')
    lines.append('')
    lines.append(f'    def double_value(self) -> int:')
    lines.append(f'        return self.value * 2')
    lines.append('')
    lines.append('')

    # A standalone function
    fn_name = f'process_{file_index:03d}'
    lines.append(f'def {fn_name}(items: list[{cls_name}], threshold: int) -> list[str]:')
    lines.append(f'    results: list[str] = []')
    lines.append(f'    for item in items:')
    lines.append(f'        if item.active and item.value > threshold:')
    lines.append(f'            results.append(item.summarize())')
    lines.append(f'    return results')
    lines.append('')
    lines.append('')

    # A helper function
    lines.append(f'def make_{fn_name}(n: int) -> list[{cls_name}]:')
    lines.append(f'    return [{cls_name}(f"item_{{i}}", i) for i in range(n)]')
    lines.append('')

    # Reference predecessor if in a chain
    if chain_pos > 0:
        prev_cls = f'Record_{file_index - 1:03d}'
        lines.append('')
        lines.append(f'def convert(old: {prev}.{prev_cls}) -> {cls_name}:')
        lines.append(f'    return {cls_name}(old.label, old.value, old.active)')
        lines.append('')

    return '\n'.join(lines)


def package_globs() -> list[str]:
    """Return the 100 per-package glob arguments for mypy."""
    return [f'pkg_{i:03d}/' for i in range(NUM_PACKAGES)]


def generate_codebase() -> None:
    """Generate the synthetic 10,000-file codebase."""
    if os.path.isdir(SRC_DIR):
        shutil.rmtree(SRC_DIR)

    total = 0
    for pkg_index in range(NUM_PACKAGES):
        pkg = f'pkg_{pkg_index:03d}'
        pkg_dir = os.path.join(SRC_DIR, pkg)
        os.makedirs(pkg_dir, exist_ok=True)

        with open(os.path.join(pkg_dir, '__init__.py'), 'w') as f:
            f.write('')

        for file_index in range(NUM_FILES_PER_PACKAGE):
            mod_name = f'mod_{file_index:03d}.py'
            path = os.path.join(pkg_dir, mod_name)
            with open(path, 'w') as f:
                f.write(generate_module_source(pkg_index, file_index))
            total += 1

    log(f'generated {total} source files in {NUM_PACKAGES} packages')


def run_mypy() -> None:
    env = get_clean_env()
    args = [MYPY_BIN, '--no-error-summary', '--show-traceback', '--num-workers', '4'] + package_globs()
    result = subprocess.run(
        args,
        cwd=SRC_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f'mypy failed:\n{result.stdout}\n{result.stderr}'
        )


def prepare_codebase(mypy_repo: str | None) -> None:
    os.makedirs(TMPDIR, exist_ok=True)
    generate_codebase()


@benchmark(
    prepare=[prepare, prepare_codebase],
    compiled_only=True,
    min_iterations=30,
    strip_outlier_runs=True,
    stable_hash_seed=True,
)
def mypy_parallel() -> None:
    cache_dir = os.path.join(SRC_DIR, '.mypy_cache')
    if os.path.isdir(cache_dir):
        shutil.rmtree(cache_dir)
    run_mypy()

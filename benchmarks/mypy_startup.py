"""Mypy startup benchmark.

Run mypy incrementally on a trivial single-file program with a warm
cache.  This measures mypy's baseline startup and shutdown overhead,
which includes the overhead of importing mypy implementation modules
and their dependencies, and the processing overhead of the cached
builtins import cycle, with almost no real type checking work.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

from benchmarking import benchmark
from benchmarks.mypy_self_check import VENV_DIR, prepare

TMPDIR = 'mypy-startup.tmpdir'
MYPY_BIN = os.path.abspath(os.path.join(VENV_DIR, 'bin', 'mypy'))
SRC_FILE = os.path.join(TMPDIR, 'main.py')
CONFIG_FILE = os.path.join(TMPDIR, 'mypy.ini')


def log(s: str) -> None:
    sys.stderr.write(f'{s}\n')
    sys.stderr.flush()


def get_clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.pop('MYPYPATH', None)
    return env


def write_src_file() -> None:
    with open(SRC_FILE, 'w') as f:
        # Make the contents of the file vary between runs, to that this
        # file and builtins have to be processed on each run.
        f.write(f'print("{time.time()}")\n')


def run_mypy() -> None:
    env = get_clean_env()
    result = subprocess.run(
        [MYPY_BIN, '--no-error-summary', '--config-file', os.path.abspath(CONFIG_FILE),
         os.path.abspath(SRC_FILE)],
        cwd=TMPDIR,
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

    with open(CONFIG_FILE, 'w') as f:
        f.write('[mypy]\nsqlite_cache = True\n')

    write_src_file()

    log('running mypy to create warm cache')
    run_mypy()
    log('warm cache ready')


@benchmark(
    prepare=[prepare, prepare_codebase],
    compiled_only=True,
    min_iterations=50,
    strip_outlier_runs=True,
    stable_hash_seed=True,
)
def mypy_startup() -> None:
    write_src_file()
    run_mypy()

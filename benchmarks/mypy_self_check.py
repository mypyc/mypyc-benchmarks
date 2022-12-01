"""Mypy self check benchmark.

Type check a vendored (fixed) copy of mypy using the version of mypy
being benchmarked, compiled using the version of mypyc being benchmarked.

This can be used to track changes in both the performance of mypy and mypyc.

Note that it may be necessary to occasionally make tweaks to the vendored
copy, in case it starts generating many errors, etc.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from benchmarking import benchmark

# Create virtualenv and local mypy repo clone here
TMPDIR = 'mypy-self-check.tmpdir'

VENV_DIR = os.path.join(TMPDIR, 'venv')

VENV_PYTHON = os.path.abspath(os.path.join(VENV_DIR, 'bin', 'python'))

MYPY_CLONE = os.path.join(TMPDIR, 'mypy')

# PEP 561 requirements for type checking (pinned for consistent runtimes)
CHECK_REQUIREMENTS = [
    "attrs==22.1.0",
    "filelock==3.8.0",
    "iniconfig==1.1.1",
    "packaging==21.3",
    "pluggy==1.0.0",
    "pyparsing==3.0.9",
    "pytest==7.2.0",
    "tomli==2.0.1",
    "types-psutil==5.9.5.5",
]


def prepare(mypy_repo: str | None) -> None:
    assert mypy_repo
    assert os.path.isdir(mypy_repo)
    assert os.path.isdir(os.path.join(mypy_repo, '.git'))

    if os.path.isdir(TMPDIR):
        shutil.rmtree(TMPDIR)

    print(f'creating venv in {os.path.abspath(VENV_DIR)}')
    subprocess.run([sys.executable, '-m', 'venv', VENV_DIR], check=True)

    print('installing build dependencies')
    pip = os.path.join(VENV_DIR, 'bin', 'pip')
    reqs = os.path.join(mypy_repo, 'build-requirements.txt')
    subprocess.run([pip, 'install', '-r', reqs], check=True)

    print('cloning mypy')
    subprocess.run(['git', 'clone', mypy_repo, MYPY_CLONE], check=True)

    print('building and installing mypy')
    env = os.environ.copy()
    env["CC"] = "clang"
    # Use -O2 since it's a bit faster to compile. The runtimes might be also be more
    # predictable than with -O3, but that's just a hypothesis.
    env["MYPYC_OPT_LEVEL"] = "2"
    if "PYTHONPATH" in env:
        del env["PYTHONPATH"]
    if "MYPYPATH" in env:
        del env["MYPYPATH"]
    subprocess.run(
        [VENV_PYTHON, 'setup.py', '--use-mypyc', 'install'],
        cwd=MYPY_CLONE,
        check=True,
        env=env,
    )

    print('verifying that we can run mypy')
    out = subprocess.run([os.path.join(VENV_DIR, 'bin', 'mypy'), '--version'], capture_output=True,
                         text=True, check=True, env=env)
    assert 'compiled: no' not in out.stdout

    print('installing dependencies for type checking')
    subprocess.run([VENV_PYTHON, '-m', 'pip', 'install'] + CHECK_REQUIREMENTS, check=True, env=env)

    print('successfully installed compiled mypy')


@benchmark(
    prepare=prepare,
    compiled_only=True,
    min_iterations=25,
    strip_outlier_runs=False,
    stable_hash_seed=True,
)
def mypy_self_check() -> None:
    assert os.path.isdir('vendor')
    if os.path.isdir('.mypy_cache'):
        shutil.rmtree('.mypy_cache')
    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        del env['PYTHONPATH']
    if 'MYPYPATH' in env:
        del env['MYPYPATH']
    subprocess.run(
        [
            os.path.join(VENV_DIR, 'bin', 'mypy'),
            '--config-file',
            'vendor/mypy/mypy_self_check.ini',
            'vendor/mypy/mypy',
        ],
        env=env,
    )

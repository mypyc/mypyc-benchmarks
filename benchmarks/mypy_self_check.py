"""Mypy self check benchmark.

Type check a vendored (fixed) copy of mypy using the version of mypy
being benchmarked, compiled using the version of mypyc being benchmarked.

This can be used to track changes in both the performance of mypy and mypyc.

Note that it may be necessary to occasionally make tweaks to the vendored
copy, in case it starts generating many errors, etc.
"""

from __future__ import annotations

import os
import re
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


def log(s: str) -> None:
    sys.stderr.write(f'{s}\n')
    sys.stderr.flush()


def get_mypy_repo_commit(mypy_repo: str) -> str:
    result = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        cwd=mypy_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_installed_mypy_version(env: dict[str, str] | None = None) -> str | None:
    """Run mypy --version and return the output, or None on failure."""
    mypy_bin = os.path.join(VENV_DIR, 'bin', 'mypy')
    if env is None:
        env = os.environ.copy()
        env.pop('PYTHONPATH', None)
        env.pop('MYPYPATH', None)
    try:
        out = subprocess.run(
            [mypy_bin, '--version'],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip()


def is_cached_build_valid(mypy_repo: str) -> bool:
    """Check if there's an existing compiled mypy matching the current repo commit."""
    version_str = get_installed_mypy_version()
    if version_str is None:
        return False
    if 'compiled: no' in version_str:
        return False
    # Extract the commit hash baked into the compiled version string.
    # Example: "mypy 1.20.0+dev.00b5064fd... (compiled: yes)"
    m = re.search(r'\+dev\.([0-9a-f]+)', version_str)
    if not m:
        return False
    installed_commit = m.group(1)
    repo_commit = get_mypy_repo_commit(mypy_repo)
    return repo_commit.startswith(installed_commit) or installed_commit.startswith(repo_commit)


def prepare(mypy_repo: str | None) -> None:
    assert mypy_repo
    assert os.path.isdir(mypy_repo)
    assert os.path.isdir(os.path.join(mypy_repo, '.git'))

    if is_cached_build_valid(mypy_repo):
        log('reusing cached compiled mypy build')
        return

    if os.path.isdir(TMPDIR):
        shutil.rmtree(TMPDIR)

    log(f'creating venv in {os.path.abspath(VENV_DIR)}')
    subprocess.run([sys.executable, '-m', 'venv', VENV_DIR], check=True)

    log('installing build dependencies')
    pip = os.path.join(VENV_DIR, 'bin', 'pip')
    subprocess.run([pip, 'install', '-U', 'pip'], check=True)

    # TODO: Remove if/when setuptools is added to build-requirements.txt
    subprocess.run([pip, 'install', '-U', 'setuptools'], check=True)

    reqs = os.path.join(mypy_repo, 'build-requirements.txt')
    subprocess.run([pip, 'install', '-r', reqs], check=True)

    log('cloning mypy')
    subprocess.run(['git', 'clone', mypy_repo, MYPY_CLONE], check=True)

    log('building and installing mypy')
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

    log('verifying that we can run mypy')
    out = subprocess.run([os.path.join(VENV_DIR, 'bin', 'mypy'), '--version'], capture_output=True,
                         text=True, check=True, env=env)
    assert 'compiled: no' not in out.stdout

    log('installing dependencies for type checking')
    subprocess.run([VENV_PYTHON, '-m', 'pip', 'install'] + CHECK_REQUIREMENTS, check=True, env=env)

    log('successfully installed compiled mypy')


@benchmark(
    prepare=prepare,
    compiled_only=True,
    min_iterations=30,
    strip_outlier_runs=True,
    stable_hash_seed=True,
)
def mypy_self_check() -> None:
    assert os.path.isdir('vendor')
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
            '--no-incremental',
            'vendor/mypy/mypy',
        ],
        env=env,
    )

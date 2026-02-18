"""Mypy incremental benchmark with mostly fresh cache and many files.

This mostly measures per-file overhead of processing meta cache files, ordering
the build, identifying modified files, constructing SCCs, etc.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time

from benchmarking import benchmark
from benchmarks.mypy_self_check import VENV_DIR, prepare

# Directory for the synthetic codebase
TMPDIR = 'mypy-fresh-incremental.tmpdir'


def log(s: str) -> None:
    sys.stderr.write(f'{s}\n')
    sys.stderr.flush()


NUM_TOP_PACKAGES = 40
NUM_SUB_PACKAGES = 50
NUM_MODULES_PER_SUB_PACKAGE = 10

STDLIB_MODULES = [
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

NUM_STDLIB_IMPORTS = 5
NUM_LOCAL_IMPORTS = 5
# Every CHAIN_STEP'th module imports the module CHAIN_STEP positions earlier,
# creating a linear import chain of length ~NUM_LEAF_MODULES / CHAIN_STEP.
CHAIN_STEP = 200

# Simulate missing third-party imports (with "# type: ignore") in 4% of files.
MISSING_MODULES = [
    'external_service_client',
    'legacy_data_processor',
    'vendor_api.wrapper',
    'custom_logging_handler',
    'internal_metrics.collector',
    'database_migration_tool',
    'async_task.scheduler',
    'config_schema_validator',
    'network_protocol.handler',
    'binary_format_parser',
    'cloud_storage.backend',
]
MISSING_IMPORT_INTERVAL = 25  # every 25th leaf module (~4%)

MYPY_BIN = os.path.abspath(os.path.join(VENV_DIR, 'bin', 'mypy'))
SRC_DIR = os.path.join(TMPDIR, 'src')
CONFIG_FILE = os.path.join(TMPDIR, 'fresh_incremental_mypy.ini')

NUM_MODULE_OVERRIDES = 30
NUM_PACKAGE_OVERRIDES = 30


def get_file_list() -> list[tuple[str, str]]:
    """Return (file_path, module_id) pairs for all modules in the synthetic codebase."""
    files: list[tuple[str, str]] = []
    for i in range(NUM_TOP_PACKAGES):
        top_pkg = f'top_level_package_{i}'
        top_dir = os.path.join(SRC_DIR, top_pkg)
        files.append((os.path.join(top_dir, '__init__.py'), top_pkg))
        for j in range(NUM_SUB_PACKAGES):
            sub_name = f'nested_subpackage_{j}'
            sub_pkg = f'{top_pkg}.{sub_name}'
            sub_dir = os.path.join(top_dir, sub_name)
            files.append((os.path.join(sub_dir, '__init__.py'), sub_pkg))
            for k in range(NUM_MODULES_PER_SUB_PACKAGE):
                mod_name = f'leaf_module_impl_{k}'
                path = os.path.join(sub_dir, f'{mod_name}.py')
                module_id = f'{sub_pkg}.{mod_name}'
                files.append((path, module_id))
    return files


def get_leaf_modules(
    files: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Return only the leaf modules (not __init__.py) from the file list."""
    return [(path, mod) for path, mod in files if not path.endswith('__init__.py')]


_all_files: list[tuple[str, str]] | None = None
_leaf_modules: list[tuple[str, str]] | None = None


def all_files() -> list[tuple[str, str]]:
    global _all_files
    if _all_files is None:
        _all_files = get_file_list()
    return _all_files


def leaf_modules() -> list[tuple[str, str]]:
    global _leaf_modules
    if _leaf_modules is None:
        _leaf_modules = get_leaf_modules(all_files())
    return _leaf_modules


def get_clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.pop('MYPYPATH', None)
    return env


def generate_config(leaf_modules: list[tuple[str, str]]) -> None:
    """Generate a mypy config file with per-module and per-package overrides."""
    lines = ['[mypy]\nsqlite_cache = True\n']

    # 30 sections targeting individual modules, spread across the file list.
    stride = len(leaf_modules) // NUM_MODULE_OVERRIDES
    for i in range(NUM_MODULE_OVERRIDES):
        module_id = leaf_modules[i * stride][1]
        lines.append(f'[mypy-{module_id}]\n')
        lines.append('strict_equality = True\n')

    # 30 sections targeting all modules within a subpackage using .* wildcard.
    seen: set[str] = set()
    pkg_stride = (NUM_TOP_PACKAGES * NUM_SUB_PACKAGES) // NUM_PACKAGE_OVERRIDES
    for i in range(NUM_PACKAGE_OVERRIDES):
        idx = i * pkg_stride
        top_idx = idx // NUM_SUB_PACKAGES
        sub_idx = idx % NUM_SUB_PACKAGES
        sub_pkg = f'top_level_package_{top_idx}.nested_subpackage_{sub_idx}'
        if sub_pkg not in seen:
            seen.add(sub_pkg)
            lines.append(f'[mypy-{sub_pkg}.*]\n')
            lines.append('strict_equality = True\n')

    with open(CONFIG_FILE, 'w') as f:
        f.writelines(lines)


def prepare_codebase(mypy_repo: str | None) -> None:
    files = all_files()
    leaves = leaf_modules()

    if os.path.isdir(TMPDIR):
        shutil.rmtree(TMPDIR)
    os.makedirs(TMPDIR, exist_ok=True)

    generate_config(leaves)

    log(f'generating synthetic codebase with {len(files)} files')
    leaf_index = 0
    for path, module_id in files:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if path.endswith('__init__.py'):
            with open(path, 'w') as f:
                f.write('')
        else:
            # Pick 5 stdlib modules based on the leaf index.
            imports = ''
            for n in range(NUM_STDLIB_IMPORTS):
                mod = STDLIB_MODULES[(leaf_index + n) % len(STDLIB_MODULES)]
                imports += f'import {mod}\n'

            # Import 5 earlier leaf modules (skip for the first few modules).
            if leaf_index >= NUM_LOCAL_IMPORTS:
                stride = leaf_index // NUM_LOCAL_IMPORTS
                for n in range(NUM_LOCAL_IMPORTS):
                    dep_index = n * stride
                    dep_module_id = leaves[dep_index][1]
                    imports += f'import {dep_module_id}\n'

            # Create a linear chain: every CHAIN_STEP'th module imports
            # the one CHAIN_STEP earlier, giving max depth ~100.
            if leaf_index >= CHAIN_STEP and leaf_index % CHAIN_STEP == 0:
                dep_module_id = leaves[leaf_index - CHAIN_STEP][1]
                imports += f'import {dep_module_id}\n'

            # Add a missing import with "# type: ignore" to ~4% of files.
            if leaf_index % MISSING_IMPORT_INTERVAL == 0:
                missing = MISSING_MODULES[leaf_index % len(MISSING_MODULES)]
                imports += f'import {missing}  # type: ignore\n'

            with open(path, 'w') as f:
                f.write(f"""\
{imports}
def top_level_function(arg: int, flag: bool) -> str:
    if flag:
        return str(arg)
    return "default"


class ServiceHandler:
    def __init__(self, name: str) -> None:
        self.name = name

    def process_request(self, data: list[int]) -> bool:
        return len(data) > 0
""")
            leaf_index += 1

    log('running mypy to create fresh cache')
    env = get_clean_env()
    result = subprocess.run(
        [MYPY_BIN, '--no-error-summary', '--config-file', os.path.abspath(CONFIG_FILE), '.'],
        cwd=SRC_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log(f'mypy output:\n{result.stdout}\n{result.stderr}')
        raise RuntimeError('mypy failed during cache creation')
    log('synthetic codebase and cache ready')


@benchmark(
    prepare=[prepare, prepare_codebase],
    compiled_only=True,
    min_iterations=30,
    strip_outlier_runs=True,
    stable_hash_seed=True,
)
def mypy_fresh_incremental() -> None:
    # Modify a file in the first 10% to create some real work for mypy.
    leaves = leaf_modules()
    num_early = len(leaves) // 10
    target_path = leaves[num_early - 1][0]
    with open(target_path) as f:
        original_content = f.read()
    try:
        with open(target_path, 'w') as f:
            f.write(original_content)
            f.write(f'\n_timestamp = "{time.time()}"\n')
        env = get_clean_env()
        result = subprocess.run(
            [MYPY_BIN, '--no-error-summary', '--config-file', os.path.abspath(CONFIG_FILE), '.'],
            cwd=SRC_DIR,
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f'mypy failed during benchmark:\n{result.stdout}\n{result.stderr}'
            )
    finally:
        with open(target_path, 'w') as f:
            f.write(original_content)

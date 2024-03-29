from typing import Tuple
from datetime import datetime
import os
import re
import subprocess


# Use clang as the C compiler since it tends to generate faster code than gcc.
CC = "clang"

DATA_DIR = "data"

# Base directory for all reports
REPORTS_DIR = 'reports'

# Subdirectory for per-benchmark reports (under REPORTS_DIR)
BENCHMARKS_DIR = 'benchmarks'

# Directories containing benchmark .py files
SOURCE_DIRS = ('benchmarks', 'microbenchmarks')

# File with information about how to scale results between different hardware
# configurations and Python versions
SCALING_FNAM = 'scaling.csv'


def get_csv_path(data_repo: str, benchmark: str, cpython: bool = False) -> str:
    data_dir = os.path.join(data_repo, DATA_DIR)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if cpython:
        benchmark += '-cpython'
    return os.path.join(data_dir, benchmark + '.csv')


def get_hardware_id() -> str:
    arch = subprocess.check_output(['uname', '-m']).strip()
    fnam = '/proc/cpuinfo'
    if arch == b'x86_64' and os.path.exists(fnam):
        with open(fnam) as f:
            data = f.read()
        if 'i5-1145G7' in data:
            # Special case for the current server hardware configuration.
            return 'Intel Core i5-1145G7 (64-bit)'
        if 'i7-2600K' in data:
            # Special case for the previous server hardware configuration.
            return 'Intel Core i7-2600K (64-bit)'
        if 'Ryzen 9 3950X' in data:
            # Another special casing.
            return 'AMD Ryzen 9 3950X (64-bit)'
    # Give up if it's not a known configuration.
    return 'UNKNOWN'


def get_os_version() -> str:
    output = subprocess.check_output(['lsb_release', '-d']).decode("ascii")
    output = output.strip()
    return ' '.join(output.split()[1:])


def get_c_compiler_version(cc: str) -> str:
    output = subprocess.check_output([cc, '--version']).decode("utf-8")
    # This seems to work for gcc and clang, at least.
    m = re.search(r'\b[0-9]+([-.][A-Za-z0-9]+)*\b', output)
    assert m is not None
    return m.group()


def split_datetime(dt: datetime) -> Tuple[str, str]:
    date, time = dt.isoformat().split('T')
    return date, time

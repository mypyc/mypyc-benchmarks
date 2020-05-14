import os
import re
import subprocess


# Use clang as the C compiler since it tends to generate faster code than gcc.
CC = "clang"


def get_csv_path(data_repo: str, benchmark: str, cpython: bool = False) -> str:
    data_dir = os.path.join(data_repo, 'data')
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
        if 'i7-2600K' in data:
            # Special case for the current server hardware configuration.
            return 'Intel Core i7-2600K (64-bit)'
    # Give up if it's not the known configuration.
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

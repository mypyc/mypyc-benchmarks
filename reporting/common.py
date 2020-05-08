import os
import subprocess


def get_csv_path(data_repo: str, benchmark: str) -> str:
    data_dir = os.path.join(data_repo, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
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

"""Utility that collects benchmark normalization factors between different configs.

This allows scaling benchmark results collected on older hardware or
older Python versions to be comparable to results collected on new
hardware. Thus after switching to new hardware or more recent Python,
there's no need to update all historical benchmark results.

You should first collect both interpreted baselines and compiled
results for both configurations in all benchmarks.

Run like this:

  python3 -m reporting.scaling <mypy-hash> <result-repo> \
      <old-hardware> <old-python> <new-hardware> <new-python> >> scaling.txt

Python version should be of form <major>.<minor>.

Example:

  python3 -m reporting.scaling 8d57ffa817526fde7715da13246f72f1b1d62b60 \
      /srv/mypyc-benchmark-results \
      "Intel Core i7-2600K (64-bit)" 3.8 \
      "Intel Core i5-1145G7 (64-bit)" 3.8 >> scaling.txt
"""

import argparse
from typing import Tuple, List, Optional

from reporting.data import load_data, DataItem, BenchmarkData


def find_item(data: List[DataItem],
              hw: str,
              py: str,
              mypy_commit: Optional[str]) -> Optional[DataItem]:
    for item in data:
        if (item.hardware_id == hw
                and item.python_version.startswith(py)
                and (mypy_commit is None or item.mypy_commit == mypy_commit)):
            return item
    return None


def calculate_scaling(all_data: BenchmarkData,
                      mypy_commit: str,
                      old_hw: str,
                      old_py: str,
                      new_hw: str,
                      new_py: str) -> List[Tuple[str, float]]:
    baseline_old = {}
    baseline_new = {}
    for bm, data in all_data.baselines.items():
        old = find_item(data, old_hw, old_py, None)
        new = find_item(data, new_hw, new_py, None)
        if old and new and old.runtime and new.runtime:
            baseline_old[bm] = old.runtime
            baseline_new[bm] = new.runtime
    compiled_old = {}
    compiled_new = {}
    for bm, data in all_data.runs.items():
        old = find_item(data, old_hw, old_py, mypy_commit)
        new = find_item(data, new_hw, new_py, mypy_commit)
        if old and new and old.runtime and new.runtime:
            compiled_old[bm] = old.runtime
            compiled_new[bm] = new.runtime
    result = []
    for bm in sorted(baseline_old.keys()):
        if bm in compiled_old:
            old_factor = baseline_old[bm] / compiled_old[bm]
            new_factor = baseline_new[bm] / compiled_new[bm]

            result.append((bm, new_factor / old_factor))
    return result


def parse_args() -> Tuple[str, str, str, str, str, str]:
    parser = argparse.ArgumentParser(
        description="""Calculate benchmark normalization scaling factors between two
                       configurations.""")
    parser.add_argument(
        "mypy_commit",
        help="""mypy commit to use for the comparison; benchmark results must be available
                for both configurations""")
    parser.add_argument("data_repo",
                        help="benchmark results repository from which to read results")
    parser.add_argument("old_hw", help="description of older hardware")
    parser.add_argument("old_py", help="old Python version (X.Y)")
    parser.add_argument("new_hw", help="description of newer hardware")
    parser.add_argument("new_py", help="new Python version (X.Y)")
    args = parser.parse_args()
    return (
        args.mypy_commit,
        args.data_repo,
        args.old_hw,
        args.old_py,
        args.new_hw,
        args.new_py,
    )


def main() -> None:
    mypy_commit, data_repo, old_hw, old_py, new_hw, new_py = parse_args()
    data = load_data(data_repo)
    factors = calculate_scaling(data, mypy_commit, old_hw, old_py, new_hw, new_py)
    with open('scaling.txt', 'a') as f:
        for benchmark, factor in factors:
            print(f'{benchmark},{factor},{old_hw},{old_py},{new_hw},{new_py}')


if __name__ == "__main__":
    main()

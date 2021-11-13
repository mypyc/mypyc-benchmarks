from importlib import import_module
from typing import Tuple, List, NamedTuple, Optional
import argparse
import glob
import re
import os
import sys
import time
import subprocess
import statistics
from pathlib import Path

from benchmarking import BenchmarkInfo, benchmarks
from typing_extensions import Final


# Minimum total time (seconds) to run a benchmark
MIN_TIME = 2.0
# Minimum number of iterations to run a benchmark
MIN_ITER = 10


BINARY_EXTENSION: Final = 'pyd' if sys.platform == 'win32' else 'so'

def run_in_subprocess(benchmark: BenchmarkInfo,
                      binary: Optional[str],
                      compiled: bool,
                      priority: bool = False) -> float:
    module = benchmark.module
    program = 'import %s; import benchmarking as bm; print("\\nelapsed:", bm.run_once("%s"))' % (
        module,
        benchmark.name,
    )

    if not compiled and binary:
        os.rename(binary, binary + '.tmp')
    cmd = [sys.executable, '-c', program]
    if priority:
        # Use nice to increase process priority.
        cmd = ['sudo', 'nice', '-n', '-5'] + cmd
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
    finally:
        if not compiled and binary:
            os.rename(binary + '.tmp', binary)

    return parse_elapsed_time(result.stdout)


def parse_elapsed_time(output: bytes) -> float:
    m = re.search(rb"\belapsed: ([-+0-9.e]+)\b", output)
    assert m is not None, 'could not find elapsed time in output:\n%r' % output
    return float(m.group(1))


def smoothen(a: List[float]) -> List[float]:
    # Keep the lowest half of values
    return sorted(a)[: (len(a) + 1) // 2]



def run_benchmark(benchmark: BenchmarkInfo,
                  binary: Optional[str],
                  raw_output: bool,
                  priority: bool,
                  interpreted: bool,
                  compiled: bool,
                  min_iter: int) -> None:
    assert compiled or interpreted
    if not raw_output:
        print('running %s' % benchmark.name)

    # Warm up
    if interpreted:
        run_in_subprocess(benchmark, binary, compiled=False)
    if compiled:
        run_in_subprocess(benchmark, binary, compiled=True)

    times_compiled = []
    times_interpreted = []
    n = 0
    while True:
        if compiled:
            t = run_in_subprocess(benchmark, binary, compiled=True, priority=priority)
            times_compiled.append(t)
        if interpreted:
            t = run_in_subprocess(benchmark, binary, compiled=False, priority=priority)
            times_interpreted.append(t)
        if not raw_output:
            sys.stdout.write('.')
            sys.stdout.flush()
        n += 1
        long_enough = sum(times_interpreted) >= MIN_TIME or sum(times_compiled) >= MIN_TIME
        if long_enough and n >= min_iter:
            break
    if not raw_output:
        print()
    times_interpreted = smoothen(times_interpreted)
    times_compiled = smoothen(times_compiled)
    n = max(len(times_interpreted), len(times_compiled))
    if interpreted:
        stdev1 = statistics.stdev(times_interpreted)
        mean1 = sum(times_interpreted) / n
    else:
        stdev1 = 0.0
        mean1 = 0.0
    if compiled:
        stdev2 = statistics.stdev(times_compiled)
        mean2 = sum(times_compiled) / n
    else:
        stdev2 = 0.0
        mean2 = 0.0
    if not raw_output:
        if interpreted:
            print('interpreted: %.6fs (avg of %d iterations; stdev %.2g%%)' % (
                mean1, n, 100.0 * stdev1 / mean1)
            )
        if compiled:
            print('compiled:    %.6fs (avg of %d iterations; stdev %.2g%%)' % (
                mean2, n, 100.0 * stdev2 / mean2)
            )
        if compiled and interpreted:
            print()
            relative = sum(times_interpreted) / sum(times_compiled)
            print('compiled is %.3fx faster' % relative)
    else:
        print('%d %.6f %.6f %.6f %.6f' % (
            n,
            sum(times_interpreted) / n,
            stdev1,
            sum(times_compiled) / n,
            stdev2))


def compile_benchmark(module: str, raw_output: bool, mypy_repo: Optional[str]) -> str:
    fnam = module.replace('.', '/') + '.py'
    if not raw_output:
        print('compiling %s...' % module)
    env = os.environ.copy()
    legacy_script = None
    if mypy_repo:
        # Use mypyc from specific mypy repository.
        env['PYTHONPATH'] = mypy_repo
        script_path = os.path.join(mypy_repo, 'scripts', 'mypyc')
        if os.path.isfile(script_path):
            # With older mypy revisions we must use scripts/mypyc.
            legacy_script = script_path
    if not legacy_script:
        cmd = [sys.executable, '-m', 'mypyc']
    else:
        cmd = [sys.executable, legacy_script]
    subprocess.run(cmd + [fnam], check=True)
    pattern = module.replace('.', '/') + f'.*.{BINARY_EXTENSION}'
    paths = glob.glob(pattern)
    assert len(paths) == 1
    return paths[0]


def import_all() -> None:
    files = glob.glob('microbenchmarks/*.py')
    files += glob.glob('benchmarks/*.py')
    for fnam in files:
        filepath = Path(fnam).resolve()
        if filepath.name == '__init__.py' or filepath.suffix != '.py':
            continue
        benchmarks_root_dir = Path(__file__).parent.resolve()
        module_parts = filepath.with_suffix("").relative_to(benchmarks_root_dir).parts
        module = ".".join(module_parts)
        import_module(module)


def delete_binaries() -> None:
    files = glob.glob(f'microbenchmarks/*.{BINARY_EXTENSION}')
    files += glob.glob(f'benchmarks/*.{BINARY_EXTENSION}')
    for fnam in files:
        os.remove(fnam)


class Args(NamedTuple):
    benchmark: str
    mypy_repo: Optional[str]
    is_list: bool
    raw: bool
    priority: bool
    compiled_only: bool
    interpreted_only: bool
    min_iter: int


def parse_args() -> Args:
    parser = argparse.ArgumentParser(
        description="Run a mypyc benchmark in compiled and/or interpreted modes.")
    parser.add_argument('benchmark', nargs='?',
                        help="name of benchmark to run (use --list to show options)")
    parser.add_argument('--mypy-repo', metavar="DIR", type=str, default=None,
                        help="""use mypyc from a mypy git repository (by default, use mypyc
                                found via PATH and PYTHONPATH)""")
    parser.add_argument('--list', action='store_true', help='show names of all benchmarks')
    parser.add_argument('--raw', action='store_true', help='use machine-readable raw output')
    parser.add_argument('--priority', action='store_true',
                        help="increase process priority using 'nice' (uses sudo)")
    parser.add_argument('-c', action='store_true',
                        help="only run in compiled mode")
    parser.add_argument('-i', action='store_true',
                        help="only run in interpreted mode")
    parser.add_argument('--min-iter', type=int, default=MIN_ITER, metavar="N",
                        help="""set minimum number of iterations (half of the results
                                will be discarded; default %d)""" % MIN_ITER)
    parsed = parser.parse_args()
    if not parsed.list and not parsed.benchmark:
        parser.print_help()
        sys.exit(2)
    args = Args(parsed.benchmark,
                parsed.mypy_repo,
                parsed.list,
                parsed.raw,
                parsed.priority,
                parsed.c,
                parsed.i,
                parsed.min_iter)
    if args.compiled_only and args.interpreted_only:
        sys.exit("error: only give one of -c and -i")
    return args


def main() -> None:
    # Delete compiled modules before importing, as they may be stale.
    delete_binaries()

    # Import before parsing args so that syntax errors get reported.
    import_all()

    args = parse_args()
    if args.is_list:
        for benchmark in sorted(benchmarks):
            suffix = ''
            if benchmark.module.startswith('microbenchmarks.'):
                suffix = ' (micro)'
            print(benchmark.name + suffix)
        sys.exit(0)

    name = args.benchmark
    for benchmark in benchmarks:
        if benchmark.name == name:
            break
    else:
        sys.exit('unknown benchmark %r' % name)

    if args.interpreted_only:
        binary = None
    else:
        binary = compile_benchmark(benchmark.module, args.raw, args.mypy_repo)

    run_benchmark(
        benchmark,
        binary,
        args.raw,
        args.priority,
        not args.compiled_only,
        not args.interpreted_only,
        args.min_iter,
    )


if __name__ == "__main__":
    main()

from importlib import import_module
from typing import Tuple
import argparse
import glob
import re
import os
import sys
import time
import subprocess
import statistics

from benchmarking import BenchmarkInfo, benchmarks


# Minimum total time (seconds) to run a benchmark
MIN_TIME = 1.0
# Minimum number of iterations to run a benchmark
MIN_ITER = 5


def run_in_subprocess(benchmark: BenchmarkInfo,
                      binary: str,
                      compiled: bool,
                      priority: bool = False) -> float:
    module = benchmark.module
    program = 'import %s; import benchmarking as bm; print("\\nelapsed:", bm.run_once("%s"))' % (
        module,
        benchmark.name,
    )

    if not compiled:
        os.rename(binary, binary + '.tmp')
    cmd = ['python3', '-c', program]
    if priority:
        # Use nice to increase process priority.
        cmd = ['sudo', 'nice', '-n', '-5'] + cmd
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
    finally:
        if not compiled:
            os.rename(binary + '.tmp', binary)

    return parse_elapsed_time(result.stdout)


def parse_elapsed_time(output: bytes) -> float:
    m = re.search(rb"\belapsed: ([-+0-9.e]+)\b", output)
    assert m is not None, 'could not find elapsed time in output:\n%r' % output
    return float(m.group(1))


def run_benchmark(benchmark: BenchmarkInfo, binary: str, raw_output: bool, priority: bool) -> None:
    if not raw_output:
        print('running %s' % benchmark.name)

    # Warm up
    run_in_subprocess(benchmark, binary, compiled=False)
    run_in_subprocess(benchmark, binary, compiled=True)

    compiled = []
    interpreted = []
    n = 0
    while True:
        t1 = run_in_subprocess(benchmark, binary, compiled=True, priority=priority)
        t2 = run_in_subprocess(benchmark, binary, compiled=False, priority=priority)
        if not raw_output:
            sys.stdout.write('.')
            sys.stdout.flush()
        n += 1
        compiled.append(t1)
        interpreted.append(t2)
        if sum(interpreted) >= MIN_TIME and n >= MIN_ITER:
            break
    if not raw_output:
        print()
    stdev1 = statistics.stdev(interpreted)
    stdev2 = statistics.stdev(compiled)
    relative = sum(interpreted) / sum(compiled)
    if not raw_output:
        print('interpreted: %.5fs (avg of %d iterations; stdev %.2g)' % (
            sum(interpreted) / n, n, stdev1)
        )
        print('compiled:    %.5fs (avg of %d iterations; stdev %.2g)' % (
            sum(compiled) / n, n, stdev2)
        )
        print()
        print('compiled is %.3fx faster' % relative)
    else:
        print('%.6f %d %.6f %.6f %.6f %.6f' % (
            relative,
            n,
            sum(interpreted) / n,
            stdev1,
            sum(compiled) / n,
            stdev2))


def compile_benchmark(module: str, raw_output: bool) -> str:
    fnam = module.replace('.', '/') + '.py'
    if not raw_output:
        print('compiling %s...' % module)
    subprocess.run(['mypyc', fnam], check=True)
    pattern = module.replace('.', '/') + '.*.so'
    paths = glob.glob(pattern)
    assert len(paths) == 1
    return paths[0]


def import_all() -> None:
    files = glob.glob('microbenchmarks/*.py')
    files += glob.glob('benchmarks/*.py')
    for fnam in files:
        if fnam.endswith('__init__.py') or not fnam.endswith('.py'):
            continue
        module = re.sub(r'[.]py$', '', fnam).replace('/', '.')
        import_module(module)


def delete_binaries() -> None:
    files = glob.glob('microbenchmarks/*.so')
    files += glob.glob('benchmarks/*.so')
    for fnam in files:
        os.remove(fnam)


def parse_args() -> Tuple[str, bool, bool, bool]:
    parser = argparse.ArgumentParser()
    parser.add_argument('benchmark', nargs='?')
    parser.add_argument('--list', action='store_true', help='show names of all benchmarks')
    parser.add_argument('--raw', action='store_true', help='use machine-readable raw output')
    parser.add_argument('--priority', action='store_true',
                        help="increase process priority using 'nice' (uses sudo)")
    args = parser.parse_args()
    if not args.list and not args.benchmark:
        parser.print_help()
        sys.exit(2)
    return args.benchmark, args.list, args.raw, args.priority


def main() -> None:
    # Delete compiled modules before importing, as they may be stale.
    delete_binaries()

    # Import before parsing args so that syntax errors get reported.
    import_all()

    name, is_list, raw_output, is_priority = parse_args()
    if is_list:
        for benchmark in sorted(benchmarks):
            suffix = ''
            if benchmark.module.startswith('microbenchmarks.'):
                suffix = ' (micro)'
            print(benchmark.name + suffix)
        sys.exit(0)

    for benchmark in benchmarks:
        if benchmark.name == name:
            break
    else:
        sys.exit('unknown benchmark %r' % name)

    binary = compile_benchmark(benchmark.module, raw_output)
    run_benchmark(benchmark, binary, raw_output, is_priority)


if __name__ == "__main__":
    main()

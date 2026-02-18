from __future__ import annotations

from typing import List, NamedTuple, Callable, Sequence, TypeVar
import time


class BenchmarkContext:
    def __init__(self) -> None:
        self.start()

    def start(self) -> None:
        self.start_time = time.time()

    def elapsed_time(self) -> float:
        return time.time() - self.start_time


class BenchmarkInfo(NamedTuple):
    name: str
    module: str
    perform: Callable[[BenchmarkContext], object]
    # Each argument is path to mypy repo we are benchmarking
    prepare: list[Callable[[str | None], None]]
    compiled_only: bool
    min_iterations: int | None
    strip_outlier_runs: bool
    stable_hash_seed: bool


benchmarks: List[BenchmarkInfo] = []


T = TypeVar("T")


PrepareArg = (
    Callable[[str | None], None]
    | Sequence[Callable[[str | None], None]]
    | None
)


def benchmark(
        *,
        prepare: PrepareArg = None,
        compiled_only: bool = False,
        min_iterations: int | None = None,
        strip_outlier_runs: bool = True,
        stable_hash_seed: bool = False) -> Callable[[Callable[[], T]], Callable[[], T]]:
    """Define a benchmark.

    Args:
        prepare: If given, called once before running the benchmark to set up external state.
            Can be a single callable or a list of callables (called in order).
            This does not run in the same process as the actual benchmark so it's mostly useful
            for setting up file system state, data files, etc.
        compiled_only: This benchmark only runs in compiled mode (no interpreted mode).
        strip_outlier_runs: If True (default), aggressively try to strip outlier runs.
            Otherwise, no (or few) outlier runs will be removed.
        stable_hash_seed: If True, use predictable hash seed in CPython (it still varies
            between runs, but it's not random)
    """
    if prepare is None:
        prepare_list: list[Callable[[str | None], None]] = []
    elif callable(prepare):
        prepare_list = [prepare]
    else:
        prepare_list = list(prepare)

    def outer_wrapper(func: Callable[[], T]) -> Callable[[], T]:
        name = func_name(func)

        def wrapper(ctx: BenchmarkContext) -> T:
            return func()

        benchmark = BenchmarkInfo(
            name,
            func.__module__,
            wrapper,
            prepare_list,
            compiled_only,
            min_iterations,
            strip_outlier_runs,
            stable_hash_seed,
        )
        benchmarks.append(benchmark)
        return func

    return outer_wrapper


# TODO: Merge with "benchmark"
def benchmark_with_context(
        func: Callable[[BenchmarkContext], T]) -> Callable[[BenchmarkContext], T]:
    name = func.__name__
    if name.startswith('__mypyc_'):
        name = name.replace('__mypyc_', '')
        name = name.replace('_decorator_helper__', '')
    benchmark = BenchmarkInfo(name, func.__module__, func, [], False, None, True, False)
    benchmarks.append(benchmark)
    return func


def run_once(benchmark_name: str) -> float:
    for benchmark in benchmarks:
        if benchmark.name == benchmark_name:
            context = BenchmarkContext()
            benchmark.perform(context)
            return context.elapsed_time()
    assert False, "unknown benchmark: %r" % benchmark_name


def func_name(func: Callable[..., object]) -> str:
    name = func.__name__
    if name.startswith('__mypyc_'):
        name = name.replace('__mypyc_', '')
        name = name.replace('_decorator_helper__', '')
    return name

from typing import List, NamedTuple, Callable, TypeVar
import time


class BenchmarkContext:
    def __init__(self) -> None:
        self.start()

    def start(self) -> None:
        self.start_time = time.time()

    def elapsed_time(self) -> float:
        return time.time() - self.start_time


BenchmarkInfo = NamedTuple("BenchmarkInfo", [
    ("name", str),
    ("module", str),
    ("perform", Callable[[BenchmarkContext], object]),
])

benchmarks = []  # type: List[BenchmarkInfo]


T = TypeVar("T")


def benchmark(func: Callable[[BenchmarkContext], T]) -> Callable[[BenchmarkContext], T]:
    name = func.__name__
    if name.startswith('__mypyc_'):
        name = name.replace('__mypyc_', '')
        name = name.replace('_decorator_helper__', '')
    benchmark = BenchmarkInfo(name, func.__module__, func)
    benchmarks.append(benchmark)
    return func


def run_once(benchmark_name: str) -> float:
    for benchmark in benchmarks:
        if benchmark.name == benchmark_name:
            context = BenchmarkContext()
            benchmark.perform(context)
            return context.elapsed_time()
    assert False, "unknown benchmark: %r" % benchmark_name

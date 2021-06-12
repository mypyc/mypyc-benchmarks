from functools import singledispatch
from typing import Any

from benchmarking import benchmark

NUM_ITER = 100_000


@singledispatch
def f(arg) -> int:
    return 1


@f.register
def g(arg: int) -> int:
    return 2


@benchmark
def dynamic_dispatch_specialized() -> None:
    x: Any = 5
    # TODO: make sure the integer addition doesn't end up affecting benchmarking results
    # (maybe remove addition if not necessary?)
    n = 0
    for i in range(NUM_ITER):
        n += f(x)
    # specialized implementation returns 2
    assert n == NUM_ITER * 2, n


@benchmark
def dynamic_dispatch_fallback() -> None:
    x: Any = "a"
    n = 0
    for i in range(NUM_ITER):
        n += f(x)
    assert n == NUM_ITER * 1, n


# For situations that we know the type of the dispatch argument at compile time, we can probably
# get a performance boost by skipping the runtime type check and inserting a call to the correct
# implementation


@benchmark
def static_dispatch_specialized() -> None:
    x: int = 5
    n = 0
    for i in range(NUM_ITER):
        n += f(x)
    assert n == NUM_ITER * 2, n


@benchmark
def static_dispatch_fallback() -> None:
    x: str = "a"
    n = 0
    for i in range(NUM_ITER):
        n += f(x)
    assert n == NUM_ITER * 1, n

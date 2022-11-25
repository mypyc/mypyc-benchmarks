from typing import Iterator

from benchmarking import benchmark


@benchmark()
def generators() -> None:
    n = 0
    k = 0
    for i in range(100 * 1000):
        for j in gen(k):
            n += j
        k += 1
        if k == 10:
            k = 0
    assert n == 1200000, n


def gen(n: int) -> Iterator[int]:
    for i in range(n):
        yield i

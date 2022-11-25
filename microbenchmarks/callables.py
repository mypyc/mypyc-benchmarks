from typing import Callable

from benchmarking import benchmark


@benchmark()
def nested_func() -> None:
    n = 0

    for i in range(100 * 1000):
        n += call_nested_fast()

    assert n == 5500000, n


def call_nested_fast() -> int:
    n = 0

    def add(d: int) -> None:
        nonlocal n
        n += d

    for i in range(10):
        add(i)
        n += 1

    return n


@benchmark()
def nested_func_escape() -> None:
    n = 0

    for i in range(100 * 1000):
        n = nested_func_inner(n)

    assert n == 300000, n


def nested_func_inner(n: int) -> int:
    def add(d: int) -> None:
        nonlocal n
        n += d

    invoke(add)
    return n


def invoke(f: Callable[[int], None]) -> None:
    for i in range(3):
        f(i)


@benchmark()
def method_object() -> None:
    a = []
    for i in range(5):
        a.append(Adder(i))
        a.append(Adder2(i))

    n = 0
    for i in range(100 * 1000):
        for adder in a:
            n = adjust(n, adder.add)

    assert n == 7500000, n


def adjust(n: int, add: Callable[[int], int]) -> int:
    for i in range(3):
        n = add(n)
    return n


class Adder:
    def __init__(self, n: int) -> None:
        self.n = n

    def add(self, x: int) -> int:
        return self.n + x


class Adder2(Adder):
    def add(self, x: int) -> int:
        return self.n + x + 1

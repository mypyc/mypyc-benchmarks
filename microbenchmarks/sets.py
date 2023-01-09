from typing import List, Tuple

from benchmarking import benchmark


@benchmark()
def in_set() -> None:
    a: List[Tuple[int, ...]] = []
    for j in range(100):
        for i in range(10):
            a.append((i * 2,))
            a.append((i, i + 2))
            a.append((i,) * 6)
            a.append(())

    n = 0
    for i in range(1000):
        for s in a:
            if 6 in s:
                n += 1
            if i in {3, 4, 5}:
                n += 1
    assert n == 412000, n


@benchmark()
def set_literal_iteration() -> None:
    n = 0
    for _ in range(1000):
        for _ in range(10):
            for i in {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}:
                n += i
            for s in {"yes", "no"}:
                if s == "yes":
                    n += 1
            for a in {None, False, 1, 2.0, 3j, "4", b"5", (6,)}:
                n += 1
    assert n == 640000, n

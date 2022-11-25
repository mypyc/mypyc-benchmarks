"""Benchmarks for built-in functions (that don't fit elsewhere)."""

from benchmarking import benchmark


@benchmark()
def min_max_pair() -> None:
    a = []
    for i in range(20):
        a.append(i * 12753 % (2**15 - 1))

    expected_min = min(a)
    expected_max = max(a)

    n = 0
    for i in range(100 * 1000):
        n = 1000000000
        m = 0

        for j in a:
            n = min(n, j)
            m = max(m, j)
        assert n == expected_min
        assert m == expected_max


@benchmark()
def min_max_sequence() -> None:
    a = []
    for i in range(1000):
        a.append([i * 2])
        a.append([i, i + 2])
        a.append([i] * 15)

    n = 0
    for i in range(100):
        for s in a:
            x = min(s)
            n += x
            x = max(s)
            n += x
    assert n == 399800000, n


@benchmark()
def map_builtin() -> None:
    a = []
    for j in range(100):
        for i in range(10):
            a.append([i * 2])
            a.append([i, i + 2])
            a.append([i] * 6)

    n = 0
    for i in range(100):
        k = 0
        for lst in a:
            x = list(map(inc, lst))
            if k == 0:
                y = "".join(map(str, lst))
                n += len(y)
            n += x[-1]
            k += 1
            if k == 3:
                k = 0
    assert n == 2450000, n


def inc(x: int) -> int:
    return x + 1

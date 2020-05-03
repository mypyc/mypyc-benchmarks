from benchmarking import benchmark


@benchmark
def catch_exceptions() -> None:
    n = 0
    for i in range(100 * 1000):
        try:
            f(i)
        except ValueError:
            n += 1
    assert n == 35714, n


def f(i: int) -> None:
    if i % 4 == 0:
        raise ValueError("problem")
    else:
        g(i)


def g(i: int) -> None:
    if i % 7 == 0:
        raise ValueError

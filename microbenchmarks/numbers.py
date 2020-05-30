"""Numeric microbenchmarks."""

from typing import List, Tuple
import random

from typing_extensions import Final

from benchmarking import benchmark, benchmark_with_context, BenchmarkContext


Matrix = List[List[float]]

SIZE: Final = 30
SEED: Final = 535


@benchmark_with_context
def matrix_multiply(bm: BenchmarkContext) -> None:
    """Naive matrix multiplication benchmark."""
    m, m2 = setup_matrix_mult()
    bm.start()
    for i in range(50):
        m = multiply(m, m2)
    assert is_close(m[0][0], 1.758765499e58), m[0][0]


def is_close(x: float, y: float) -> bool:
    return 0.999999 <= x / y <= 1.000001


def setup_matrix_mult() -> Tuple[Matrix, Matrix]:
    return make_matrix(SIZE, SIZE), make_matrix(SIZE, SIZE)


def make_matrix(w: int, h: int) -> Matrix:
    random.seed(SEED)
    result = []
    for i in range(h):
        result.append([random.random() for _ in range(w)])
    return result


def multiply(a: Matrix, b: Matrix) -> Matrix:
    result = []
    for i in range(len(a)):
        result.append([0.0] * len(b[0]))
        for j in range(len(b[0])):
            x = 0.0
            for k in range(len(b)):
                x += a[i][k] * b[k][j]
            result[-1][j] = x
    return result


@benchmark
def int_to_float() -> None:
    a = [1, 4, 6, 7, 8, 9]
    x = 0.0
    for i in range(1000 * 1000):
        for n in a:
            x += float(n)
    assert x == 35000000.0, x


@benchmark
def str_to_float() -> None:
    a = ['1', '1.234567', '44324', '23.4', '-43.44e-4']
    x = 0.0
    for i in range(1000 * 1000):
        for n in a:
            x += float(n)
    assert is_close(x, 44349630223.26009), x


@benchmark
def float_abs() -> None:
    a = [1, -1.234567, 44324, 23.4, -43.44e-4]
    x = 0.0
    for i in range(1000 * 1000):
        for n in a:
            x += abs(n)
    assert is_close(x, 44349638911.052574), x


@benchmark
def int_divmod() -> None:
    a = [1, 1235, 5434, 394879374, -34453]
    n = 0
    for i in range(1000 * 1000):
        for x in a:
            q, r = divmod(x, 23)
            n += q + r
    assert n == 17167493000000, n


@benchmark
def int_list() -> None:
    a = list(range(200))
    b = list(reversed(a))
    c = [-1, 3, 7, 1234] * 40
    n = 0
    for i in range(4000):
        n += sum_ints(a)
        n += min_int(a)
        n += min_int(b)
        n += sum_ints(b)
        n += sum_ints(c)
        n += min_int(c)
    assert n == 358076000, n


def sum_ints(a: List[int]) -> int:
    s = 0
    for x in a:
        s += x
    return s


def min_int(a: List[int]) -> int:
    minimum = a[0]
    for i in range(1, len(a)):
        x = a[i]
        if x < minimum:
            minimum = x
    return minimum

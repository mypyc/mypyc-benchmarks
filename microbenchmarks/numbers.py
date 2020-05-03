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

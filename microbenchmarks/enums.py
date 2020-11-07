from enum import Enum

from benchmarking import benchmark

class MyEnum(Enum):
    A = 1
    B = 2
    C = 3


@benchmark
def enums() -> None:
    a = [MyEnum.A, MyEnum.B, MyEnum.C] * 10
    n = 0
    for i in range(100000):
        for x in a:
            if x is MyEnum.A:
                n += 1
            elif x is MyEnum.B:
                n += 2
    assert n == 3000000, n

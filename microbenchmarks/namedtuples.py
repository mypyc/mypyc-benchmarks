from collections import namedtuple
from typing import NamedTuple, List

from benchmarking import benchmark

NT1 = NamedTuple('NT1', [('n', int), ('l', List[str])])
NT2 = namedtuple('NT2', ['n', 'l', 'b'])


@benchmark
def create_namedtuple() -> None:
    N1 = 20
    N2 = 10
    l = ['x']
    a = [NT1(0, l)] * N1
    b = [NT2(0, l, False)] * N2
    for i in range(10000):
        for n in range(N1):
            a[n] = NT1(n, l)
        for n in range(N1):
            a[n] = NT1(n=n, l=l)
        for n in range(N2):
            b[n] = NT2(n, l, False)


@benchmark
def unpack_namedtuple() -> None:
    N1 = 30
    N2 = 10
    a = []
    for n in range(N1):
        a.append(NT1(n, [str(n)]))
    b = []
    for n in range(N2):
        b.append(NT2(n, [str(n)], n % 2 == 0))
    c = 0
    for i in range(100000):
        for nt1 in a:
            n, l = nt1
            c += n
            c += len(l)
        for nt2 in b:
            n, l, _ = nt2
            c += n
            c += len(l)
    assert c == 52000000, c


@benchmark
def get_namedtuple_item() -> None:
    N1 = 30
    N2 = 10
    a = []
    for n in range(N1):
        a.append(NT1(n, [str(n)]))
    b = []
    for n in range(N2):
        b.append(NT2(n, [str(n)], n % 2 == 0))
    c = 0
    for i in range(100000):
        for nt1 in a:
            c += nt1.n
            c += len(nt1.l)
            c += len(nt1[1])
        for nt2 in b:
            c += nt2.n
            c += len(nt2[1])
            if nt2.b:
                c += 1
    assert c == 55500000, c

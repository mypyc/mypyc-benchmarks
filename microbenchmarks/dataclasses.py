from dataclasses import dataclass
from typing import List, Dict

from benchmarking import benchmark

@dataclass
class C:
    n: int
    l: List[str]
    b: bool

    def add(self, m: int) -> None:
        self.n = self.get() + m

    def get(self) -> int:
        return self.n ^ 1


@dataclass
class C2:
    l: List[str]
    n: int


@benchmark()
def create_dataclass() -> None:
    N = 40
    a = [C(1, [], True)] * N
    l = ['x']
    for i in range(10000):
        for n in range(N):
            a[n] = C(n, l, False)
        b = []
        for n in range(N):
            b.append(C2(n=n, l=l))


@benchmark()
def dataclass_attr_access() -> None:
    N = 40
    a = []
    for n in range(N):
        a.append(C(n, [str(n)], n % 3 == 0))
    c = 0
    for i in range(100000):
        for o in a:
            c += o.n
            c += len(o.l)
            if o.b:
                c -= 1
            o.n ^= 1
    assert c == 80600000, c


@benchmark()
def dataclass_method() -> None:
    N = 40
    a = []
    for n in range(N):
        a.append(C(n, [str(n)], n % 3 == 0))
    c = 0
    for i in range(10000):
        for o in a:
            o.add(i & 3)
            c += o.n
    assert c == 3007600000, c


@dataclass(frozen=True)
class F:
    n: int
    s: str


@benchmark()
def dataclass_as_dict_key() -> None:
    d: Dict[F, int] = {}
    a = [F(i % 4, str(i % 3)) for i in range(100)]
    for i in range(1000):
        for f in a:
            if f in d:
                d[f] += 1
            else:
                d[f] = 1
    assert len(d) == 12, len(d)

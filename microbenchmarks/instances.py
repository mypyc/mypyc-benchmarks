from __future__ import annotations

from benchmarking import benchmark


@benchmark()
def super_method() -> None:
    n = 0
    for i in range(10 * 1000):
        a = []
        for j in range(10):
            a.append(Cls(j, "x"))
        for j in range(5):
            for obj in a:
                n += obj.method(i)
    assert n == 2502500000, n


class Base:
    def __init__(self, x: int) -> None:
        self.x = x

    def method(self, x: int) -> int:
        return self.x + x


class Cls(Base):
    def __init__(self, x: int, y: str) -> None:
        super().__init__(x)
        self.y = y

    def method(self, x: int) -> int:
        x = super().method(x)
        return x + 1


@benchmark()
def super_method_alt() -> None:
    n = 0
    for i in range(10 * 1000):
        a = []
        for j in range(10):
            a.append(Cls2(j, "x"))
        for j in range(10):
            for obj in a:
                n += obj.method(i)
    assert n == 5005000000, n


class Base2:
    def __init__(self, x: int) -> None:
        super(Base2, self).__init__()  # Call object.__init__
        self.x = x

    def method(self, x: int) -> int:
        return self.x + x


class Cls2(Base):
    def __init__(self, x: int, y: str) -> None:
        super(Cls2, self).__init__(x)
        self.y = y

    def method(self, x: int) -> int:
        x = super(Cls2, self).method(x)
        return x + 1


class Simple:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def update(self) -> Simple:
        return Simple(self.y, self.x + 1)


@benchmark()
def alloc_short_lived_simple() -> None:
    n = 0
    for i in range(1000 * 1000):
        s = Simple(i, 3)
        s = s.update()
        s = s.update()
        s = s.update()
        n += s.x
    assert n == 4000000, n


class Linked:
    def __init__(self, x: int, next: Linked | None) -> None:
        self.x = x
        self.next = next

    def sum(self) -> int:
        n = self.x
        o = self.next
        while o:
            n += o.x
            o = o.next
        return n


@benchmark()
def alloc_short_lived_linked() -> None:
    n = 0
    for i in range(1000 * 1000):
        o = Linked(i, None)
        o = Linked(1, o)
        o = Linked(2, o)
        o = Linked(3, o)
        n += o.sum() & 7
    assert n == 3500000, n


@benchmark()
def alloc_long_lived_simple() -> None:
    a = []
    for i in range(1000):
        b = []
        for j in range(1000):
            b.append(Simple(j, i))
        a.append(b)
    n = 0
    for b in a:
        for s in b:
            n += s.x
    assert n == 499500000, n


@benchmark()
def alloc_long_lived_linked() -> None:
    a = []
    for i in range(100 * 1000):
        o = Linked(i, None)
        for j in range(10):
            o = Linked(j, o)
        a.append(o)
    n = 0
    for o in a:
        n += o.sum()
    assert n == 5004450000, n

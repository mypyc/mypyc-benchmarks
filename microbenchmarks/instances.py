from benchmarking import benchmark


@benchmark
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


@benchmark
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

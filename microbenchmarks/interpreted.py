"""Benchmarks that access compiled code from interpreted code."""

from benchmarking import benchmark


def func0() -> None:
    pass


def func1(x: str) -> str:
    return x


def func3(count: int, name: str, thing: object) -> int:
    return count


@benchmark
def call_function_from_interpreted() -> None:
    code = """
def run():
    for i in range(500000):
        func0()
        func1('foobar')
        func1('xyz')
        func3(i, 'foobar', 2.3)
        func3(5, 'foo', True)
        func3(i, name='foobar', thing=2.3)
run()
"""
    exec(code, globals())


class C:
    def __init__(self, count: int, name: str) -> None:
        self.count = count
        self.name = name

    def method0(self) -> None:
        pass

    def method1(self, x: str) -> str:
        return x

    def method3(self, count: int, name: str, thing: object) -> int:
        return count


@benchmark
def call_method_from_interpreted() -> None:
    code = """
def run():
    obj = C(44, 'foobar')
    for i in range(500000):
        obj.method0()
        obj.method1('foobar')
        obj.method1('xyz')
        obj.method3(i, 'foobar', 2.3)
        obj.method3(5, 'foo', True)
        obj.method3(i, name='foobar', thing=2.3)
run()
"""
    exec(code, globals())


@benchmark
def call_type_from_interpreted() -> None:
    code = """
def run():
    obj = C(44, 'foobar')
    for i in range(500000):
        C(i, 'foobar')
        C(55, 'bar')
        C(count=55, name='bar')
run()
"""
    exec(code, globals())


@benchmark
def access_attr_from_interpreted() -> None:
    code = """
def run():
    o1 = C(44, 'foobar')
    o2 = C(23, 'har')
    n = 0
    for i in range(500000):
        o1.count
        o2.name
        o2.count
        o1.name
        o1.count += 1
run()
"""
    exec(code, globals())

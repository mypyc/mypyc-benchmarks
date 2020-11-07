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


@benchmark
def call_method_from_interpreted() -> None:
    pass


@benchmark
def call_type_from_interpreted() -> None:
    pass


@benchmark
def access_attr_from_interpreted() -> None:
    pass

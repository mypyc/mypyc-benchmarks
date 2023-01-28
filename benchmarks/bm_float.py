"""
Artificial, floating point-heavy benchmark originally used by Factor.

Adapted to mypyc by Jukka Lehtosalo
"""
from __future__ import annotations
from math import sin, cos, sqrt, isclose

from benchmarking import benchmark


POINTS = 100000


class Point(object):
    __slots__ = ('x', 'y', 'z')

    def __init__(self, i: float) -> None:
        self.x = x = sin(i)
        self.y = cos(i) * 3
        self.z = (x * x) / 2

    def __repr__(self) -> str:
        return "<Point: x=%s, y=%s, z=%s>" % (self.x, self.y, self.z)

    def normalize(self) -> None:
        x = self.x
        y = self.y
        z = self.z
        norm = sqrt(x * x + y * y + z * z)
        self.x /= norm
        self.y /= norm
        self.z /= norm

    def maximize(self, other: Point) -> Point:
        self.x = self.x if self.x > other.x else other.x
        self.y = self.y if self.y > other.y else other.y
        self.z = self.z if self.z > other.z else other.z
        return self


def maximize(points: list[Point]) -> Point:
    next = points[0]
    for p in points[1:]:
        next = next.maximize(p)
    return next


@benchmark()
def bm_float() -> None:
    n = POINTS
    points = []
    for i in range(n):
        points.append(Point(i))
    for p in points:
        p.normalize()
    result = maximize(points)
    assert isclose(result.x, 0.8944271890997864)
    assert isclose(result.y, 1.0)
    assert isclose(result.z, 0.4472135954456972)

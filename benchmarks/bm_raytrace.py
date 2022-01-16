# mypy: disallow-untyped-defs

"""
This file contains definitions for a simple raytracer.
Copyright Callum and Tony Garnock-Jones, 2008.

This file may be freely redistributed under the MIT license,
http://www.opensource.org/licenses/mit-license.php

From http://www.lshift.net/blog/2008/10/29/toy-raytracer-in-python
"""

import array
import math

from typing import List, Tuple, Optional, Union, overload
from typing_extensions import Final

from benchmarking import benchmark


DEFAULT_WIDTH = 100
DEFAULT_HEIGHT = 100
EPSILON = 0.00001


class Vector:

    def __init__(self, initx: float, inity: float, initz: float) -> None:
        self.x = initx
        self.y = inity
        self.z = initz

    def __str__(self) -> str:
        return '(%s,%s,%s)' % (self.x, self.y, self.z)

    def __repr__(self) -> str:
        return 'Vector(%s,%s,%s)' % (self.x, self.y, self.z)

    def magnitude(self) -> float:
        return math.sqrt(self.dot(self))

    @overload
    def __add__(self, other: 'Vector') -> 'Vector': ...
    @overload
    def __add__(self, other: 'Point') -> 'Point': ...
    def __add__(self, other: Union['Vector', 'Point']) -> Union['Vector', 'Point']:
        if other.isPoint():
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        else:
            return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector') -> 'Vector':
        other.mustBeVector()
        return Vector(self.x - other.x, self.y - other.y, self.z - other.z)

    def scale(self, factor: float) -> 'Vector':
        return Vector(factor * self.x, factor * self.y, factor * self.z)

    def dot(self, other: 'Vector') -> float:
        other.mustBeVector()
        return (self.x * other.x) + (self.y * other.y) + (self.z * other.z)

    def cross(self, other: 'Vector') -> 'Vector':
        other.mustBeVector()
        return Vector(self.y * other.z - self.z * other.y,
                      self.z * other.x - self.x * other.z,
                      self.x * other.y - self.y * other.x)

    def normalized(self) -> 'Vector':
        return self.scale(1.0 / self.magnitude())

    def negated(self) -> 'Vector':
        return self.scale(-1)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return False
        return (self.x == other.x) and (self.y == other.y) and (self.z == other.z)

    def isVector(self) -> bool:
        return True

    def isPoint(self) -> bool:
        return False

    def mustBeVector(self) -> 'Vector':
        return self

    def mustBePoint(self) -> None:
        raise TypeError('Vectors are not points!')

    def reflectThrough(self, normal: 'Vector') -> 'Vector':
        d = normal.scale(self.dot(normal))
        return self - d.scale(2)


Vector_ZERO: Final = Vector(0, 0, 0)
Vector_RIGHT: Final = Vector(1, 0, 0)
Vector_UP: Final = Vector(0, 1, 0)
Vector_OUT: Final = Vector(0, 0, 1)

assert Vector_RIGHT.reflectThrough(Vector_UP) == Vector_RIGHT
assert Vector(-1, -1, 0).reflectThrough(Vector_UP) == Vector(-1, 1, 0)


class Point:

    def __init__(self, initx: float, inity: float, initz: float) -> None:
        self.x = initx
        self.y = inity
        self.z = initz

    def __str__(self) -> str:
        return '(%s,%s,%s)' % (self.x, self.y, self.z)

    def __repr__(self) -> str:
        return 'Point(%s,%s,%s)' % (self.x, self.y, self.z)

    def __add__(self, other: Vector) -> 'Point':
        other.mustBeVector()
        return Point(self.x + other.x, self.y + other.y, self.z + other.z)

    @overload
    def __sub__(self, other: Vector) -> 'Point': ...
    @overload
    def __sub__(self, other: 'Point') -> Vector: ...
    def __sub__(self, other: Union['Point', Vector]) -> Union['Point', Vector]:
        if other.isPoint():
            return Vector(self.x - other.x, self.y - other.y, self.z - other.z)
        else:
            return Point(self.x - other.x, self.y - other.y, self.z - other.z)

    def isVector(self) -> bool:
        return False

    def isPoint(self) -> bool:
        return True

    def mustBeVector(self) -> None:
        raise TypeError('Points are not vectors!')

    def mustBePoint(self) -> 'Point':
        return self


class Object:
    def intersectionTime(self, ray: 'Ray') -> Optional[float]:
        raise NotImplementedError

    def normalAt(self, p: Point) -> Vector:
        raise NotImplementedError


class Sphere(Object):

    def __init__(self, centre: Point, radius: float) -> None:
        centre.mustBePoint()
        self.centre = centre
        self.radius = radius

    def __repr__(self) -> str:
        return 'Sphere(%s,%s)' % (repr(self.centre), self.radius)

    def intersectionTime(self, ray: 'Ray') -> Optional[float]:
        cp = self.centre - ray.point
        v = cp.dot(ray.vector)
        discriminant = (self.radius * self.radius) - (cp.dot(cp) - v * v)
        if discriminant < 0:
            return None
        else:
            return v - math.sqrt(discriminant)

    def normalAt(self, p: Point) -> Vector:
        return (p - self.centre).normalized()


class Halfspace(Object):

    def __init__(self, point: Point, normal: Vector) -> None:
        self.point = point
        self.normal = normal.normalized()

    def __repr__(self) -> str:
        return 'Halfspace(%s,%s)' % (repr(self.point), repr(self.normal))

    def intersectionTime(self, ray: 'Ray') -> Optional[float]:
        v = ray.vector.dot(self.normal)
        if v:
            return 1 / -v
        else:
            return None

    def normalAt(self, p: Point) -> Vector:
        return self.normal


class Ray:

    def __init__(self, point: Point, vector: Vector) -> None:
        self.point = point
        self.vector = vector.normalized()

    def __repr__(self) -> str:
        return 'Ray(%s,%s)' % (repr(self.point), repr(self.vector))

    def pointAtTime(self, t: float) -> Point:
        return self.point + self.vector.scale(t)


Point_ZERO: Final = Point(0, 0, 0)


class Canvas:

    def __init__(self, width: int, height: int) -> None:
        self.bytes = array.array('B', [0] * (width * height * 3))
        for i in range(width * height):
            self.bytes[i * 3 + 2] = 255
        self.width = width
        self.height = height

    def plot(self, x: int, y: int, r: float, g: float, b: float) -> None:
        i = ((self.height - y - 1) * self.width + x) * 3
        self.bytes[i] = max(0, min(255, int(r * 255)))
        self.bytes[i + 1] = max(0, min(255, int(g * 255)))
        self.bytes[i + 2] = max(0, min(255, int(b * 255)))

    def write_ppm(self, filename: str) -> None:
        header = 'P6 %d %d 255\n' % (self.width, self.height)
        with open(filename, "wb") as fp:
            fp.write(header.encode('ascii'))
            fp.write(self.bytes.tobytes())


def firstIntersection(
    intersections: List[Tuple[Object, Optional[float], 'Surface']]
) -> Optional[Tuple[Object, float, 'Surface']]:
    result: Optional[Tuple[Object, float, Surface]] = None
    for i in intersections:
        candidateT = i[1]
        if candidateT is not None and candidateT > -EPSILON:
            if result is None or candidateT < result[1]:
                result = (i[0], candidateT, i[2])
    return result


Colour = Tuple[float, float, float]


class Scene:

    def __init__(self) -> None:
        self.objects: List[Tuple[Object, Surface]] = []
        self.lightPoints: List[Point] = []
        self.position = Point(0, 1.8, 10)
        self.lookingAt = Point_ZERO
        self.fieldOfView = 45
        self.recursionDepth = 0

    def moveTo(self, p: Point) -> None:
        self.position = p

    def lookAt(self, p: Point) -> None:
        self.lookingAt = p

    def addObject(self, object: Object, surface: 'Surface') -> None:
        self.objects.append((object, surface))

    def addLight(self, p: Point) -> None:
        self.lightPoints.append(p)

    def render(self, canvas: Canvas) -> None:
        fovRadians = math.pi * (self.fieldOfView / 2.0) / 180.0
        halfWidth = math.tan(fovRadians)
        halfHeight = 0.75 * halfWidth
        width = halfWidth * 2
        height = halfHeight * 2
        pixelWidth = width / (canvas.width - 1)
        pixelHeight = height / (canvas.height - 1)

        eye = Ray(self.position, self.lookingAt - self.position)
        vpRight = eye.vector.cross(Vector_UP).normalized()
        vpUp = vpRight.cross(eye.vector).normalized()

        for y in range(canvas.height):
            for x in range(canvas.width):
                xcomp = vpRight.scale(x * pixelWidth - halfWidth)
                ycomp = vpUp.scale(y * pixelHeight - halfHeight)
                ray = Ray(eye.point, eye.vector + xcomp + ycomp)
                colour = self.rayColour(ray)
                canvas.plot(x, y, *colour)

    def rayColour(self, ray: Ray) -> Colour:
        if self.recursionDepth > 3:
            return (0, 0, 0)
        try:
            self.recursionDepth = self.recursionDepth + 1
            intersections = [(o, o.intersectionTime(ray), s)
                             for (o, s) in self.objects]
            i = firstIntersection(intersections)
            if i is None:
                return (0, 0, 0)  # the background colour
            else:
                (o, t, s) = i
                p = ray.pointAtTime(t)
                return s.colourAt(self, ray, p, o.normalAt(p))
        finally:
            self.recursionDepth = self.recursionDepth - 1

    def _lightIsVisible(self, l: Point, p: Point) -> bool:
        for (o, s) in self.objects:
            t = o.intersectionTime(Ray(p, l - p))
            if t is not None and t > EPSILON:
                return False
        return True

    def visibleLights(self, p: Point) -> List[Point]:
        result = []
        for l in self.lightPoints:
            if self._lightIsVisible(l, p):
                result.append(l)
        return result


def addColours(a: Colour, scale: float, b: Colour) -> Colour:
    return (a[0] + scale * b[0],
            a[1] + scale * b[1],
            a[2] + scale * b[2])


class Surface:
    def colourAt(self, scene: Scene, ray: Ray, p: Point, normal: Vector) -> Colour:
        raise NotImplementedError


class SimpleSurface(Surface):

    def __init__(self,
                 *,
                 baseColour: Colour = (1, 1, 1),
                 specularCoefficient: float = 0.2,
                 lambertCoefficient: float = 0.6) -> None:
        self.baseColour = baseColour
        self.specularCoefficient = specularCoefficient
        self.lambertCoefficient = lambertCoefficient
        self.ambientCoefficient = 1.0 - self.specularCoefficient - self.lambertCoefficient

    def baseColourAt(self, p: Point) -> Colour:
        return self.baseColour

    def colourAt(self, scene: Scene, ray: Ray, p: Point, normal: Vector) -> Colour:
        b = self.baseColourAt(p)

        c: Colour = (0, 0, 0)
        if self.specularCoefficient > 0:
            reflectedRay = Ray(p, ray.vector.reflectThrough(normal))
            reflectedColour = scene.rayColour(reflectedRay)
            c = addColours(c, self.specularCoefficient, reflectedColour)

        if self.lambertCoefficient > 0:
            lambertAmount: float = 0
            for lightPoint in scene.visibleLights(p):
                contribution = (lightPoint - p).normalized().dot(normal)
                if contribution > 0:
                    lambertAmount = lambertAmount + contribution
            lambertAmount = min(1, lambertAmount)
            c = addColours(c, self.lambertCoefficient * lambertAmount, b)

        if self.ambientCoefficient > 0:
            c = addColours(c, self.ambientCoefficient, b)

        return c


class CheckerboardSurface(SimpleSurface):

    def __init__(self,
                 *,
                 baseColour: Colour = (1, 1, 1),
                 specularCoefficient: float = 0.2,
                 lambertCoefficient: float = 0.6,
                 otherColor: Colour = (0, 0, 0),
                 checkSize: float = 1) -> None:
        super().__init__(baseColour=baseColour,
                         specularCoefficient=specularCoefficient,
                         lambertCoefficient=lambertCoefficient)
        self.otherColour = otherColor
        self.checkSize = checkSize

    def baseColourAt(self, p: Point) -> Colour:
        v = p - Point_ZERO
        v.scale(1.0 / self.checkSize)
        if ((int(abs(v.x) + 0.5)
             + int(abs(v.y) + 0.5)
             + int(abs(v.z) + 0.5)) % 2):
            return self.otherColour
        else:
            return self.baseColour


def bench_raytrace(loops: int, width: int, height: int, filename: Optional[str]) -> None:
    range_it = range(loops)

    for i in range_it:
        canvas = Canvas(width, height)
        s = Scene()
        s.addLight(Point(30, 30, 10))
        s.addLight(Point(-10, 100, 30))
        s.lookAt(Point(0, 3, 0))
        s.addObject(Sphere(Point(1, 3, -10), 2),
                    SimpleSurface(baseColour=(1, 1, 0)))
        for y in range(6):
            s.addObject(Sphere(Point(-3 - y * 0.4, 2.3, -5), 0.4),
                        SimpleSurface(baseColour=(y / 6.0, 1 - y / 6.0, 0.5)))
        s.addObject(Halfspace(Point(0, 0, 0), Vector_UP),
                    CheckerboardSurface())
        s.render(canvas)

    if filename:
        canvas.write_ppm(filename)


@benchmark
def raytrace() -> None:
    bench_raytrace(1, DEFAULT_WIDTH, DEFAULT_HEIGHT, None)

from librt.strings import StringWriter
from mypy_extensions import i64, i32

from benchmarking import benchmark


@benchmark(compiled_variant=True)
def rot13() -> None:
    values = ["foo bar", "longer strings With UPPER CASE as well.", "..-..--.", "\u1234"]
    n = 0
    for i in range(1000 * 1000):
        for v in values:
            n += len(rot13_translate(v))
    assert n == 55000000


def rot13_translate(s: str) -> str:
    w = StringWriter()
    for i in range(i64(len(s))):
        c: i32 = ord(s[i])
        if c >= ord('a') and c <= ord('z'):
            rotated: i32 = c + 13
            if rotated > ord('z'):
                rotated -= 26
            w.append(rotated)
        elif c >= ord('A') and c <= ord('Z'):
            rotated = c + 13
            if rotated > ord('Z'):
                rotated -= 26
            w.append(rotated)
        else:
            w.append(c)
    return w.getvalue()

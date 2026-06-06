from librt.strings import BytesWriter
from mypy_extensions import i64, u8

from benchmarking import benchmark


@benchmark(compiled_variant=True)
def bytes_normalize() -> None:
    a = []
    for i in range(1000):
        a.append(b'Foobar  %d' % i)
        a.append(b'%d-ab\tasdfsdf-asdf\n' % i)
        a.append(b'yeah')
    n = 0
    for i in range(1000):
        for s in a:
            n += len(normalize_whitespace(s))
    assert n == 33780000, n


def normalize_whitespace(b: bytes) -> bytes:
    w = BytesWriter()
    i: i64 = 0
    n: i64 = len(b)
    while i < n:
        c: u8 = b[i]
        if not (c == ord(' ') or c == ord('\t')):
            break
        i += 1
    while i < n:
        c = b[i]
        while i < n:
            c = b[i]
            if c == ord(' ') or c == ord('\t'):
                break
            w.append(c)
            i += 1
        while i < n:
            c = b[i]
            if not (c == ord(' ') or c == ord('\t')):
                break
            i += 1
        if i < n:
            w.append(ord(' '))
    return w.getvalue()

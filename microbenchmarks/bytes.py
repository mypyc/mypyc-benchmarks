from benchmarking import benchmark


@benchmark
def bytes_concat() -> None:
    a = []
    for i in range(1000):
        a.append(b'Foobar-%d' % i)
        a.append(b'  %d str' % i)

    n = 0
    for i in range(1000):
        for s in a:
            b = b'foo' + s
            if b == s:
                n += 1
            b += b'bar'
            if b != s:
                n += 1
    assert n == 2000000, n


@benchmark
def bytes_methods() -> None:
    """Use a mix of bytes methods (but not split/join)."""
    a = []
    for i in range(1000):
        a.append(b'Foobar-%d' % i)
        a.append(b'  %d str' % i)

    n = 0
    for i in range(100):
        for s in a:
            if s.startswith(b'foo'):
                n += 1
            if s.endswith(b'r'):
                n += 1
            if s.replace(b'-', b'/') != s:
                n += 1
            if s.strip() != s:
                n += 1
            if s.rstrip() != s:
                n += 1
            if s.lower() == s:
                n += 1
    assert n == 400000, n


@benchmark
def bytes_format() -> None:
    a = []
    for i in range(1000):
        a.append(b'Foobar-%d' % i)
        a.append(b'%d str' % i)

    n = 0
    for i in range(100):
        for s in a:
            n += len(b"foobar %s stuff" % s)
            ss = b"foobar %s stuff" % s
            n += len(b"%s-%s" % (s, ss))
    assert n == 10434000, n


@benchmark
def bytes_slicing() -> None:
    a = []
    for i in range(1000):
        a.append(b'Foobar-%d' % i)
        a.append(b'%d str' % i)

    n = 0
    for i in range(1000):
        for s in a:
            n += len(s[2:-2])
            if s[:3] == b'Foo':
                n += 1
            if s[-2:] == b'00':
                n += 1
    assert n == 9789000, n


@benchmark
def bytes_split_and_join() -> None:
    a = []
    for i in range(1000):
        a.append(b'Foobar-%d' % i)
        a.append(b'%d-ab-asdfsdf-asdf' % i)
        a.append(b'yeah')
    n = 0
    for i in range(100):
        for s in a:
            items = s.split(b'-')
            if b'-'.join(items) == s:
                n += 1
    assert n == 300000, n


@benchmark
def bytes_searching() -> None:
    a = []
    for i in range(1000):
        a.append(b'Foobar-%d' % i)
        a.append(b'%d-ab-asdfsdf-asdf' % i)
        a.append(b'yeah')
    n = 0
    for i in range(100):
        for s in a:
            if b'i' in s:
                n += 1
            if s.find(b'asd') >= 0:
                n += 1
            n += s.index(b'a')
    assert n == 1089000, n


@benchmark
def bytes_call() -> None:
    a = []
    for i in range(100):
        a.append([65, 55])
        a.append([0, 1, 2, 3])
        a.append([100])

    n = 0
    for i in range(10 * 1000):
        for s in a:
            b = bytes(s)
            n += len(b)

    assert n == 7000000, n


@benchmark
def bytes_indexing() -> None:
    a = []
    for i in range(1000):
        a.append(b'Foobar-%d' % i)
        a.append(b'%d-ab-asdfsdf-asdf' % i)
        a.append(b'yeah')
    n = 0
    for i in range(100):
        for s in a:
            for j in range(len(s)):
                if s[j] == 97:
                    n += 1
    assert n == 500000, n

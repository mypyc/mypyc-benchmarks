from benchmarking import benchmark


@benchmark
def str_methods() -> None:
    """Use a mix of popular str methods (but not split/join)."""
    a = []
    for i in range(1000):
        a.append('Foobar-%d' % i)
        a.append('  %d str' % i)

    n = 0
    for i in range(100):
        for s in a:
            if s.startswith('foo'):
                n += 1
            if s.endswith('r'):
                n += 1
            if s.replace('-', '/') != s:
                n += 1
            if s.strip() != s:
                n += 1
            if s.rstrip() != s:
                n += 1
            if s.lower() == s:
                n += 1
    assert n == 400000, n


@benchmark
def str_methods_2() -> None:
    """Use a mix of popular str methods."""
    a = []
    for i in range(1000):
        a.append('FOOBAR-%d' % i)
        a.append('  %d str' % i)

    n = 0
    for i in range(100):
        for s in a:
            if s.startswith(('  1', '  2', '  3')):
                n += 1
            if s.endswith(('4', '5', '6')):
                n += 1
            if s.lstrip() != s:
                n += 1
            if s.lstrip(' ') != s:
                n += 1
            if s.rstrip('123') != s:
                n += 1
            if s.upper() == s:
                n += 1
            x, y, z = s.partition('-')
            if y:
                n += 1
            x, y, z = s.rpartition('-')
            if y:
                n += 1
    assert n == 593300, n


@benchmark
def str_format() -> None:
    a = []
    for i in range(1000):
        a.append('Foobar-%d' % i)
        a.append('%d str' % i)

    n = 0
    for i in range(100):
        for s in a:
            n += len("foobar {} stuff".format(s))
            ss = "foobar %s stuff" % s
            n += len("%s-%s" % (s, ss))
    assert n == 10434000, n


@benchmark
def str_format_percent_operator() -> None:
    a = []
    tmp_str = "Foobar"
    for i in range(1000):
        for _ in range(5):
            a.append('%s' % tmp_str)
        a.append('%s-%d' % (tmp_str, i))
        a.append('%d %f str' % (i, i * 2.0))

    n = 0
    for i in range(100):
        for s in a:
            n += len("foobar %s stuff" % s)
            ss = "foobar %s stuff" % s
            n += len("%d-%s-%s" % (i, s, ss))
    assert n == 38397500, n


@benchmark
def str_format_format_method() -> None:
    a = []
    tmp_str = "Foobar"
    for i in range(1000):
        for _ in range(5):
            a.append('{}'.format(tmp_str))
        a.append('{}-{}'.format(tmp_str, i))
        a.append('{} {} str'.format(i, i * 2.0))

    n = 0
    for i in range(100):
        for s in a:
            n += len("foobar {} stuff".format(s))
            ss = "foobar {} stuff".format(s)
            n += len("{}-{}-{}".format(i, s, ss))
    assert n == 36897500, n


@benchmark
def str_format_fstring() -> None:
    a = []
    tmp_str = "Foobar"
    for i in range(1000):
        for _ in range(5):
            a.append(f'{tmp_str}')
        a.append(f'{tmp_str}-{i}')
        a.append(f'{i} {i*2.0} str')

    n = 0
    for i in range(100):
        for s in a:
            n += len(f"foobar {s} stuff")
            ss = f"foobar {s} stuff"
            n += len(f"{i}-{s}-{ss}")
    assert n == 36897500, n


@benchmark
def str_slicing() -> None:
    a = []
    for i in range(1000):
        a.append('Foobar-%d' % i)
        a.append('%d str' % i)

    n = 0
    for i in range(1000):
        for s in a:
            n += len(s[2:-2])
            if s[:3] == 'Foo':
                n += 1
            if s[-2:] == '00':
                n += 1
    assert n == 9789000, n


@benchmark
def split_and_join() -> None:
    a = []
    for i in range(1000):
        a.append('Foobar-%d' % i)
        a.append('%d-ab-asdfsdf-asdf' % i)
        a.append('yeah')
    n = 0
    for i in range(100):
        for s in a:
            items = s.split('-')
            if '-'.join(items) == s:
                n += 1
    assert n == 300000, n


@benchmark
def encode_decode() -> None:
    a = []
    for i in range(1000):
        a.append('Foobar-%d' % i)
        a.append('%d-ab-asdfsdf-asdf' % i)
        a.append('yeah')
    n = 0
    for i in range(100):
        for s in a:
            b = s.encode("ascii")
            if b.decode("ascii") != s:
                n += 1

            b = s.encode("utf8")
            if b.decode("utf8") == s:
                n += 1
    assert n == 300000, n


@benchmark
def str_searching() -> None:
    a = []
    for i in range(1000):
        a.append('Foobar-%d' % i)
        a.append('%d-ab-asdfsdf-asdf' % i)
        a.append('yeah')
    n = 0
    for i in range(100):
        for s in a:
            if 'i' in s:
                n += 1
            if s.find('asd') >= 0:
                n += 1
            n += s.index('a')
    assert n == 1089000, n


@benchmark
def str_call() -> None:
    a = []
    for i in range(100):
        a.append(Cls(i))

    n = 0
    for i in range(10 * 1000):
        for obj in a:
            s1 = str(obj)
            s2 = str(s1)  # No-op
            n += len(s2)

    assert n == 1900000, n


class Cls:
    def __init__(self, x: int) -> None:
        self.x = x

    def __str__(self) -> str:
        return str(self.x)


@benchmark
def ord_builtin() -> None:
    a = []
    for i in range(1000):
        a.append('Foobar-%d' % i)
        a.append('%d-ab-asdfsdf-asdf' % i)
        a.append('yeah')
    n = 0
    for i in range(50):
        for s in a:
            for j in range(len(s)):
                if 97 <= ord(s[j]) <= 122:
                    n += 1
                if is_upper_case_letter(s[j]):
                    n += 2
                if s[j] == ord('a'):
                    n += 3
    assert n == 1200000, n


def is_upper_case_letter(ch: str) -> bool:
    return 65 <= ord(ch) <= 90

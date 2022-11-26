"""List and tuple benchmarks."""

from typing import List, Tuple

from benchmarking import benchmark


@benchmark()
def list_slicing() -> None:
    a = []
    for i in range(1000):
        a.append([i * 2])
        a.append([i, i + 2])
        a.append([i] * 6)
        a.append([])

    n = 0
    for i in range(100):
        for s in a:
            n += len(s[2:-2])
            if len(s[:2]) < 2:
                n += 1
            if s[-2:] == [0]:
                n += 1
            if s == s[::-1]:
                n += 1
    assert n == 700100, n


@benchmark()
def tuple_slicing() -> None:
    a = []  # type: List[Tuple[int, ...]]
    for i in range(1000):
        a.append((i * 2,))
        a.append((i, i + 2))
        a.append((i,) * 6)
        a.append(())

    n = 0
    for i in range(100):
        for s in a:
            n += len(s[2:-2])
            if len(s[:2]) < 2:
                n += 1
            if s[-2:] == (0,):
                n += 1
            if s == s[::-1]:
                n += 1
    assert n == 700100, n


@benchmark()
def in_list() -> None:
    a = []
    for j in range(100):
        for i in range(10):
            a.append([i * 2])
            a.append([i, i + 2])
            a.append([i] * 6)
            a.append([])

    n = 0
    for i in range(1000):
        for s in a:
            if 6 in s:
                n += 1
            if i in [3, 4, 5]:
                n += 1
    assert n == 412000, n


@benchmark()
def in_tuple() -> None:
    a = []  # type: List[Tuple[int, ...]]
    for j in range(100):
        for i in range(10):
            a.append((i * 2,))
            a.append((i, i + 2))
            a.append((i,) * 6)
            a.append(())

    n = 0
    for i in range(1000):
        for s in a:
            if 6 in s:
                n += 1
            if i in (3, 4, 5):
                n += 1
    assert n == 412000, n


@benchmark()
def list_append_small() -> None:
    n = 0
    for i in range(200 * 1000):
        a = []
        for j in range(i % 10):
            a.append(j + i)
        n += len(a)
    assert n == 900000, n


@benchmark()
def list_append_large() -> None:
    n = 0
    for i in range(2000):
        a = []
        for j in range(i):
            a.append(j + i)
        n += len(a)
    assert n == 1999000, n


@benchmark()
def list_from_tuple() -> None:
    a = []  # type: List[Tuple[int, ...]]
    for j in range(100):
        for i in range(10):
            a.append((i * 2,))
            a.append((i, i + 2))
            a.append((i,) * 6)
            a.append(())

    n = 0
    for i in range(1000):
        for tup in a:
            lst = list(tup)
            n += len(lst)
    assert n == 9000000, n


@benchmark()
def list_from_range() -> None:
    a = []
    for j in range(100):
        for i in range(23):
            a.append(i * 7 % 9)

    n = 0
    for i in range(1000):
        for j in a:
            lst = list(range(j))
            n += len(lst)
    assert n == 8800000, n


@benchmark()
def tuple_from_iterable() -> None:
    a = []
    for i in range(100):
        a.append([i * 2])
        a.append([i, i + 2])
        a.append([i] * 6)
        a.append([])

    n = 0
    for i in range(1000):
        for s in a:
            t1 = tuple(s)
            t2 = tuple(j + 1 for j in s)
            n += len(t1) + len(t2)
    assert n == 1800000, n


@benchmark()
def list_copy() -> None:
    a = []
    for i in range(100):
        a.append([i * 2])
        a.append([i, i + 2])
        a.append([i] * 6)
        a.append([])

    for i in range(1000):
        for s in a:
            s2 = s.copy()
            s3 = s[:]
            assert s2 == s3


@benchmark()
def list_remove() -> None:
    for j in range(10 * 1000):
        a = []
        for i in range(10):
            a.append(list(range(11 + i)))

        for i in range(10):
            for s in a:
                s.remove(i)

        total = sum(len(s) for s in a)
        assert total == 55, total


@benchmark()
def list_insert() -> None:
    for j in range(10 * 1000):
        a: List[int] = []
        for i in range(10):
            a.insert(0, i)
        for i in range(5):
            a.insert(5, i)

        assert len(a) == 15


@benchmark()
def list_index() -> None:
    a = []
    for i in range(100):
        a.append([i * 2, 44])
        a.append([44, i, i + 2])
        a.append([i] * 6 + [44])
        a.append([44])

    n = 0
    for i in range(1000):
        for s in a:
            n += s.index(44)
    assert n == 693000, n


@benchmark()
def list_add_in_place() -> None:
    for i in range(100 * 1000):
        a: List[int] = []
        n = id(a)
        l = 5 + i % 10
        for j in range(l):
            a += [j]
        assert len(a) == l
        assert id(a) == n


@benchmark()
def list_concatenate() -> None:
    flag = False
    x = ["x", "y", "z"]
    y = ["1, 2"]
    n = 0
    for i in range(1000 * 1000):
        a = x
        if flag:
            b = a + a
        else:
            b = y + a + y
        n += len(a + b)
        flag = not flag
    assert n == 8500000, n


@benchmark()
def list_equality() -> None:
    a = [1, 2]
    n = 0
    for i in range(10000):
        for j in range(100):
            if a == [1, j]:
                n += 1
            if a == [i, 2]:
                n += 1
    assert n == 10100, n


@benchmark()
def tuple_equality() -> None:
    t = (1, 2)
    n = 0
    for i in range(10000):
        a = []
        a.append((i, 5))
        for j in range(100):
            if t == (1, j):
                n += 1
            if t == (i, 2):
                n += 1
            if a[0] == (j, 5):
                a.append((j, 6))
                n += 1
    assert n == 10200, n


@benchmark()
def list_comprehension() -> None:
    a = [1, 2, 4, 6, 8, 13, 17]
    n = 0
    for i in range(100000):
        for j in range(20):
            b = [x for x in a if x < j]
            n += len(b)
    assert n == 8200000, n


@benchmark()
def multiple_assignment() -> None:
    x = 0
    y = 1
    a = [2, 3]
    n = 0
    for i in range(1000000):
        x, y = y, x
        a[0], a[1] = a[1], a[0]
        xx, yy = a
        n += x + xx
    assert n == 3000000, n


@benchmark()
def list_for_reversed() -> None:
    a = []
    for i in range(1000):
        a.append([i * 2])
        a.append([i, i + 2])
        a.append([i] * 12)
        a.append([])
    n = 0
    for i in range(100):
        for aa in a:
            for s in reversed(aa):
                n += s
    assert n == 799400000, n


@benchmark()
def sieve() -> None:
    n = 0
    for i in range(1000):
        n += num_primes(1000)
    assert n == 168000, n


def num_primes(n: int) -> int:
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, n + 1):
        if is_prime[i] and i * i <= n:
            j = i * i
            while j <= n:
                is_prime[j] = False
                j += i
    count = 0
    for b in is_prime:
        if b:
            count += 1
    return count


@benchmark()
def sorted_with_key() -> None:
    n = 10
    a = []
    for i in range(n):
        aa = []
        for j in range(i):
            aa.append(j * 971 % 11)
        a.append(aa)
    a2 = [(str(i), i * 5 % 11) for i in range(20)]
    c = 0
    for i in range(20000):
        for seq in a:
            c += len(sorted(seq, key=lambda x: -x))
        a3 = sorted(a2, key=lambda x: x[1])
        c += len(sorted(a3, key=lambda x: x[0]))
    assert c == 1300000, c

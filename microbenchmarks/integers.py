from benchmarking import benchmark, benchmark_with_context, BenchmarkContext


@benchmark()
def int_bitwise_ops() -> None:
    a = []
    for i in range(1000):
        a.append(i * i * 12753 % (2**20 - 1))
    b = a[10:50]

    n = 0

    for i in range(50):
        for j in a:
            for k in b:
                j |= k
                j &= ~(j ^ k)
                x = j >> 5
                n += x
                n += x << 1
                n &= 0xffffff

    assert n == 4867360, n


@benchmark_with_context
def int_long_bitwise_ops(bm: BenchmarkContext) -> None:
    a = []
    for i in range(1000):
        a.append(i * i ** (i // 15))
    b = a[10:500:10]

    n = 0

    for i in range(10):
        for j in a:
            for k in b:
                j |= k
                j &= ~(j ^ k)
                if (1 << (i * 19)) & j:
                    n += 1
                n += j & 1

    assert n == 122000, n

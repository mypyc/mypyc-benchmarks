from librt.vecs import vec
from mypy_extensions import i64

from benchmarking import benchmark


@benchmark(compiled_variant=True)
def sieve_packed() -> None:
    n = 0
    for i in range(1000):
        n += num_primes_vec(1000)
    assert n == 168000, n


def num_primes_vec(n: i64) -> i64:
    is_prime = vec[bool]([True] * (n + 1))
    is_prime[0] = is_prime[1] = False
    for i in range(i64(2), n + 1):
        if is_prime[i] and i * i <= n:
            j: i64 = i * i
            while j <= n:
                is_prime[j] = False
                j += i
    count: i64 = 0
    for b in is_prime:
        if b:
            count += 1
    return count

# mypyc benchmarks

This is a collection of mypyc benchmarks. They are intended to track
performance of mypyc against interpreted CPython. They are also useful
for validating that a mypyc enhancement results in a measurable
performance improvement.

*Some benchmarks are microbenchmarks that are only useful for finding
big performance differences related to specific operations or language
features. They don't reflect real-world performance.*

## Benchmark results

We have a service that automatically collects benchmark results for
all mypyc and mypy commits:

* [Benchmark results](https://github.com/mypyc/mypyc-benchmark-results/blob/master/reports/summary-main.md)
* [Microbenchmark results](https://github.com/mypyc/mypyc-benchmark-results/blob/master/reports/summary-microbenchmarks.md)

## Running benchmarks

Prerequisites:

* Python 3.10 or later on Linux, macOS, or Windows
* `venv` installed (`python3-venv` on Ubuntu)
* A working Python C development environment
* Cloned mypy git repository (in addition to mypyc-benchmarks repository)
* A Python environment with mypy `test-requirements.txt` installed

Display the names of available benchmarks using `runbench.py --list`:

```
$ python3 runbench.py --list
binary_trees
bytes_call (micro)
bytes_concat (micro)
bytes_format (micro)
bytes_indexing (micro)
...
```

Microbenchmarks are distinguished by `(micro)`.

Run a benchmark using `runbench.py --mypy-repo <dir> <name>`:

```
$ python3 runbench.py --mypy-repo ~/src/mypy richards
...
running richards
......
interpreted: 0.190326s (avg of 6 iterations; stdev 1%)
compiled:    0.019284s (avg of 6 iterations; stdev 1.6%)

compiled is 9.870x faster
```

This runs the benchmark in both compiled and interpreted modes using
the mypyc from the given mypy repository, and reports the relative
performance.

Use `runbench.py -c ...` to only run the compiled benchmark.

Run a benchmark first using the mypy master branch and then your local
branch to see how well your branch does relative to master.

## Documentation

There is more information in the
[documentation](https://github.com/mypyc/mypyc-benchmarks/blob/master/doc/benchmarks.rst).

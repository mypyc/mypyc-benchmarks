# mypyc benchmarks

This is a collection of mypyc benchmarks. They are intended to track
performance of mypyc against interpreted CPython. They are also useful
for validating that a mypyc enhancement results in a measurable
performance improvement.

*Some benchmarks are microbenchmarks that are only useful for finding
big performance differences related to specific operations or language
features. They don't reflect real-world performance.*

## Prerequisites

* Python 3.7 or later on Linux (or macOS?)
* `mypyc` in `PATH`
* A working Python C development environment

## Running benchmarks

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

Run a benchmark using `runbench.py <name>`:

```
$ python3 runbench.py richards
...
running richards
......
interpreted: 0.190326s (avg of 6 iterations; stdev 1%)
compiled:    0.019284s (avg of 6 iterations; stdev 1.6%)

compiled is 9.870x faster
```

This runs the benchmark in both compiled and interpreted modes, and
reports the relative performance.

Use `runbench -c <name>` to only run the compiled benchmark.

## Documentation

There is more information in the
[documentation](https://github.com/mypyc/mypyc-benchmarks/blob/master/doc/benchmarks.rst).

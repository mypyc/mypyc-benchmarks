Benchmarks
**********

The benchmarks are divided into two categories: benchmarks and
microbenchmarks. All non-microbenchmarks are documented below.

Microbenchmarks are not reliable and must be used with care. They
cannot be used to estimate real-world performance.


richards
--------

The classic Python Richards benchmark.

Adapted to mypyc from https://github.com/python/pyperformance.

Based on a Java version.

Based on original version written in BCPL by Dr Martin Richards in 1981 at
Cambridge University Computer Laboratory, England and a C++ version derived
from a Smalltalk version written by L Peter Deutsch.

Java version: Copyright (C) 1995 Sun Microsystems, Inc. Translation from C++,
Mario Wolczko Outer loop added by Alex Jacoby


deltablue
---------

DeltaBlue benchmark

Adapted to mypyc from https://github.com/python/pyperformance.

Ported for the PyPy project. Contributed by Daniel Lindsley

This implementation of the DeltaBlue benchmark was directly ported from the
`V8's source code
<https://github.com/v8/v8/blob/master/benchmarks/deltablue.js>`_,
which was in turn derived from the Smalltalk implementation by John Maloney and
Mario Wolczko. The original Javascript implementation was licensed under the
GPL.

It's been updated in places to be more idiomatic to Python (for loops over
collections, a couple magic methods, ``OrderedCollection`` being a list &
things altering those collections changed to the builtin methods) but largely
retains the layout & logic from the original. (Ugh.)


hexiom
------

Solver of Hexiom board game (level 25 hard coded).

Adapted to mypyc from https://github.com/python/pyperformance.


nqueens
-------

Simple, brute-force N-Queens solver.

See `Eight queens puzzle <https://en.wikipedia.org/wiki/Eight_queens_puzzle>`_.

Adapted to mypyc from https://github.com/python/pyperformance.


spectral_norm
-------------

MathWorld: "Hundred-Dollar, Hundred-Digit Challenge Problems", Challenge #3.
http://mathworld.wolfram.com/Hundred-DollarHundred-DigitChallengeProblems.html

The Computer Language Benchmarks Game
http://benchmarksgame.alioth.debian.org/u64q/spectralnorm-description.html#spectralnorm

Contributed by Sebastien Loisel. Fixed by Isaac Gouy. Sped up by Josh Goldfoot.
Dirtily sped up by Simon Descarpentries. Concurrency by Jason Stitt.

Adapted to mypyc from https://github.com/python/pyperformance.


binary_trees
------------

Adapted from the Computer Language Benchmarks Game:
https://benchmarksgame-team.pages.debian.net/benchmarksgame/performance/binarytrees.html

The implementation is new.

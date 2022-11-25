"""Binary trees benchmark.

Adapted from the Computer Language Benchmarks Game:
https://benchmarksgame-team.pages.debian.net/benchmarksgame/performance/binarytrees.html
"""

import gc

from benchmarking import benchmark


class Tree:
    def __init__(self, depth: int) -> None:
        if depth == 0:
            self.left = None
            self.right = None
        else:
            self.left = Tree(depth - 1)
            self.right = Tree(depth - 1)

    def check(self) -> int:
        if self.left is not None:
            assert self.right is not None
            return 1 + self.left.check() + self.right.check()
        else:
            return 1


@benchmark()
def binary_trees() -> None:
    # If unadjusted, most time will be spent doing GC.
    gc.set_threshold(10000)

    min_depth = 4
    max_depth = 18  # Original uses 21, but it takes too long
    stretch_depth = max_depth + 1

    print("stretch tree of depth {} check: {}".format(stretch_depth, Tree(stretch_depth).check()))

    long_lived_tree = Tree(max_depth)

    for d in range(min_depth, stretch_depth, 2):
        iterations = 2**(max_depth + min_depth - d)

        check = 0
        for i in range(1, iterations + 1):
            check += Tree(d).check()

        print("{} trees of depth {} check: {}".format(iterations, d, check))

    print("long lived tree of depth {} check: {}".format(max_depth, long_lived_tree.check()))

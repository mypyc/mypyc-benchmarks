from functools import singledispatch

from benchmarking import benchmark

NUM_ITER = 500


class Tree:
    pass


class Leaf(Tree):
    pass


class Node(Tree):
    def __init__(self, value: int, left: Tree, right: Tree) -> None:
        self.value = value
        self.left = left
        self.right = right


@singledispatch
def calc_sum(x: Tree) -> int:
    raise TypeError("invalid type for x")


@calc_sum.register(Leaf)
def sum_leaf(x: Leaf) -> int:
    return 0


@calc_sum.register(Node)
def sum_node(x: Node) -> int:
    return x.value + calc_sum(x.left) + calc_sum(x.right)


def build(n: int) -> Tree:
    if n == 0:
        return Leaf()
    return Node(n, build(n - 1), build(n - 1))


@benchmark()
def sum_tree_singledispatch() -> None:
    # making the tree too big causes building the tree to take too long or just crash python entirely
    tree = build(10)
    n: int = 0
    for i in range(NUM_ITER):
        n += calc_sum(tree)

    # calc_sum(tree) should be 2036
    assert n == NUM_ITER * 2036, n

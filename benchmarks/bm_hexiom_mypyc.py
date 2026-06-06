# mypy: disallow-untyped-defs

"""
Solver of Hexiom board game.

Benchmark from Laurent Vaucher.

Source: https://github.com/slowfrog/hexiom : hexiom2.py, level36.txt

(Main function tweaked by Armin Rigo.)
(Migrated to mypyc and modernized by Jukka Lehtosalo.)
"""

from __future__ import annotations
from typing import cast, IO
from io import StringIO

from typing_extensions import Final
from mypy_extensions import i64

from librt.vecs import vec, append, remove

from benchmarking import benchmark

# 2016-07-07: CPython 3.6 takes ~25 ms to solve the board level 25
DEFAULT_LEVEL = 25


##################################
class Dir(object):

    def __init__(self, x: i64, y: i64) -> None:
        self.x = x
        self.y = y


DIRS: Final = vec[Dir]([Dir(1, 0),
                        Dir(-1, 0),
                        Dir(0, 1),
                        Dir(0, -1),
                        Dir(1, 1),
                        Dir(-1, -1)])

EMPTY: Final = 7

##################################

EMPTY_CELLS: Final = vec[vec[i64]]()


class Done(object):
    MIN_CHOICE_STRATEGY: Final = 0
    MAX_CHOICE_STRATEGY: Final = 1
    HIGHEST_VALUE_STRATEGY: Final = 2
    FIRST_STRATEGY: Final = 3
    MAX_NEIGHBORS_STRATEGY: Final = 4
    MIN_NEIGHBORS_STRATEGY: Final = 5

    def __init__(self, count: i64, cells: vec[vec[i64]] = EMPTY_CELLS) -> None:
        self.count = count
        self.cells = (
            cells if len(cells) else vec[vec[i64]](
                [
                    vec[i64]([0, 1, 2, 3, 4, 5, 6, EMPTY]) for i in range(count)
                ]
            )
        )

    def clone(self) -> Done:
        return Done(self.count, vec[vec[i64]]([self.cells[i][:] for i in range(self.count)]))

    def __getitem__(self, i: i64) -> vec[i64]:
        return self.cells[i]

    def set_done(self, i: i64, v: i64) -> None:
        self.cells[i] = vec[i64]([v])

    def already_done(self, i: i64) -> bool:
        return len(self.cells[i]) == 1

    def remove(self, i: i64, v: i64) -> bool:
        if v in self.cells[i]:
            self.cells[i] = remove(self.cells[i], v)
            return True
        else:
            return False

    def remove_all(self, v: i64) -> None:
        for i in range(self.count):
            self.remove(i, v)

    def remove_unfixed(self, v: i64) -> bool:
        changed = False
        for i in range(self.count):
            if not self.already_done(i):
                if self.remove(i, v):
                    changed = True
        return changed

    def filter_tiles(self, tiles: vec[i64]) -> None:
        for v in range(i64(8)):
            if tiles[v] == 0:
                self.remove_all(v)

    def next_cell_min_choice(self) -> i64:
        minlen: i64 = 10
        mini: i64 = -1
        for i in range(self.count):
            if 1 < len(self.cells[i]) < minlen:
                minlen = len(self.cells[i])
                mini = i
        return mini

    def next_cell_max_choice(self) -> i64:
        maxlen: i64 = 1
        maxi: i64 = -1
        for i in range(self.count):
            if maxlen < len(self.cells[i]):
                maxlen = len(self.cells[i])
                maxi = i
        return maxi

    def next_cell_highest_value(self) -> i64:
        maxval: i64 = -1
        maxi: i64 = -1
        for i in range(self.count):
            if (not self.already_done(i)):
                maxvali: i64 = max(k for k in self.cells[i] if k != EMPTY)
                if maxval < maxvali:
                    maxval = maxvali
                    maxi = i
        return maxi

    def next_cell_first(self) -> i64:
        for i in range(self.count):
            if (not self.already_done(i)):
                return i
        return -1

    def next_cell_max_neighbors(self, pos: Pos) -> i64:
        maxn: i64 = -1
        maxi: i64 = -1
        for i in range(self.count):
            if not self.already_done(i):
                cells_around = pos.hex.get_by_id(i).links
                n = sum(1 if (self.already_done(nid) and (self[nid][0] != EMPTY)) else 0
                        for nid in cells_around)
                if n > maxn:
                    maxn = n
                    maxi = i
        return maxi

    def next_cell_min_neighbors(self, pos: Pos) -> i64:
        minn: i64 = 7
        mini: i64 = -1
        for i in range(self.count):
            if not self.already_done(i):
                cells_around = pos.hex.get_by_id(i).links
                n = sum(1 if (self.already_done(nid) and (self[nid][0] != EMPTY)) else 0
                        for nid in cells_around)
                if n < minn:
                    minn = n
                    mini = i
        return mini

    def next_cell(self, pos: Pos, strategy: i64 = HIGHEST_VALUE_STRATEGY) -> i64:
        if strategy == Done.HIGHEST_VALUE_STRATEGY:
            return self.next_cell_highest_value()
        elif strategy == Done.MIN_CHOICE_STRATEGY:
            return self.next_cell_min_choice()
        elif strategy == Done.MAX_CHOICE_STRATEGY:
            return self.next_cell_max_choice()
        elif strategy == Done.FIRST_STRATEGY:
            return self.next_cell_first()
        elif strategy == Done.MAX_NEIGHBORS_STRATEGY:
            return self.next_cell_max_neighbors(pos)
        elif strategy == Done.MIN_NEIGHBORS_STRATEGY:
            return self.next_cell_min_neighbors(pos)
        else:
            raise Exception("Wrong strategy: %d" % strategy)

##################################


class Node(object):

    def __init__(self, pos: tuple[i64, i64], id: i64, links: vec[i64]) -> None:
        self.pos = pos
        self.id = id
        self.links = links

##################################


class Hex(object):

    def __init__(self, size: i64) -> None:
        self.size: i64 = size
        self.count: i64 = 3 * size * (size - 1) + 1
        self.nodes_by_id = vec[Node | None]([None] * self.count)
        self.nodes_by_pos = {}
        id: i64 = 0
        for y in range(size):
            for x in range(size + y):
                pos = (x, y)
                node = Node(pos, id, vec[i64]())
                self.nodes_by_pos[pos] = node
                self.nodes_by_id[node.id] = node
                id += 1
        for y in range(1, size):
            for x in range(y, size * 2 - 1):
                ry = size + y - 1
                pos = (x, ry)
                node = Node(pos, id, vec[i64]())
                self.nodes_by_pos[pos] = node
                self.nodes_by_id[node.id] = node
                id += 1

    def link_nodes(self) -> None:
        for node in self.nodes_by_id:
            assert node is not None
            (x, y) = node.pos
            for dir in DIRS:
                nx = x + dir.x
                ny = y + dir.y
                if self.contains_pos((nx, ny)):
                    node.links = append(node.links, self.nodes_by_pos[(nx, ny)].id)

    def contains_pos(self, pos: tuple[i64, i64]) -> bool:
        return pos in self.nodes_by_pos

    def get_by_pos(self, pos: tuple[i64, i64]) -> Node:
        return self.nodes_by_pos[pos]

    def get_by_id(self, id: i64) -> Node:
        node = self.nodes_by_id[id]
        return cast(Node, node)


##################################
class Pos(object):

    def __init__(self, hex: Hex, tiles: vec[i64], done: Done | None = None) -> None:
        self.hex = hex
        self.tiles = tiles
        self.done = Done(hex.count) if done is None else done

    def clone(self) -> 'Pos':
        return Pos(self.hex, self.tiles, self.done.clone())

##################################


def constraint_pass(pos: Pos, last_move: i64 | None = None) -> bool:
    changed = False
    left = pos.tiles[:]
    done = pos.done

    # Remove impossible values from free cells
    free_cells = (vec[i64]([x for x in range(done.count)]) if last_move is None
                  else pos.hex.get_by_id(last_move).links)
    for i in free_cells:
        if not done.already_done(i):
            vmax: i64 = 0
            vmin: i64 = 0
            cells_around = pos.hex.get_by_id(i).links
            for nid in cells_around:
                if done.already_done(nid):
                    if done[nid][0] != EMPTY:
                        vmin += 1
                        vmax += 1
                else:
                    vmax += 1

            for num in range(i64(7)):
                if (num < vmin) or (num > vmax):
                    if done.remove(i, num):
                        changed = True

    # Computes how many of each value is still free
    for cell in done.cells:
        if len(cell) == 1:
            left[cell[0]] -= 1

    for v in range(i64(8)):
        # If there is none, remove the possibility from all tiles
        if (pos.tiles[v] > 0) and (left[v] == 0):
            if done.remove_unfixed(v):
                changed = True
        else:
            possible: i64 = 0
            for cell in done.cells:
                if v in cell:
                    possible += 1
            # If the number of possible cells for a value is exactly the number of available tiles
            # put a tile in each cell
            if pos.tiles[v] == possible:
                for i in range(done.count):
                    cell = done.cells[i]
                    if (not done.already_done(i)) and (v in cell):
                        done.set_done(i, v)
                        changed = True

    # Force empty or non-empty around filled cells
    filled_cells = (vec[i64]([x for x in range(done.count)]) if last_move is None
                    else vec[i64]([last_move]))
    for i in filled_cells:
        if done.already_done(i):
            num = done[i][0]
            empties: i64 = 0
            filled: i64 = 0
            unknown = vec[i64]()
            cells_around = pos.hex.get_by_id(i).links
            for nid in cells_around:
                if done.already_done(nid):
                    if done[nid][0] == EMPTY:
                        empties += 1
                    else:
                        filled += 1
                else:
                    unknown = append(unknown, nid)
            if len(unknown) > 0:
                if num == filled:
                    for u in unknown:
                        if EMPTY in done[u]:
                            done.set_done(u, EMPTY)
                            changed = True
                        # else:
                        #    raise Exception("Houston, we've got a problem")
                elif num == filled + len(unknown):
                    for u in unknown:
                        if done.remove(u, EMPTY):
                            changed = True

    return changed


ASCENDING: Final = 1
DESCENDING: Final = -1


def find_moves(pos: Pos, strategy: i64, order: i64) -> list[tuple[i64, i64]]:
    done = pos.done
    cell_id = done.next_cell(pos, strategy)
    if cell_id < 0:
        return []

    if order == ASCENDING:
        return [(cell_id, v) for v in done[cell_id]]
    else:
        # Try higher values first and EMPTY last
        moves = list(reversed([(cell_id, v)
                               for v in done[cell_id] if v != EMPTY]))
        if EMPTY in done[cell_id]:
            moves.append((cell_id, EMPTY))
        return moves


def play_move(pos: Pos, move: tuple[i64, i64]) -> None:
    (cell_id, i) = move
    pos.done.set_done(cell_id, i)


def print_pos(pos: Pos, output: IO[str]) -> None:
    hex = pos.hex
    done = pos.done
    size = hex.size
    for y in range(size):
        print(" " * (size - y - 1), end="", file=output)
        for x in range(size + y):
            pos2 = (x, y)
            id = hex.get_by_pos(pos2).id
            if done.already_done(id):
                c = str(done[id][0]) if done[id][
                    0] != EMPTY else "."
            else:
                c = "?"
            print("%s " % c, end="", file=output)
        print(end="\n", file=output)
    for y in range(1, size):
        print(" " * y, end="", file=output)
        for x in range(y, size * 2 - 1):
            ry = size + y - 1
            pos2 = (x, ry)
            id = hex.get_by_pos(pos2).id
            if done.already_done(id):
                c = str(done[id][0]) if done[id][
                    0] != EMPTY else "."
            else:
                c = "?"
            print("%s " % c, end="", file=output)
        print(end="\n", file=output)


OPEN: Final = 0
SOLVED: Final = 1
IMPOSSIBLE: Final = -1


def solved(pos: Pos, output: StringIO, verbose: bool = False) -> i64:
    hex = pos.hex
    tiles = pos.tiles[:]
    done = pos.done
    exact = True
    all_done = True
    for i in range(hex.count):
        if len(done[i]) == 0:
            return IMPOSSIBLE
        elif done.already_done(i):
            num: i64 = done[i][0]
            tiles[num] -= 1
            if (tiles[num] < 0):
                return IMPOSSIBLE
            vmax: i64 = 0
            vmin: i64 = 0
            if num != EMPTY:
                cells_around = hex.get_by_id(i).links
                for nid in cells_around:
                    if done.already_done(nid):
                        if done[nid][0] != EMPTY:
                            vmin += 1
                            vmax += 1
                    else:
                        vmax += 1

                if (num < vmin) or (num > vmax):
                    return IMPOSSIBLE
                if num != vmin:
                    exact = False
        else:
            all_done = False

    if (not all_done) or (not exact):
        return OPEN

    print_pos(pos, output)
    return SOLVED


def solve_step(prev: Pos, strategy: i64, order: i64, output: StringIO, first: bool = False) -> i64:
    if first:
        pos = prev.clone()
        while constraint_pass(pos):
            pass
    else:
        pos = prev

    moves = find_moves(pos, strategy, order)
    if len(moves) == 0:
        return solved(pos, output)
    else:
        for move in moves:
            # print("Trying (%d, %d)" % (move[0], move[1]))
            ret: i64 = OPEN
            new_pos = pos.clone()
            play_move(new_pos, move)
            # print_pos(new_pos, sys.stdout)
            while constraint_pass(new_pos, move[0]):
                pass
            cur_status = solved(new_pos, output)
            if cur_status != OPEN:
                ret = cur_status
            else:
                ret = solve_step(new_pos, strategy, order, output)
            if ret == SOLVED:
                return SOLVED
    return IMPOSSIBLE


def check_valid(pos: Pos) -> None:
    hex = pos.hex
    tiles = pos.tiles
    # fill missing entries in tiles
    tot: i64 = 0
    for i in range(i64(8)):
        if tiles[i] > 0:
            tot += tiles[i]
        else:
            tiles[i] = 0
    # check total
    if tot != hex.count:
        raise Exception(
            "Invalid input. Expected %d tiles, got %d." % (hex.count, tot))


def solve(pos: Pos, strategy: i64, order: i64, output: StringIO) -> object:
    check_valid(pos)
    return solve_step(pos, strategy, order, output, first=True)


# TODO Write an 'iterator' to go over all x,y positions

def read_file(file: str) -> Pos:
    lines = [line.strip("\r\n") for line in file.splitlines()]
    size = int(lines[0])
    hex = Hex(size)
    linei = 1
    tiles = 8 * [0]
    done = Done(hex.count)
    for y in range(size):
        line = lines[linei][size - y - 1:]
        p = 0
        for x in range(size + y):
            tile = line[p:p + 2]
            p += 2
            if tile[1] == ".":
                inctile = EMPTY
            else:
                inctile = int(tile)
            if inctile >= len(tiles) or inctile < 0:
                assert False, (inctile, tiles)
            tiles[inctile] = tiles[inctile] + 1  # TODO
            # Look for locked tiles
            if tile[0] == "+":
                # print("Adding locked tile: %d at pos %d, %d, id=%d" %
                #      (inctile, x, y, hex.get_by_pos((x, y)).id))
                done.set_done(hex.get_by_pos((x, y)).id, inctile)

        linei += 1
    for y in range(1, size):
        ry = size - 1 + y
        line = lines[linei][y:]
        p = 0
        for x in range(y, size * 2 - 1):
            tile = line[p:p + 2]
            p += 2
            if tile[1] == ".":
                inctile = EMPTY
            else:
                inctile = int(tile)
            tiles[inctile] += 1
            # Look for locked tiles
            if tile[0] == "+":
                # print("Adding locked tile: %d at pos %d, %d, id=%d" %
                #      (inctile, x, ry, hex.get_by_pos((x, ry)).id))
                done.set_done(hex.get_by_pos((x, ry)).id, inctile)
        linei += 1
    hex.link_nodes()
    tv = vec[i64]([x for x in tiles])
    done.filter_tiles(tv)
    return Pos(hex, tv, done)


def solve_file(file: str, strategy: i64, order: i64, output: StringIO) -> None:
    pos = read_file(file)
    solve(pos, strategy, order, output)


LEVELS: Final = {}

LEVELS[2] = ("""
2
  . 1
 . 1 1
  1 .
""", """\
 1 1
. . .
 1 1
""")

LEVELS[10] = ("""
3
  +.+. .
 +. 0 . 2
 . 1+2 1 .
  2 . 0+.
   .+.+.
""", """\
  . . 1
 . 1 . 2
0 . 2 2 .
 . . . .
  0 . .
""")

LEVELS[20] = ("""
3
   . 5 4
  . 2+.+1
 . 3+2 3 .
 +2+. 5 .
   . 3 .
""", """\
  3 3 2
 4 5 . 1
3 5 2 . .
 2 . . .
  . . .
""")

LEVELS[25] = ("""
3
   4 . .
  . . 2 .
 4 3 2 . 4
  2 2 3 .
   4 2 4
""", """\
  3 4 2
 2 4 4 .
. . . 4 2
 . 2 4 3
  . 2 .
""")

LEVELS[30] = ("""
4
    5 5 . .
   3 . 2+2 6
  3 . 2 . 5 .
 . 3 3+4 4 . 3
  4 5 4 . 5 4
   5+2 . . 3
    4 . . .
""", """\
   3 4 3 .
  4 6 5 2 .
 2 5 5 . . 2
. . 5 4 . 4 3
 . 3 5 4 5 4
  . 2 . 3 3
   . . . .
""")

LEVELS[36] = ("""
4
    2 1 1 2
   3 3 3 . .
  2 3 3 . 4 .
 . 2 . 2 4 3 2
  2 2 . . . 2
   4 3 4 . .
    3 2 3 3
""", """\
   3 4 3 2
  3 4 4 . 3
 2 . . 3 4 3
2 . 1 . 3 . 2
 3 3 . 2 . 2
  3 . 2 . 2
   2 2 . 1
""")


def main(loops: i64, level: i64) -> None:
    board, solution = LEVELS[level]
    order = DESCENDING
    strategy = Done.FIRST_STRATEGY
    stream: StringIO | None
    stream = StringIO()

    board = board.strip()
    expected = solution.rstrip()

    range_it = range(loops)

    for _ in range_it:
        stream = StringIO()
        solve_file(board, strategy, order, stream)
        output = stream.getvalue()
        stream = None

    output = '\n'.join(line.rstrip() for line in output.splitlines())
    if output != expected:
        raise AssertionError("got a wrong answer:\n%s\nexpected:\n%s"
                             % (output, expected))


@benchmark(compiled_variant=True)
def hexiom() -> None:
    main(10, DEFAULT_LEVEL)  # Second argument: an item of LEVELS

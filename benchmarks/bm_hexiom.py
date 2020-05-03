# mypy: disallow-untyped-defs

"""
Solver of Hexiom board game.

Benchmark from Laurent Vaucher.

Source: https://github.com/slowfrog/hexiom : hexiom2.py, level36.txt

(Main function tweaked by Armin Rigo.)
"""

from __future__ import division, print_function
from typing import Dict, Any, Optional, List, Tuple, cast, IO

from typing_extensions import Final
from six.moves import xrange, StringIO
from six import u as u_lit, text_type

from benchmarking import benchmark

# 2016-07-07: CPython 3.6 takes ~25 ms to solve the board level 25
DEFAULT_LEVEL = 25


##################################
class Dir(object):

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


DIRS: Final = [Dir(1, 0),
               Dir(-1, 0),
               Dir(0, 1),
               Dir(0, -1),
               Dir(1, 1),
               Dir(-1, -1)]

EMPTY: Final = 7

##################################


class Done(object):
    MIN_CHOICE_STRATEGY: Final = 0
    MAX_CHOICE_STRATEGY: Final = 1
    HIGHEST_VALUE_STRATEGY: Final = 2
    FIRST_STRATEGY: Final = 3
    MAX_NEIGHBORS_STRATEGY: Final = 4
    MIN_NEIGHBORS_STRATEGY: Final = 5

    def __init__(self, count: int, empty: bool = False) -> None:
        self.count = count
        self.cells = None if empty else [
            [0, 1, 2, 3, 4, 5, 6, EMPTY] for i in xrange(count)]

    def clone(self) -> 'Done':
        ret = Done(self.count, True)
        assert self.cells is not None
        ret.cells = [self.cells[i][:] for i in xrange(self.count)]
        return ret

    def __getitem__(self, i: int) -> List[int]:
        assert self.cells is not None
        return self.cells[i]

    def set_done(self, i: int, v: int) -> None:
        assert self.cells is not None
        self.cells[i] = [v]

    def already_done(self, i: int) -> bool:
        assert self.cells is not None
        return len(self.cells[i]) == 1

    def remove(self, i: int, v: int) -> bool:
        assert self.cells is not None
        if v in self.cells[i]:
            self.cells[i].remove(v)
            return True
        else:
            return False

    def remove_all(self, v: int) -> None:
        for i in xrange(self.count):
            self.remove(i, v)

    def remove_unfixed(self, v: int) -> bool:
        changed = False
        for i in xrange(self.count):
            if not self.already_done(i):
                if self.remove(i, v):
                    changed = True
        return changed

    def filter_tiles(self, tiles: List[int]) -> None:
        for v in xrange(8):
            if tiles[v] == 0:
                self.remove_all(v)

    def next_cell_min_choice(self) -> int:
        minlen = 10
        mini = -1
        assert self.cells is not None
        for i in xrange(self.count):
            if 1 < len(self.cells[i]) < minlen:
                minlen = len(self.cells[i])
                mini = i
        return mini

    def next_cell_max_choice(self) -> int:
        maxlen = 1
        maxi = -1
        assert self.cells is not None
        for i in xrange(self.count):
            if maxlen < len(self.cells[i]):
                maxlen = len(self.cells[i])
                maxi = i
        return maxi

    def next_cell_highest_value(self) -> int:
        maxval = -1
        maxi = -1
        assert self.cells is not None
        for i in xrange(self.count):
            if (not self.already_done(i)):
                maxvali = max(k for k in self.cells[i] if k != EMPTY)
                if maxval < maxvali:
                    maxval = maxvali
                    maxi = i
        return maxi

    def next_cell_first(self) -> int:
        for i in xrange(self.count):
            if (not self.already_done(i)):
                return i
        return -1

    def next_cell_max_neighbors(self, pos: 'Pos') -> int:
        maxn = -1
        maxi = -1
        for i in xrange(self.count):
            if not self.already_done(i):
                cells_around = pos.hex.get_by_id(i).links
                n = sum(1 if (self.already_done(nid) and (self[nid][0] != EMPTY)) else 0
                        for nid in cells_around)
                if n > maxn:
                    maxn = n
                    maxi = i
        return maxi

    def next_cell_min_neighbors(self, pos: 'Pos') -> int:
        minn = 7
        mini = -1
        for i in xrange(self.count):
            if not self.already_done(i):
                cells_around = pos.hex.get_by_id(i).links
                n = sum(1 if (self.already_done(nid) and (self[nid][0] != EMPTY)) else 0
                        for nid in cells_around)
                if n < minn:
                    minn = n
                    mini = i
        return mini

    def next_cell(self, pos: 'Pos', strategy: int = HIGHEST_VALUE_STRATEGY) -> int:
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

    def __init__(self, pos: Tuple[int, int], id: int, links: List[int]) -> None:
        self.pos = pos
        self.id = id
        self.links = links

##################################


class Hex(object):

    def __init__(self, size: int) -> None:
        self.size = size
        self.count = 3 * size * (size - 1) + 1
        self.nodes_by_id: List[Optional[Node]] = [None] * self.count
        self.nodes_by_pos = {}
        id = 0
        for y in xrange(size):
            for x in xrange(size + y):
                pos = (x, y)
                node = Node(pos, id, [])
                self.nodes_by_pos[pos] = node
                self.nodes_by_id[node.id] = node
                id += 1
        for y in xrange(1, size):
            for x in xrange(y, size * 2 - 1):
                ry = size + y - 1
                pos = (x, ry)
                node = Node(pos, id, [])
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
                    node.links.append(self.nodes_by_pos[(nx, ny)].id)

    def contains_pos(self, pos: Tuple[int, int]) -> bool:
        return pos in self.nodes_by_pos

    def get_by_pos(self, pos: Tuple[int, int]) -> Node:
        return self.nodes_by_pos[pos]

    def get_by_id(self, id: int) -> Node:
        node = self.nodes_by_id[id]
        return cast(Node, node)


##################################
class Pos(object):

    def __init__(self, hex: Hex, tiles: List[int], done: Optional[Done] = None) -> None:
        self.hex = hex
        self.tiles = tiles
        self.done = Done(hex.count) if done is None else done

    def clone(self) -> 'Pos':
        return Pos(self.hex, self.tiles, self.done.clone())

##################################


def constraint_pass(pos: Pos, last_move: Optional[int] = None) -> bool:
    changed = False
    left = pos.tiles[:]
    done = pos.done

    # Remove impossible values from free cells
    free_cells = (range(done.count) if last_move is None
                  else pos.hex.get_by_id(last_move).links)
    for i in free_cells:
        if not done.already_done(i):
            vmax = 0
            vmin = 0
            cells_around = pos.hex.get_by_id(i).links
            for nid in cells_around:
                if done.already_done(nid):
                    if done[nid][0] != EMPTY:
                        vmin += 1
                        vmax += 1
                else:
                    vmax += 1

            for num in xrange(7):
                if (num < vmin) or (num > vmax):
                    if done.remove(i, num):
                        changed = True

    # Computes how many of each value is still free
    assert done.cells is not None
    for cell in done.cells:
        if len(cell) == 1:
            left[cell[0]] -= 1

    for v in xrange(8):
        # If there is none, remove the possibility from all tiles
        if (pos.tiles[v] > 0) and (left[v] == 0):
            if done.remove_unfixed(v):
                changed = True
        else:
            possible = sum((1 if v in cell else 0) for cell in done.cells)
            # If the number of possible cells for a value is exactly the number of available tiles
            # put a tile in each cell
            if pos.tiles[v] == possible:
                for i in xrange(done.count):
                    cell = done.cells[i]
                    if (not done.already_done(i)) and (v in cell):
                        done.set_done(i, v)
                        changed = True

    # Force empty or non-empty around filled cells
    filled_cells = (range(done.count) if last_move is None
                    else [last_move])
    for i in filled_cells:
        if done.already_done(i):
            num = done[i][0]
            empties = 0
            filled = 0
            unknown = []
            cells_around = pos.hex.get_by_id(i).links
            for nid in cells_around:
                if done.already_done(nid):
                    if done[nid][0] == EMPTY:
                        empties += 1
                    else:
                        filled += 1
                else:
                    unknown.append(nid)
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


def find_moves(pos: Pos, strategy: int, order: int) -> List[Tuple[int, int]]:
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


def play_move(pos: Pos, move: Tuple[int, int]) -> None:
    (cell_id, i) = move
    pos.done.set_done(cell_id, i)


def print_pos(pos: Pos, output: IO[str]) -> None:
    hex = pos.hex
    done = pos.done
    size = hex.size
    for y in xrange(size):
        print(u_lit(" ") * (size - y - 1), end=u_lit(""), file=output)
        for x in xrange(size + y):
            pos2 = (x, y)
            id = hex.get_by_pos(pos2).id
            if done.already_done(id):
                c = text_type(done[id][0]) if done[id][
                    0] != EMPTY else u_lit(".")
            else:
                c = u_lit("?")
            print(u_lit("%s ") % c, end=u_lit(""), file=output)
        print(end=u_lit("\n"), file=output)
    for y in xrange(1, size):
        print(u_lit(" ") * y, end=u_lit(""), file=output)
        for x in xrange(y, size * 2 - 1):
            ry = size + y - 1
            pos2 = (x, ry)
            id = hex.get_by_pos(pos2).id
            if done.already_done(id):
                c = text_type(done[id][0]) if done[id][
                    0] != EMPTY else u_lit(".")
            else:
                c = u_lit("?")
            print(u_lit("%s ") % c, end=u_lit(""), file=output)
        print(end=u_lit("\n"), file=output)


OPEN: Final = 0
SOLVED: Final = 1
IMPOSSIBLE: Final = -1


def solved(pos: Pos, output: StringIO, verbose: bool = False) -> int:
    hex = pos.hex
    tiles = pos.tiles[:]
    done = pos.done
    exact = True
    all_done = True
    for i in xrange(hex.count):
        if len(done[i]) == 0:
            return IMPOSSIBLE
        elif done.already_done(i):
            num = done[i][0]
            tiles[num] -= 1
            if (tiles[num] < 0):
                return IMPOSSIBLE
            vmax = 0
            vmin = 0
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


def solve_step(prev: Pos, strategy: int, order: int, output: StringIO, first: bool = False) -> int:
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
            ret = OPEN
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
    tot = 0
    for i in xrange(8):
        if tiles[i] > 0:
            tot += tiles[i]
        else:
            tiles[i] = 0
    # check total
    if tot != hex.count:
        raise Exception(
            "Invalid input. Expected %d tiles, got %d." % (hex.count, tot))


def solve(pos: Pos, strategy: int, order: int, output: StringIO) -> object:
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
    for y in xrange(size):
        line = lines[linei][size - y - 1:]
        p = 0
        for x in xrange(size + y):
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
                #      (inctile, x, y, hex.get_by_pos((x, y)).id))
                done.set_done(hex.get_by_pos((x, y)).id, inctile)

        linei += 1
    for y in xrange(1, size):
        ry = size - 1 + y
        line = lines[linei][y:]
        p = 0
        for x in xrange(y, size * 2 - 1):
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
    done.filter_tiles(tiles)
    return Pos(hex, tiles, done)


def solve_file(file: str, strategy: int, order: int, output: StringIO) -> None:
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


def main(loops: int, level: int) -> None:
    board, solution = LEVELS[level]
    order = DESCENDING
    strategy = Done.FIRST_STRATEGY
    stream: Optional[StringIO]
    stream = StringIO()

    board = board.strip()
    expected = solution.rstrip()

    range_it = xrange(loops)

    for _ in range_it:
        stream = StringIO()
        solve_file(board, strategy, order, stream)
        output = stream.getvalue()
        stream = None

    output = '\n'.join(line.rstrip() for line in output.splitlines())
    if output != expected:
        raise AssertionError("got a wrong answer:\n%s\nexpected:\n%s"
                             % (output, expected))


@benchmark
def hexiom() -> None:
    main(10, DEFAULT_LEVEL)  # Second argument: an item of LEVELS

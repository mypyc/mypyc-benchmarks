"""
deltablue.py
============

Ported for the PyPy project.
Contributed by Daniel Lindsley

This implementation of the DeltaBlue benchmark was directly ported
from the `V8's source code`_, which was in turn derived
from the Smalltalk implementation by John Maloney and Mario
Wolczko. The original Javascript implementation was licensed under the GPL.

It's been updated in places to be more idiomatic to Python (for loops over
collections, a couple magic methods, ``OrderedCollection`` being a list & things
altering those collections changed to the builtin methods) but largely retains
the layout & logic from the original. (Ugh.)

.. _`V8's source code`: (https://github.com/v8/v8/blob/master/benchmarks/deltablue.js)
"""

from __future__ import print_function, annotations
from abc import abstractmethod
from typing import Optional, Iterable, List

from typing_extensions import Final

from benchmarking import benchmark


# The JS variant implements "OrderedCollection", which basically completely
# overlaps with ``list``. So we'll cheat. :D
OrderedCollection = list


# HOORAY FOR GLOBALS... Oh wait.
# In spirit of the original, we'll keep it, but ugh.
planner: Optional[Planner] = None


class Strength(object):
    def __init__(self, strength: int, name: str) -> None:
        super(Strength, self).__init__()
        self.strength = strength
        self.name = name

    @classmethod
    def stronger(cls, s1: Strength, s2: Strength) -> bool:
        return s1.strength < s2.strength

    @classmethod
    def weaker(cls, s1: Strength, s2: Strength) -> bool:
        return s1.strength > s2.strength

    @classmethod
    def weakest_of(cls, s1: Strength, s2: Strength) -> Strength:
        if cls.weaker(s1, s2):
            return s1

        return s2

    @classmethod
    def strongest(cls, s1: Strength, s2: Strength) -> Strength:
        if cls.stronger(s1, s2):
            return s1

        return s2

    def next_weaker(self) -> Strength:
        strengths = {
            0: WEAKEST,
            1: WEAK_DEFAULT,
            2: NORMAL,
            3: STRONG_DEFAULT,
            4: PREFERRED,
            # TODO: This looks like a bug in the original code. Shouldn't this be
            #       ``STRONG_PREFERRED? Keeping for porting sake...
            5: REQUIRED,
        }
        return strengths[self.strength]


REQUIRED: Final = Strength(0, "required")
STRONG_PREFERRED: Final = Strength(1, "strongPreferred")
PREFERRED: Final = Strength(2, "preferred")
STRONG_DEFAULT: Final = Strength(3, "strongDefault")
NORMAL: Final = Strength(4, "normal")
WEAK_DEFAULT: Final = Strength(5, "weakDefault")
WEAKEST: Final = Strength(6, "weakest")


class Constraint(object):

    def __init__(self, strength: Strength) -> None:
        super(Constraint, self).__init__()
        self.strength = strength

    def add_constraint(self) -> None:
        global planner
        self.add_to_graph()
        assert planner is not None
        planner.incremental_add(self)

    def satisfy(self, mark: int) -> Optional[Constraint]:
        global planner
        self.choose_method(mark)

        if not self.is_satisfied():
            if self.strength == REQUIRED:
                print('Could not satisfy a required constraint!')

            return None

        self.mark_inputs(mark)
        out = self.output()
        overridden = out.determined_by

        if overridden is not None:
            overridden.mark_unsatisfied()

        out.determined_by = self

        assert planner is not None
        if not planner.add_propagate(self, mark):
            print('Cycle encountered')

        out.mark = mark
        return overridden

    def destroy_constraint(self) -> None:
        global planner
        if self.is_satisfied():
            assert planner is not None
            planner.incremental_remove(self)
        else:
            self.remove_from_graph()

    def is_input(self) -> bool:
        return False

    @abstractmethod
    def add_to_graph(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove_from_graph(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_satisfied(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def mark_unsatisfied(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def output(self) -> Variable:
        raise NotImplementedError

    @abstractmethod
    def recalculate(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def choose_method(self, mark: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def mark_inputs(self, mark: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def inputs_known(self, mark: int) -> bool:
        raise NotImplementedError


class UrnaryConstraint(Constraint):

    def __init__(self, v: Variable, strength: Strength) -> None:
        super(UrnaryConstraint, self).__init__(strength)
        self.my_output = v
        self.satisfied = False
        self.add_constraint()

    def add_to_graph(self) -> None:
        self.my_output.add_constraint(self)
        self.satisfied = False

    def choose_method(self, mark: int) -> None:
        if self.my_output.mark != mark and \
           Strength.stronger(self.strength, self.my_output.walk_strength):
            self.satisfied = True
        else:
            self.satisfied = False

    def is_satisfied(self) -> bool:
        return self.satisfied

    def mark_inputs(self, mark: int) -> None:
        # No-ops.
        pass

    def output(self) -> Variable:
        # Ugh. Keeping it for consistency with the original. So much for
        # "we're all adults here"...
        return self.my_output

    def recalculate(self) -> None:
        self.my_output.walk_strength = self.strength
        self.my_output.stay = not self.is_input()

        if self.my_output.stay:
            self.execute()

    def mark_unsatisfied(self) -> None:
        self.satisfied = False

    def inputs_known(self, mark: int) -> bool:
        return True

    def remove_from_graph(self) -> None:
        if self.my_output is not None:
            self.my_output.remove_constraint(self)
            self.satisfied = False


class StayConstraint(UrnaryConstraint):

    def __init__(self, v: Variable, string: Strength) -> None:
        super(StayConstraint, self).__init__(v, string)

    def execute(self) -> None:
        # The methods, THEY DO NOTHING.
        pass


class EditConstraint(UrnaryConstraint):

    def __init__(self, v: Variable, string: Strength) -> None:
        super(EditConstraint, self).__init__(v, string)

    def is_input(self) -> bool:
        return True

    def execute(self) -> None:
        # This constraint also does nothing.
        pass


class Direction(object):
    # Hooray for things that ought to be structs!
    NONE: Final = 0
    FORWARD: Final = 1
    BACKWARD: Final = -1


class BinaryConstraint(Constraint):

    def __init__(self, v1: Variable, v2: Variable, strength: Strength) -> None:
        super(BinaryConstraint, self).__init__(strength)
        self.v1 = v1
        self.v2 = v2
        self.direction = Direction.NONE
        self.add_constraint()

    def choose_method(self, mark: int) -> None:
        if self.v1.mark == mark:
            if self.v2.mark != mark and Strength.stronger(self.strength, self.v2.walk_strength):
                self.direction = Direction.FORWARD
            else:
                self.direction = Direction.BACKWARD

        if self.v2.mark == mark:
            if self.v1.mark != mark and Strength.stronger(self.strength, self.v1.walk_strength):
                self.direction = Direction.BACKWARD
            else:
                self.direction = Direction.NONE

        if Strength.weaker(self.v1.walk_strength, self.v2.walk_strength):
            if Strength.stronger(self.strength, self.v1.walk_strength):
                self.direction = Direction.BACKWARD
            else:
                self.direction = Direction.NONE
        else:
            if Strength.stronger(self.strength, self.v2.walk_strength):
                self.direction = Direction.FORWARD
            else:
                self.direction = Direction.BACKWARD

    def add_to_graph(self) -> None:
        self.v1.add_constraint(self)
        self.v2.add_constraint(self)
        self.direction = Direction.NONE

    def is_satisfied(self) -> bool:
        return self.direction != Direction.NONE

    def mark_inputs(self, mark: int) -> None:
        self.input().mark = mark

    def input(self) -> Variable:
        if self.direction == Direction.FORWARD:
            return self.v1

        return self.v2

    def output(self) -> Variable:
        if self.direction == Direction.FORWARD:
            return self.v2

        return self.v1

    def recalculate(self) -> None:
        ihn = self.input()
        out = self.output()
        out.walk_strength = Strength.weakest_of(
            self.strength, ihn.walk_strength)
        out.stay = ihn.stay

        if out.stay:
            self.execute()

    def mark_unsatisfied(self) -> None:
        self.direction = Direction.NONE

    def inputs_known(self, mark: int) -> bool:
        i = self.input()
        return i.mark == mark or i.stay or i.determined_by is None

    def remove_from_graph(self) -> None:
        if self.v1 is not None:
            self.v1.remove_constraint(self)

        if self.v2 is not None:
            self.v2.remove_constraint(self)

        self.direction = Direction.NONE


class ScaleConstraint(BinaryConstraint):

    def __init__(self, src: Variable, scale: Variable, offset: Variable, dest: Variable,
                 strength: Strength) -> None:
        self.direction = Direction.NONE
        self.scale = scale
        self.offset = offset
        super(ScaleConstraint, self).__init__(src, dest, strength)

    def add_to_graph(self) -> None:
        super(ScaleConstraint, self).add_to_graph()
        self.scale.add_constraint(self)
        self.offset.add_constraint(self)

    def remove_from_graph(self) -> None:
        super(ScaleConstraint, self).remove_from_graph()

        if self.scale is not None:
            self.scale.remove_constraint(self)

        if self.offset is not None:
            self.offset.remove_constraint(self)

    def mark_inputs(self, mark: int) -> None:
        super(ScaleConstraint, self).mark_inputs(mark)
        self.scale.mark = mark
        self.offset.mark = mark

    def execute(self) -> None:
        if self.direction == Direction.FORWARD:
            self.v2.value = self.v1.value * self.scale.value + self.offset.value
        else:
            self.v1.value = (
                self.v2.value - self.offset.value) / self.scale.value

    def recalculate(self) -> None:
        ihn = self.input()
        out = self.output()
        out.walk_strength = Strength.weakest_of(
            self.strength, ihn.walk_strength)
        out.stay = ihn.stay and self.scale.stay and self.offset.stay

        if out.stay:
            self.execute()


class EqualityConstraint(BinaryConstraint):

    def execute(self) -> None:
        self.output().value = self.input().value


class Variable(object):

    def __init__(self, name: str, initial_value: float = 0) -> None:
        super(Variable, self).__init__()
        self.name = name
        self.value = initial_value
        self.constraints: List[Constraint] = OrderedCollection()
        self.determined_by: Optional[Constraint] = None
        self.mark = 0
        self.walk_strength = WEAKEST
        self.stay = True

    def __repr__(self) -> str:
        # To make debugging this beast from pdb easier...
        return '<Variable: %s - %s>' % (
            self.name,
            self.value
        )

    def add_constraint(self, constraint: Constraint) -> None:
        self.constraints.append(constraint)

    def remove_constraint(self, constraint: Constraint) -> None:
        self.constraints.remove(constraint)

        if self.determined_by == constraint:
            self.determined_by = None


class Planner(object):

    def __init__(self) -> None:
        super(Planner, self).__init__()
        self.current_mark = 0

    def incremental_add(self, constraint: Constraint) -> None:
        mark = self.new_mark()
        overridden = constraint.satisfy(mark)

        while overridden is not None:
            overridden = overridden.satisfy(mark)

    def incremental_remove(self, constraint: Constraint) -> None:
        out = constraint.output()
        constraint.mark_unsatisfied()
        constraint.remove_from_graph()
        unsatisfied = self.remove_propagate_from(out)
        strength = REQUIRED
        # Do-while, the Python way.
        repeat = True

        while repeat:
            for u in unsatisfied:
                if u.strength == strength:
                    self.incremental_add(u)

                strength = strength.next_weaker()

            repeat = strength != WEAKEST

    def new_mark(self) -> int:
        self.current_mark += 1
        return self.current_mark

    def make_plan(self, sources: List[Constraint]) -> Plan:
        mark = self.new_mark()
        plan = Plan()
        todo = sources

        while len(todo):
            c = todo.pop(0)

            if c.output().mark != mark and c.inputs_known(mark):
                plan.add_constraint(c)
                c.output().mark = mark
                self.add_constraints_consuming_to(c.output(), todo)

        return plan

    def extract_plan_from_constraints(self, constraints: Iterable[Constraint]) -> Plan:
        sources = OrderedCollection()

        for c in constraints:
            if c.is_input() and c.is_satisfied():
                sources.append(c)

        return self.make_plan(sources)

    def add_propagate(self, c: Constraint, mark: int) -> bool:
        todo = OrderedCollection()
        todo.append(c)

        while len(todo):
            d = todo.pop(0)

            if d.output().mark == mark:
                self.incremental_remove(c)
                return False

            d.recalculate()
            self.add_constraints_consuming_to(d.output(), todo)

        return True

    def remove_propagate_from(self, out: Variable) -> List[Constraint]:
        out.determined_by = None
        out.walk_strength = WEAKEST
        out.stay = True
        unsatisfied = OrderedCollection()
        todo = OrderedCollection()
        todo.append(out)

        while len(todo):
            v = todo.pop(0)

            for c in v.constraints:
                if not c.is_satisfied():
                    unsatisfied.append(c)

            determining = v.determined_by

            for c in v.constraints:
                if c != determining and c.is_satisfied():
                    c.recalculate()
                    todo.append(c.output())

        return unsatisfied

    def add_constraints_consuming_to(self, v: Variable, coll: List[Constraint]) -> None:
        determining = v.determined_by
        cc = v.constraints

        for c in cc:
            if c != determining and c.is_satisfied():
                # I guess we're just updating a reference (``coll``)? Seems
                # inconsistent with the rest of the implementation, where they
                # return the lists...
                coll.append(c)


class Plan(object):

    def __init__(self) -> None:
        super(Plan, self).__init__()
        self.v: List[Constraint] = []

    def add_constraint(self, c: Constraint) -> None:
        self.v.append(c)

    def __len__(self) -> int:
        return len(self.v)

    def __getitem__(self, index: int) -> Constraint:
        return self.v[index]

    def execute(self) -> None:
        for c in self.v:
            c.execute()


# Main

def chain_test(n: int) -> None:
    """
    This is the standard DeltaBlue benchmark. A long chain of equality
    constraints is constructed with a stay constraint on one end. An
    edit constraint is then added to the opposite end and the time is
    measured for adding and removing this constraint, and extracting
    and executing a constraint satisfaction plan. There are two cases.
    In case 1, the added constraint is stronger than the stay
    constraint and values must propagate down the entire length of the
    chain. In case 2, the added constraint is weaker than the stay
    constraint so it cannot be accomodated. The cost in this case is,
    of course, very low. Typical situations lie somewhere between these
    two extremes.
    """
    global planner
    planner = Planner()
    prev: Optional[Variable] = None

    # We need to go up to n inclusively.
    for i in range(n + 1):
        name = "v%s" % i
        v = Variable(name)

        if prev is not None:
            EqualityConstraint(prev, v, REQUIRED)

        if i == 0:
            first = v

        if i == n:
            last = v

        prev = v

    StayConstraint(last, STRONG_DEFAULT)
    edit = EditConstraint(first, PREFERRED)
    edits = OrderedCollection()
    edits.append(edit)
    plan = planner.extract_plan_from_constraints(edits)

    for i in range(100):
        first.value = i
        plan.execute()

        if last.value != i:
            print("Chain test failed.")


def projection_test(n: int) -> None:
    """
    This test constructs a two sets of variables related to each
    other by a simple linear transformation (scale and offset). The
    time is measured to change a variable on either side of the
    mapping and to change the scale and offset factors.
    """
    global planner
    planner = Planner()
    scale = Variable("scale", 10)
    offset = Variable("offset", 1000)

    dests = OrderedCollection()

    for i in range(n):
        src = Variable("src%s" % i, i)
        dst = Variable("dst%s" % i, i)
        dests.append(dst)
        StayConstraint(src, NORMAL)
        ScaleConstraint(src, scale, offset, dst, REQUIRED)

    change(src, 17)

    if dst.value != 1170:
        print("Projection 1 failed")

    change(dst, 1050)

    assert src is not None
    if src.value != 5:
        print("Projection 2 failed")

    change(scale, 5)

    for i in range(n - 1):
        if dests[i].value != (i * 5 + 1000):
            print("Projection 3 failed")

    change(offset, 2000)

    for i in range(n - 1):
        if dests[i].value != (i * 5 + 2000):
            print("Projection 4 failed")


def change(v: Variable, new_value: int) -> None:
    global planner
    edit = EditConstraint(v, PREFERRED)
    edits = OrderedCollection()
    edits.append(edit)

    assert planner is not None
    plan = planner.extract_plan_from_constraints(edits)

    for i in range(10):
        v.value = new_value
        plan.execute()

    edit.destroy_constraint()


def run_delta_blue(n: int) -> None:
    chain_test(n)
    projection_test(n)


@benchmark
def deltablue() -> None:
    n = 100
    for i in range(10):
        run_delta_blue(n)

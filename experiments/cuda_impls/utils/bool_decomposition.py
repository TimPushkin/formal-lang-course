from itertools import product
from typing import Any
from typing import NamedTuple

import pycubool as cb
from pyformlang.finite_automaton import Epsilon
from pyformlang.finite_automaton import EpsilonNFA

from project.cfpq.rsm import Rsm


class BoolDecomposition:
    class StateInfo(NamedTuple):
        data: Any
        is_start: bool
        is_final: bool

        def __eq__(self, other):
            return (
                isinstance(other, BoolDecomposition.StateInfo)
                and self.data == other.data
            )

        def __hash__(self):
            return hash(self.data)

    def __init__(
        self,
        states: list[StateInfo] | None = None,
        adjs: dict[Any, cb.Matrix] | None = None,
    ):
        self.states: list[BoolDecomposition.StateInfo] = (
            states if states is not None else []
        )
        self.adjs: dict[Any, cb.Matrix] = adjs if adjs is not None else {}

    @classmethod
    def from_nfa(
        cls, nfa: EpsilonNFA, sort_states: bool = False
    ) -> "BoolDecomposition":
        # Construct states, removing duplicates
        states = list(
            set(
                cls.StateInfo(
                    data=st.value,
                    is_start=st in nfa.start_states,
                    is_final=st in nfa.final_states,
                )
                for st in nfa.states
            )
        )
        if sort_states:
            states = sorted(states, key=lambda st: st.data)

        # Construct adjacency matrices
        adjs = {}
        transitions = nfa.to_dict()
        for n_from in transitions:
            for symbol, ns_to in transitions[n_from].items():
                adj = adjs.setdefault(
                    symbol.value if not isinstance(symbol, Epsilon) else symbol,
                    cb.Matrix.empty((len(states), len(states))),
                )
                beg_index = next(i for i, s in enumerate(states) if s.data == n_from)
                for n_to in ns_to if isinstance(ns_to, set) else {ns_to}:
                    end_index = next(i for i, s in enumerate(states) if s.data == n_to)
                    adj[beg_index, end_index] = True

        return cls(states, adjs)

    @classmethod
    def from_rsm(cls, rsm: Rsm, sort_states: bool = False) -> "BoolDecomposition":
        # Construct states with respect to box variables, removing duplicates
        states = list(
            {
                cls.StateInfo(
                    data=(var, st.value),
                    is_start=st in nfa.start_states,
                    is_final=st in nfa.final_states,
                )
                for var, nfa in rsm.boxes.items()
                for st in nfa.states
            }
        )
        if sort_states:
            states.sort(key=lambda st: (st.data[0].value, st.data[1]))

        # Construct adjacency matrices
        adjs = {}
        for var, nfa in rsm.boxes.items():
            transitions = nfa.to_dict()
            for n_from in transitions:
                for symbol, ns_to in transitions[n_from].items():
                    adj = adjs.setdefault(
                        symbol.value if not isinstance(symbol, Epsilon) else symbol,
                        cb.Matrix.empty((len(states), len(states))),
                    )
                    start_index = next(
                        i for i, s in enumerate(states) if s.data == (var, n_from)
                    )
                    for n_to in ns_to if isinstance(ns_to, set) else {ns_to}:
                        end_index = next(
                            i for i, s in enumerate(states) if s.data == (var, n_to)
                        )
                        adj[start_index, end_index] = True

        return cls(states, adjs)

    def intersect(self, other: "BoolDecomposition") -> "BoolDecomposition":
        # Set of states of the intersection is the product of the given sets of states
        # State is "start" if both of its element states are "start"
        # State is "final" if both of its element states are "final"
        states = [
            self.StateInfo(
                data=(st1.data, st2.data),
                is_start=st1.is_start and st2.is_start,
                is_final=st1.is_final and st2.is_final,
            )
            for st1, st2 in product(self.states, other.states)
        ]
        if len(states) == 0:  # Not to create empty matrices
            return BoolDecomposition([], {})

        # Set of symbols of the intersection is the union of the given sets of symbols
        # Adjacency matrix for a symbol is a kronecker product of the given matrices of
        # this symbol
        adjs = {}
        for symbol in set(self.adjs.keys()).union(set(other.adjs.keys())):
            if symbol in self.adjs and symbol in other.adjs:
                adjs[symbol] = self.adjs[symbol].kronecker(other.adjs[symbol])
            else:
                adjs[symbol] = cb.Matrix.empty((len(states), len(states)))

        return BoolDecomposition(states, adjs)

    def transitive_closure_any_symbol(self) -> tuple[list[int], list[int]]:
        if len(self.states) == 0:  # pycubool cannot create empty matrices
            return [], []

        # Gather all matrices to get all existing paths
        adj_all = cb.Matrix.empty((len(self.states), len(self.states)))
        for adj in self.adjs.values():
            adj_all = adj_all.ewiseadd(adj)

        # Transitive closure by repeated-squaring-like approach
        while True:
            # nvals gives the number of paths
            prev_path_num = adj_all.nvals
            # Multiplication gives new paths, while sum retains the old ones
            adj_all.mxm(adj_all, out=adj_all, accumulate=True)
            # If no new paths appear, all paths have been discovered
            if prev_path_num == adj_all.nvals:
                break

        # Convert to a more user-friendly representation
        return adj_all.to_lists()

    def _direct_sum(self, other: "BoolDecomposition") -> "BoolDecomposition":
        states = self.states + other.states

        adjs = {}
        for symbol in set(self.adjs.keys()).intersection(set(other.adjs.keys())):
            dsum = cb.Matrix.empty((len(states), len(states)))
            for i, j in self.adjs[symbol]:
                dsum[i, j] = True
            for i, j in other.adjs[symbol]:
                dsum[len(self.states) + i, len(self.states) + j] = True
            adjs[symbol] = dsum

        return BoolDecomposition(states, adjs)

    def constrained_bfs(
        self, constraint: "BoolDecomposition", separated: bool = False
    ) -> set[int] | set[tuple[int, int]]:
        # Save states number because will use them heavily for matrix construction
        n = len(constraint.states)

        direct_sum = constraint._direct_sum(self)

        # Create initial front from starts of constraint (left) and self (right)
        start_states_indices = [i for i, st in enumerate(self.states) if st.is_start]
        init_front = (
            _init_bfs_front(self.states, constraint.states)
            if not separated
            else _init_separated_bfs_front(
                self.states, constraint.states, start_states_indices
            )
        )

        # Create visited, fill with zeroes instead of init_front to get rid of initial
        # positions in the result
        visited = cb.Matrix.empty(init_front.shape)

        # Perform matrix-multiplication-based-BFS until visited stops changing
        while True:
            old_visited_nvals = visited.nvals

            # Perform a BFS step for each matrix in direct sum
            for adj in direct_sum.adjs.values():
                # Compute new front for the symbol
                front_part = (
                    visited.mxm(adj) if init_front is None else init_front.mxm(adj)
                )
                # Transform the resulting front so that:
                # 1. It only contains rows with non-zeros in both parts.
                # 2. Its left part contains non-zeroes only on its main diagonal.
                visited = visited.ewiseadd(_transform_front_part(front_part, n))

            # Can use visited instead now
            init_front = None

            # If no new non-zero elements have appeared, we've visited all we can
            if visited.nvals == old_visited_nvals:
                break

        # If visited a final self-state in final constraint-state, we found a result
        results = set()
        for i, j in visited.to_list():
            # Check that the element is from the self part (which is the main BFS part)
            # and the final state requirements are satisfied
            if j >= n and constraint.states[i % n].is_final:  # % is for separated BFS
                self_st_index = j - n
                if self.states[self_st_index].is_final:
                    results.add(
                        self_st_index
                        if not separated
                        else (start_states_indices[i // n], self_st_index)
                    )
        return results


def _init_bfs_front(
    self_states: list[BoolDecomposition.StateInfo],
    constr_states: list[BoolDecomposition.StateInfo],
    self_start_indices: list[int] | None = None,
) -> cb.Matrix:
    front = cb.Matrix.empty((len(constr_states), len(constr_states) + len(self_states)))

    if self_start_indices is None:
        self_start_indices = [j for j, st in enumerate(self_states) if st.is_start]

    for i, st in enumerate(constr_states):
        if st.is_start:
            front[i, i] = True  # Mark diagonal element as start
            for j in self_start_indices:
                front[i, len(constr_states) + j] = True  # Fill start row

    return front


def _init_separated_bfs_front(
    self_states: list[BoolDecomposition.StateInfo],
    constr_states: list[BoolDecomposition.StateInfo],
    start_states_indices: list[int],
) -> cb.Matrix:
    fronts = [
        _init_bfs_front(
            self_states,
            constr_states,
            self_start_indices=[st_i],
        )
        for st_i in start_states_indices
    ]

    if len(fronts) == 0:
        return cb.Matrix.empty(
            (len(constr_states), len(constr_states) + len(self_states))
        )

    # Build the united front as a vertical stack of the separated fronts
    result = cb.Matrix.empty(
        (len(fronts) * len(constr_states), len(constr_states) + len(self_states))
    )
    vstack_helper = cb.Matrix.empty((len(fronts), 1))
    for i, front in enumerate(fronts):
        vstack_helper.build(rows={i}, cols={0})
        result = result.ewiseadd(vstack_helper.kronecker(front))
    return result


def _transform_front_part(front_part: cb.Matrix, constr_states_num: int) -> cb.Matrix:
    transformed_front_part = cb.Matrix.empty(front_part.shape)
    # Perform the transformation by rows
    for i, j in front_part.to_list():
        # If the element is from the constraint part
        if j < constr_states_num:
            non_zero_row_right = front_part[i : i + 1, constr_states_num:]
            # If the right part contains non-zero elements
            if non_zero_row_right.nvals > 0:
                # Account for separated front
                row_shift = i // constr_states_num * constr_states_num
                # Mark the row in the left part
                transformed_front_part[row_shift + j, j] = True
                # Update right part of the row
                for _, r_j in non_zero_row_right:
                    transformed_front_part[
                        row_shift + j, constr_states_num + r_j
                    ] = True
    return transformed_front_part

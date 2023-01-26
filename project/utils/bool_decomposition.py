from itertools import product
from typing import Any
from typing import NamedTuple
from typing import TYPE_CHECKING

from pyformlang.finite_automaton import Epsilon
from pyformlang.finite_automaton import EpsilonNFA
from scipy import sparse

if TYPE_CHECKING:
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
        adjs: dict[Any, sparse.csr_array] | None = None,
    ):
        self.states: list[BoolDecomposition.StateInfo] = (
            states if states is not None else []
        )
        self.adjs: dict[Any, sparse.csr_array] = adjs if adjs is not None else {}

    @classmethod
    def from_nfa(
        cls, nfa: EpsilonNFA, sort_states: bool = False
    ) -> "BoolDecomposition":
        # Construct states, removing duplicates
        states = list(
            {
                cls.StateInfo(
                    data=st.value,
                    is_start=st in nfa.start_states,
                    is_final=st in nfa.final_states,
                )
                for st in nfa.states
            }
        )
        if sort_states:
            states.sort(key=lambda st: st.data)

        # Construct adjacency matrices
        adjs = {}
        transitions = nfa.to_dict()
        for n_from in transitions:
            for symbol, ns_to in transitions[n_from].items():
                adj = adjs.setdefault(
                    symbol.value if not isinstance(symbol, Epsilon) else symbol,
                    sparse.dok_array((len(states), len(states)), dtype=bool),
                )
                start_index = next(i for i, s in enumerate(states) if s.data == n_from)
                for n_to in ns_to if isinstance(ns_to, set) else {ns_to}:
                    end_index = next(i for i, s in enumerate(states) if s.data == n_to)
                    adj[start_index, end_index] = True
        # DOK is good for construction, CSR is good for calculations
        for key in adjs:
            adjs[key] = adjs[key].tocsr()

        return cls(states, adjs)

    @classmethod
    def from_rsm(cls, rsm: "Rsm", sort_states: bool = False) -> "BoolDecomposition":
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
                        sparse.dok_array((len(states), len(states)), dtype=bool),
                    )
                    start_index = next(
                        i for i, s in enumerate(states) if s.data == (var, n_from)
                    )
                    for n_to in ns_to if isinstance(ns_to, set) else {ns_to}:
                        end_index = next(
                            i for i, s in enumerate(states) if s.data == (var, n_to)
                        )
                        adj[start_index, end_index] = True
        # DOK is good for construction, CSR is good for calculations
        for key in adjs:
            adjs[key] = adjs[key].tocsr()

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
                adjs[symbol] = sparse.csr_array(
                    sparse.kron(self.adjs[symbol], other.adjs[symbol], format="csr")
                )
            else:
                adjs[symbol] = sparse.csr_array((len(states), len(states)), dtype=bool)

        return BoolDecomposition(states, adjs)

    def transitive_closure_any_symbol(self) -> tuple[list[int], list[int]]:
        # Gather all matrices to get all existing paths
        adj_all = sum(
            self.adjs.values(),
            start=sparse.csr_array((len(self.states), len(self.states)), dtype=bool),
        )
        # Remove explicit zeroes (just in case) to use nnz later
        adj_all.eliminate_zeros()

        # Transitive closure by repeated-squaring-like approach
        while True:
            # nnz gives the number of paths
            prev_path_num = adj_all.nnz
            # Multiplication gives new paths, while sum retains the old ones
            adj_all += adj_all @ adj_all
            # If no new paths appear, all paths have been discovered
            if prev_path_num == adj_all.nnz:
                break

        # Convert to a more user-friendly representation
        return adj_all.nonzero()

    def _direct_sum(self, other: "BoolDecomposition") -> "BoolDecomposition":
        states = self.states + other.states

        adjs = {}
        for symbol in set(self.adjs.keys()).intersection(set(other.adjs.keys())):
            adjs[symbol] = sparse.csr_array(
                sparse.bmat([[self.adjs[symbol], None], [None, other.adjs[symbol]]])
            )

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
        visited = sparse.csr_array(init_front.shape, dtype=bool)

        # Perform matrix-multiplication-based-BFS until visited stops changing
        while True:
            old_visited_nnz = visited.nnz

            # Perform a BFS step for each matrix in direct sum
            for adj in direct_sum.adjs.values():
                # Compute new front for the symbol
                front_part = visited @ adj if init_front is None else init_front @ adj
                # Transform the resulting front so that:
                # 1. It only contains rows with non-zeros in both parts.
                # 2. Its left part contains non-zeroes only on its main diagonal.
                visited += _transform_front_part(front_part, n)

            # Can use visited instead now
            init_front = None

            # If no new non-zero elements have appeared, we've visited all we can
            if visited.nnz == old_visited_nnz:
                break

        # If visited a final self-state in final constraint-state, we found a result
        results = set()
        for i, j in zip(*visited.nonzero()):
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
    self_start_row: sparse.lil_array | None = None,
) -> sparse.csr_array:
    front = sparse.lil_array(
        (len(constr_states), len(constr_states) + len(self_states)), dtype=bool
    )

    if self_start_row is None:
        self_start_row = sparse.lil_array(
            [st.is_start for st in self_states], dtype=bool
        )

    for i, st in enumerate(constr_states):
        if st.is_start:
            front[i, i] = True  # Mark diagonal element as start
            front[i, len(constr_states) :] = self_start_row  # Fill start row

    return front.tocsr()


def _init_separated_bfs_front(
    self_states: list[BoolDecomposition.StateInfo],
    constr_states: list[BoolDecomposition.StateInfo],
    start_states_indices: list[int],
) -> sparse.csr_array:
    fronts = [
        _init_bfs_front(
            self_states,
            constr_states,
            self_start_row=sparse.lil_array(
                [i == st_i for i in range(len(self_states))], dtype=bool
            ),
        )
        for st_i in start_states_indices
    ]
    return (
        sparse.csr_array(sparse.vstack(fronts))
        if len(fronts) > 0
        else sparse.csr_array(
            (len(constr_states), len(constr_states) + len(self_states)), dtype=bool
        )
    )


def _transform_front_part(
    front_part: sparse.csr_array, constr_states_num: int
) -> sparse.csr_array:
    transformed_front_part = sparse.lil_array(front_part.shape, dtype=bool)
    # Perform the transformation by rows
    for i, j in zip(*front_part.nonzero()):
        # If the element is from the constraint part
        if j < constr_states_num:
            non_zero_row_right = front_part.getrow(i).tolil()[[0], constr_states_num:]
            # If the right part contains non-zero elements
            if non_zero_row_right.nnz > 0:
                # Account for separated front
                row_shift = i // constr_states_num * constr_states_num
                # Mark the row in the left part
                transformed_front_part[row_shift + j, j] = True
                # Move the right part of the row, saving what's already been moved
                transformed_front_part[
                    [row_shift + j], constr_states_num:
                ] += non_zero_row_right
    return transformed_front_part.tocsr()

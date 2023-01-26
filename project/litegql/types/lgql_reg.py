from copy import copy
from copy import deepcopy
from pathlib import Path
from typing import Generic
from typing import TYPE_CHECKING

import networkx as nx
import pyformlang.cfg as c
import pyformlang.finite_automaton as fa
import pyformlang.regular_expression as re

from project.cfpq.rsm import Rsm
from project.litegql.types.automaton_like import AutomatonLike
from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_edge import Edge
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_set import Set
from project.litegql.types.typing_utils import are_of_same_lgql_type
from project.litegql.types.typing_utils import OtherVertexT
from project.litegql.types.typing_utils import VertexT
from project.rpq.fa_utils import concat_fas
from project.rpq.fa_utils import graph_to_nfa
from project.rpq.fa_utils import intersect_fas
from project.rpq.fa_utils import iter_fa_transitions
from project.rpq.fa_utils import map_fa_states
from project.rpq.fa_utils import star_fa
from project.rpq.fa_utils import union_fas
from project.utils.bool_decomposition import BoolDecomposition
from project.utils.graph_utils import load_graph_from_cfpq_data

if TYPE_CHECKING:
    from project.litegql.types.lgql_cfg import Cfg
    from project.litegql.types.lgql_string import String


class Reg(AutomatonLike[VertexT], Generic[VertexT]):
    class Meta(AutomatonLike.CollectionMeta):
        @property
        def _str_prefix(self) -> str:
            return Reg.__name__

    def __init__(
        self,
        # Not using epsilon transitions as they have obscure labels
        nfa: fa.NondeterministicFiniteAutomaton,
        elem_meta: BaseType.Meta = Int.Meta(),
    ):
        if (
            not isinstance(nfa, fa.NondeterministicFiniteAutomaton)
            or not are_of_same_lgql_type(s.value for s in nfa.states)
            # Not using String as it is a Reg itself
            or not all(isinstance(s.value, str) for s in nfa.symbols)
        ):
            raise TypeError("Expected NFA with states of same type and string labels")
        if len(nfa.states) > 0:
            elem_meta = next(iter(nfa.states)).value.meta
        self._nfa = nfa
        self._meta = Reg.Meta(elem_meta)

    @classmethod
    def from_file(cls, path: Path) -> "Reg[Int]":
        with open(path, "r") as f:
            g = nx.drawing.nx_pydot.read_dot(f)
        return cls(
            map_fa_states(graph_to_nfa(g, with_epsilons=False), lambda n: Int(int(n))),
            Int.Meta(),
        )

    @classmethod
    def from_raw_str(cls, raw_str: str, start_index: int = 0) -> "Reg[Int]":
        raw_nfa = re.Regex(raw_str).to_epsilon_nfa().remove_epsilon_transitions()
        index_map = {s: Int(i) for i, s in enumerate(raw_nfa.states, start=start_index)}
        return cls(map_fa_states(raw_nfa, lambda s: index_map[s]), Int.Meta())

    @classmethod
    def from_dataset(cls, graph_name: str) -> "Reg[Int]":
        g = load_graph_from_cfpq_data(graph_name)
        return cls(map_fa_states(graph_to_nfa(g, with_epsilons=False), Int), Int.Meta())

    def to_cfg(self) -> "Cfg[VertexT]":
        from project.litegql.types.lgql_cfg import Cfg

        start_var = c.Variable("S")
        start_box = fa.NondeterministicFiniteAutomaton(
            states=copy(self._nfa.states),
            start_state=copy(self._nfa.start_states),
            final_states=copy(self._nfa.final_states),
        )
        for s_from, symb, s_to in iter_fa_transitions(self._nfa):
            start_box.add_transition(s_from, c.Terminal(symb.value), s_to)
        return Cfg(Rsm(start_var, {start_var: start_box}), self.meta.elem_meta)

    def add_starts(self, vs: Set[VertexT]) -> "Reg[VertexT]":
        self._assert_compatible_set(vs)
        nfa = self._nfa.copy().remove_epsilon_transitions()
        for v in vs.value:
            nfa.add_start_state(fa.State(v))
        return Reg(nfa, self.meta.elem_meta)

    def add_finals(self, vs: Set[VertexT]) -> "Reg[VertexT]":
        self._assert_compatible_set(vs)
        nfa = self._nfa.copy().remove_epsilon_transitions()
        for v in vs.value:
            nfa.add_final_state(fa.State(v))
        return Reg(nfa, self.meta.elem_meta)

    def set_starts(self, vs: Set[VertexT]) -> "Reg[VertexT]":
        self._assert_compatible_set(vs)
        nfa = fa.NondeterministicFiniteAutomaton(
            states=copy(self._nfa.states),
            input_symbols=copy(self._nfa.symbols),
            transition_function=deepcopy(self._nfa._transition_function),
            start_state=vs.value,
            final_states=copy(self._nfa.final_states),
        )
        return Reg(nfa, self.meta.elem_meta)

    def set_finals(self, vs: Set[VertexT]) -> "Reg[VertexT]":
        self._assert_compatible_set(vs)
        nfa = fa.NondeterministicFiniteAutomaton(
            states=copy(self._nfa.states),
            input_symbols=copy(self._nfa.symbols),
            transition_function=deepcopy(self._nfa._transition_function),
            start_state=copy(self._nfa.start_states),
            final_states=vs.value,
        )
        return Reg(nfa, self.meta.elem_meta)

    def get_starts(self) -> Set[VertexT]:
        return Set({s.value for s in self._nfa.start_states}, self.meta.elem_meta)

    def get_finals(self) -> Set[VertexT]:
        return Set({s.value for s in self._nfa.final_states}, self.meta.elem_meta)

    def get_vertices(self) -> Set[VertexT]:
        return Set({s.value for s in self._nfa.states}, self.meta.elem_meta)

    def get_edges(self) -> Set[Edge[VertexT]]:
        from project.litegql.types.lgql_string import String

        edges = {
            Edge(s_from.value, String(symb.value), s_to.value)
            for s_from, symb, s_to in iter_fa_transitions(self._nfa)
        }
        return Set(edges, Edge.Meta(self.meta.elem_meta))

    def get_labels(self) -> "Set[String]":
        from project.litegql.types.lgql_string import String

        return Set({String(s.value) for s in self._nfa.symbols}, String.Meta())

    def get_reachables(self) -> Set[Pair[VertexT, VertexT]]:
        reachables = set(
            # Have to explicitly add start-finals in case they will not appear in the
            # transitive closure
            Pair(s.value, s.value)
            for s in self._nfa.start_states.intersection(self._nfa.final_states)
        )
        decomp = BoolDecomposition.from_nfa(self._nfa)
        for n_from_i, n_to_i in zip(*decomp.transitive_closure_any_symbol()):
            n_from = decomp.states[n_from_i]
            n_to = decomp.states[n_to_i]
            if n_from.is_start and n_to.is_final:
                reachables.add(Pair(n_from.data, n_to.data))
        return Set(reachables, self.meta.elem_meta)

    # Cannot use implementations of the operations below from pyformlang as they throw
    # away vertex data types

    def intersect(
        self, other: AutomatonLike[OtherVertexT]
    ) -> AutomatonLike[Pair[VertexT, OtherVertexT]]:
        from project.litegql.types.lgql_cfg import Cfg

        if isinstance(other, Reg):
            nfa = intersect_fas(self._nfa, other._nfa, Pair)
            return Reg(nfa, Pair.Meta(self.meta.elem_meta, other.meta.elem_meta))
        elif isinstance(other, Cfg):
            return Cfg(
                other._rsm.intersect(self._nfa, swapped=True, pair=Pair),
                Pair.Meta(self.meta.elem_meta, other.meta.elem_meta),
            )

        # Incompatible type
        actual_type = other.meta if isinstance(other, BaseType) else type(other)
        raise TypeError(f"Expected automaton-like, got {actual_type}")

    def concat(self, other: AutomatonLike[VertexT]) -> AutomatonLike[VertexT]:
        self._assert_compatible_automaton_like(other)

        if isinstance(other, Reg):
            nfa = concat_fas(self._nfa, other._nfa).remove_epsilon_transitions()
            return Reg(nfa, self.meta.elem_meta)

        # other is a cfg
        return self.to_cfg().concat(other)

    def union(self, other: AutomatonLike[VertexT]) -> AutomatonLike[VertexT]:
        self._assert_compatible_automaton_like(other)

        if isinstance(other, Reg):
            nfa = union_fas(self._nfa, other._nfa)
            return Reg(nfa, self.meta.elem_meta)

        # other is a cfg
        return self.to_cfg().union(other)

    def star(self) -> "Reg[VertexT]":
        return Reg(
            star_fa(self._nfa.copy()).remove_epsilon_transitions(), self.meta.elem_meta
        )

    @property
    def meta(self) -> Meta:
        return self._meta

    def __repr__(self) -> str:
        return f"{self.meta}{repr(self._nfa)}"

    def __str__(self) -> str:
        try:
            nfa_str = str(self._nfa.to_regex())
        except ValueError:  # pyformlang can transform only simple NFAs
            nfa_str = (
                f"({len(self._nfa.states)} states, {len(self._nfa.symbols)} symbols)"
            )
        return f"{self.meta}{nfa_str}"

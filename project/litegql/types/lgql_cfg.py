from copy import deepcopy
from pathlib import Path
from typing import Generic

import pyformlang.cfg as c
import pyformlang.finite_automaton as fa

from project.cfpq.rsm import Rsm
from project.litegql.types.automaton_like import AutomatonLike
from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_edge import Edge
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_reg import Reg
from project.litegql.types.lgql_set import Set
from project.litegql.types.lgql_string import String
from project.litegql.types.typing_utils import are_of_same_lgql_type
from project.litegql.types.typing_utils import OtherVertexT
from project.litegql.types.typing_utils import VertexT
from project.rpq.fa_utils import map_fa_states


class Cfg(AutomatonLike[VertexT], Generic[VertexT]):
    class Meta(AutomatonLike.CollectionMeta):
        @property
        def _str_prefix(self) -> str:
            return Cfg.__name__

    @staticmethod
    def _get_all_states(rsm: Rsm) -> set[fa.State]:
        return {s for box in rsm.boxes.values() for s in box.states}

    @staticmethod
    def _get_all_symbols(rsm: Rsm) -> set[fa.Symbol]:
        return {s for box in rsm.boxes.values() for s in box.symbols}

    def __init__(self, rsm: Rsm, elem_meta: BaseType.Meta = Int.Meta()):
        if not isinstance(rsm, Rsm) or not all(
            # Not using epsilon transitions as they have obscure labels
            isinstance(box, fa.NondeterministicFiniteAutomaton)
            for box in rsm.boxes.values()
        ):
            raise TypeError("Expected RSM with non-epsilon NFAs as boxes")

        states = self._get_all_states(rsm)
        symbols = self._get_all_symbols(rsm)
        if not are_of_same_lgql_type(s.value for s in states) or not all(
            # Not using String for similarity with Reg
            (isinstance(s.value, c.Terminal) and isinstance(s.value.value, str))
            or isinstance(s.value, c.Variable)
            for s in symbols
        ):
            raise TypeError(
                "Expected NFA with states of same type and terminals or variables as "
                "labels"
            )

        if len(states) > 0:
            elem_meta = next(iter(states)).value.meta

        self._rsm = rsm
        self._meta = Cfg.Meta(elem_meta)

    @classmethod
    def from_raw_str(cls, raw_str: str, start_index: int = 0) -> "Cfg[Int]":
        rsm = Rsm.from_cfg(c.CFG.from_text(raw_str), start_index)
        for var in rsm.boxes:
            rsm.boxes[var] = map_fa_states(rsm.boxes[var], Int)
        return cls(rsm, Int.Meta())

    @classmethod
    def from_file(cls, path: Path) -> "Cfg[Int]":
        rsm = Rsm.from_dot_file(path)
        for var in rsm.boxes:
            rsm.boxes[var] = map_fa_states(rsm.boxes[var], lambda n: Int(int(n)))
        return cls(rsm, Int.Meta())

    def add_starts(self, vs: Set[VertexT]) -> "Cfg[VertexT]":
        self._assert_compatible_set(vs)
        return Cfg(deepcopy(self._rsm).add_starts(vs.value), self.meta.elem_meta)

    def add_finals(self, vs: Set[VertexT]) -> "Cfg[VertexT]":
        self._assert_compatible_set(vs)
        return Cfg(deepcopy(self._rsm).add_finals(vs.value), self.meta.elem_meta)

    def set_starts(self, vs: Set[VertexT]) -> "Cfg[VertexT]":
        self._assert_compatible_set(vs)
        return Cfg(deepcopy(self._rsm).set_starts(vs.value), self.meta.elem_meta)

    def set_finals(self, vs: Set[VertexT]) -> "Cfg[VertexT]":
        self._assert_compatible_set(vs)
        return Cfg(deepcopy(self._rsm).set_finals(vs.value), self.meta.elem_meta)

    def get_starts(self) -> Set[VertexT]:
        return Set({s.value for s in self._rsm.get_starts()}, self.meta.elem_meta)

    def get_finals(self) -> Set[VertexT]:
        return Set({s.value for s in self._rsm.get_finals()}, self.meta.elem_meta)

    def get_vertices(self) -> Set[VertexT]:
        return Set({s.value for s in self._rsm.get_states()}, self.meta.elem_meta)

    @staticmethod
    def _symbol_to_label(symb: fa.Symbol) -> String:
        return String(
            symb.value.value
            if isinstance(symb.value, c.Terminal)
            else f"<var>{symb.value.value}"
        )

    def get_edges(self) -> Set[Edge[VertexT]]:
        edges = {
            Edge(s_from.value, self._symbol_to_label(symb), s_to.value)
            for s_from, symb, s_to in self._rsm.get_transitions()
        }
        return Set(edges, self.meta.elem_meta)

    def get_labels(self) -> Set[String]:
        labels = {
            String(symb.value.value)
            for _, symb, _ in self._rsm.get_transitions()
            if isinstance(symb.value, c.Terminal)
        }
        return Set(labels, String.Meta())

    def get_reachables(self) -> Set[Pair[VertexT, VertexT]]:
        return Set(
            {Pair(s1.value, s2.value) for (s1, s2) in self._rsm.get_reachables()},
            Pair.Meta(self.meta.elem_meta, self.meta.elem_meta),
        )

    def intersect(self, other: Reg[OtherVertexT]) -> "Cfg[Pair[VertexT, OtherVertexT]]":
        if not isinstance(other, Reg):
            raise TypeError("Can intersect context-free with regular only")

        return Cfg(
            self._rsm.intersect(other._nfa, pair=Pair),
            Pair.Meta(self.meta.elem_meta, other.meta.elem_meta),
        )

    @staticmethod
    def _remove_epsilons(rsm: Rsm) -> Rsm:
        for var, box in rsm.boxes.items():
            if isinstance(box, fa.EpsilonNFA):
                rsm.boxes[var] = box.remove_epsilon_transitions()
        return rsm

    def concat(self, other: AutomatonLike[VertexT]) -> "Cfg[VertexT]":
        self._assert_compatible_automaton_like(other)
        if isinstance(other, Reg):
            other = other.to_cfg()
        return Cfg(
            self._remove_epsilons(self._rsm.concat(other._rsm)), self.meta.elem_meta
        )

    def union(self, other: AutomatonLike[VertexT]) -> "Cfg[VertexT]":
        self._assert_compatible_automaton_like(other)
        if isinstance(other, Reg):
            other = other.to_cfg()
        return Cfg(self._rsm.union(other._rsm), self.meta.elem_meta)

    def star(self) -> "Cfg[VertexT]":
        return Cfg(self._remove_epsilons(self._rsm.star()), self.meta.elem_meta)

    @property
    def meta(self) -> Meta:
        return self._meta

    def __repr__(self) -> str:
        return f"{self.meta}{repr(self._rsm)}"

    def __str__(self) -> str:
        def var_as_str(v: c.Variable) -> str:
            prefix = "(start) " if v is self._rsm.start else ""
            return prefix + v.value

        def box_as_str(box: fa.NondeterministicFiniteAutomaton) -> str:
            try:
                return str(box.to_regex())
            except ValueError:  # pyformlang can transform only simple NFAs
                return f"({len(box.states)} states, {len(box.symbols)} symbols)"

        boxes_str = "; ".join(
            f"{var_as_str(v)} -> {box_as_str(box)}"
            for v, box in self._rsm.boxes.items()
        )
        return f"{self.meta}({boxes_str})"

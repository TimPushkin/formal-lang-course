from collections.abc import Set as AbstractSet
from copy import deepcopy
from itertools import product
from pathlib import Path
from typing import Any
from typing import Callable

import networkx as nx
import pydot
import pyformlang.cfg as c
import pyformlang.finite_automaton as fa
from scipy import sparse

from project.cfpq.ecfg import Ecfg
from project.rpq.fa_utils import concat_fas
from project.rpq.fa_utils import ConcreteFA
from project.rpq.fa_utils import iter_fa_transitions
from project.rpq.fa_utils import star_fa
from project.rpq.fa_utils import union_fas
from project.utils.bool_decomposition import BoolDecomposition


class Rsm:
    def __init__(self, start: c.Variable, boxes: dict[c.Variable, fa.EpsilonNFA]):
        self.start = start
        self.boxes = boxes

    @classmethod
    def from_cfg(cls, cfg: c.CFG, start_index: int = 0) -> "Rsm":
        """Preserves Terminals and Variables in the labels of the resulting boxes."""
        last_state = fa.State(start_index)  # Ensure no overlapping for correct union
        boxes: dict[c.Variable, fa.NondeterministicFiniteAutomaton] = {}
        # Sort to get determined results
        for p in sorted(cfg.productions, key=str):
            nfa = fa.NondeterministicFiniteAutomaton()
            nfa.add_start_state(last_state)
            for obj in p.body:
                if isinstance(obj, c.Epsilon):
                    continue
                next_state = fa.State(last_state.value + 1)
                nfa.add_transition(last_state, obj, next_state)
                last_state = next_state
            # Not checking for emptiness because pyformlang treats empty as epsilon
            nfa.add_final_state(last_state)
            last_state = fa.State(last_state.value + 1)
            if p.head in boxes:
                boxes[p.head] = union_fas(boxes[p.head], nfa)
            else:
                boxes[p.head] = nfa
        if cfg.start_symbol not in boxes:
            boxes[cfg.start_symbol] = fa.NondeterministicFiniteAutomaton(
                start_state={last_state}
            )
        return cls(start=cfg.start_symbol or c.Variable("S"), boxes=boxes)

    @classmethod
    def from_ecfg(cls, ecfg: Ecfg) -> "Rsm":
        return cls(
            ecfg.start,
            {head: body.to_epsilon_nfa() for head, body in ecfg.productions.items()},
        )

    @classmethod
    def from_dot_file(cls, path: Path) -> "Rsm":
        g = pydot.graph_from_dot_file(path)[0]

        start_var = c.Variable(g.get_name())

        boxes: dict[c.Variable, fa.NondeterministicFiniteAutomaton] = {}
        for subg in g.get_subgraph_list():
            var = c.Variable(subg.get_name())

            subg = nx.drawing.nx_pydot.from_pydot(subg)
            nfa = fa.NondeterministicFiniteAutomaton(states=set(subg.nodes))
            for n, data in subg.nodes.data():
                if data.get("is_start", "True") != "False":
                    nfa.add_start_state(n)
                if data.get("is_final", "True") != "False":
                    nfa.add_final_state(n)
            for pred, succ, symb in subg.edges.data("label", default=""):
                lab = c.Variable(symb) if symb.isupper() else c.Terminal(symb)
                nfa.add_transition(pred, lab, succ)

            if var in boxes:
                boxes[var] = union_fas(boxes[var], nfa)
            else:
                boxes[var] = nfa

        # Ensure a correct start box always exist
        if start_var not in boxes:
            boxes[start_var] = fa.NondeterministicFiniteAutomaton(start_state={0})

        return cls(start_var, boxes)

    def minimize(self) -> "Rsm":
        for var, box in self.boxes.items():
            self.boxes[var] = box.minimize()
        return self

    def add_starts(self, starts: AbstractSet) -> "Rsm":
        box = self.boxes[self.start]
        for s in starts:
            box.add_start_state(s)
        return self

    def add_finals(self, finals: AbstractSet) -> "Rsm":
        box = self.boxes[self.start]
        for s in finals:
            box.add_final_state(s)
        return self

    def set_starts(self, starts: AbstractSet) -> "Rsm":
        box = self.boxes[self.start]
        self.boxes[self.start] = type(box)(
            states=box.states,
            input_symbols=box.symbols,
            transition_function=box._transition_function,
            start_state=starts,
            final_states=box.final_states,
        )
        return self

    def set_finals(self, finals: AbstractSet) -> "Rsm":
        box = self.boxes[self.start]
        self.boxes[self.start] = type(box)(
            states=box.states,
            input_symbols=box.symbols,
            transition_function=box._transition_function,
            start_state=box.start_states,
            final_states=finals,
        )
        return self

    def get_starts(self) -> set[fa.State]:
        return self.boxes[self.start].start_states

    def get_finals(self) -> set[fa.State]:
        return self.boxes[self.start].final_states

    def get_states(self) -> set[fa.State]:
        return {s for box in self.boxes.values() for s in box.states}

    def get_transitions(self) -> set[tuple[fa.State, fa.Symbol, fa.State]]:
        return {
            (s_from, symb, s_to)
            for box in self.boxes.values()
            for s_from, symb, s_to in iter_fa_transitions(box)
        }

    def get_reachables(self) -> set[tuple[fa.State, fa.State]]:
        # First remove all variable transitions as they may actually be non-terminable
        # (e.g. have no finishes or always lead to infinite recursion) and then
        # gradually add them back until no new transitions appear

        decomp = BoolDecomposition.from_rsm(self)
        nonterminatable_adjs = {}
        res = set()

        # Initialize non-terminable transitions explicitly handling start-final nodes in
        # case they will not appear in transitive closures
        for var in set(self.boxes).union(decomp.adjs):
            if not isinstance(var, c.Variable):
                continue
            start_finals = (
                self.boxes[var].start_states.intersection(self.boxes[var].final_states)
                if var in self.boxes
                else set()
            )
            if len(start_finals) == 0 and var in decomp.adjs:
                nonterminatable_adjs[var] = decomp.adjs.pop(var)
            if var == self.start:
                res |= {(s, s) for s in start_finals}

        # Iteratively compute transitive closures and add new variable transitions
        while True:
            old_len = len(nonterminatable_adjs)

            transitive_closure_indices = zip(*decomp.transitive_closure_any_symbol())
            for n_from_i, n_to_i in transitive_closure_indices:
                n_from = decomp.states[n_from_i]
                n_to = decomp.states[n_to_i]
                if n_from.is_start and n_to.is_final:
                    var1, s1 = n_from.data
                    var2, s2 = n_to.data
                    assert var1 == var2
                    if var1 in nonterminatable_adjs:
                        decomp.adjs[var1] = nonterminatable_adjs.pop(var1)
                    if var1 == self.start:
                        res.add((fa.State(s1), fa.State(s2)))

            if len(nonterminatable_adjs) == old_len:
                break

        return res

    # Should not be used with RSMs created from ECFG as their transitions are not boxed
    # with Variables and Terminals
    def intersect(
        self,
        nfa: fa.EpsilonNFA,
        swapped: bool = False,
        pair: Callable[[Any, Any], Any] = lambda u, v: (u, v),
    ) -> "Rsm":
        from project.cfpq.tensor import constrained_transitive_closure_by_tensor_decomp

        # Intersect using tensor CFPQ -- this will create a "raw" intersection RSM. Sort
        # states to always get the same RSM as a result.
        self_decomp = BoolDecomposition.from_rsm(self, sort_states=True)
        nfa_decomp = BoolDecomposition.from_nfa(
            nfa.remove_epsilon_transitions(), sort_states=True
        )
        # NFA decompositions use bare values, while RSMs are boxed, so need to box NFAs
        for symb in list(nfa_decomp.adjs):  # list() to create a copy
            nfa_decomp.adjs[c.Terminal(symb)] = nfa_decomp.adjs.pop(symb)
        # nfa_decomp gets changed in-place here
        constrained_transitive_closure_by_tensor_decomp(nfa_decomp, self_decomp)
        intersection = (
            self_decomp.intersect(nfa_decomp)
            if not swapped
            else nfa_decomp.intersect(self_decomp)
        )

        def unpack(
            si: BoolDecomposition.StateInfo,
        ) -> tuple[c.Variable, BoolDecomposition.StateInfo]:
            if not swapped:
                (var, d1), d2 = si.data
            else:
                d1, (var, d2) = si.data
            return var, BoolDecomposition.StateInfo((d1, d2), si.is_start, si.is_final)

        # Remap variable transitions

        all_vars = set(self.boxes.keys())

        def new_var(body: c.Variable) -> c.Variable:
            var = c.Variable((body.value, 1))
            while var in all_vars:
                var = c.Variable((body.value, var.value[1] + 1))
            all_vars.add(var)
            return var

        nfa_sf = {
            (var, s, f): var
            for var in self.boxes
            for s in nfa.start_states
            for f in nfa.final_states
        }
        for symb, adj in [  # Not using items() directly to create a copy
            (s, a) for s, a in intersection.adjs.items() if isinstance(s, c.Variable)
        ]:
            intersection.adjs[symb] = adj.todok()  # Will change modify by indices
            for s_from_i, s_to_i in zip(*adj.nonzero()):
                box_var, s_from = unpack(intersection.states[s_from_i])
                box_var_, s_to = unpack(intersection.states[s_to_i])
                assert box_var == box_var_  # There are no edges between boxes

                if symb != box_var:
                    continue

                # Not using setdefault() to avoid unnecessary new_var() calls
                nfa_sf_key = (
                    (box_var, s_from.data[1], s_to.data[1])
                    if not swapped
                    else (box_var, s_from.data[0], s_to.data[0])
                )
                if nfa_sf_key not in nfa_sf:
                    nfa_sf[nfa_sf_key] = new_var(box_var)
                new_symb = nfa_sf[nfa_sf_key]

                # First remove then add in case of adding an existing edge
                intersection.adjs[symb][s_from_i, s_to_i] = False
                intersection.adjs.setdefault(
                    new_symb, sparse.dok_array(adj.shape, dtype=bool)
                )[s_from_i, s_to_i] = True

        # Construct intersection boxes
        boxes: dict[c.Variable, fa.NondeterministicFiniteAutomaton] = {}

        for s in intersection.states:
            box_var, s = unpack(s)
            box = boxes.setdefault(box_var, fa.NondeterministicFiniteAutomaton())
            p = pair(*s.data)
            if s.is_start:
                box.add_start_state(p)
            if s.is_final:
                box.add_final_state(p)

        box_to_sf = {
            var: set(
                (st.value, fn.value)
                for st, fn in product(box.start_states, box.final_states)
            )
            for var, box in self.boxes.items()
        }
        box_to_vars: dict[c.Variable, set[c.Variable]] = {}
        for (box, _, _), var in nfa_sf.items():
            box_to_vars.setdefault(box, set()).add(var)

        for symb, adj in intersection.adjs.items():
            for s_from_i, s_to_i in zip(*adj.nonzero()):
                main_box_var, s_from = unpack(intersection.states[s_from_i])
                main_box_var_, s_to = unpack(intersection.states[s_to_i])
                assert main_box_var == main_box_var_  # There are no edges between boxes

                for box_var in box_to_vars[main_box_var]:
                    box = boxes.setdefault(
                        box_var, fa.NondeterministicFiniteAutomaton()
                    )
                    box.add_transition(pair(*s_from.data), symb, pair(*s_to.data))

                    if box_var != symb:
                        continue

                    for st, fn in box_to_sf[main_box_var]:
                        if not swapped:
                            box.add_start_state(pair(st, s_from.data[1]))
                            box.add_final_state(pair(fn, s_to.data[1]))
                        else:
                            box.add_start_state(pair(s_from.data[0], st))
                            box.add_final_state(pair(s_to.data[0], fn))

        return Rsm(self.start, boxes)

    @staticmethod
    def _suffixed_boxes(
        boxes: dict[c.Variable, ConcreteFA], suffix: int
    ) -> dict[c.Variable, ConcreteFA]:
        def suffixed_box(box: ConcreteFA) -> ConcreteFA:
            new_box = type(box)(
                start_state=deepcopy(box.start_states),
                final_states=deepcopy(box.final_states),
            )
            for s_from, symb, s_to in iter_fa_transitions(box):
                new_box.add_transition(
                    s_from,
                    c.Variable((symb.value, suffix))
                    if isinstance(symb.value, c.Variable)
                    else symb,
                    s_to,
                )
            return new_box

        return {
            c.Variable((var.value, suffix)): suffixed_box(box)
            for var, box in boxes.items()
        }

    def _combine(
        self,
        other: "Rsm",
        get_start_box: Callable[[fa.EpsilonNFA, fa.EpsilonNFA], fa.EpsilonNFA],
    ) -> "Rsm":
        # Make variables distinctive
        fst_boxes = self._suffixed_boxes(self.boxes, 1)
        snd_boxes = self._suffixed_boxes(other.boxes, 2)

        # Construct the start box
        new_start = c.Variable("S")
        start_box = get_start_box(
            fst_boxes[c.Variable((self.start, 1))],
            snd_boxes[c.Variable((other.start, 2))],
        )

        return Rsm(new_start, {new_start: start_box} | fst_boxes | snd_boxes)

    def concat(self, other: "Rsm") -> "Rsm":
        return self._combine(other, concat_fas)

    def union(self, other: "Rsm") -> "Rsm":
        return self._combine(other, union_fas)

    def star(self) -> "Rsm":
        boxes = self._suffixed_boxes(self.boxes, 1)
        boxes[c.Variable("S")] = star_fa(boxes[c.Variable((self.start, 1))])
        return Rsm(self.start, boxes)

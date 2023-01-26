from typing import Any
from typing import Callable
from typing import Generator
from typing import TypeVar

import networkx as nx
import pyformlang.finite_automaton as fa
import pyformlang.regular_expression as re

from project.utils.bool_decomposition import BoolDecomposition


def regex_to_min_dfa(regex: str | re.Regex) -> fa.DeterministicFiniteAutomaton:
    if not isinstance(regex, re.Regex):
        regex = re.Regex(regex)
    min_dfa = regex.to_epsilon_nfa().minimize()
    return min_dfa


def graph_to_nfa(
    graph: nx.Graph,
    start_states: set | None = None,
    final_states: set | None = None,
    with_epsilons: bool = True,
) -> fa.EpsilonNFA | fa.NondeterministicFiniteAutomaton:
    nfa = (fa.EpsilonNFA if with_epsilons else fa.NondeterministicFiniteAutomaton)(
        states=set(graph.nodes),
        start_state=set(graph.nodes) if start_states is None else start_states,
        final_states=set(graph.nodes) if final_states is None else final_states,
    )

    for pred, succ, symb in graph.edges.data(
        "label", default=fa.Epsilon() if with_epsilons else ""
    ):
        nfa.add_transition(pred, symb, succ)

    return nfa


def iter_fa_transitions(
    a: fa.FiniteAutomaton,
) -> Generator[tuple[fa.State, fa.Symbol, fa.State], None, None]:
    transitions: dict[fa.State, dict[fa.Symbol, fa.State | set[fa.State]]] = a.to_dict()
    for s_from in transitions:
        for label, ss_to in transitions[s_from].items():
            for s_to in ss_to if isinstance(ss_to, set) else {ss_to}:
                yield s_from, label, s_to


ConcreteFA = TypeVar(
    "ConcreteFA",
    fa.DeterministicFiniteAutomaton,
    fa.NondeterministicFiniteAutomaton,
    fa.EpsilonNFA,
)


def map_fa_states(a: ConcreteFA, f: Callable[[Any], Any]) -> ConcreteFA:
    nfa = type(a)(
        states={f(s.value) for s in a.states},
        start_state=f(a.start_state.value)
        if isinstance(a, fa.DeterministicFiniteAutomaton)
        else {f(s.value) for s in a.start_states},
        final_states={f(s.value) for s in a.final_states},
    )
    for s_from, symb, s_to in iter_fa_transitions(a):
        nfa.add_transition(f(s_from.value), symb, f(s_to.value))
    return nfa


def intersect_fas(
    fa1: ConcreteFA,
    fa2: ConcreteFA,
    pair: Callable[[Any, Any], Any],
) -> ConcreteFA:
    decomp1 = BoolDecomposition.from_nfa(fa1)
    decomp2 = BoolDecomposition.from_nfa(fa2)
    intersection = decomp1.intersect(decomp2)

    a = type(fa1)()
    # Add starts and finals separately in case there are no transitions between them
    for s_info in intersection.states:
        s_wrapped = pair(*s_info.data)
        if s_info.is_start:
            a.add_start_state(s_wrapped)
        if s_info.is_final:
            a.add_final_state(s_wrapped)
    # Add transitions
    for symb, adj in intersection.adjs.items():
        for s_from_i, s_to_i in zip(*adj.nonzero()):
            s_from_info = intersection.states[s_from_i]
            s_from_wrapped = pair(*s_from_info.data)
            s_to_info = intersection.states[s_to_i]
            s_to_wrapped = pair(*s_to_info.data)

            a.add_transition(s_from_wrapped, symb, s_to_wrapped)
    return a


def concat_fas(fa1: fa.FiniteAutomaton, fa2: fa.FiniteAutomaton) -> fa.EpsilonNFA:
    enfa = fa.EpsilonNFA(
        states=fa1.states | fa2.states,
        start_state=fa1.start_states,
        final_states=fa2.final_states,
    )

    for s_from, symb, s_to in iter_fa_transitions(fa1):
        enfa.add_transition(s_from, symb, s_to)
    for s_from, symb, s_to in iter_fa_transitions(fa2):
        enfa.add_transition(s_from, symb, s_to)

    for s_from in fa1.final_states:
        for s_to in (
            fa2.start_states
            if isinstance(fa2.start_states, set)
            else {fa2.start_states}
        ):
            enfa.add_transition(s_from, fa.Epsilon(), s_to)

    return enfa


def union_fas(
    fa1: fa.FiniteAutomaton, fa2: fa.FiniteAutomaton
) -> fa.NondeterministicFiniteAutomaton | fa.EpsilonNFA:
    nfa_class = (
        fa.NondeterministicFiniteAutomaton
        if all(
            isinstance(
                nfa,
                (fa.DeterministicFiniteAutomaton, fa.NondeterministicFiniteAutomaton),
            )
            for nfa in (fa1, fa2)
        )
        else fa.EpsilonNFA
    )
    nfa = nfa_class(
        states=fa1.states | fa2.states,
        start_state=fa1.start_states.union(fa2.start_states),
        final_states=fa1.final_states.union(fa2.final_states),
    )

    for s_from, symb, s_to in iter_fa_transitions(fa1):
        nfa.add_transition(s_from, symb, s_to)
    for s_from, symb, s_to in iter_fa_transitions(fa2):
        nfa.add_transition(s_from, symb, s_to)

    return nfa


def star_fa(
    # Cannot allow DFAs for the current implementation since their copy() is a DFA, not
    # EpsilonNFA
    a: fa.NondeterministicFiniteAutomaton
    | fa.EpsilonNFA,
) -> fa.EpsilonNFA:
    assert len(a.states) > 0

    enfa = (
        a.copy()
        if len(a.start_states) > 0
        else fa.EpsilonNFA(
            states=a.states,
            input_symbols=a.symbols,
            transition_function=a._transition_function,
            start_state={next(iter(a.states))},  # Ensure there is a start state
            final_states=a.final_states,
        )
    )
    for start in enfa.start_states:
        for final in enfa.final_states:
            enfa.add_transition(final, fa.Epsilon(), start)
        enfa.add_final_state(start)
    return enfa

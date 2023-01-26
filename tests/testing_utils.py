import inspect
import json
import pathlib
from collections.abc import Callable
from typing import Any
from typing import TextIO
from typing import TypeVar

import networkx as nx
import pydot
from pyformlang import finite_automaton as fa
from pytest import fixture

from project.litegql.grammar.LiteGQLParser import LiteGQLParser
from project.litegql.parsing import get_parser
from project.rpq.fa_utils import iter_fa_transitions


def _open_test_json(
    test_name: str, add_filename_suffix: bool, filename: str | None = None
) -> TextIO:
    with pathlib.Path(inspect.stack()[2].filename) as f:
        parent = f.parent
        if filename is None:
            filename = f.stem
        if add_filename_suffix:
            filename += f"_{test_name}"
    return open(parent / "data" / f"{filename}.json")


_T = TypeVar("_T")


def load_test_data(
    test_name: str,
    transform: Callable[[dict], _T | tuple | list[tuple]],
    *,
    data_filename: str | None = None,
    add_filename_suffix: bool = False,
    is_aggregated: bool = False,
) -> list[_T] | list[tuple]:
    with _open_test_json(test_name, add_filename_suffix, data_filename) as f:
        test_datas = json.load(f)
    if not is_aggregated:
        return [transform(test_data) for test_data in test_datas[test_name]]
    else:
        res = []
        for test_data in test_datas[test_name]:
            res += transform(test_data)
        return res


def load_test_ids(
    test_name: str,
    *,
    data_filename: str | None = None,
    add_filename_suffix: bool = False,
    get_repeats: Callable[[dict], int] = lambda _: 1,
) -> list[str]:
    with _open_test_json(test_name, add_filename_suffix, data_filename) as f:
        test_datas = json.load(f)
    return [
        test_data["description"]
        for test_data in test_datas[test_name]
        for _ in range(get_repeats(test_data))
    ]


def dot_str_to_graph(dot: str) -> nx.Graph:
    return nx.drawing.nx_pydot.from_pydot(pydot.graph_from_dot_data(dot)[0])


def dot_str_to_nfa(dot: str) -> fa.EpsilonNFA:
    graph = dot_str_to_graph(dot)

    # Convert string-represented booleans in nodes from dot files
    for _, data in graph.nodes.data():
        if data["is_start"] in ("True", "False"):
            data["is_start"] = data["is_start"] == "True"
        if data["is_final"] in ("True", "False"):
            data["is_final"] = data["is_final"] == "True"
    # Convert string-represented epsilons in edges from dot files
    for _, _, data in graph.edges.data():
        if data["label"] == "epsilon":
            data["label"] = fa.Epsilon()

    return fa.EpsilonNFA.from_networkx(graph)


def are_equivalent(
    fa1: fa.DeterministicFiniteAutomaton
    | fa.NondeterministicFiniteAutomaton
    | fa.EpsilonNFA,
    fa2: fa.DeterministicFiniteAutomaton
    | fa.NondeterministicFiniteAutomaton
    | fa.EpsilonNFA,
) -> bool:
    # pyformlang silently fails to check for equivalence automatas with no start state
    # when minimized. But we can say such automatas are equivalent since they accept no
    # words
    min1 = fa1.minimize()
    min2 = fa2.minimize()
    return (
        len(min1.start_states) == 0
        and len(min2.start_states) == 0
        or min1.is_equivalent_to(min2)
        # Sometimes this works when the above does not
        or min1.get_difference(min2).is_empty()
    )


@fixture
def content_file_path(request, tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "test_file"
    with open(path, "w") as f:
        f.write(request.param)
    return path


def reconstruct_if_equal_nodes(
    nfa1: fa.NondeterministicFiniteAutomaton,
    nfa2: fa.NondeterministicFiniteAutomaton,
    get_next: Callable[[Any], Any],
) -> fa.NondeterministicFiniteAutomaton:
    mapping = {}
    for s in nfa2.states:
        new_s = s
        while new_s in nfa1.states or new_s in nfa2.states or new_s in mapping.values():
            new_s = fa.State(get_next(new_s.value))
        mapping[s] = new_s

    new_nfa2 = fa.NondeterministicFiniteAutomaton(
        start_state={mapping[s] for s in nfa2.start_states},
        final_states={mapping[s] for s in nfa2.final_states},
    )
    for s_from, symb, s_to in iter_fa_transitions(nfa2):
        new_nfa2.add_transition(mapping[s_from], symb, mapping[s_to])
    return new_nfa2


def fail(*_args, **_kwargs):
    assert False


@fixture(name="ctx")
def expr_ctx(request) -> LiteGQLParser.ExprContext:
    return get_parser(request.param).expr()

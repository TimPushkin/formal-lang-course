from copy import deepcopy
from pathlib import Path
from typing import Any

import pyformlang.finite_automaton as fa
import pytest

from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_edge import Edge
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_reg import Reg
from project.litegql.types.lgql_set import Set
from project.litegql.types.lgql_string import String
from project.utils.graph_utils import load_graph_from_cfpq_data
from tests.testing_utils import are_equivalent
from tests.testing_utils import content_file_path  # noqa
from tests.testing_utils import load_test_data
from tests.testing_utils import load_test_ids
from tests.testing_utils import reconstruct_if_equal_nodes


def _get_incorrect_nfas() -> list:
    nfa_with_incorrect_state_types = fa.DeterministicFiniteAutomaton({1, 2, 3})
    nfa_with_different_state_types = fa.DeterministicFiniteAutomaton(
        {Int(1), Int(2), Bool(False)}
    )
    nfa_with_incorrect_symbol_types = fa.DeterministicFiniteAutomaton()
    nfa_with_incorrect_symbol_types.add_transition(Int(1), String(""), Int(2))
    return [
        1,
        True,
        String(""),
        Set(set()),
        fa.EpsilonNFA(),
        nfa_with_incorrect_state_types,
        nfa_with_different_state_types,
        nfa_with_incorrect_symbol_types,
    ]


@pytest.mark.parametrize("nfa", _get_incorrect_nfas())
def test_reg_init_incorrect(nfa: Any):
    with pytest.raises(TypeError):
        Reg(nfa)


@pytest.mark.parametrize(
    "content_file_path, expected_vertices, expected_edges",
    load_test_data(
        "test_reg_from_file",
        lambda d: (
            d["dot_text"],
            Set({Int(n) for n in d["expected_vertices"]}),
            Set(
                {
                    Edge(Int(st), String(lab), Int(fn))
                    for st, lab, fn in d["expected_edges"]
                }
            ),
        ),
    ),
    indirect=["content_file_path"],
    ids=load_test_ids("test_reg_from_file"),
)
def test_reg_from_file(
    content_file_path: Path, expected_vertices: Set[Int], expected_edges: Set[Edge[Int]]
):
    r = Reg.from_file(content_file_path)
    assert r.meta.elem_meta == Int.Meta()
    assert r.get_vertices() == expected_vertices
    assert r.get_edges() == expected_edges


@pytest.mark.parametrize(
    "regex_str, expected_labels",
    load_test_data(
        "test_reg_from_raw_str",
        lambda d: (d["regex_str"], Set({String(s) for s in d["expected_labels"]})),
    ),
    ids=load_test_ids("test_reg_from_raw_str"),
)
def test_reg_from_raw_str(regex_str: str, expected_labels: Set[String]):
    r = Reg.from_raw_str(regex_str)
    assert r.meta.elem_meta == Int.Meta()
    assert r.get_labels() == expected_labels


@pytest.fixture
def expected_vertices_and_edges(request) -> tuple[Set[Int], Set[Edge[Int]]]:
    graph_name = request.param
    assert isinstance(graph_name, str)

    graph = load_graph_from_cfpq_data(graph_name)
    expected_vertices = {Int(v) for v in graph.nodes}
    expected_edges = {
        Edge(Int(st), String(lab), Int(fn)) for st, fn, lab in graph.edges.data("label")
    }
    return expected_vertices, expected_edges


@pytest.mark.parametrize(
    "graph_name, expected_vertices_and_edges",
    load_test_data("test_reg_from_dataset", lambda d: (d, d)),
    indirect=["expected_vertices_and_edges"],
)
def test_reg_from_dataset(
    graph_name: str, expected_vertices_and_edges: tuple[Set[Int], Set[Edge[Int]]]
):
    expected_vertices, expected_edges = expected_vertices_and_edges

    r = Reg.from_dataset(graph_name)

    assert r.get_vertices().value == expected_vertices
    assert r.get_edges().value == expected_edges


@pytest.fixture
def reg_from_file(request, tmp_path: Path) -> Reg[Int]:
    path = tmp_path / "test_graph.dot"
    with open(path, "w") as f:
        f.write(request.param)
    return Reg.from_file(path)


@pytest.mark.parametrize(
    "reg_from_file, expected_labels",
    load_test_data(
        "test_reg_from_file",
        lambda d: (d["dot_text"], {String(lab) for st, lab, fn in d["expected_edges"]}),
    ),
    indirect=["reg_from_file"],
    ids=load_test_ids("test_reg_from_file"),
)
def test_reg_get_labels(reg_from_file: Reg, expected_labels: set[String]):
    assert reg_from_file.get_labels().value == expected_labels


@pytest.mark.parametrize(
    "reg_from_file, expected_reachables",
    load_test_data(
        "test_reg_from_file",
        lambda d: (
            d["dot_text"],
            {Pair(Int(fst), Int(snd)) for fst, snd in d["expected_reachables"]},
        ),
    ),
    indirect=["reg_from_file"],
    ids=load_test_ids("test_reg_from_file"),
)
def test_reg_get_reachables(
    reg_from_file: Reg, expected_reachables: set[Pair[Int, Int]]
):
    assert reg_from_file.get_reachables().value == expected_reachables


@pytest.mark.parametrize(
    "reg, expected",
    load_test_data(
        "test_reg_star",
        lambda d: (Reg.from_raw_str(d["reg"]), Reg.from_raw_str(d["expected_star"])),
    ),
    ids=load_test_data("test_reg_star", lambda d: d["reg"]),
)
def test_reg_star(reg: Reg[Int], expected: Reg[Int]):
    old_edges = deepcopy(reg.get_edges())

    actual = reg.star()

    assert reg.get_edges() == old_edges  # No in-place mutation should occur
    assert isinstance(actual, Reg)
    assert are_equivalent(actual._nfa, expected._nfa)


@pytest.mark.parametrize(
    "reg1, reg2, expected",
    load_test_data(
        "TestRegCombinations",
        lambda d: (
            Reg.from_raw_str(d["reg1"]),
            Reg.from_raw_str(d["reg2"]),
            Reg.from_raw_str(d["expected_intersect"]),
        ),
    ),
    ids=load_test_data("TestRegCombinations", lambda d: f"{d['reg1']}, {d['reg2']}"),
)
def test_reg_intersect(reg1: Reg[Int], reg2: Reg[Int], expected: Reg[Int]):
    old_edges = deepcopy(reg1.get_edges())

    actual = reg1.intersect(reg2)

    assert reg1.get_edges() == old_edges  # No in-place mutation should occur
    assert isinstance(actual, Reg)
    assert are_equivalent(actual._nfa, expected._nfa)


@pytest.mark.parametrize(
    "reg1, reg2, expected",
    load_test_data(
        "TestRegCombinations",
        lambda d: (
            Reg.from_raw_str(d["reg1"]),
            Reg.from_raw_str(d["reg2"]),
            Reg.from_raw_str(d["expected_concat"]),
        ),
    ),
    ids=load_test_data("TestRegCombinations", lambda d: f"{d['reg1']}, {d['reg2']}"),
)
def test_reg_concat(reg1: Reg[Int], reg2: Reg[Int], expected: Reg[Int]):
    reg2._nfa = reconstruct_if_equal_nodes(  # Make sure no overlapping occurs
        reg1._nfa, reg2._nfa, lambda n: Int(n.value + 1)
    )
    old_edges = deepcopy(reg1.get_edges())

    actual = reg1.concat(reg2)

    assert reg1.get_edges() == old_edges  # No in-place mutation should occur
    assert isinstance(actual, Reg)
    assert are_equivalent(actual._nfa, expected._nfa)


@pytest.mark.parametrize(
    "reg1, reg2, expected",
    load_test_data(
        "TestRegCombinations",
        lambda d: (
            Reg.from_raw_str(d["reg1"]),
            Reg.from_raw_str(d["reg2"]),
            Reg.from_raw_str(d["expected_union"]),
        ),
    ),
    ids=load_test_data("TestRegCombinations", lambda d: f"{d['reg1']}, {d['reg2']}"),
)
def test_reg_union(reg1: Reg[Int], reg2: Reg[Int], expected: Reg[Int]):
    reg2._nfa = reconstruct_if_equal_nodes(  # Make sure no overlapping occurs
        reg1._nfa, reg2._nfa, lambda n: Int(n.value + 1)
    )
    old_edges = deepcopy(reg1.get_edges())

    actual = reg1.union(reg2)

    assert reg1.get_edges() == old_edges  # No in-place mutation should occur
    assert isinstance(actual, Reg)
    assert are_equivalent(actual._nfa, expected._nfa)

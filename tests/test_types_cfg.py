from copy import deepcopy
from pathlib import Path
from typing import Any

import pyformlang.cfg as c
import pyformlang.finite_automaton as fa
import pyformlang.regular_expression as re
import pytest

from project.cfpq.rsm import Rsm
from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_cfg import Cfg
from project.litegql.types.lgql_edge import Edge
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_set import Set
from project.litegql.types.lgql_string import String
from project.rpq.fa_utils import iter_fa_transitions
from tests.testing_utils import are_equivalent
from tests.testing_utils import content_file_path  # noqa
from tests.testing_utils import load_test_data
from tests.testing_utils import load_test_ids
from tests.testing_utils import reconstruct_if_equal_nodes


def _get_incorrect_rsms() -> list:
    rsm_with_incorrect_box_type = Rsm(
        c.Variable("S"),
        {
            c.Variable("A"): fa.DeterministicFiniteAutomaton(),
            c.Variable("B"): fa.EpsilonNFA(),
        },
    )

    rsm_with_incorrect_state_types = Rsm(
        c.Variable("S"), {c.Variable("S"): fa.DeterministicFiniteAutomaton({1, 2, 3})}
    )

    rsm_with_different_state_types = Rsm(
        c.Variable("S"),
        {
            c.Variable("S"): fa.NondeterministicFiniteAutomaton(
                {Int(1), Int(2), Bool(False)}
            )
        },
    )

    nfa_with_incorrect_symbol_types = fa.DeterministicFiniteAutomaton()
    nfa_with_incorrect_symbol_types.add_transition(
        Int(1), c.Terminal(String("")), Int(2)
    )
    rsm_with_incorrect_symbol_types = Rsm(
        c.Variable("S"),
        {c.Variable("S"): nfa_with_incorrect_symbol_types},
    )

    return [
        1,
        True,
        String(""),
        Set(set()),
        fa.NondeterministicFiniteAutomaton(),
        rsm_with_incorrect_box_type,
        rsm_with_incorrect_state_types,
        rsm_with_different_state_types,
        rsm_with_incorrect_symbol_types,
    ]


@pytest.mark.parametrize("rsm", _get_incorrect_rsms())
def test_reg_init_incorrect(rsm: Any):
    with pytest.raises(TypeError):
        Cfg(rsm)


@pytest.mark.parametrize(
    "content_file_path, expected_vertices, expected_edges",
    load_test_data(
        "test_cfg_from_file",
        lambda d: (
            d["dot_text"],
            Set({Int(n) for n in d["expected_vertices"]}),
            Set(
                {
                    Edge(Int(st), String(lab), Int(fn))
                    for st, lab, fn in d["expected_edges"]
                },
                Edge.Meta(Int.Meta()),
            ),
        ),
    ),
    indirect=["content_file_path"],
    ids=load_test_ids("test_cfg_from_file"),
)
def test_cfg_from_file(
    content_file_path: Path, expected_vertices: Set[Int], expected_edges: Set[Edge[Int]]
):
    cfg = Cfg.from_file(content_file_path)
    assert cfg.meta.elem_meta == Int.Meta()
    assert cfg.get_vertices() == expected_vertices
    assert cfg.get_edges() == expected_edges


@pytest.mark.parametrize(
    "cfg_str, expected_vertices, expected_labels",
    load_test_data(
        "test_cfg_from_raw_str",
        lambda d: (
            d["cfg_str"],
            Set({Int(n) for n in d["expected_vertices"]}),
            Set({String(s) for s in d["expected_labels"]}),
        ),
    ),
    ids=load_test_ids("test_cfg_from_raw_str"),
)
def test_cfg_from_raw_str(
    cfg_str: str, expected_vertices: Set[Int], expected_labels: Set[String]
):
    cfg = Cfg.from_raw_str(cfg_str)
    assert cfg.meta.elem_meta == Int.Meta()
    assert cfg.get_vertices() == expected_vertices
    # Cannot test edges as they depend on set ordering
    assert cfg.get_labels() == expected_labels


@pytest.mark.parametrize(
    "cfg, expected",
    load_test_data(
        "test_cfg_get_edges",
        lambda d: (
            Cfg.from_raw_str(d["cfg_str"]),
            {Edge(Int(st), String(lab), Int(fn)) for st, lab, fn in d["expected"]},
        ),
    ),
    ids=load_test_ids("test_cfg_get_edges"),
)
def test_cfg_get_edges(cfg: Cfg[Int], expected: set[Edge]):
    assert cfg.get_edges().value == expected


@pytest.mark.parametrize(
    "cfg, expected",
    load_test_data(
        "test_cfg_from_raw_str",
        lambda d: (
            Cfg.from_raw_str(d["cfg_str"]),
            {Pair(Int(fst), Int(snd)) for fst, snd in d["expected_reachables"]},
        ),
    ),
    ids=load_test_ids("test_cfg_from_raw_str"),
)
def test_reg_get_reachables(cfg: Cfg, expected: set[Pair[Int, Int]]):
    assert cfg.get_reachables().value == expected


def prepare_boxes(raw_boxes: dict[str, str]) -> dict[str, fa.EpsilonNFA]:
    return {var: re.Regex(regex).to_epsilon_nfa() for var, regex in raw_boxes.items()}


def assert_equivalent_boxes(
    actual: dict[c.Variable, fa.EpsilonNFA],
    expected: dict[str, fa.EpsilonNFA] | dict[c.Variable, fa.EpsilonNFA],
    wrapped_expected: bool = False,
    wrapped_states: bool = False,
):
    def unwrap_var(v: c.Variable) -> str:
        if isinstance(v.value, str):
            return v.value
        value, suffix = v.value
        return f"{value}_{suffix}"

    def unwrap_state(s: fa.State) -> str:
        s1, s2 = s.value
        return f"{s1}_{s2}"

    def unwrap_box(nfa: fa.EpsilonNFA) -> fa.EpsilonNFA:
        unwrapped_nfa = fa.EpsilonNFA(
            start_state={
                s if not wrapped_states else unwrap_state(s) for s in nfa.start_states
            },
            final_states={
                s if not wrapped_states else unwrap_state(s) for s in nfa.final_states
            },
        )
        for s_from, symb, s_to in iter_fa_transitions(nfa):
            new_symb = (
                unwrap_var(symb.value)
                if isinstance(symb.value, c.Variable)
                else symb.value.value
            )
            new_from = s_from if not wrapped_states else unwrap_state(s_from)
            new_to = s_to if not wrapped_states else unwrap_state(s_to)
            unwrapped_nfa.add_transition(new_from, new_symb, new_to)
        return unwrapped_nfa

    assert len(actual) == len(expected)
    for var in actual:
        actual_box = unwrap_box(actual[var])
        expected_box = (
            expected[unwrap_var(var)]
            if not wrapped_expected
            else unwrap_box(expected[var])
        )
        assert are_equivalent(actual_box, expected_box)


@pytest.mark.parametrize(
    "cfg, expected_boxes",
    load_test_data(
        "test_cfg_star",
        lambda d: (Cfg.from_raw_str(d["cfg_str"]), prepare_boxes(d["expected_boxes"])),
    ),
    ids=load_test_data("test_cfg_star", lambda d: d["cfg_str"]),
)
def test_cfg_star(cfg: Cfg[Int], expected_boxes: dict[str, fa.EpsilonNFA]):
    old_edges = deepcopy(cfg.get_edges())

    actual = cfg.star()

    assert cfg.get_edges() == old_edges  # No in-place mutation should occur
    assert_equivalent_boxes(actual._rsm.boxes, expected_boxes)


@pytest.mark.parametrize(
    "cfg1, cfg2, expected_boxes",
    load_test_data(
        "TestCfgCombinations",
        lambda d: (
            Cfg.from_raw_str(d["cfg1"]),
            Cfg.from_raw_str(d["cfg2"]),
            prepare_boxes(d["expected_boxes_concat"]),
        ),
    ),
    ids=load_test_data("TestCfgCombinations", lambda d: f"{d['cfg1']}, {d['cfg2']}"),
)
def test_cfg_concat(
    cfg1: Cfg[Int], cfg2: Cfg[Int], expected_boxes: dict[str, fa.EpsilonNFA]
):
    # Start boxes are combined, so should have no overlapping
    cfg2._rsm.boxes[cfg2._rsm.start] = reconstruct_if_equal_nodes(
        cfg1._rsm.boxes[cfg1._rsm.start],
        cfg2._rsm.boxes[cfg2._rsm.start],
        lambda n: Int(n.value + 1),
    )
    old_edges = deepcopy(cfg1.get_edges())

    actual = cfg1.concat(cfg2)

    assert cfg1.get_edges() == old_edges  # No in-place mutation should occur
    assert_equivalent_boxes(actual._rsm.boxes, expected_boxes)


@pytest.mark.parametrize(
    "cfg1, cfg2, expected_boxes",
    load_test_data(
        "TestCfgCombinations",
        lambda d: (
            Cfg.from_raw_str(d["cfg1"]),
            Cfg.from_raw_str(d["cfg2"]),
            prepare_boxes(d["expected_boxes_union"]),
        ),
    ),
    ids=load_test_data("TestCfgCombinations", lambda d: f"{d['cfg1']}, {d['cfg2']}"),
)
def test_cfg_union(
    cfg1: Cfg[Int], cfg2: Cfg[Int], expected_boxes: dict[str, fa.EpsilonNFA]
):
    # Start boxes are combined, so should have no overlapping
    cfg2._rsm.boxes[cfg2._rsm.start] = reconstruct_if_equal_nodes(
        cfg1._rsm.boxes[cfg1._rsm.start],
        cfg2._rsm.boxes[cfg2._rsm.start],
        lambda n: Int(n.value + 1),
    )
    old_edges = deepcopy(cfg1.get_edges())

    actual = cfg1.union(cfg2)

    assert cfg1.get_edges() == old_edges  # No in-place mutation should occur
    assert_equivalent_boxes(actual._rsm.boxes, expected_boxes)

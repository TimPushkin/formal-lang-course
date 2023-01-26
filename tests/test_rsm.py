from copy import deepcopy
from pathlib import Path

import pytest
from pyformlang import cfg as c
from pyformlang import finite_automaton as fa

from project.cfpq.ecfg import Ecfg
from project.cfpq.rsm import Rsm
from project.rpq.fa_utils import iter_fa_transitions
from tests.test_types_cfg import assert_equivalent_boxes
from tests.testing_utils import are_equivalent
from tests.testing_utils import content_file_path  # noqa
from tests.testing_utils import dot_str_to_nfa
from tests.testing_utils import load_test_data
from tests.testing_utils import load_test_ids


def _unwrap_cfg_nfa_symbols(nfa: fa.EpsilonNFA) -> fa.EpsilonNFA:
    unwrapped_nfa = fa.EpsilonNFA(
        start_state=nfa.start_states, final_states=nfa.final_states
    )
    for s_from, symb, s_to in iter_fa_transitions(nfa):
        unwrapped_nfa.add_transition(s_from, symb.value.value, s_to)
    return unwrapped_nfa


@pytest.mark.parametrize(
    "cfg, expected",
    load_test_data(
        "test_rsm_from_cfg",
        lambda d: (
            c.CFG.from_text(d["cfg"]),
            Rsm(
                c.Variable(d["rsm"]["start"]),
                {
                    c.Variable(var): dot_str_to_nfa(nfa)
                    for var, nfa in d["rsm"]["boxes"].items()
                },
            ),
        ),
    ),
    ids=load_test_ids("test_rsm_from_cfg"),
)
class TestFromCfg:
    def test_same_start(self, cfg: c.CFG, expected: Rsm):
        actual = Rsm.from_cfg(cfg)

        assert actual.start == expected.start

    def test_boxes_are_equivalent(self, cfg: c.CFG, expected: Rsm):
        actual = Rsm.from_cfg(cfg)

        assert len(actual.boxes) == len(expected.boxes)
        for var in expected.boxes:
            # pyformlang cannot test for equivalents when there are both variables and
            # terminals as symbols, but we can differentiate based on the capitalization
            assert are_equivalent(
                _unwrap_cfg_nfa_symbols(actual.boxes[var]), expected.boxes[var]
            )


@pytest.mark.parametrize(
    "ecfg, expected",
    load_test_data(
        "test_rsm_from_cfg",
        lambda d: (
            Ecfg.from_cfg(c.CFG.from_text(d["cfg"])),
            Rsm(
                c.Variable(d["rsm"]["start"]),
                {
                    c.Variable(var): dot_str_to_nfa(nfa)
                    for var, nfa in d["rsm"]["boxes"].items()
                },
            ),
        ),
    ),
    ids=load_test_ids("test_rsm_from_cfg"),
)
class TestFromEcfg:
    def test_same_start(self, ecfg: Ecfg, expected: Rsm):
        actual = Rsm.from_ecfg(ecfg)

        assert actual.start == expected.start

    def test_boxes_are_equivalent(self, ecfg: Ecfg, expected: Rsm):
        actual = Rsm.from_ecfg(ecfg)

        assert len(actual.boxes) == len(expected.boxes)
        for var in expected.boxes:
            assert are_equivalent(actual.boxes[var], expected.boxes[var])


@pytest.mark.parametrize(
    "content_file_path, expected",
    load_test_data(
        "test_rsm_from_dot_file",
        lambda d: (
            d["dot_text"],
            Rsm(
                c.Variable(d["rsm"]["start"]),
                {
                    c.Variable(var): dot_str_to_nfa(nfa)
                    for var, nfa in d["rsm"]["boxes"].items()
                },
            ),
        ),
    ),
    indirect=["content_file_path"],
    ids=load_test_ids("test_rsm_from_dot_file"),
)
class TestFromDotFile:
    def test_same_start(self, content_file_path: Path, expected: Rsm):
        actual = Rsm.from_dot_file(content_file_path)

        assert actual.start == expected.start

    def test_boxes_are_equivalent(self, content_file_path: c.CFG, expected: Rsm):
        actual = Rsm.from_dot_file(content_file_path)

        assert len(actual.boxes) == len(expected.boxes)
        for var in expected.boxes:
            # pyformlang cannot test for equivalents when there are both variables and
            # terminals as symbols, but can differentiate based on the capitalization
            assert are_equivalent(
                _unwrap_cfg_nfa_symbols(actual.boxes[var]), expected.boxes[var]
            )


@pytest.mark.parametrize(
    "original",
    load_test_data(
        "test_rsm_from_cfg",
        lambda d: Rsm.from_ecfg(Ecfg.from_cfg(c.CFG.from_text(d["cfg"]))),
    ),
    ids=load_test_ids("test_rsm_from_cfg"),
)
def test_minimized_are_equivalent_to_original(original: Rsm):
    minimized = deepcopy(original).minimize()

    assert len(minimized.boxes) == len(original.boxes)
    for var in original.boxes:
        assert are_equivalent(minimized.boxes[var], original.boxes[var])


@pytest.mark.parametrize(
    "rsm, expected",
    load_test_data(
        "test_rsm_get_reachables_from_cfg",
        lambda d: (
            Rsm.from_cfg(c.CFG.from_text(d["cfg"])),
            {(fa.State(v1), fa.State(v2)) for v1, v2 in d["expected"]},
        ),
    ),
    ids=load_test_ids("test_rsm_get_reachables_from_cfg"),
)
def test_rsm_get_reachables_from_cfg(
    rsm: Rsm, expected: set[tuple[fa.State, fa.State]]
):
    actual = rsm.get_reachables()
    assert actual == expected


@pytest.mark.parametrize(
    "content_file_path, expected",
    load_test_data(
        "test_rsm_get_reachables_from_file",
        lambda d: (
            d["dot_text"],
            {(fa.State(v1), fa.State(v2)) for v1, v2 in d["expected"]},
        ),
    ),
    indirect=["content_file_path"],
    ids=load_test_ids("test_rsm_get_reachables_from_file"),
)
def test_rsm_get_reachables_from_file(
    content_file_path: Path, expected: set[tuple[fa.State, fa.State]]
):
    rsm = Rsm.from_dot_file(content_file_path)

    actual = rsm.get_reachables()

    assert actual == expected


@pytest.mark.parametrize(
    "content_file_path, nfa, expected_boxes",
    load_test_data(
        "test_rsm_intersect",
        lambda d: (
            d["rsm"],
            dot_str_to_nfa(d["nfa"]),
            {var: dot_str_to_nfa(nfa) for var, nfa in d["expected_boxes"].items()},
        ),
    ),
    indirect=["content_file_path"],
    ids=load_test_ids("test_rsm_intersect"),
)
@pytest.mark.parametrize("swapped", [False, True], ids=["default", "swapped"])
def test_rsm_intersect(
    content_file_path: Path,
    nfa: fa.NondeterministicFiniteAutomaton,
    swapped: bool,
    expected_boxes: dict[str, fa.EpsilonNFA],
):
    rsm = Rsm.from_dot_file(content_file_path)

    actual = rsm.intersect(nfa, swapped)

    assert_equivalent_boxes(actual.boxes, expected_boxes, wrapped_states=True)

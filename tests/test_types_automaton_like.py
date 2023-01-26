from copy import deepcopy
from pathlib import Path

import pytest
from pyformlang.finite_automaton import EpsilonNFA

from project.litegql.types.automaton_like import AutomatonLike
from project.litegql.types.lgql_cfg import Cfg
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_reg import Reg
from project.litegql.types.lgql_set import Set
from tests.test_types_cfg import assert_equivalent_boxes
from tests.test_types_cfg import prepare_boxes
from tests.testing_utils import load_test_data
from tests.testing_utils import load_test_ids
from tests.testing_utils import reconstruct_if_equal_nodes


@pytest.fixture
def automaton_like(request, tmp_path: Path) -> AutomatonLike[Int]:
    cls, init_data = request.param

    if cls is Reg:
        path = tmp_path / "test_graph.dot"
        with open(path, "w") as f:
            f.write(init_data)
        return cls.from_file(path)

    assert cls is Cfg
    return cls.from_raw_str(init_data)


@pytest.mark.parametrize(
    "automaton_like",
    [
        *load_test_data(
            "test_reg_from_file",
            lambda d: (Reg, d["dot_text"]),
            data_filename="test_types_reg",
        ),
        *load_test_data(
            "test_cfg_from_raw_str",
            lambda d: (Cfg, d["cfg_str"]),
            data_filename="test_types_cfg",
        ),
    ],
    indirect=["automaton_like"],
    ids=[
        *[
            "(reg) " + n
            for n in load_test_ids("test_reg_from_file", data_filename="test_types_reg")
        ],
        *[
            "(cfg) " + n
            for n in load_test_ids(
                "test_cfg_from_raw_str", data_filename="test_types_cfg"
            )
        ],
    ],
)
@pytest.mark.parametrize(
    "vertices",
    [
        Set(set()),
        Set({Int(1), Int(2)}),
        Set({Int(999999), Int(-9999999), Int(2309494982)}),
    ],
    ids=["no vertices", "small int vertices", "large int vertices"],
)
class TestAutomatonLikeStartsFinalsModification:
    def test_add_starts(self, automaton_like: AutomatonLike[Int], vertices: Set[Int]):
        expected_old_starts = deepcopy(automaton_like.get_starts())
        expected_new_starts = Set(
            automaton_like.get_starts().value.union(vertices.value),
            vertices.meta.elem_meta,
        )

        new_reg = automaton_like.add_starts(vertices)

        assert automaton_like.get_starts() == expected_old_starts
        assert new_reg.get_starts() == expected_new_starts

    def test_add_finals(self, automaton_like: AutomatonLike[Int], vertices: Set[Int]):
        expected_old_finals = deepcopy(automaton_like.get_finals())
        expected_new_finals = Set(
            automaton_like.get_finals().value.union(vertices.value),
            vertices.meta.elem_meta,
        )

        new_reg = automaton_like.add_finals(vertices)

        assert automaton_like.get_finals() == expected_old_finals
        assert new_reg.get_finals() == expected_new_finals

    def test_set_starts(self, automaton_like: AutomatonLike[Int], vertices: Set[Int]):
        expected_old_starts = deepcopy(automaton_like.get_starts())

        new_reg = automaton_like.set_starts(vertices)

        assert automaton_like.get_starts() == expected_old_starts
        assert new_reg.get_starts() == vertices

    def test_set_finals(self, automaton_like: AutomatonLike[Int], vertices: Set[Int]):
        expected_old_finals = deepcopy(automaton_like.get_finals())

        new_reg = automaton_like.set_finals(vertices)

        assert automaton_like.get_finals() == expected_old_finals
        assert new_reg.get_finals() == vertices


def _ensure_no_overlapping(al1: AutomatonLike[Int], al2: AutomatonLike[Int]):
    if isinstance(al1, Reg) and isinstance(al2, Cfg):
        al2._rsm.boxes[al2._rsm.start] = reconstruct_if_equal_nodes(
            al1._nfa, al2._rsm.boxes[al2._rsm.start], lambda n: Int(n.value + 1)
        )
    elif isinstance(al1, Cfg) and isinstance(al2, Reg):
        al2._nfa = reconstruct_if_equal_nodes(
            al1._rsm.boxes[al1._rsm.start], al2._nfa, lambda n: Int(n.value + 1)
        )


@pytest.mark.parametrize(
    "al1, al2, expected_boxes",
    load_test_data(
        "TestAutomatonLikeCombinations",
        lambda d: (
            (
                Reg.from_raw_str(d["reg"]),
                Cfg.from_raw_str(d["cfg"]),
                prepare_boxes(d["expected_boxes_intersect"]),
            ),
            (
                Cfg.from_raw_str(d["cfg"]),
                Reg.from_raw_str(d["reg"]),
                prepare_boxes(d["expected_boxes_intersect"]),
            ),
        ),
        is_aggregated=True,
    ),
    ids=load_test_data(
        "TestAutomatonLikeCombinations",
        lambda d: [
            f"(reg-cfg) {d['reg']}, {d['cfg']}",
            f"(cfg-reg) {d['cfg']}, {d['reg']}",
        ],
        is_aggregated=True,
    ),
)
def test_rsm_intersect(
    al1: AutomatonLike[Int],
    al2: AutomatonLike[Int],
    expected_boxes: dict[str, EpsilonNFA],
):
    old_edges = deepcopy(al1.get_edges())
    _ensure_no_overlapping(al1, al2)

    actual = al1.intersect(al2)

    assert al1.get_edges() == old_edges  # No in-place mutation should occur
    assert isinstance(actual, Cfg)
    assert_equivalent_boxes(actual._rsm.boxes, expected_boxes)


@pytest.mark.parametrize(
    "al1, al2, expected_boxes",
    load_test_data(
        "TestAutomatonLikeCombinations",
        lambda d: [
            (
                Reg.from_raw_str(d["reg"]),
                Cfg.from_raw_str(d["cfg"]),
                prepare_boxes(d["expected_boxes_concat_reg_cfg"]),
            ),
            (
                Cfg.from_raw_str(d["cfg"]),
                Reg.from_raw_str(d["reg"]),
                prepare_boxes(d["expected_boxes_concat_cfg_reg"]),
            ),
        ],
        is_aggregated=True,
    ),
    ids=load_test_data(
        "TestAutomatonLikeCombinations",
        lambda d: [
            f"(reg-cfg) {d['reg']}, {d['cfg']}",
            f"(cfg-reg) {d['cfg']}, {d['reg']}",
        ],
        is_aggregated=True,
    ),
)
def test_automaton_like_concat(
    al1: AutomatonLike[Int],
    al2: AutomatonLike[Int],
    expected_boxes: dict[str, EpsilonNFA],
):
    old_edges = deepcopy(al1.get_edges())
    _ensure_no_overlapping(al1, al2)

    actual = al1.concat(al2)

    assert al1.get_edges() == old_edges  # No in-place mutation should occur
    assert isinstance(actual, Cfg)
    assert_equivalent_boxes(actual._rsm.boxes, expected_boxes)


@pytest.mark.parametrize(
    "al1, al2, expected_boxes",
    load_test_data(
        "TestAutomatonLikeCombinations",
        lambda d: [
            (
                Reg.from_raw_str(d["reg"]),
                Cfg.from_raw_str(d["cfg"]),
                prepare_boxes(d["expected_boxes_union_reg_cfg"]),
            ),
            (
                Cfg.from_raw_str(d["cfg"]),
                Reg.from_raw_str(d["reg"]),
                prepare_boxes(d["expected_boxes_union_cfg_reg"]),
            ),
        ],
        is_aggregated=True,
    ),
    ids=load_test_data(
        "TestAutomatonLikeCombinations",
        lambda d: [
            f"(reg-cfg) {d['reg']}, {d['cfg']}",
            f"(cfg-reg) {d['cfg']}, {d['reg']}",
        ],
        is_aggregated=True,
    ),
)
def test_reg_union(
    al1: AutomatonLike[Int],
    al2: AutomatonLike[Int],
    expected_boxes: dict[str, EpsilonNFA],
):
    _ensure_no_overlapping(al1, al2)
    old_edges = deepcopy(al1.get_edges())

    actual = al1.union(al2)

    assert al1.get_edges() == old_edges  # No in-place mutation should occur
    assert isinstance(actual, Cfg)
    assert_equivalent_boxes(actual._rsm.boxes, expected_boxes)

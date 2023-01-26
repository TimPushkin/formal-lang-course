from typing import Any

import pytest

from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_set import Set
from project.litegql.types.typing_utils import LgqlT

_CORRECT_INITS = [
    (None, None, Set.Meta(Int.Meta())),
    (set(), None, Set.Meta(Int.Meta())),
    (None, Bool.Meta(), Set.Meta(Bool.Meta())),
    (None, Set.Meta(Int.Meta()), Set.Meta(Set.Meta(Int.Meta()))),
    ({Bool(True)}, None, Set.Meta(Bool.Meta())),
    ({Bool(True)}, Int.Meta(), Set.Meta(Bool.Meta())),
    (
        {Set({Set({Pair(Int(0), Int(1))})})},
        None,
        Set.Meta(Set.Meta(Set.Meta(Pair.Meta(Int.Meta(), Int.Meta())))),
    ),
]


@pytest.mark.parametrize("vs, elem_meta, expected_meta", _CORRECT_INITS)
def test_set_correct_meta(
    vs: set[BaseType] | None,
    elem_meta: BaseType.Meta | None,
    expected_meta: Set.Meta,
):
    match vs, elem_meta:
        case None, None:
            s = Set()
        case None, _:
            s = Set(elem_meta=elem_meta)
        case _, None:
            s = Set(vs)
        case _:
            s = Set(vs, elem_meta)
    assert s.meta == expected_meta


@pytest.mark.parametrize("vs", [vs for (vs, _, _) in _CORRECT_INITS if vs is not None])
class TestSetByValue:
    def test_value(self, vs: set[BaseType]):
        s = Set(vs)
        assert len(s.value) == len(vs)
        for actual, expected in zip(Set(vs).value, vs):
            assert actual == expected

    def test_equality(self, vs: set[BaseType]):
        s1 = Set(vs)
        s2 = Set(vs)
        assert s1 == s2
        assert hash(s1) == hash(s2)


@pytest.mark.parametrize(
    "vs, elem_meta",
    [
        (1, None),
        (True, None),
        ({1}, None),
        ({True}, None),
        ({Int(1), Bool(True)}, None),
        ({Set({Set({Int(1)})}), Set({Set({Bool(True)})})}, None),
        ({Int(1), Bool(True)}, Int.Meta()),
        ({Int(1), Bool(True)}, Bool.Meta()),
        (
            {Set({Set({Int(1)})}), Set({Set({Bool(True)})})},
            Set.Meta(Set.Meta(Int.Meta())),
        ),
    ],
)
def test_set_init_incorrect(vs: Any, elem_meta: Any):
    with pytest.raises(TypeError):
        match vs, elem_meta:
            case None, None:
                Set()
            case None, _:
                Set(elem_meta=elem_meta)
            case _, None:
                Set(vs)
            case _:
                Set(vs, elem_meta)


@pytest.mark.parametrize(
    "vs",
    [
        set(),
        {Int(1), Int(2), Int(-3), Int(999)},
        {Bool(True), Bool(False)},
        {
            Pair(Pair(Int(1), Int(2)), Pair(Int(1), Int(2))),
            Pair(Pair(Int(4), Int(5)), Pair(Int(6), Int(7))),
        },
        {Set(set()), Set({Int(1), Int(2)})},
    ],
)
def test_set_contains_its_elements(vs: set):
    s = Set(vs)
    for v in vs:
        assert s.contains(v).value


@pytest.mark.parametrize(
    "s, item, expected",
    [
        (Set(), Int(1), False),
        (Set({Bool(True), Bool(False)}), Bool(False), True),
        (
            Set(
                {
                    Pair(Pair(Int(1), Int(2)), Pair(Int(1), Int(2))),
                    Pair(Pair(Int(4), Int(5)), Pair(Int(6), Int(7))),
                }
            ),
            Pair(Pair(Int(1), Int(2)), Pair(Int(1), Int(2))),
            True,
        ),
        (
            Set(
                {
                    Pair(Pair(Int(1), Int(2)), Pair(Int(1), Int(2))),
                    Pair(Pair(Int(4), Int(5)), Pair(Int(6), Int(7))),
                }
            ),
            Pair(Pair(Int(4), Int(5)), Pair(Int(6), Int(7))),
            True,
        ),
        (
            Set(
                {
                    Pair(Pair(Int(1), Int(2)), Pair(Int(1), Int(2))),
                    Pair(Pair(Int(4), Int(5)), Pair(Int(6), Int(7))),
                }
            ),
            Pair(Pair(Int(4), Int(5)), Pair(Int(6), Int(8))),
            False,
        ),
    ],
)
def test_contains_other_correct(s: Set[LgqlT], item: LgqlT, expected: bool):
    assert s.contains(item).value == expected


@pytest.mark.parametrize(
    "s, item",
    [
        (Set(), Bool(True)),
        (Set({Bool(True), Bool(False)}), Int(1)),
        (
            Set(
                {
                    Pair(Pair(Int(1), Int(2)), Pair(Int(1), Int(2))),
                    Pair(Pair(Int(4), Int(5)), Pair(Int(6), Int(7))),
                }
            ),
            Pair(
                Pair(Pair(Int(1), Int(2)), Pair(Int(1), Int(2))),
                Pair(Pair(Int(1), Int(2)), Pair(Int(1), Int(2))),
            ),
        ),
    ],
)
def test_contains_other_incorrect(s: Set, item: Any):
    with pytest.raises(TypeError):
        s.contains(item)

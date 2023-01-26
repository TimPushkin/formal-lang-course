from typing import Any

import pytest

from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.vertex_type import VertexType

_CORRECT_INITS = [
    (Int(0), Int(0), Pair.Meta(Int.Meta(), Int.Meta())),
    (
        Pair(Pair(Int(1), Int(2)), Pair(Int(3), Int(4))),
        Pair(Pair(Int(5), Int(6)), Int(7)),
        Pair.Meta(
            Pair.Meta(
                Pair.Meta(Int.Meta(), Int.Meta()), Pair.Meta(Int.Meta(), Int.Meta())
            ),
            Pair.Meta(Pair.Meta(Int.Meta(), Int.Meta()), Int.Meta()),
        ),
    ),
]


@pytest.mark.parametrize("fst, snd, expected_meta", _CORRECT_INITS)
def test_pair_init_correct(fst: VertexType, snd: VertexType, expected_meta: Pair.Meta):
    p = Pair(fst, snd)
    assert p.fst == fst
    assert p.snd == snd
    assert p.meta == expected_meta


@pytest.mark.parametrize(
    "fst, snd",
    [(fst, snd) for fst, snd, _ in _CORRECT_INITS],
)
def test_pair_equality(fst: VertexType, snd: VertexType):
    p1 = Pair(fst, snd)
    p2 = Pair(fst, snd)
    assert p1 == p2
    assert hash(p1) == hash(p2)


@pytest.mark.parametrize(
    "fst, snd",
    [
        (0, 1),
        (Int(0), 1),
        (Bool(False), Bool(False)),
        (Int(1), Bool(True)),
    ],
)
def test_pair_init_incorrect(fst: Any, snd: Any):
    with pytest.raises(TypeError):
        Pair(fst, snd)

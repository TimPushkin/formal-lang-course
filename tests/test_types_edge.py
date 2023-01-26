from typing import Any

import pytest

from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_edge import Edge
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_string import String
from project.litegql.types.vertex_type import VertexType

_CORRECT_INITS = [
    (Int(0), String(""), Int(0), Edge.Meta(Int.Meta())),
    (
        Pair(Int(2), Pair(Int(3), Int(4))),
        String("some label"),
        Pair(Int(6), Pair(Int(7), Int(8))),
        Edge.Meta(Pair.Meta(Int.Meta(), Pair.Meta(Int.Meta(), Int.Meta()))),
    ),
]


@pytest.mark.parametrize("st, lab, fn, expected_meta", _CORRECT_INITS)
def test_edge_init_correct(
    st: VertexType, lab: String, fn: VertexType, expected_meta: Pair.Meta
):
    e = Edge(st, lab, fn)
    assert e.st == st
    assert e.lab == lab
    assert e.fn == fn
    assert e.meta == expected_meta


@pytest.mark.parametrize(
    "st, lab, fn",
    [(st, lab, fn) for st, lab, fn, _ in _CORRECT_INITS],
)
def test_edge_equality(st: VertexType, lab: String, fn: VertexType):
    e1 = Edge(st, lab, fn)
    e2 = Edge(st, lab, fn)
    assert e1 == e2
    assert hash(e1) == hash(e2)


@pytest.mark.parametrize(
    "st, lab, fn",
    [
        (0, String(""), 1),
        (Int(0), String(""), 1),
        (Bool(False), String(""), Bool(False)),
        (Int(1), String(""), Bool(True)),
        (Int(1), String(""), Pair(Int(1), Int(0))),
        (
            Pair(
                Pair(Pair(Int(1), Int(1)), Pair(Int(1), Int(1))),
                Pair(Pair(Int(1), Int(1)), Pair(Int(1), Int(1))),
            ),
            String(""),
            Pair(Pair(Int(1), Int(1)), Pair(Int(1), Int(1))),
        ),
        (Int(1), Int(1), Int(1)),
    ],
)
def test_edge_init_incorrect(st: Any, lab: Any, fn: Any):
    with pytest.raises(TypeError):
        Edge(st, lab, fn)

import pytest

import project.litegql.pattern_matching as pm
from project.litegql.pattern_matching import match
from project.litegql.pattern_matching import Pattern
from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_edge import Edge
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_set import Set
from project.litegql.types.lgql_string import String


@pytest.mark.parametrize(
    "pat, value, expected",
    [
        (pm.Wildcard(), Int(1), {}),
        (pm.Wildcard(), Pair(Int(1), Int(2)), {}),
        (pm.Wildcard(), Edge(Int(1), String(""), Int(2)), {}),
        (pm.Wildcard(), Set({Int(1), Int(2)}), {}),
        (pm.Name("n"), Int(1), {"n": Int(1)}),
        (pm.Name("Pair"), Pair(Int(1), Int(2)), {"Pair": Pair(Int(1), Int(2))}),
        (
            pm.Name("_edge_3"),
            Edge(Int(1), String(""), Int(2)),
            {"_edge_3": Edge(Int(1), String(""), Int(2))},
        ),
        (pm.Name("x"), Set({Int(1), Int(2)}), {"x": Set({Int(1), Int(2)})}),
        (pm.Unpair(pm.Wildcard(), pm.Wildcard()), Pair(Int(1), Int(1)), {}),
        (
            pm.Unpair(pm.Name("fst"), pm.Name("snd")),
            Pair(Int(1), Int(2)),
            {"fst": Int(1), "snd": Int(2)},
        ),
        (
            pm.Unpair(
                pm.Unpair(pm.Name("a"), pm.Unpair(pm.Wildcard(), pm.Name("b"))),
                pm.Name("c"),
            ),
            Pair(
                Pair(Pair(Int(1), Int(2)), Pair(Int(3), Int(4))),
                Pair(Pair(Int(5), Int(6)), Pair(Int(7), Int(8))),
            ),
            {
                "a": Pair(Int(1), Int(2)),
                "b": Int(4),
                "c": Pair(Pair(Int(5), Int(6)), Pair(Int(7), Int(8))),
            },
        ),
        (
            pm.Unedge(pm.Name("st"), pm.Name("lab"), pm.Name("fn")),
            Edge(Int(1), String(""), Int(2)),
            {"st": Int(1), "lab": String(""), "fn": Int(2)},
        ),
        (
            pm.Unedge(
                pm.Name("a"), pm.Wildcard(), pm.Unpair(pm.Wildcard(), pm.Name("b"))
            ),
            Edge(
                Pair(Pair(Int(1), Int(2)), Pair(Int(3), Int(4))),
                String(""),
                Pair(Pair(Int(5), Int(6)), Pair(Int(7), Int(8))),
            ),
            {
                "a": Pair(Pair(Int(1), Int(2)), Pair(Int(3), Int(4))),
                "b": Pair(Int(7), Int(8)),
            },
        ),
    ],
)
def test_match_positive(pat: Pattern, value: BaseType, expected: dict[str, BaseType]):
    assert match(pat, value) == expected


@pytest.mark.parametrize(
    "pat, value",
    [
        (pm.Unpair(pm.Wildcard(), pm.Wildcard()), Int(1)),
        (pm.Unpair(pm.Wildcard(), pm.Wildcard()), Edge(Int(1), String("l"), Int(2))),
        (
            pm.Unpair(pm.Wildcard(), pm.Unpair(pm.Wildcard(), pm.Wildcard())),
            Pair(Int(1), Int(2)),
        ),
        (pm.Unedge(pm.Wildcard(), pm.Wildcard(), pm.Wildcard()), Int(0)),
        (pm.Unedge(pm.Wildcard(), pm.Wildcard(), pm.Wildcard()), Pair(Int(1), Int(2))),
        (
            pm.Unedge(
                pm.Wildcard(), pm.Unpair(pm.Wildcard(), pm.Wildcard()), pm.Wildcard()
            ),
            Edge(Int(1), String(""), Int(2)),
        ),
        (
            pm.Unedge(
                pm.Wildcard(),
                pm.Unedge(pm.Wildcard(), pm.Wildcard(), pm.Wildcard()),
                pm.Wildcard(),
            ),
            Edge(Int(1), String(""), Int(2)),
        ),
    ],
)
def test_match_negative(pat: Pattern, value: BaseType):
    with pytest.raises(ValueError):
        match(pat, value)

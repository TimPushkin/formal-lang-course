import pytest

from project.litegql.grammar.LiteGQLParser import LiteGQLParser
from project.litegql.interpret_visitor import InterpretVisitor
from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_set import Set
from project.litegql.types.lgql_string import String
from tests.testing_utils import expr_ctx  # noqa
from tests.testing_utils import fail


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ("1 in {}", Bool(False)),
        ("1 in {1, 2, 3}", Bool(True)),
        (
            "((1, 2), (3, 4)) in {((1, 2), (3, 4)), ((2, 2), (2, 2))}",
            Bool(True),
        ),
        ("{5} in {{}, {1, 2, 3}, {5}}", Bool(True)),
        (
            "((1, 2), (3, 5)) in {((1, 2), (3, 4)), ((2, 2), (2, 2))}",
            Bool(False),
        ),
        ("{{5}} in {{{}}, {{1, 2, 3}, {5}}}", Bool(False)),
    ],
    indirect=["ctx"],
)
def test_visit_contains(ctx: LiteGQLParser.ContainsContext, expected: Bool):
    actual = InterpretVisitor(output=fail).visitContains(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx",
    [
        "true in {1, 2}",
        "true in {}",
        "((1, 2), (3, 4)) in {((true, true), (true, true))}",
        "{5} in {{{}}, {{1, 2, 3}, {5}}}",
    ],
    indirect=["ctx"],
)
def test_visit_contains_incorrect(ctx: LiteGQLParser.ContainsContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitContains(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ("map({_ -> true}, {})", Set()),
        ("map({_ -> 1}, {1, 2, 3})", Set({Int(1)})),
        ("map({_ -> -1}, {1})", Set({Int(-1)})),
        ("map({x -> x}, {1, 2, 3})", Set({Int(1), Int(2), Int(3)})),
        (
            "map({x -> {x}}, {1, 2, 3}",
            Set({Set({Int(1)}), Set({Int(2)}), Set({Int(3)})}),
        ),
        (
            "map({x -> x}, {(1, 2), (3, 4)}",
            Set({Pair(Int(1), Int(2)), Pair(Int(3), Int(4))}),
        ),
        (
            "map({(fst, snd) -> (snd, fst)}, {(1, 2), (3, 4)}",
            Set({Pair(Int(2), Int(1)), Pair(Int(4), Int(3))}),
        ),
        (
            'map({(st, lab, _) -> lab}, {(1, "a", 2), (3, "b", 4)}',
            Set({String("a"), String("b")}),
        ),
        (
            'map({((u, _), _, (_, v)) -> (u, v)}, {((1, 2), "a", (3, 4)), '
            '((5, 6), "a", (7, 8))}',
            Set({Pair(Int(1), Int(4)), Pair(Int(5), Int(8))}),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_map(ctx: LiteGQLParser.MapContext, expected: Set):
    actual = InterpretVisitor(output=fail).visitMap(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx",
    [
        "map({_ -> 1}, 1)",
        "map({_ -> 1}, (1, 2))",
        'map({_ -> 1}, (1, "a", 2))',
        'map({_ -> 1}, r"a b c")',
    ],
    indirect=["ctx"],
)
def test_visit_map_incorrect_iterable(ctx: LiteGQLParser.MapContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitMap(ctx)


@pytest.mark.parametrize(
    "ctx",
    ["map({(_, _) -> 1}, {1, 2, 3})", "map({(_, _, _) -> 1}, {(1, 2), (3, 4)})"],
    indirect=["ctx"],
)
def test_visit_map_incorrect_pattern(ctx: LiteGQLParser.MapContext):
    with pytest.raises(ValueError):
        InterpretVisitor(output=fail).visitMap(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        (
            "filter({_ -> true}, {(1, 2), (3, 4)})",
            Set({Pair(Int(1), Int(2)), Pair(Int(3), Int(4))}),
        ),
        (
            "filter({_ -> false}, {(1, 2), (3, 4)})",
            Set(elem_meta=Pair.Meta(Int.Meta(), Int.Meta())),
        ),
        ("filter({_ -> true}, {})", Set()),
        (
            "filter({(x, _) -> x in {1, 2}}, {(1, 1), (3, 1), (3, 3), (5, 2), "
            "(2, -1)})",
            Set({Pair(Int(1), Int(1)), Pair(Int(2), Int(-1))}),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_filter(ctx: LiteGQLParser.FilterContext, expected: Set):
    actual = InterpretVisitor(output=fail).visitFilter(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx",
    [
        "filter({_ -> true}, 1)",
        "filter({_ -> true}, (1, 2))",
        'filter({_ -> true}, (1, "a", 2))',
        'filter({_ -> true}, r"a b c")',
    ],
    indirect=["ctx"],
)
def test_visit_filter_incorrect_iterable(ctx: LiteGQLParser.FilterContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitFilter(ctx)


@pytest.mark.parametrize(
    "ctx",
    ["filter({_ -> 1}, {1, 2, 3})", "filter({_ -> (true, true)}, {(1, 2), (3, 4)})"],
    indirect=["ctx"],
)
def test_visit_filter_incorrect_lambda(ctx: LiteGQLParser.FilterContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitFilter(ctx)


@pytest.mark.parametrize(
    "ctx",
    [
        "filter({(_, _) -> true}, {1, 2, 3})",
        "filter({(_, _, _) -> true}, {(1, 2), (3, 4)})",
    ],
    indirect=["ctx"],
)
def test_visit_filter_incorrect_pattern(ctx: LiteGQLParser.FilterContext):
    with pytest.raises(ValueError):
        InterpretVisitor(output=fail).visitFilter(ctx)

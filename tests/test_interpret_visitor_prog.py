import pytest

from project.litegql.grammar.LiteGQLParser import LiteGQLParser
from project.litegql.interpret_visitor import InterpretVisitor
from project.litegql.parsing import get_parser
from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_set import Set
from tests.testing_utils import fail


@pytest.fixture(name="ctx")
def prog_ctx(request) -> LiteGQLParser.ProgContext:
    return get_parser(request.param).prog()


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ("", {}),
        ("x = 1; y = 2", {"x": Int(1), "y": Int(2)}),
        ("x = 1; x = 2", {"x": Int(2)}),
        ("x = 1; x = true", {"x": Bool(True)}),
        ("x = 1; y = 1; x = true", {"x": Bool(True), "y": Int(1)}),
        ("x = {}}; y = 1; x = y", {"x": Int(1), "y": Int(1)}),
        (
            "x = 1; y = map({v -> v}, {1, 2, 3})",
            {"x": Int(1), "y": Set({Int(1), Int(2), Int(3)})},
        ),
        ("x = 1; y = map({v -> x}, {1, 2, 3})", {"x": Int(1), "y": Set({Int(1)})}),
        (
            "x = 1; y = map({x -> x}, {1, 2, 3})",
            {"x": Int(1), "y": Set({Int(1), Int(2), Int(3)})},
        ),
        (
            "x = 1; y = map({x -> map({x -> 0}, x)}, {{1}, {2}, {3}})",
            {"x": Int(1), "y": Set({Set({Int(0)})})},
        ),
    ],
    indirect=["ctx"],
)
def test_prog_scopes(ctx: LiteGQLParser.ProgContext, expected: dict[str, BaseType]):
    visitor = InterpretVisitor(output=fail)

    visitor.visitProg(ctx)

    assert len(visitor._scopes) == 1
    assert visitor._scopes[0] == expected


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ("print(1); print(2)", [str(Int(1)), str(Int(2))]),
        ("x = (1, 2); print(x)", [str(Pair(Int(1), Int(2)))]),
    ],
    indirect=["ctx"],
)
def test_prog_prints(ctx: LiteGQLParser.ProgContext, expected: list[str]):
    actual = []

    InterpretVisitor(output=actual.append).visitProg(ctx)

    assert actual == expected

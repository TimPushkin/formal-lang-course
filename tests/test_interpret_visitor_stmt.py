import pytest

from project.litegql.grammar.LiteGQLParser import LiteGQLParser
from project.litegql.interpret_visitor import InterpretVisitor
from project.litegql.parsing import get_parser
from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_set import Set
from tests.testing_utils import fail


@pytest.fixture(name="ctx")
def stmt_ctx(request) -> LiteGQLParser.StmtContext:
    return get_parser(request.param).stmt()


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ("x = 1", {"x": Int(1)}),
        ("_abc123 = map({x -> x}, {1, 2})", {"_abc123": Set({Int(1), Int(2)})}),
    ],
    indirect=["ctx"],
)
def test_visit_bind(ctx: LiteGQLParser.BindContext, expected: dict[str, BaseType]):
    visitor = InterpretVisitor(output=fail)

    visitor.visitBind(ctx)

    assert visitor._scopes[0] == expected


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('print("")', [""]),
        ("print(1)", [str(Int(1))]),
        ("print({1, 2, 3})", [str(Set({Int(1), Int(2), Int(3)}))]),
    ],
    indirect=["ctx"],
)
def test_visit_print(ctx: LiteGQLParser.PrintContext, expected: list[str]):
    actual = []

    InterpretVisitor(output=actual.append).visitPrint(ctx)

    assert actual == expected

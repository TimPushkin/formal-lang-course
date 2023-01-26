import pytest

from project.litegql.grammar.LiteGQLParser import LiteGQLParser
from project.litegql.interpret_visitor import InterpretVisitor
from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_cfg import Cfg
from project.litegql.types.lgql_edge import Edge
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_reg import Reg
from project.litegql.types.lgql_set import Set
from project.litegql.types.lgql_string import String
from tests.test_types_cfg import assert_equivalent_boxes
from tests.testing_utils import are_equivalent
from tests.testing_utils import expr_ctx  # noqa
from tests.testing_utils import fail


@pytest.mark.parametrize(
    "ctx, expected",
    [("true", Bool(True)), ("false", Bool(False))],
    indirect=["ctx"],
)
def test_visit_bool(ctx: LiteGQLParser.BoolContext, expected: Bool):
    actual = InterpretVisitor(output=fail).visitBool(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx, expected",
    [("0", Int(0)), ("-123", Int(-123)), ("234", Int(234))],
    indirect=["ctx"],
)
def test_visit_int(ctx: LiteGQLParser.IntContext, expected: Int):
    actual = InterpretVisitor(output=fail).visitInt(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx, expected",
    [('""', String("")), ('"abc"', String("abc")), ('"123"', String("123"))],
    indirect=["ctx"],
)
def test_visit_string(ctx: LiteGQLParser.StringContext, expected: String):
    actual = InterpretVisitor(output=fail).visitString(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ("{}", Set()),
        ("{1, 2, 3}", Set({Int(1), Int(2), Int(3)})),
        ("{true, true, false, false, true}", Set({Bool(True), Bool(False)})),
        ("{{}, {1, 2, 3}}", Set({Set(), Set({Int(1), Int(2), Int(3)})})),
    ],
    indirect=["ctx"],
)
def test_visit_set(ctx: LiteGQLParser.SetContext, expected: Set):
    actual = InterpretVisitor(output=fail).visitSet(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx, expected",
    [('r""', Reg.from_raw_str("")), ('r"a b c"', Reg.from_raw_str("a b c"))],
    indirect=["ctx"],
)
def test_visit_reg(ctx: LiteGQLParser.RegContext, expected: Reg[Int]):
    actual = InterpretVisitor(output=fail).visitReg(ctx)
    assert are_equivalent(actual._nfa, expected._nfa)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('c""', Cfg.from_raw_str("")),
        ('c"S -> a S b S | epsilon"', Cfg.from_raw_str("S -> a S b S | epsilon")),
    ],
    indirect=["ctx"],
)
def test_visit_cfg(ctx: LiteGQLParser.CfgContext, expected: Cfg[Int]):
    actual = InterpretVisitor(output=fail).visitCfg(ctx)
    assert actual._rsm.start == expected._rsm.start
    assert_equivalent_boxes(
        actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
    )


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ("(1, 2)", Pair(Int(1), Int(2))),
        ("((1, 2), (3 , 4))", Pair(Pair(Int(1), Int(2)), Pair(Int(3), Int(4)))),
    ],
    indirect=["ctx"],
)
def test_visit_pair(ctx: LiteGQLParser.PairContext, expected: Pair):
    actual = InterpretVisitor(output=fail).visitPair(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx",
    ["(true, false)", "((1, 2), (3, {}))"],
    indirect=["ctx"],
)
def test_visit_pair_incorrect(ctx: LiteGQLParser.PairContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitPair(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('(1, "abc", 2)', Edge(Int(1), String("abc"), Int(2))),
        (
            '((1, 2), "", (3 , 4))',
            Edge(Pair(Int(1), Int(2)), String(""), Pair(Int(3), Int(4))),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_edge(ctx: LiteGQLParser.EdgeContext, expected: Edge):
    actual = InterpretVisitor(output=fail).visitEdge(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx",
    ["(1, 2, 3)", "((1, 2), (3 , 4), (5 , 6))"],
    indirect=["ctx"],
)
def test_visit_edge_incorrect(ctx: LiteGQLParser.EdgeContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitEdge(ctx)

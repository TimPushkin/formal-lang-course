import pytest

from project.litegql.grammar.LiteGQLParser import LiteGQLParser
from project.litegql.interpret_visitor import InterpretVisitor
from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_cfg import Cfg
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_reg import Reg
from project.litegql.types.lgql_string import String
from tests.test_types_cfg import assert_equivalent_boxes
from tests.testing_utils import are_equivalent  # noqa
from tests.testing_utils import expr_ctx  # noqa
from tests.testing_utils import fail


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ("(true)", Bool(True)),
        ("((((1 , 2))))", Pair(Int(1), Int(2))),
        ('(("a" | "b")*)', String("a").union(String("b")).star()),
        (
            '(r"a b" | (("c" | ("d")) | "e"))',
            String("c").union(
                String("d", start_index=2).union(
                    String("e", start_index=4).union(
                        Reg.from_raw_str("a b", start_index=6)
                    )
                )
            ),
        ),
        (
            '(("a" | "b") . ("c" | "d"))',
            String("a")
            .union(String("b", start_index=2))
            .concat(String("c", start_index=4).union(String("d", start_index=6))),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_parens(ctx: LiteGQLParser.ParensContext, expected: BaseType):
    actual = InterpretVisitor(output=fail).visitParens(ctx)
    if isinstance(actual, Reg):
        assert are_equivalent(actual._nfa, expected._nfa)
    elif isinstance(actual, Cfg):
        assert actual._rsm.start == expected._rsm.start
        assert_equivalent_boxes(
            actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
        )
    else:
        assert actual == expected


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('("a" | "b")*', String("a").union(String("b", start_index=2)).star()),
        (
            'map({(_, l, _) -> l}, get_edges(r"a b c"))',
            Reg.from_raw_str("a b c").get_labels(),
        ),
        (
            'get_reachables(load("skos") & "subClassOf"))',
            Reg.from_dataset("skos")
            .intersect(String("subClassOf", start_index=2))
            .get_reachables(),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_expr(ctx: LiteGQLParser.ExprContext, expected: BaseType):
    actual = InterpretVisitor(output=fail).visit(ctx)
    if isinstance(actual, Reg):
        assert are_equivalent(actual._nfa, expected._nfa)
    elif isinstance(actual, Cfg):
        assert actual._rsm.start == expected._rsm.start
        assert_equivalent_boxes(
            actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
        )
    else:
        assert actual == expected


@pytest.fixture(name="visitor")
def visitor_with_increased_start_index(request):
    visitor = InterpretVisitor(output=fail)
    visitor._automaton_start_index = request.param
    return visitor


@pytest.mark.parametrize(
    "ctx",
    [
        '"abc defg hijk lmno"',
        'r"a b c"',
        'c"S -> a S b S | A\nA -> B\nB -> epsilon"',
    ],
    indirect=["ctx"],
)
@pytest.mark.parametrize("visitor", [0, 10, -100], indirect=["visitor"])
def test_automaton_start_index(
    ctx: LiteGQLParser.ExprContext, visitor: InterpretVisitor
):
    initial_start_index = visitor._automaton_start_index

    vertices = visitor.visit(ctx).get_vertices().value

    assert visitor._automaton_start_index == initial_start_index + len(vertices)
    assert vertices == set(
        Int(n) for n in range(initial_start_index, initial_start_index + len(vertices))
    )

import pytest

from project.litegql.interpret_visitor import InterpretVisitor
from project.litegql.parsing import get_parser
from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_reg import Reg
from project.litegql.types.lgql_set import Set
from tests.testing_utils import expr_ctx  # noqa
from tests.testing_utils import fail


@pytest.mark.parametrize("var", ["x", "AbC", "_something123"])
@pytest.mark.parametrize(
    "value", [Int(1), Set({Int(1), Int(2)}), Reg.from_raw_str("a")]
)
def test_visit_var_global(var: str, value: BaseType):
    visitor = InterpretVisitor(output=fail)
    visitor._scopes[0][var] = value

    actual = visitor.visitVar(get_parser(var).expr())

    assert actual == value

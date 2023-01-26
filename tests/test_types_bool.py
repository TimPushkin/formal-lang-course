from typing import Any

import pytest

from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_int import Int


@pytest.mark.parametrize("v", [True, False])
class TestBoolInitCorrect:
    def test_init(self, v: bool):
        Bool(v)

    def test_equality(self, v: bool):
        b1 = Bool(v)
        b2 = Bool(v)
        assert b1 == b2
        assert hash(b1) == hash(b2)


@pytest.mark.parametrize(
    "v", [0, 1, -1, Int(1), Bool(True), "something", tuple(), set()]
)
def test_bool_init_incorrect(v: Any):
    with pytest.raises(TypeError):
        Bool(v)


def test_bools_have_equal_meta():
    assert Bool(True).meta == Bool(False).meta

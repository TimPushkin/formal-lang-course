from typing import Any

import pytest

from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_int import Int


@pytest.mark.parametrize("v", [0, 1, 100, -100])
class TestIntInitCorrect:
    def test_init(self, v: int):
        Int(v)

    def test_equality(self, v: int):
        n1 = Int(v)
        n2 = Int(v)
        assert n1 == n2
        assert hash(n1) == hash(n2)


@pytest.mark.parametrize("v", [0.0, Int(1), Bool(True), "something", tuple(), set()])
def test_int_init_incorrect(v: Any):
    with pytest.raises(TypeError):
        Int(v)


def test_ints_have_equal_meta():
    assert Int(5).meta == Int(-100).meta

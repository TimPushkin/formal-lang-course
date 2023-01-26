from typing import Any

import pytest

from project.litegql.types.lgql_set import Set
from project.litegql.types.lgql_string import String


@pytest.mark.parametrize(
    "v", ["", "abc", "123", "      ", "\n", "a* (b | c)", "epsilon"]
)
class TestStrInitCorrect:
    def test_init(self, v: str):
        String(v)

    def test_equality(self, v: str):
        s1 = String(v)
        s2 = String(v)
        assert s1 == s2
        assert hash(s1) == hash(s2)

    def test_value(self, v: str):
        s = String(v)
        assert s.value == v

    def test_str(self, v: str):
        s = String(v)
        assert str(s) == v


@pytest.mark.parametrize("v", [1, True, Set({String("1")}), String("abc")])
def test_string_init_incorrect(v: Any):
    with pytest.raises(TypeError):
        String(v)

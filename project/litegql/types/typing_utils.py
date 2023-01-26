from typing import Iterable
from typing import TypeVar

from project.litegql.types.base_type import BaseType
from project.litegql.types.vertex_type import VertexType

LgqlT = TypeVar("LgqlT", bound=BaseType)
VertexT = TypeVar("VertexT", bound=VertexType)
OtherVertexT = TypeVar("OtherVertexT", bound=VertexType)  # Used for pairs


def are_of_same_lgql_type(vs: Iterable) -> bool:
    iterator = iter(vs)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    # first is checked separately in case vs cannot be re-iterated from the beginning
    return isinstance(first, BaseType) and all(
        isinstance(v, BaseType) and first.meta == v.meta for v in iterator
    )


def is_of_vertex_type(v: LgqlT) -> bool:
    return isinstance(v, VertexType)

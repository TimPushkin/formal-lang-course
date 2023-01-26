from typing import Generic
from typing import TYPE_CHECKING

from project.litegql.types.base_type import BaseType
from project.litegql.types.typing_utils import are_of_same_lgql_type
from project.litegql.types.typing_utils import is_of_vertex_type
from project.litegql.types.typing_utils import VertexT

if TYPE_CHECKING:
    from project.litegql.types.lgql_string import String


class Edge(BaseType, Generic[VertexT]):
    class Meta(BaseType.CollectionMeta):
        @property
        def _str_prefix(self) -> str:
            return Edge.__name__

    def __init__(self, st: VertexT, lab: "String", fn: VertexT):
        from project.litegql.types.lgql_string import String

        if (
            not is_of_vertex_type(st)
            or not are_of_same_lgql_type((st, fn))
            or not isinstance(lab, String)
        ):
            raise TypeError("Expected edge with vertexes of same type and string label")
        self._st, self._lab, self._fn = st, lab, fn
        assert self._st.meta == self._fn.meta
        self._meta = Edge.Meta(self._st.meta)

    @property
    def st(self) -> VertexT:
        return self._st

    @property
    def lab(self) -> "String":
        return self._lab

    @property
    def fn(self) -> VertexT:
        return self._fn

    @property
    def meta(self) -> Meta:
        return self._meta

    def __eq__(self, other) -> bool | type(NotImplemented):
        return (
            self._st == other._st and self._lab == other._lab and self._fn == other._fn
            if isinstance(other, Edge)
            else NotImplemented
        )

    def __hash__(self) -> int:
        return hash((self._st, self._lab, self._fn))

    def __repr__(self) -> str:
        return f"{Edge.__name__}({repr(self._st)}, {repr(self._lab)}, {repr(self._fn)})"

    def __str__(self) -> str:
        return f"{self._st}-{self._lab}->{self._fn}"

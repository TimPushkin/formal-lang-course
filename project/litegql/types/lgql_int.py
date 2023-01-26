from project.litegql.types.vertex_type import VertexType


class Int(VertexType):
    class Meta(VertexType.Meta):
        def __repr__(self):
            return Int.__name__

    _meta = Meta()

    def __init__(self, v: int):
        if not isinstance(v, int):
            raise TypeError("Expected int")
        self._v = v

    @property
    def value(self) -> int:
        return self._v

    @property
    def meta(self) -> Meta:
        return self._meta

    def __eq__(self, other) -> bool | type(NotImplemented):
        return self._v == other._v if isinstance(other, Int) else NotImplemented

    def __lt__(self, other) -> bool | type(NotImplemented):
        return self._v < other._v if isinstance(other, Int) else NotImplemented

    def __hash__(self) -> int:
        return hash(self._v)

    def __repr__(self) -> str:
        return str(self._v)

from project.litegql.types.base_type import BaseType


class Bool(BaseType):
    class Meta(BaseType.Meta):
        def __repr__(self) -> str:
            return Bool.__name__

    _meta = Meta()

    def __init__(self, v: bool):
        if not isinstance(v, bool):
            raise TypeError("Expected bool")
        self._v = v

    @property
    def value(self) -> bool:
        return self._v

    @property
    def meta(self) -> Meta:
        return self._meta

    def __eq__(self, other) -> bool | type(NotImplemented):
        return self._v == other._v if isinstance(other, Bool) else NotImplemented

    def __hash__(self) -> int:
        return hash(self._v)

    def __repr__(self) -> str:
        return str(self._v)

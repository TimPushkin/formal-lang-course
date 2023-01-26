import collections.abc
from typing import Generic

from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_int import Int
from project.litegql.types.typing_utils import are_of_same_lgql_type
from project.litegql.types.typing_utils import LgqlT


class Set(BaseType, Generic[LgqlT]):
    class Meta(BaseType.CollectionMeta):
        @property
        def _str_prefix(self) -> str:
            return Set.__name__

    def __init__(
        self,
        vs: collections.abc.Set[LgqlT] | None = None,
        elem_meta: BaseType.Meta = Int.Meta(),
    ):
        if vs is None:
            vs = frozenset()
        if not isinstance(vs, collections.abc.Set) or not are_of_same_lgql_type(vs):
            raise TypeError("Expected set with elements of same LiteGQL type")
        if len(vs) > 0:
            elem_meta = next(iter(vs)).meta
        self._vs = frozenset(vs)
        self._meta = Set.Meta(elem_meta)

    # Not using __contains__ as it should not raise for non-element-typed items, and it
    # returns raw bools
    def contains(self, item: LgqlT) -> Bool:
        if not isinstance(item, BaseType) or item.meta != self.meta.elem_meta:
            actual_type = item.meta if isinstance(item, BaseType) else type(item)
            raise TypeError(
                f"Cannot check if {actual_type} is among {self.meta.elem_meta} elements"
            )
        return Bool(item in self._vs)

    @property
    def value(self) -> frozenset[LgqlT]:
        return self._vs

    @property
    def meta(self) -> Meta:
        return self._meta

    def __eq__(self, other) -> bool | type(NotImplemented):
        return self._vs == other._vs if isinstance(other, Set) else NotImplemented

    def __hash__(self) -> int:
        return hash(self._vs)

    def __repr__(self) -> str:
        repr_elems = ", ".join(str(v) for v in self._vs)
        repr_meta = f", {repr(self.meta.elem_meta)}" if len(self._vs) == 0 else ""
        return f"Set({repr_elems}{repr_meta})"

    def __str__(self) -> str:
        # Collections usually use repr() of their elements
        return "{" + ", ".join(str(v) for v in self._vs) + "}"

from typing import Generic

from project.litegql.types.typing_utils import is_of_vertex_type
from project.litegql.types.typing_utils import OtherVertexT as SndVertexT
from project.litegql.types.typing_utils import VertexT as FstVertexT
from project.litegql.types.vertex_type import VertexType


class Pair(VertexType, Generic[FstVertexT, SndVertexT]):
    class Meta(VertexType.Meta):
        """
        Used to store the actual "deep" type of an instance.

        Allows different meta-types for the elements of a pair.
        """

        def __init__(self, fst_meta: VertexType.Meta, snd_meta: VertexType.Meta):
            if not isinstance(fst_meta, VertexType.Meta) or not isinstance(
                snd_meta, VertexType.Meta
            ):
                raise TypeError("Expected vertex meta-type")
            self._fst_meta = fst_meta
            self._snd_meta = snd_meta

        @property
        def fst_meta(self) -> VertexType.Meta:
            return self._fst_meta

        @property
        def snd_meta(self) -> VertexType.Meta:
            return self._snd_meta

        def __eq__(self, other) -> bool | type(NotImplemented):
            return (
                self._fst_meta == other._fst_meta and self._snd_meta == other._snd_meta
                if isinstance(other, Pair.Meta)
                else NotImplemented
            )

        def __hash__(self) -> int:
            return hash((self._fst_meta, self._snd_meta))

        def __repr__(self) -> str:
            return f"{Pair.__name__}[{self._fst_meta}, {self._snd_meta}]"

    def __init__(self, fst: FstVertexT, snd: SndVertexT):
        if not is_of_vertex_type(fst) or not is_of_vertex_type(snd):
            raise TypeError("Expected pair with elements of vertex type")
        self._fst, self._snd = fst, snd
        self._meta = Pair.Meta(self._fst.meta, self._snd.meta)

    @property
    def fst(self) -> FstVertexT:
        return self._fst

    @property
    def snd(self) -> SndVertexT:
        return self._snd

    @property
    def meta(self) -> Meta:
        return self._meta

    def __eq__(self, other) -> bool | type(NotImplemented):
        return (
            self._fst == other._fst and self._snd == other._snd
            if isinstance(other, Pair)
            else NotImplemented
        )

    def __lt__(self, other) -> bool | type(NotImplemented):
        return (
            self._fst < other._fst
            or (self._fst == other._fst and self._snd < other._snd)
            if isinstance(other, Pair)
            else NotImplemented
        )

    def __hash__(self) -> int:
        return hash((self._fst, self._snd))

    def __repr__(self) -> str:
        return f"({repr(self._fst)}, {repr(self._snd)})"

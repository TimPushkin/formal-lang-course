import abc
from pathlib import Path
from typing import Generic
from typing import TYPE_CHECKING

from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_edge import Edge
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_set import Set
from project.litegql.types.typing_utils import OtherVertexT
from project.litegql.types.typing_utils import VertexT

if TYPE_CHECKING:
    from project.litegql.types.lgql_string import String


class AutomatonLike(BaseType, Generic[VertexT], abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_file(cls, path: Path) -> "AutomatonLike[Int]":
        ...

    @classmethod
    @abc.abstractmethod
    def from_raw_str(cls, raw_str: str, start_index: int = 0) -> "AutomatonLike[Int]":
        ...

    @abc.abstractmethod
    def add_starts(self, vs: Set[VertexT]) -> "AutomatonLike[VertexT]":
        ...

    @abc.abstractmethod
    def add_finals(self, vs: Set[VertexT]) -> "AutomatonLike[VertexT]":
        ...

    @abc.abstractmethod
    def set_starts(self, vs: Set[VertexT]) -> "AutomatonLike[VertexT]":
        ...

    @abc.abstractmethod
    def set_finals(self, vs: Set[VertexT]) -> "AutomatonLike[VertexT]":
        ...

    @abc.abstractmethod
    def get_starts(self) -> Set[VertexT]:
        ...

    @abc.abstractmethod
    def get_finals(self) -> Set[VertexT]:
        ...

    @abc.abstractmethod
    def get_vertices(self) -> Set[VertexT]:
        ...

    @abc.abstractmethod
    def get_edges(self) -> Set[Edge[VertexT]]:
        ...

    @abc.abstractmethod
    def get_labels(self) -> Set["String"]:
        ...

    @abc.abstractmethod
    def get_reachables(self) -> Set[Pair[VertexT, VertexT]]:
        ...

    @abc.abstractmethod
    def intersect(
        self, other: "AutomatonLike[OtherVertexT]"
    ) -> "AutomatonLike[Pair[VertexT, OtherVertexT]]":
        ...

    @abc.abstractmethod
    def concat(self, other: "AutomatonLike[VertexT]") -> "AutomatonLike[VertexT]":
        ...

    @abc.abstractmethod
    def union(self, other: "AutomatonLike[VertexT]") -> "AutomatonLike[VertexT]":
        ...

    @abc.abstractmethod
    def star(self) -> "AutomatonLike[VertexT]":
        ...

    def _assert_compatible_set(self, vs: Set[VertexT]):
        if not isinstance(vs, Set) or self.meta.elem_meta != vs.meta.elem_meta:
            actual_type = vs.meta if isinstance(vs, BaseType) else type(vs)
            raise TypeError(
                f"Expected {self.meta.elem_meta} elements, got {actual_type}"
            )

    def _assert_compatible_automaton_like(self, a: "AutomatonLike[VertexT]"):
        if not isinstance(a, AutomatonLike) or self.meta.elem_meta != a.meta.elem_meta:
            actual_type = a.meta if isinstance(a, BaseType) else type(a)
            raise TypeError(
                f"Expected automaton-like of {self.meta.elem_meta}, got {actual_type}"
            )

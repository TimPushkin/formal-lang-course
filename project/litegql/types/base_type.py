import abc


class BaseType(abc.ABC):
    class Meta(abc.ABC):
        """Used to store the actual "deep" type of an instance."""

        @abc.abstractmethod
        def __repr__(self) -> str:
            ...

        def __eq__(self, other) -> bool | type(NotImplemented):
            # Not using isinstance(other, type(self)) because it may be asymmetrical
            return True if type(other) == type(self) else NotImplemented

        def __hash__(self) -> int:
            return hash(type(self))

    class CollectionMeta(Meta, abc.ABC):
        """
        Used to store the actual "deep" type of an instance.

        It is required for collections to remember the "deep" type of their elements
        including the type of elements' elements (if any) at runtime.

        E.g. it is used to properly compare Set<Set<Int>> and Set<Set<Bool>> -- using
        instanceof is impossible here if any of the sets in question are empty.
        """

        def __init__(self, elem_meta: "BaseType.Meta"):
            if not isinstance(elem_meta, BaseType.Meta):
                raise TypeError("Expected meta-type")
            self._elem_meta = elem_meta

        @property
        def elem_meta(self) -> "BaseType.Meta":
            return self._elem_meta

        @property
        @abc.abstractmethod
        def _str_prefix(self) -> str:
            ...

        def __eq__(self, other) -> bool | type(NotImplemented):
            return (
                self._elem_meta == other._elem_meta
                if isinstance(other, type(self))
                else NotImplemented
            )

        def __hash__(self) -> int:
            return hash(self._elem_meta)

        def __repr__(self) -> str:
            return f"{self._str_prefix}[{self.elem_meta}]"

    @property
    @abc.abstractmethod
    def meta(self) -> Meta:
        ...

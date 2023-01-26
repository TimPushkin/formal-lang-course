from pathlib import Path

import pyformlang.finite_automaton as fa

from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_reg import Reg


class String(Reg[Int]):
    class Meta(BaseType.Meta):
        def __repr__(self) -> str:
            return String.__name__

    def __init__(self, v: str, start_index: int = 0):
        if not isinstance(v, str):
            raise TypeError("Expected str")
        # Not using a DFA not to get behavioral differences with Reg
        nfa = fa.NondeterministicFiniteAutomaton()
        start, final = Int(start_index), Int(start_index + 1)
        # Explicitly converting str to Symbol in case of "epsilon"/"$"
        nfa.add_transition(start, fa.Symbol(v), final)
        nfa.add_start_state(start)
        nfa.add_final_state(final)
        super().__init__(nfa)

    @classmethod
    def from_file(cls, path: Path) -> Reg[Int]:
        with open(path, "r") as f:
            s = f.read()
        return cls(s)

    @classmethod
    def from_raw_str(cls, raw_str: str, start_index: int = 0) -> "String":
        return cls(raw_str, start_index)

    @classmethod
    def from_dataset(cls, graph_name: str) -> Reg[Int]:
        return Reg.from_dataset(graph_name)

    @property
    def value(self) -> str:
        return next(iter(self._nfa.symbols)).value

    def __eq__(self, other) -> bool | type(NotImplemented):
        return (
            self.value == other.value if isinstance(other, String) else NotImplemented
        )

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return self.value

    # Have to define explicitly to override Reg
    def __str__(self) -> str:
        return self.value

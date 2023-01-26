from pyformlang.cfg import CFG
from pyformlang.cfg import Terminal
from pyformlang.cfg import Variable
from pyformlang.regular_expression import Regex


class Ecfg:
    def __init__(
        self,
        variables: set[Variable],
        terminals: set[Terminal],
        start: Variable,
        productions: dict[Variable, Regex],
    ):
        self.variables = variables
        self.terminals = terminals
        self.start = start
        self.productions = productions

    @classmethod
    def from_cfg(cls, cfg: CFG):
        variables = set(cfg.variables)
        start_symbol = (
            cfg.start_symbol if cfg.start_symbol is not None else Variable("S")
        )
        variables.add(start_symbol)

        # Ensure there is always a start production
        productions: dict[Variable, Regex] = {start_symbol: Regex("")}
        for p in cfg.productions:
            body = Regex(" ".join(o.value for o in p.body) if len(p.body) > 0 else "$")
            if p.head in productions:
                productions[p.head] = productions[p.head].union(body)
            else:
                productions[p.head] = body

        return cls(variables, set(cfg.terminals), start_symbol, productions)

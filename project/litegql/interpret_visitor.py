import logging
from pathlib import Path
from typing import Callable

import project.litegql.pattern_matching as pm
from project.litegql.grammar.LiteGQLParser import LiteGQLParser
from project.litegql.grammar.LiteGQLVisitor import LiteGQLVisitor
from project.litegql.types.automaton_like import AutomatonLike
from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_bool import Bool
from project.litegql.types.lgql_cfg import Cfg
from project.litegql.types.lgql_edge import Edge
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_reg import Reg
from project.litegql.types.lgql_set import Set
from project.litegql.types.lgql_string import String
from project.litegql.types.typing_utils import LgqlT


class InterpretVisitor(LiteGQLVisitor):
    def __init__(self, output: Callable[[str], None] = print):
        self.output = output
        self.log = lambda msg: logging.debug(msg)  # The lambda is required
        self._scopes: list[dict[str, BaseType]] = [{}]
        self._automaton_start_index = 0  # To make automatons with non-repeating states

    def set_var(self, var: str, value: BaseType):
        self.log(f"set_var: scope depth {len(self._scopes)}")
        self._scopes[-1][var] = value

    def get_var(self, var: str) -> BaseType:
        for scope in reversed(self._scopes):
            if var in scope:
                return scope[var]
        self.log(f"get_var: {var} not found in {len(self._scopes)} scopes")
        raise RuntimeError(f"Unknown variable: {var}")

    def add_scope(self, scope: dict[str, BaseType]):
        self._scopes.append(scope)
        self.log(f"add_scope: {len(self._scopes)} scopes")

    def pop_scope(self):
        assert len(self._scopes) > 1  # Cannot pop the global scope
        self._scopes.pop()
        self.log(f"pop_scope: {len(self._scopes)} scopes")

    # statement

    def visitPrint(self, ctx: LiteGQLParser.PrintContext):
        value = self.visit(ctx.expr())
        self.log(f"print: {value}")
        self.output(str(value))

    def visitBind(self, ctx: LiteGQLParser.BindContext):
        var = ctx.ID().getText()
        self.log(f"bind: var {var}")
        value = self.visit(ctx.expr())
        self.log(f"bind: value {value}")
        self.set_var(var, value)

    # expression

    def visitParens(self, ctx: LiteGQLParser.ParensContext) -> BaseType:
        return self.visit(ctx.expr())

    # type

    def visitBool(self, ctx: LiteGQLParser.BoolContext) -> Bool:
        text = ctx.BOOL().getText()
        self.log(f"bool: {text}")
        return Bool(text == "true")

    def visitInt(self, ctx: LiteGQLParser.IntContext) -> Int:
        text = ctx.INT().getText()
        self.log(f"int: {text}")
        return Int(int(text))

    def visitString(self, ctx: LiteGQLParser.StringContext) -> String:
        text = ctx.STR().getText()
        self.log(f"string: {text}")
        s = String(text[1:-1], self._automaton_start_index)
        self._automaton_start_index += len(s.get_vertices().value)
        return s

    def visitSet(self, ctx: LiteGQLParser.SetContext) -> Set:
        vs: set[BaseType] = set()
        n = ctx.getChildCount()
        self.log(f"set: child count {n}")
        for elem_ctx in ctx.expr():
            v = self.visit(elem_ctx)
            vs.add(v)
        self.log(f"set: elems count {len(vs)}")
        return Set(vs, Int.Meta())

    def visitReg(self, ctx: LiteGQLParser.RegContext) -> Reg[Int]:
        text = ctx.REG().getText()
        self.log(f"reg: {text}")
        r = Reg.from_raw_str(text[2:-1], start_index=self._automaton_start_index)
        self._automaton_start_index += len(r.get_vertices().value)
        return r

    def visitCfg(self, ctx: LiteGQLParser.CfgContext) -> Cfg[Int]:
        text = ctx.CFG().getText()
        self.log(f"cfg: {text}")
        c = Cfg.from_raw_str(text[2:-1], start_index=self._automaton_start_index)
        self._automaton_start_index += len(c.get_vertices().value)
        return c

    def visitPair(self, ctx: LiteGQLParser.PairContext) -> Pair:
        fst = self.visit(ctx.expr(0))
        snd = self.visit(ctx.expr(1))
        self.log(f"pair: ({fst}, {snd})")
        return Pair(fst, snd)

    def visitEdge(self, ctx: LiteGQLParser.EdgeContext) -> Edge:
        st = self.visit(ctx.expr(0))
        lab = self.visit(ctx.expr(1))
        fn = self.visit(ctx.expr(2))
        self.log(f"edge: ({st}, {lab}, {fn})")
        return Edge(st, lab, fn)

    # variable

    def visitVar(self, ctx: LiteGQLParser.VarContext) -> BaseType:
        var = ctx.ID().getText()
        self.log(f"var: {var}")
        return self.get_var(var)

    # set operations

    def visitContains(self, ctx: LiteGQLParser.ContainsContext) -> Bool:
        item = self.visit(ctx.expr(0))
        elems = self.visit(ctx.expr(1))
        self.log(f"contains: {item} in {elems}")

        if not isinstance(elems, Set):
            raise TypeError(f"Can only check for Set inclusion, got {elems.meta}")

        return elems.contains(item)

    def visitMap(self, ctx: LiteGQLParser.MapContext) -> Set:
        pat, action = self.visit(ctx.lambda_())
        elems = self.visit(ctx.expr())
        self.log(f"map: meta {elems.meta}")

        if not isinstance(elems, Set):
            raise TypeError(
                f"map expects a Set as its second argument, got {elems.meta}"
            )

        self.log(f"map: elems size {len(elems.value)}")

        mapped: set[BaseType] = set()
        for elem in elems.value:
            self.add_scope(pm.match(pat, elem))
            mapped.add(action())
            self.pop_scope()
        self.log(f"map: mapped size {len(mapped)}")

        return Set(mapped)  # Will get Set[Int] if mapped is empty

    def visitFilter(self, ctx: LiteGQLParser.FilterContext) -> Set:
        pat, action = self.visit(ctx.lambda_())
        elems: Set[LgqlT] = self.visit(ctx.expr())
        self.log(f"filter: elems meta {elems.meta}")

        if not isinstance(elems, Set):
            raise TypeError(
                f"filter expects a Set as its second argument, got {elems.meta}"
            )

        self.log(f"filter: elems size {len(elems.value)}")

        filtered: set[LgqlT] = set()
        for elem in elems.value:
            self.add_scope(pm.match(pat, elem))
            res = action()
            if not isinstance(res, Bool):
                raise TypeError(f"filter expects lambda to return Bool, got {res.meta}")
            if res.value:
                filtered.add(elem)
            self.pop_scope()
        self.log(f"map: mapped size {len(filtered)}")

        return Set(filtered, elems.meta.elem_meta)

    # lambda

    def visitLambda(
        self, ctx: LiteGQLParser.LambdaContext
    ) -> tuple[pm.Pattern, Callable[[], BaseType]]:
        pat = self.visit(ctx.pattern())
        self.log(f"lambda: pattern {pat}")

        # Not sure if it is a good idea to capture a parsing context
        def action():
            value = self.visit(ctx.expr())
            self.log(f"lambda: value {value}")
            return value

        return pat, action

    # pattern

    def visitWildcard(self, ctx: LiteGQLParser.WildcardContext) -> pm.Wildcard:
        return pm.Wildcard()

    def visitName(self, ctx: LiteGQLParser.NameContext) -> pm.Name:
        return pm.Name(ctx.ID().getText())

    def visitUnpair(self, ctx: LiteGQLParser.UnpairContext) -> pm.Unpair:
        fst = self.visit(ctx.pattern(0))
        snd = self.visit(ctx.pattern(1))
        return pm.Unpair(fst, snd)

    def visitUnedge(self, ctx: LiteGQLParser.UnedgeContext) -> pm.Unedge:
        st = self.visit(ctx.pattern(0))
        lab = self.visit(ctx.pattern(1))
        fn = self.visit(ctx.pattern(2))
        return pm.Unedge(st, lab, fn)

    # automaton-like operations

    def visitLoad(self, ctx: LiteGQLParser.LoadContext) -> Reg[Int] | Cfg[Int]:
        arg = self.visit(ctx.expr())

        if not isinstance(arg, String):
            raise TypeError(f"visit expects String as its argument, got {arg.meta}")

        path = Path(arg.value)
        if path.is_file():
            self.log(f"load: from file")
            if path.name.startswith("cfg"):
                res = Cfg.from_file(path)
            else:
                res = Reg.from_file(path)
        else:
            self.log(f"load: from dataset")
            try:
                res = Reg.from_dataset(arg.value)
            except FileNotFoundError as e:
                self.log(f"load: {e}")
                raise ValueError(
                    f"Cannot load {arg}: it is neither a file, nor can it be loaded "
                    f"from the graph dataset"
                )

        self.log(f"load: loaded {res.meta}")

        return res

    @staticmethod
    def _assert_automaton_like(method_name: str, arg: BaseType):
        if not isinstance(arg, AutomatonLike):
            raise TypeError(
                f"{method_name} expects String, Reg, or Cfg as its first argument, got "
                f"{arg.meta}"
            )

    def visitAddStarts(self, ctx: LiteGQLParser.AddStartsContext) -> Reg | Cfg:
        arg1 = self.visit(ctx.expr(0))
        self._assert_automaton_like("add_starts", arg1)
        arg2 = self.visit(ctx.expr(1))
        return arg1.add_starts(arg2)

    def visitAddFinals(self, ctx: LiteGQLParser.AddFinalsContext) -> Reg | Cfg:
        arg1 = self.visit(ctx.expr(0))
        self._assert_automaton_like("add_finals", arg1)
        arg2 = self.visit(ctx.expr(1))
        return arg1.add_finals(arg2)

    def visitSetStarts(self, ctx: LiteGQLParser.SetStartsContext) -> Reg | Cfg:
        arg1 = self.visit(ctx.expr(0))
        self._assert_automaton_like("set_starts", arg1)
        arg2 = self.visit(ctx.expr(1))
        return arg1.set_starts(arg2)

    def visitSetFinals(self, ctx: LiteGQLParser.SetFinalsContext) -> Reg | Cfg:
        arg1 = self.visit(ctx.expr(0))
        self._assert_automaton_like("set_finals", arg1)
        arg2 = self.visit(ctx.expr(1))
        return arg1.set_finals(arg2)

    def visitGetStarts(self, ctx: LiteGQLParser.GetStartsContext) -> Set[Int | Pair]:
        arg = self.visit(ctx.expr())
        self._assert_automaton_like("get_starts", arg)
        return arg.get_starts()

    def visitGetFinals(self, ctx: LiteGQLParser.GetFinalsContext) -> Set[Int | Pair]:
        arg = self.visit(ctx.expr())
        self._assert_automaton_like("get_finals", arg)
        return arg.get_finals()

    def visitGetVertices(
        self, ctx: LiteGQLParser.GetVerticesContext
    ) -> Set[Int | Pair]:
        arg = self.visit(ctx.expr())
        self._assert_automaton_like("get_vertices", arg)
        return arg.get_vertices()

    def visitGetEdges(self, ctx: LiteGQLParser.GetEdgesContext) -> Set[Edge]:
        arg = self.visit(ctx.expr())
        self._assert_automaton_like("get_edges", arg)
        return arg.get_edges()

    def visitGetLabels(self, ctx: LiteGQLParser.GetLabelsContext) -> Set[String]:
        arg = self.visit(ctx.expr())
        self._assert_automaton_like("get_labels", arg)
        return arg.get_labels()

    def visitGetReachables(self, ctx: LiteGQLParser.GetReachablesContext) -> Set[Pair]:
        arg = self.visit(ctx.expr())
        self._assert_automaton_like("get_reachables", arg)
        return arg.get_reachables()

    def visitIntersect(
        self, ctx: LiteGQLParser.IntersectContext
    ) -> Reg[Pair] | Cfg[Pair]:
        arg1 = self.visit(ctx.expr(0))
        self._assert_automaton_like("intersect", arg1)
        arg2 = self.visit(ctx.expr(1))
        self._assert_automaton_like("intersect", arg2)
        return arg1.intersect(arg2)

    def visitConcat(self, ctx: LiteGQLParser.ConcatContext) -> Reg | Cfg:
        arg1 = self.visit(ctx.expr(0))
        self._assert_automaton_like("concat", arg1)
        arg2 = self.visit(ctx.expr(1))
        self._assert_automaton_like("concat", arg2)
        return arg1.concat(arg2)

    def visitUnion(self, ctx: LiteGQLParser.UnionContext) -> Reg | Cfg:
        arg1 = self.visit(ctx.expr(0))
        self._assert_automaton_like("union", arg1)
        arg2 = self.visit(ctx.expr(1))
        self._assert_automaton_like("union", arg2)
        return arg1.union(arg2)

    def visitStar(self, ctx: LiteGQLParser.StarContext) -> Reg | Cfg:
        arg = self.visit(ctx.expr())
        self._assert_automaton_like("star", arg)
        return arg.star()

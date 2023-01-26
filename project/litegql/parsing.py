from pathlib import Path

import antlr4
import pydot

from project.litegql.grammar.LiteGQLLexer import LiteGQLLexer
from project.litegql.grammar.LiteGQLListener import LiteGQLListener
from project.litegql.grammar.LiteGQLParser import LiteGQLParser


def get_parser(inp: str) -> LiteGQLParser:
    chars = antlr4.InputStream(inp)
    lexer = LiteGQLLexer(chars)
    tokens = antlr4.CommonTokenStream(lexer)
    return LiteGQLParser(tokens)


def check(inp: str) -> bool:
    parser = get_parser(inp)
    parser.removeErrorListeners()
    parser.prog()
    return parser.getNumberOfSyntaxErrors() == 0


def save_parse_tree_as_dot(inp: str, path: Path | str):
    parser = get_parser(inp)
    tree = parser.prog()
    if parser.getNumberOfSyntaxErrors() > 0:
        raise ValueError("Parsing failed")
    builder = _DotTreeBuilder()
    walker = antlr4.ParseTreeWalker()
    walker.walk(builder, tree)
    if not builder.dot.write(str(path)):
        raise RuntimeError(f"Cannot save dot grammar to {path}")


class _DotTreeBuilder(LiteGQLListener):
    def __init__(self):
        self.dot = pydot.Dot("parse_tree", strict=True)
        self._curr_id = 0
        self._id_stack = []

    def enterEveryRule(self, ctx: antlr4.ParserRuleContext):
        self.dot.add_node(
            pydot.Node(self._curr_id, label=LiteGQLParser.ruleNames[ctx.getRuleIndex()])
        )
        if len(self._id_stack) > 0:
            self.dot.add_edge(pydot.Edge(self._id_stack[-1], self._curr_id))
        self._id_stack.append(self._curr_id)
        self._curr_id += 1

    def exitEveryRule(self, ctx: antlr4.ParserRuleContext):
        self._id_stack.pop()

    def visitTerminal(self, node: antlr4.TerminalNode):
        self.dot.add_node(pydot.Node(self._curr_id, label=f"'{node}'", shape="box"))
        self.dot.add_edge(pydot.Edge(self._id_stack[-1], self._curr_id))
        self._curr_id += 1

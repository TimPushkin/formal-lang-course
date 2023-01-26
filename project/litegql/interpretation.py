from typing import Callable

from project.litegql.interpret_visitor import InterpretVisitor
from project.litegql.parsing import get_parser


def interpret(code: str, output: Callable[[str], None] = print):
    parser = get_parser(code)
    tree = parser.prog()
    if parser.getNumberOfSyntaxErrors() > 0:
        raise ValueError("Parsing failed")
    visitor = InterpretVisitor(output)
    visitor.visit(tree)

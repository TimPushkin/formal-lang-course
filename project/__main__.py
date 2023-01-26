import logging
from argparse import ArgumentParser
from pathlib import Path

from project.litegql.interpretation import interpret

logging.disable(logging.CRITICAL)  # Disable CFPQ_Data logs

parser = ArgumentParser()
parser.add_argument("code_path", type=Path)
args = parser.parse_args()

with open(args.code_path, "r") as f:
    code = f.read()

try:
    interpret(code)
except RuntimeError as e:
    exit(e)

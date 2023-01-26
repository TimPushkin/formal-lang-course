import inspect
from pathlib import Path

import pytest

from project.litegql.interpretation import interpret

SCRIPTS_DIR = Path(inspect.stack()[0].filename).parent / "scripts"


@pytest.fixture(name="code")
def get_code(request) -> str:
    with open(request.param, "r") as f:
        text = f.read()
    return text


@pytest.fixture
def open_scripts_dir(monkeypatch):
    monkeypatch.chdir(SCRIPTS_DIR)


@pytest.mark.parametrize(
    "code",
    sorted(SCRIPTS_DIR.glob("*.lgql")),
    indirect=["code"],
    ids=[p.name for p in sorted(SCRIPTS_DIR.glob("*.lgql"))],
)
def test_interpret(code: str, open_scripts_dir):
    interpret(code)

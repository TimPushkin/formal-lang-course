from pathlib import Path

import pytest
from pyformlang import cfg as c

from project.cfpq import cfg_utils
from tests.testing_utils import content_file_path  # noqa
from tests.testing_utils import load_test_data
from tests.testing_utils import load_test_ids


def _assert_equal_cfgs(cfg1: c.CFG, cfg2: c.CFG):
    assert cfg1.start_symbol == cfg2.start_symbol
    assert cfg1.productions == cfg2.productions


@pytest.mark.parametrize(
    "content_file_path, start, expected",
    load_test_data(
        "test_cfg_utils",
        lambda d: (
            d["cfg_text"],
            d["start"],
            c.CFG.from_text(
                d["cfg_text"],
                c.Variable(d["start"]),
            )
            if d["start"] is not None
            else c.CFG.from_text(d["cfg_text"]),
        ),
    ),
    indirect=["content_file_path"],
    ids=load_test_ids("test_cfg_utils"),
)
def test_read_cfg(content_file_path: Path, start: str, expected: c.CFG):
    actual = (
        cfg_utils.read_cfg(content_file_path, start)
        if start is not None
        else cfg_utils.read_cfg(content_file_path)
    )

    _assert_equal_cfgs(actual, expected)


@pytest.mark.parametrize(
    "raw_cfg, start, expected",
    load_test_data(
        "test_cfg_utils",
        lambda d: (
            d["cfg_text"],
            d["start"],
            c.CFG.from_text(
                d["expected_wcnf"],
                c.Variable(d["start"]),
            )
            if d["start"] is not None
            else c.CFG.from_text(d["expected_wcnf"]),
        ),
    ),
    ids=load_test_ids("test_cfg_utils"),
)
def test_cfg_to_wcnf(raw_cfg: str, start: str, expected: c.CFG):
    actual = (
        cfg_utils.cfg_to_wcnf(raw_cfg, start)
        if start is not None
        else cfg_utils.cfg_to_wcnf(raw_cfg)
    )

    _assert_equal_cfgs(actual, expected)


@pytest.mark.parametrize(
    "cfg, word, expected",
    load_test_data(
        "test_accepts",
        lambda d: [
            (
                c.CFG.from_text(d["cfg"]),
                inp["word"],
                inp["expected"],
            )
            for inp in d["inputs"]
        ],
        is_aggregated=True,
    ),
    ids=load_test_ids("test_accepts", get_repeats=lambda d: len(d["inputs"])),
)
def test_accepts(cfg: c.CFG, word: str, expected: bool):
    actual = cfg_utils.accepts(cfg, word)

    assert actual == expected

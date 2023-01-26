from pathlib import Path

import pytest

from project.litegql.grammar.LiteGQLParser import LiteGQLParser
from project.litegql.interpret_visitor import InterpretVisitor
from project.litegql.parsing import get_parser
from project.litegql.types.lgql_cfg import Cfg
from project.litegql.types.lgql_edge import Edge
from project.litegql.types.lgql_int import Int
from project.litegql.types.lgql_pair import Pair
from project.litegql.types.lgql_reg import Reg
from project.litegql.types.lgql_set import Set
from project.litegql.types.lgql_string import String
from tests.test_types_cfg import assert_equivalent_boxes
from tests.testing_utils import are_equivalent
from tests.testing_utils import content_file_path  # noqa
from tests.testing_utils import expr_ctx  # noqa
from tests.testing_utils import fail
from tests.testing_utils import load_test_data
from tests.testing_utils import load_test_ids


@pytest.mark.parametrize(
    "content_file_path",
    load_test_data(
        "test_reg_from_file", lambda d: d["dot_text"], data_filename="test_types_reg"
    ),
    indirect=["content_file_path"],
    ids=load_test_ids("test_reg_from_file", data_filename="test_types_reg"),
)
def test_visit_load_from_file_reg(content_file_path: Path):
    expected = Reg.from_file(content_file_path)

    actual = InterpretVisitor(output=fail).visitLoad(
        get_parser(f'load("{content_file_path}")').expr()
    )

    assert are_equivalent(actual._nfa, expected._nfa)


@pytest.fixture
def cfg_file_path(request, tmp_path: Path) -> Path:
    path = tmp_path / "cfg.dot"
    with open(path, "w") as f:
        f.write(request.param)
    return path


@pytest.mark.parametrize(
    "cfg_file_path",
    load_test_data(
        "test_cfg_from_file", lambda d: d["dot_text"], data_filename="test_types_cfg"
    ),
    indirect=["cfg_file_path"],
    ids=load_test_ids("test_cfg_from_file", data_filename="test_types_cfg"),
)
def test_visit_load_from_file_cfg(cfg_file_path: Path):
    expected = Cfg.from_file(cfg_file_path)

    actual = InterpretVisitor(output=fail).visitLoad(
        get_parser(f'load("{cfg_file_path}")').expr()
    )

    assert actual._rsm.start == expected._rsm.start
    assert_equivalent_boxes(
        actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
    )


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('load("skos")', Reg.from_dataset("skos")),
        ('load("ls")', Reg.from_dataset("ls")),
    ],
    indirect=["ctx"],
)
def test_visit_load_from_dataset(ctx: LiteGQLParser.LoadContext, expected: Reg[Int]):
    actual = InterpretVisitor(output=fail).visitLoad(ctx)
    assert are_equivalent(actual._nfa, expected._nfa)


@pytest.mark.parametrize(
    "ctx",
    ['load("non-existent-file-12345678")', 'load("cfg-non-existent-file-12345678")'],
    indirect=["ctx"],
)
def test_visit_load_incorrect(ctx: LiteGQLParser.LoadContext):
    with pytest.raises(ValueError):
        InterpretVisitor(output=fail).visitLoad(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('add_starts(r"a b c", {})', Reg.from_raw_str("a b c").add_starts(Set())),
        (
            'add_starts("some str", {-1, 999})',
            String("some str").add_starts(Set({Int(-1), Int(999)})),
        ),
        (
            'add_starts(r"a b c", {-1, 999})',
            Reg.from_raw_str("a b c").add_starts(Set({Int(-1), Int(999)})),
        ),
        (
            'add_starts(c"S -> a S b | epsilon", {0, 10})',
            Cfg.from_raw_str("S -> a S b | epsilon").add_starts(Set({Int(0), Int(10)})),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_add_starts(ctx: LiteGQLParser.AddStartsContext, expected: Reg | Cfg):
    actual = InterpretVisitor(output=fail).visitAddStarts(ctx)
    assert isinstance(actual, (Reg, Cfg))
    if isinstance(actual, Reg):
        assert are_equivalent(actual._nfa, expected._nfa)
    else:
        assert actual._rsm.start == expected._rsm.start
        assert_equivalent_boxes(
            actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
        )


@pytest.mark.parametrize(
    "ctx",
    ["add_starts(1, {-1, 999})", 'add_starts(r"a b c", 0)'],
    indirect=["ctx"],
)
def test_visit_add_starts_incorrect(ctx: LiteGQLParser.AddStartsContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitAddStarts(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('add_finals(r"a b c", {})', Reg.from_raw_str("a b c").add_finals(Set())),
        (
            'add_finals("some str", {-1, 999})',
            String("some str").add_finals(Set({Int(-1), Int(999)})),
        ),
        (
            'add_finals(r"a b c", {-1, 999})',
            Reg.from_raw_str("a b c").add_finals(Set({Int(-1), Int(999)})),
        ),
        (
            'add_finals(c"S -> a S b | epsilon", {0, 10})',
            Cfg.from_raw_str("S -> a S b | epsilon").add_finals(Set({Int(0), Int(10)})),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_add_finals(ctx: LiteGQLParser.AddFinalsContext, expected: Reg | Cfg):
    actual = InterpretVisitor(output=fail).visitAddFinals(ctx)
    assert isinstance(actual, (Reg, Cfg))
    if isinstance(actual, Reg):
        assert are_equivalent(actual._nfa, expected._nfa)
    else:
        assert actual._rsm.start == expected._rsm.start
        assert_equivalent_boxes(
            actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
        )


@pytest.mark.parametrize(
    "ctx",
    ["add_finals(1, {-1, 999})", 'add_finals(r"a b c", 0)'],
    indirect=["ctx"],
)
def test_visit_add_finals_incorrect(ctx: LiteGQLParser.AddFinalsContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitAddStarts(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('set_starts(r"a b c", {})', Reg.from_raw_str("a b c").set_starts(Set())),
        (
            'set_starts("some str", {-1, 999})',
            String("some str").set_starts(Set({Int(-1), Int(999)})),
        ),
        (
            'set_starts(r"a b c", {-1, 999})',
            Reg.from_raw_str("a b c").set_starts(Set({Int(-1), Int(999)})),
        ),
        (
            'set_starts(c"S -> a S b | epsilon", {0, 10})',
            Cfg.from_raw_str("S -> a S b | epsilon").set_starts(Set({Int(0), Int(10)})),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_set_starts(ctx: LiteGQLParser.SetStartsContext, expected: Reg | Cfg):
    actual = InterpretVisitor(output=fail).visitSetStarts(ctx)
    assert isinstance(actual, (Reg, Cfg))
    if isinstance(actual, Reg):
        assert are_equivalent(actual._nfa, expected._nfa)
    else:
        assert actual._rsm.start == expected._rsm.start
        assert_equivalent_boxes(
            actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
        )


@pytest.mark.parametrize(
    "ctx",
    ["set_starts(1, {-1, 999})", 'set_starts(r"a b c", 0)'],
    indirect=["ctx"],
)
def test_visit_set_starts_incorrect(ctx: LiteGQLParser.SetStartsContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitSetStarts(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('set_finals(r"a b c", {})', Reg.from_raw_str("a b c").set_finals(Set())),
        (
            'set_finals("some str", {-1, 999})',
            String("some str").set_finals(Set({Int(-1), Int(999)})),
        ),
        (
            'set_finals(r"a b c", {-1, 999})',
            Reg.from_raw_str("a b c").set_finals(Set({Int(-1), Int(999)})),
        ),
        (
            'set_finals(c"S -> a S b | epsilon", {0, 10})',
            Cfg.from_raw_str("S -> a S b | epsilon").set_finals(Set({Int(0), Int(10)})),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_set_finals(ctx: LiteGQLParser.SetFinalsContext, expected: Reg | Cfg):
    actual = InterpretVisitor(output=fail).visitSetFinals(ctx)
    assert isinstance(actual, (Reg, Cfg))
    if isinstance(actual, Reg):
        assert are_equivalent(actual._nfa, expected._nfa)
    else:
        assert actual._rsm.start == expected._rsm.start
        assert_equivalent_boxes(
            actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
        )


@pytest.mark.parametrize(
    "ctx",
    ["set_finals(1, {-1, 999})", 'set_finals(r"a b c", 0)'],
    indirect=["ctx"],
)
def test_visit_set_finals_incorrect(ctx: LiteGQLParser.SetFinalsContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitSetStarts(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('get_starts("some str")', String("some str").get_starts()),
        ('get_starts(r"a b c")', Reg.from_raw_str("a b c").get_starts()),
        (
            'get_starts(c"S -> a S b | epsilon")',
            Cfg.from_raw_str("S -> a S b | epsilon").get_starts(),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_get_starts(
    ctx: LiteGQLParser.GetStartsContext, expected: Set[Int | Pair]
):
    actual = InterpretVisitor(output=fail).visitGetStarts(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx",
    ["get_starts(1)", "get_starts(false)", "get_starts({-1, 999})"],
    indirect=["ctx"],
)
def test_visit_get_starts_incorrect(ctx: LiteGQLParser.GetStartsContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitGetStarts(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('get_starts("some str")', String("some str").get_finals()),
        ('get_finals(r"a b c")', Reg.from_raw_str("a b c").get_finals()),
        (
            'get_finals(c"S -> a S b | epsilon")',
            Cfg.from_raw_str("S -> a S b | epsilon").get_finals(),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_get_finals(
    ctx: LiteGQLParser.GetFinalsContext, expected: Set[Int | Pair]
):
    actual = InterpretVisitor(output=fail).visitGetFinals(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx",
    ["get_finals(1)", "get_finals(false)", "get_finals({-1, 999})"],
    indirect=["ctx"],
)
def test_visit_get_finals_incorrect(ctx: LiteGQLParser.GetFinalsContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitGetFinals(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('get_vertices("some str")', String("some str").get_vertices()),
        ('get_vertices(r"a b c")', Reg.from_raw_str("a b c").get_vertices()),
        (
            'get_vertices(c"S -> a S b | epsilon")',
            Cfg.from_raw_str("S -> a S b | epsilon").get_vertices(),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_get_vertices(
    ctx: LiteGQLParser.GetVerticesContext, expected: Set[Int | Pair]
):
    actual = InterpretVisitor(output=fail).visitGetVertices(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx",
    ["get_vertices(1)", "get_vertices(false)", "get_vertices({-1, 999})"],
    indirect=["ctx"],
)
def test_visit_get_vertices_incorrect(ctx: LiteGQLParser.GetVerticesContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitGetVertices(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('get_edges("some str")', String("some str").get_edges()),
        ('get_edges(r"a b c")', Reg.from_raw_str("a b c").get_edges()),
        (
            'get_edges(c"S -> a S b | epsilon")',
            Cfg.from_raw_str("S -> a S b | epsilon").get_edges(),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_get_edges(ctx: LiteGQLParser.GetVerticesContext, expected: Set[Edge]):
    actual = InterpretVisitor(output=fail).visitGetEdges(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx",
    ["get_edges(1)", "get_edges(false)", "get_edges({-1, 999})"],
    indirect=["ctx"],
)
def test_visit_get_edges_incorrect(ctx: LiteGQLParser.GetEdgesContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitGetEdges(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('get_labels("some str")', String("some str").get_labels()),
        ('get_labels(r"a b c")', Reg.from_raw_str("a b c").get_labels()),
        (
            'get_labels(c"S -> a S b | epsilon")',
            Cfg.from_raw_str("S -> a S b | epsilon").get_labels(),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_get_labels(ctx: LiteGQLParser.GetLabelsContext, expected: Set[String]):
    actual = InterpretVisitor(output=fail).visitGetLabels(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx",
    ["get_labels(1)", "get_labels(false)", "get_labels({-1, 999})"],
    indirect=["ctx"],
)
def test_visit_get_labels_incorrect(ctx: LiteGQLParser.GetLabelsContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitGetLabels(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('get_reachables("some str")', String("some str").get_reachables()),
        ('get_reachables(r"a b c")', Reg.from_raw_str("a b c").get_reachables()),
        (
            'get_reachables(c"S -> a S b | epsilon")',
            Cfg.from_raw_str("S -> a S b | epsilon").get_reachables(),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_get_reachables(
    ctx: LiteGQLParser.GetReachablesContext, expected: Set[Pair]
):
    actual = InterpretVisitor(output=fail).visitGetReachables(ctx)
    assert actual == expected


@pytest.mark.parametrize(
    "ctx",
    ["get_reachables(1)", "get_reachables(false)", "get_reachables({-1, 999})"],
    indirect=["ctx"],
)
def test_visit_get_reachables_incorrect(ctx: LiteGQLParser.GetReachablesContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitGetReachables(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('"a" & "a"', String("a").intersect(String("a", start_index=2))),
        ('"a" & r"a*"', String("a").intersect(Reg.from_raw_str("a*", start_index=2))),
        (
            '"a" & c"S -> a"',
            String("a").intersect(Cfg.from_raw_str("S -> a", start_index=2)),
        ),
        ('r"a b c" & "a"', Reg.from_raw_str("a b c").intersect(String("a"))),
        (
            'r"a b c" & r"a*"',
            Reg.from_raw_str("a b c").intersect(Reg.from_raw_str("a*", start_index=4)),
        ),
        (
            'r"a b c" & c"S -> a"',
            Reg.from_raw_str("a b c").intersect(
                Cfg.from_raw_str("S -> a", start_index=4)
            ),
        ),
        (
            'c"S -> a S b | $" & "ab"',
            Cfg.from_raw_str("S -> a S b | $").intersect(
                String("ab", start_index=-100)
            ),
        ),
        (
            'c"S -> a S b | $" & r"a* b*"',
            Cfg.from_raw_str("S -> a S b | $").intersect(
                Reg.from_raw_str("a* b*", start_index=-100)
            ),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_intersect(ctx: LiteGQLParser.IntersectContext, expected: Reg | Cfg):
    actual = InterpretVisitor(output=fail).visitIntersect(ctx)
    assert isinstance(actual, (Reg, Cfg))
    if isinstance(actual, Reg):
        assert are_equivalent(actual._nfa, expected._nfa)
    else:
        assert actual._rsm.start == expected._rsm.start
        assert_equivalent_boxes(
            actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
        )


@pytest.mark.parametrize(
    "ctx",
    [
        "1 & 2",
        "true & false",
        "{1, 2} & {3, 4}",
        'c"S -> a S b | $" & c"S -> a S b S | $"',
    ],
    indirect=["ctx"],
)
def test_visit_intersect_incorrect(ctx: LiteGQLParser.IntersectContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitIntersect(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('"a" . "a"', String("a").concat(String("a", start_index=2))),
        ('"a" . r"a*"', String("a").concat(Reg.from_raw_str("a*", start_index=2))),
        (
            '"a" . c"S -> a"',
            String("a").concat(Cfg.from_raw_str("S -> a", start_index=2)),
        ),
        (
            'r"a b c" . "a"',
            Reg.from_raw_str("a b c").concat(String("a", start_index=6)),
        ),
        (
            'r"a b c" . r"a*"',
            Reg.from_raw_str("a b c").concat(Reg.from_raw_str("a*", start_index=6)),
        ),
        (
            'r"a b c" . c"S -> a"',
            Reg.from_raw_str("a b c").concat(Cfg.from_raw_str("S -> a", start_index=6)),
        ),
        (
            'c"S -> a S b | $" . "ab"',
            Cfg.from_raw_str("S -> a S b | $").concat(String("ab", start_index=-100)),
        ),
        (
            'c"S -> a S b | $" . r"a* b*"',
            Cfg.from_raw_str("S -> a S b | $").concat(
                Reg.from_raw_str("a* b*", start_index=-100)
            ),
        ),
        (
            'c"S -> a S b | $" . c"S -> a S b S | $"',
            Cfg.from_raw_str("S -> a S b | $").concat(
                Cfg.from_raw_str("S -> a S b S | $", start_index=-100)
            ),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_concat(ctx: LiteGQLParser.ConcatContext, expected: Reg | Cfg):
    actual = InterpretVisitor(output=fail).visitConcat(ctx)
    assert isinstance(actual, (Reg, Cfg))
    if isinstance(actual, Reg):
        assert are_equivalent(actual._nfa, expected._nfa)
    else:
        assert actual._rsm.start == expected._rsm.start
        assert_equivalent_boxes(
            actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
        )


@pytest.mark.parametrize(
    "ctx",
    ["1 . 2", "true . false", "{1, 2} . {3, 4}"],
    indirect=["ctx"],
)
def test_visit_concat_incorrect(ctx: LiteGQLParser.ConcatContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitConcat(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('"a" | "a"', String("a").union(String("a", start_index=2))),
        ('"a" | r"a*"', String("a").union(Reg.from_raw_str("a*", start_index=2))),
        (
            '"a" | c"S -> a"',
            String("a").union(Cfg.from_raw_str("S -> a", start_index=2)),
        ),
        ('r"a b c" | "a"', Reg.from_raw_str("a b c").union(String("a", start_index=6))),
        (
            'r"a b c" | r"a*"',
            Reg.from_raw_str("a b c").union(Reg.from_raw_str("a*", start_index=6)),
        ),
        (
            'r"a b c" | c"S -> a"',
            Reg.from_raw_str("a b c").union(Cfg.from_raw_str("S -> a", start_index=6)),
        ),
        (
            'c"S -> a S b | $" | "ab"',
            Cfg.from_raw_str("S -> a S b | $").union(String("ab", start_index=-100)),
        ),
        (
            'c"S -> a S b | $" | r"a* b*"',
            Cfg.from_raw_str("S -> a S b | $").union(
                Reg.from_raw_str("a* b*", start_index=-100)
            ),
        ),
        (
            'c"S -> a S b | $" | c"S -> a S b S | $"',
            Cfg.from_raw_str("S -> a S b | $").union(
                Cfg.from_raw_str("S -> a S b S | $", start_index=-100)
            ),
        ),
    ],
    indirect=["ctx"],
)
def test_visit_union(ctx: LiteGQLParser.UnionContext, expected: Reg | Cfg):
    actual = InterpretVisitor(output=fail).visitUnion(ctx)
    assert isinstance(actual, (Reg, Cfg))
    if isinstance(actual, Reg):
        assert are_equivalent(actual._nfa, expected._nfa)
    else:
        assert actual._rsm.start == expected._rsm.start
        assert_equivalent_boxes(
            actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
        )


@pytest.mark.parametrize(
    "ctx",
    ["1 | 2", "true | false", "{1, 2} | {3, 4}"],
    indirect=["ctx"],
)
def test_visit_union_incorrect(ctx: LiteGQLParser.UnionContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitUnion(ctx)


@pytest.mark.parametrize(
    "ctx, expected",
    [
        ('"a"* ', String("a").star()),
        ('r"a b c"*', Reg.from_raw_str("a b c").star()),
        ('c"S -> a S b | $"*', Cfg.from_raw_str("S -> a S b | $").star()),
    ],
    indirect=["ctx"],
)
def test_visit_star(ctx: LiteGQLParser.StarContext, expected: Reg | Cfg):
    actual = InterpretVisitor(output=fail).visitStar(ctx)
    assert isinstance(actual, (Reg, Cfg))
    if isinstance(actual, Reg):
        assert are_equivalent(actual._nfa, expected._nfa)
    else:
        assert actual._rsm.start == expected._rsm.start
        assert_equivalent_boxes(
            actual._rsm.boxes, expected._rsm.boxes, wrapped_expected=True
        )


@pytest.mark.parametrize("ctx", ["1*", "true*", "{1, 2}*"], indirect=["ctx"])
def test_visit_star_incorrect(ctx: LiteGQLParser.StarContext):
    with pytest.raises(TypeError):
        InterpretVisitor(output=fail).visitStar(ctx)

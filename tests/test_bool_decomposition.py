import pytest
from pyformlang import cfg as c
from pyformlang import finite_automaton as fa
from scipy.sparse import csr_array

from project.cfpq.rsm import Rsm
from project.utils.bool_decomposition import BoolDecomposition
from tests.testing_utils import dot_str_to_nfa
from tests.testing_utils import load_test_data
from tests.testing_utils import load_test_ids


def _dict_to_nfa_state_info(d: dict) -> BoolDecomposition.StateInfo:
    return BoolDecomposition.StateInfo(d["data"], d["is_start"], d["is_final"])


def _dict_to_rsm_state_info(d: dict) -> BoolDecomposition.StateInfo:
    var, val = d["data"]
    return BoolDecomposition.StateInfo(
        (c.Variable(var), val), d["is_start"], d["is_final"]
    )


def _dict_to_adjs(d: dict[str, list[list[int]]]) -> dict[str, csr_array]:
    return {s: csr_array(l) for s, l in d.items()}


def _check_adjs_are_equal(adjs1: dict[str, csr_array], adjs2: dict[str, csr_array]):
    for (symbol1, adj1), (symbol2, adj2) in zip(
        sorted(adjs1.items()), sorted(adjs2.items())
    ):
        assert symbol1 == symbol2
        assert (adj1 - adj2).nnz == 0


class TestFromNfa:
    @pytest.mark.parametrize(
        "nfa, expected_states",
        load_test_data(
            "TestFromNfa",
            lambda d: (
                dot_str_to_nfa(d["graph"]),
                [_dict_to_nfa_state_info(st) for st in d["expected_states"]],
            ),
            add_filename_suffix=True,
        ),
        ids=load_test_ids("TestFromNfa", add_filename_suffix=True),
    )
    def test_states_are_correct(
        self, nfa: fa.EpsilonNFA, expected_states: list[BoolDecomposition.StateInfo]
    ):
        decomp = BoolDecomposition.from_nfa(nfa, sort_states=True)

        assert decomp.states == expected_states

    @pytest.mark.parametrize(
        "nfa, expected_adjs",
        load_test_data(
            "TestFromNfa",
            lambda d: (dot_str_to_nfa(d["graph"]), _dict_to_adjs(d["expected_adjs"])),
            add_filename_suffix=True,
        ),
        ids=load_test_ids("TestFromNfa", add_filename_suffix=True),
    )
    def test_adjs_are_correct(
        self, nfa: fa.EpsilonNFA, expected_adjs: dict[str, csr_array]
    ):
        decomp = BoolDecomposition.from_nfa(nfa, sort_states=True)

        _check_adjs_are_equal(decomp.adjs, expected_adjs)


class TestFromRsm:
    @pytest.mark.parametrize(
        "rsm, expected_states",
        load_test_data(
            "TestFromRsm",
            lambda d: (
                Rsm(
                    c.Variable("S"),
                    {
                        c.Variable(var): dot_str_to_nfa(nfa)
                        for var, nfa in d["rsm_boxes"].items()
                    },
                ),
                [_dict_to_rsm_state_info(st) for st in d["expected_states"]],
            ),
            add_filename_suffix=True,
        ),
        ids=load_test_ids("TestFromRsm", add_filename_suffix=True),
    )
    def test_states_are_correct(
        self, rsm: Rsm, expected_states: list[BoolDecomposition.StateInfo]
    ):
        decomp = BoolDecomposition.from_rsm(rsm, sort_states=True)

        assert decomp.states == expected_states

    @pytest.mark.parametrize(
        "rsm, expected_adjs",
        load_test_data(
            "TestFromRsm",
            lambda d: (
                Rsm(
                    c.Variable("S"),
                    {
                        c.Variable(var): dot_str_to_nfa(nfa)
                        for var, nfa in d["rsm_boxes"].items()
                    },
                ),
                _dict_to_adjs(d["expected_adjs"]),
            ),
            add_filename_suffix=True,
        ),
        ids=load_test_ids("TestFromRsm", add_filename_suffix=True),
    )
    def test_adjs_are_correct(self, rsm: Rsm, expected_adjs: dict[str, csr_array]):
        decomp = BoolDecomposition.from_rsm(rsm, sort_states=True)

        _check_adjs_are_equal(decomp.adjs, expected_adjs)


class TestIntersect:
    @pytest.mark.parametrize(
        "states1, adjs1, states2, adjs2, expected_states",
        load_test_data(
            "TestIntersect",
            lambda d: (
                [_dict_to_nfa_state_info(st) for st in d["states1"]],
                _dict_to_adjs(d["adjs1"]),
                [_dict_to_nfa_state_info(st) for st in d["states2"]],
                _dict_to_adjs(d["adjs2"]),
                [
                    BoolDecomposition.StateInfo(
                        tuple(st["data"]), st["is_start"], st["is_final"]
                    )
                    for st in d["expected_states"]
                ],
            ),
            add_filename_suffix=True,
        ),
        ids=load_test_ids("TestIntersect", add_filename_suffix=True),
    )
    def test_states_are_correct(
        self,
        states1: list[BoolDecomposition.StateInfo],
        adjs1: dict[str, csr_array],
        states2: list[BoolDecomposition.StateInfo],
        adjs2: dict[str, csr_array],
        expected_states: list[BoolDecomposition.StateInfo],
    ):
        decomp1 = BoolDecomposition(states1, adjs1)
        decomp2 = BoolDecomposition(states2, adjs2)

        intersection = decomp1.intersect(decomp2)

        assert intersection.states == expected_states

    @pytest.mark.parametrize(
        "states1, adjs1, states2, adjs2, expected_adjs",
        load_test_data(
            "TestIntersect",
            lambda d: (
                [_dict_to_nfa_state_info(st) for st in d["states1"]],
                _dict_to_adjs(d["adjs1"]),
                [_dict_to_nfa_state_info(st) for st in d["states2"]],
                _dict_to_adjs(d["adjs2"]),
                _dict_to_adjs(d["expected_adjs"]),
            ),
            add_filename_suffix=True,
        ),
        ids=load_test_ids("TestIntersect", add_filename_suffix=True),
    )
    def test_adjs_are_correct(
        self,
        states1: list[BoolDecomposition.StateInfo],
        adjs1: dict[str, csr_array],
        states2: list[BoolDecomposition.StateInfo],
        adjs2: dict[str, csr_array],
        expected_adjs: dict[str, csr_array],
    ):
        decomp1 = BoolDecomposition(states1, adjs1)
        decomp2 = BoolDecomposition(states2, adjs2)

        intersection = decomp1.intersect(decomp2)

        _check_adjs_are_equal(intersection.adjs, expected_adjs)


class TestTransitiveClosureAnySymbol:
    @pytest.mark.parametrize(
        "adjs, expected_indices",
        load_test_data(
            "TestTransitiveClosureAnySymbol",
            lambda d: (
                _dict_to_adjs(d["adjs"]),
                {tuple(pair) for pair in d["expected_indices"]},
            ),
            add_filename_suffix=True,
        ),
        ids=load_test_ids("TestTransitiveClosureAnySymbol", add_filename_suffix=True),
    )
    def test_closure_is_correct(
        self, adjs: dict[str, csr_array], expected_indices: set[tuple]
    ):
        states_num = next(iter(adjs.values())).shape[0] if len(adjs) > 0 else 0
        states = [BoolDecomposition.StateInfo(i, True, True) for i in range(states_num)]
        decomp = BoolDecomposition(states, adjs)

        actual_indices = decomp.transitive_closure_any_symbol()

        assert set(zip(*actual_indices)) == expected_indices


class TestConstrainedBfs:
    @pytest.mark.parametrize(
        "main_states, main_adjs, constr_states, constr_adjs, expected",
        load_test_data(
            "TestConstrainedBfs",
            lambda d: (
                [_dict_to_nfa_state_info(st) for st in d["main_states"]],
                _dict_to_adjs(d["main_adjs"]),
                [_dict_to_nfa_state_info(st) for st in d["constr_states"]],
                _dict_to_adjs(d["constr_adjs"]),
                {end for _, end in d["expected"]},
            ),
            add_filename_suffix=True,
        ),
        ids=load_test_ids("TestConstrainedBfs", add_filename_suffix=True),
    )
    def test_not_separated(
        self,
        main_states: list[BoolDecomposition.StateInfo],
        main_adjs: dict[str, csr_array],
        constr_states: list[BoolDecomposition.StateInfo],
        constr_adjs: dict[str, csr_array],
        expected: set[int],
    ):
        main_decomp = BoolDecomposition(main_states, main_adjs)
        constraint_decomp = BoolDecomposition(constr_states, constr_adjs)

        actual = main_decomp.constrained_bfs(constraint_decomp)

        assert actual == expected

    @pytest.mark.parametrize(
        "main_states, main_adjs, constr_states, constr_adjs, expected",
        load_test_data(
            "TestConstrainedBfs",
            lambda d: (
                [_dict_to_nfa_state_info(st) for st in d["main_states"]],
                _dict_to_adjs(d["main_adjs"]),
                [_dict_to_nfa_state_info(st) for st in d["constr_states"]],
                _dict_to_adjs(d["constr_adjs"]),
                {(i, j) for i, j in d["expected"]},
            ),
            add_filename_suffix=True,
        ),
        ids=load_test_ids("TestConstrainedBfs", add_filename_suffix=True),
    )
    def test_separated(
        self,
        main_states: list[BoolDecomposition.StateInfo],
        main_adjs: dict[str, csr_array],
        constr_states: list[BoolDecomposition.StateInfo],
        constr_adjs: dict[str, csr_array],
        expected: set[tuple[int, int]],
    ):
        main_decomp = BoolDecomposition(main_states, main_adjs)
        constraint_decomp = BoolDecomposition(constr_states, constr_adjs)

        actual = main_decomp.constrained_bfs(constraint_decomp, separated=True)

        assert actual == expected

import networkx as nx
import pytest
from pyformlang import finite_automaton as fa

from project.rpq import fa_utils
from project.utils import graph_utils
from testing_utils import dot_str_to_graph
from testing_utils import load_test_data
from testing_utils import load_test_ids


def _check_is_isomorphic(actual_fa: fa.FiniteAutomaton, expected_fa_graph: nx.Graph):
    actual_fa_graph = actual_fa.to_networkx()

    # Remove "_starting" nodes added by pyformlang
    for node in list(actual_fa_graph.nodes):
        if isinstance(node, str) and node.endswith("_starting"):
            actual_fa_graph.remove_node(node)

    # Convert string-represented booleans in nodes from dot files
    for _, data in expected_fa_graph.nodes.data():
        if data["is_start"] in ("True", "False"):
            data["is_start"] = data["is_start"] == "True"
        if data["is_final"] in ("True", "False"):
            data["is_final"] = data["is_final"] == "True"
    # Convert string-represented epsilons in edges from dot files
    for _, _, data in expected_fa_graph.edges.data():
        if data["label"] == "ε":
            data["label"] = fa.Epsilon

    assert nx.is_isomorphic(
        actual_fa_graph,
        expected_fa_graph,
        node_match=nx.isomorphism.categorical_node_match(
            ["is_start", "is_final"], [None, None]
        ),
        edge_match=nx.isomorphism.categorical_edge_match("label", None),
    )


class TestRegexToMinDfa:
    @pytest.mark.parametrize(
        "raw_regex, expected_dfa_graph",
        load_test_data(
            "TestRegexToMinDfa.test_regex_converts_to_correct_dfa",
            lambda d: (d["raw_regex"], dot_str_to_graph(d["expected_dfa_dot"])),
        ),
        ids=load_test_ids("TestRegexToMinDfa.test_regex_converts_to_correct_dfa"),
    )
    def test_regex_converts_to_correct_dfa(
        self, raw_regex: str, expected_dfa_graph: nx.Graph
    ):
        min_dfa = fa_utils.regex_to_min_dfa(raw_regex)

        _check_is_isomorphic(min_dfa, expected_dfa_graph)


class TestGraphToNfa:
    @pytest.mark.parametrize(
        "graph, start_states, final_states, expected_nfa_graph",
        load_test_data(
            "TestGraphToNfa.test_on_predefined_graph",
            lambda d: (
                dot_str_to_graph(d["graph"]),
                d["start_states"],
                d["final_states"],
                dot_str_to_graph(d["expected_nfa_graph"]),
            ),
        ),
        ids=load_test_ids("TestGraphToNfa.test_on_predefined_graph"),
    )
    def test_on_predefined_graph(
        self,
        graph: nx.Graph,
        start_states: set | None,
        final_states: set | None,
        expected_nfa_graph: nx.Graph,
    ):
        nfa = fa_utils.graph_to_nfa(graph, start_states, final_states)

        _check_is_isomorphic(nfa, expected_nfa_graph)

    @pytest.mark.parametrize(
        "first_cycle_num, second_cycle_num",
        load_test_data(
            "TestGraphToNfa.test_on_synthetic_graph",
            lambda d: (d["first_cycle_num"], d["second_cycle_num"]),
        ),
        ids=load_test_ids("TestGraphToNfa.test_on_synthetic_graph"),
    )
    def test_on_synthetic_graph(self, first_cycle_num: int, second_cycle_num: int):
        expected_graph = graph_utils.build_labeled_two_cycles_graph(
            first_cycle_num, "a", second_cycle_num, "b"
        )

        nfa = fa_utils.graph_to_nfa(expected_graph, set(), set())

        # Not testing start and final as already tested on predefined graphs
        assert nx.is_isomorphic(
            nfa.to_networkx(),
            expected_graph,
            edge_match=nx.isomorphism.categorical_edge_match("label", None),
        )

    @pytest.mark.parametrize(
        "dataset_graph_name",
        load_test_data(
            "TestGraphToNfa.test_on_dataset_graph",
            lambda d: pytest.param(
                d["dataset_graph_name"], marks=pytest.mark.skip("broken dataset")
            ),
        ),
        ids=load_test_ids("TestGraphToNfa.test_on_dataset_graph"),
    )
    def test_on_dataset_graph(self, dataset_graph_name: str):
        expected_graph = graph_utils.load_graph_from_cfpq_data(dataset_graph_name)

        nfa = fa_utils.graph_to_nfa(expected_graph, set(), set())

        # Not testing start and final as already tested on predefined graphs
        assert nx.is_isomorphic(
            nfa.to_networkx(),
            expected_graph,
            edge_match=nx.isomorphism.categorical_edge_match("label", None),
        )

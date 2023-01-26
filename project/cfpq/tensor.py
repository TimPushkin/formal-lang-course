import networkx as nx
import pyformlang.cfg as c
import pyformlang.finite_automaton as fa
from scipy.sparse import csr_array
from scipy.sparse import eye

from project.cfpq.ecfg import Ecfg
from project.cfpq.rsm import Rsm
from project.utils.bool_decomposition import BoolDecomposition
from project.utils.node_type import NodeType


def constrained_transitive_closure_by_tensor_decomp(
    graph_decomp: BoolDecomposition, rsm_decomp: BoolDecomposition
) -> BoolDecomposition:
    # Add self loops for nullable variables: epsilon-transitions are not allowed and
    # hence it is enough to check for boxes that have start-final nodes -- variables
    # that are nullable transitively from the variables of such boxes will be added
    # later by the algorithm
    assert all(not isinstance(t, c.Epsilon) for t in rsm_decomp.adjs)
    diag = csr_array(eye(len(graph_decomp.states), dtype=bool))
    for s in rsm_decomp.states:
        if not (s.is_start and s.is_final):
            continue
        v = s.data[0]  # Not using value() to discriminate variables from terminals
        if v in graph_decomp.adjs:
            graph_decomp.adjs[v] += diag
        else:
            graph_decomp.adjs[v] = diag.copy()

    # Compute intersection closures while new edges appear
    transitive_closure_size = 0
    while True:
        # Compute transitive closure of intersection
        transitive_closure_indices = list(
            zip(*rsm_decomp.intersect(graph_decomp).transitive_closure_any_symbol())
        )

        # If no new edges appear, we are done
        if len(transitive_closure_indices) == transitive_closure_size:
            break
        transitive_closure_size = len(transitive_closure_indices)

        # Iterate over non-empty indices
        for i, j in transitive_closure_indices:
            # Translate intersection indices into RSM decomposition indices
            r_i, r_j = i // len(graph_decomp.states), j // len(graph_decomp.states)
            # If the edge is from a start RSM node to a final RSM node
            s, f = rsm_decomp.states[r_i], rsm_decomp.states[r_j]
            if s.is_start and f.is_final:
                # Get the variable of the box of this edge
                assert s.data[0] == f.data[0]  # There are no edges between boxes
                v = s.data[0]

                # Translate intersection indices into graph decomposition indices
                g_i, g_j = i % len(graph_decomp.states), j % len(graph_decomp.states)
                # Cannot directly update CSR arrays element-wise
                ij_graph_adj = csr_array(
                    ([True], ([g_i], [g_j])),
                    shape=(len(graph_decomp.states), len(graph_decomp.states)),
                    dtype=bool,
                )

                # Add the edge to the graph (not its value to discriminate it later)
                if v in graph_decomp.adjs:
                    graph_decomp.adjs[v] += ij_graph_adj
                else:
                    graph_decomp.adjs[v] = ij_graph_adj.copy()

    return graph_decomp


def constrained_transitive_closure_by_tensor(
    graph: nx.Graph, cfg: c.CFG
) -> set[tuple[NodeType, c.Variable, NodeType]]:
    graph_decomp = constrained_transitive_closure_by_tensor_decomp(
        BoolDecomposition.from_nfa(
            fa.NondeterministicFiniteAutomaton.from_networkx(graph)
        ),
        BoolDecomposition.from_rsm(Rsm.from_ecfg(Ecfg.from_cfg(cfg)).minimize()),
    )

    result = set()
    for v, adj in graph_decomp.adjs.items():
        # Filter out the initial edges
        if isinstance(v, c.Variable):
            for i, j in zip(*adj.nonzero()):
                result.add(
                    (graph_decomp.states[i].data, v, graph_decomp.states[j].data)
                )
    return result

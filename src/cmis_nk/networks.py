from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import networkx as nx


NetworkType = Literal["LINE", "COMPLETE", "RANDOM", "SMALL_WORLD"]


@dataclass
class NetworkFactory:
    """Factory for agent communication graphs."""

    network_type: NetworkType
    seed: Optional[int] = None

    def build(self, num_agents: int, **params) -> nx.Graph:
        if self.network_type == "LINE":
            graph = nx.path_graph(num_agents)
        elif self.network_type == "COMPLETE":
            graph = nx.complete_graph(num_agents)
        elif self.network_type == "RANDOM":
            p = params.get("p", 0.3)
            graph = nx.erdos_renyi_graph(num_agents, p, seed=self.seed)
        elif self.network_type == "SMALL_WORLD":
            k = params.get("k", 4)
            beta = params.get("beta", 0.1)
            graph = nx.watts_strogatz_graph(num_agents, k, beta, seed=self.seed)
        else:
            raise ValueError(f"Unsupported network_type={self.network_type}")
        nx.set_node_attributes(graph, {node: {"label": f"Agent{node}"} for node in graph.nodes})
        return graph

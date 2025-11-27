from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import combinations
from typing import Dict, Iterable, List, Optional, Protocol, Sequence, Tuple

import networkx as nx
import numpy as np
import pandas as pd

from .agents import Agent
from .simulation import SimulationConfig, SimulationEngine, SimulationResult


class GameValueProtocol(Protocol):
    def evaluate(self, sim_result: SimulationResult, coalition: Sequence[Agent]) -> float:
        ...


class AverageFinalScoreProtocol(GameValueProtocol):
    def evaluate(self, sim_result: SimulationResult, coalition: Sequence[Agent]) -> float:
        scores = [sim_result.final_scores.get(agent.agent_id, 0.0) for agent in coalition]
        return float(np.mean(scores)) if scores else 0.0


@dataclass
class GameTableRecord:
    coalition_id: int
    members: Tuple[str, ...]
    size: int
    mean_value: float
    std_value: float
    runs: int
    notes: str = ""


class GameTableBuilder:
    """Generate cooperative game tables from coalition simulations."""

    def __init__(
        self,
        landscape,
        agents: List[Agent],
        base_graph: nx.Graph,
        sim_config: SimulationConfig,
        runs: int = 5,
        protocol: Optional[GameValueProtocol] = None,
        rng_seed: Optional[int] = None,
    ) -> None:
        self.landscape = landscape
        self.agents = agents
        self.base_graph = base_graph
        self.sim_config = sim_config
        self.runs = runs
        self.protocol = protocol or AverageFinalScoreProtocol()
        self.rng = np.random.default_rng(rng_seed)
        self.records: List[GameTableRecord] = []

    def build_table(self, max_size: Optional[int] = None) -> pd.DataFrame:
        self.records.clear()
        coalition_index = 0
        for coalition_ids in self._enumerate_coalitions(max_size=max_size):
            coalition_agents = [self.agents[i] for i in coalition_ids]
            member_labels = tuple(agent.player_id for agent in coalition_agents)
            if not coalition_agents:
                self.records.append(
                    GameTableRecord(
                        coalition_id=coalition_index,
                        members=member_labels,
                        size=0,
                        mean_value=0.0,
                        std_value=0.0,
                        runs=0,
                        notes="empty coalition",
                    )
                )
                coalition_index += 1
                continue
            values: List[float] = []
            subgraph = self.base_graph.subgraph([agent.agent_id for agent in coalition_agents]).copy()
            for run_idx in range(self.runs):
                cfg = replace(self.sim_config, rng_seed=int(self.rng.integers(0, 1_000_000_000)))
                engine = SimulationEngine(
                    landscape=self.landscape,
                    agents=coalition_agents,
                    graph=subgraph,
                    config=cfg,
                )
                result = engine.run()
                values.append(self.protocol.evaluate(result, coalition_agents))
            mean_value = float(np.mean(values))
            std_value = float(np.std(values))
            self.records.append(
                GameTableRecord(
                    coalition_id=coalition_index,
                    members=member_labels,
                    size=len(coalition_agents),
                    mean_value=mean_value,
                    std_value=std_value,
                    runs=self.runs,
                )
            )
            coalition_index += 1
        return self.to_dataframe()

    def _enumerate_coalitions(self, max_size: Optional[int]) -> Iterable[Tuple[int, ...]]:
        num_agents = len(self.agents)
        yield tuple()
        for size in range(1, num_agents + 1):
            if max_size and size > max_size:
                break
            for combo in combinations(range(num_agents), size):
                yield combo

    def to_dataframe(self) -> pd.DataFrame:
        data = [record.__dict__ for record in self.records]
        return pd.DataFrame(data)

    def to_csv(self, path: str) -> None:
        df = self.to_dataframe()
        df.to_csv(path, index=False)

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Optional

import networkx as nx
import numpy as np

from .agents import Agent, initialize_states
from .landscape import NKLandscape


@dataclass
class SimulationConfig:
    rounds: int = 200
    velocity: float = 1.0
    error_rate: float = 0.0
    local_search_scope: Literal["assigned", "all"] = "assigned"
    mode: Literal["generic", "lf_pure"] = "generic"
    rng_seed: Optional[int] = None
    accept_equal: bool = True

    @classmethod
    def lf_pure(cls, rounds: int = 200, rng_seed: Optional[int] = None) -> "SimulationConfig":
        return cls(
            rounds=rounds,
            velocity=1.0,
            error_rate=0.0,
            local_search_scope="assigned",
            mode="lf_pure",
            rng_seed=rng_seed,
            accept_equal=False,
        )


@dataclass
class SimulationResult:
    history: List[Dict[str, float]]
    final_scores: Dict[int, float]
    best_score: float
    best_state: Optional[np.ndarray]


class SimulationEngine:
    """Runs LF-style exploration/exploitation dynamics on an NK landscape."""

    def __init__(
        self,
        landscape: NKLandscape,
        agents: List[Agent],
        graph: nx.Graph,
        config: SimulationConfig,
        initial_states: Optional[Dict[int, np.ndarray]] = None,
    ) -> None:
        self.landscape = landscape
        self.agents = agents
        self.graph = graph
        self.config = config
        self.rng = np.random.default_rng(config.rng_seed)
        if initial_states is None:
            self.states = initialize_states(agents, landscape.N, seed=config.rng_seed)
        else:
            self.states = {aid: state.copy() for aid, state in initial_states.items()}

    def run(self) -> SimulationResult:
        states = {aid: state.copy() for aid, state in self.states.items()}
        history: List[Dict[str, float]] = []
        best_score = float("-inf")
        best_state: Optional[np.ndarray] = None
        for round_idx in range(self.config.rounds):
            states = self._run_round(states)
            score_map = self._evaluate_scores(states)
            if score_map:
                round_mean = float(np.mean(list(score_map.values())))
                round_max = float(np.max(list(score_map.values())))
                best_agent = max(score_map, key=score_map.get)
                if round_max > best_score:
                    best_score = round_max
                    best_state = states[best_agent].copy()
            else:
                round_mean = 0.0
                round_max = 0.0
            history.append(
                {
                    "round": float(round_idx),
                    "mean_score": round_mean,
                    "max_score": round_max,
                }
            )
        final_scores = self._evaluate_scores(states)
        return SimulationResult(
            history=history,
            final_scores=final_scores,
            best_score=best_score if best_score > float("-inf") else 0.0,
            best_state=best_state,
        )

    def _run_round(self, states: Dict[int, np.ndarray]) -> Dict[int, np.ndarray]:
        current_scores = self._evaluate_scores(states)
        next_states: Dict[int, np.ndarray] = {}
        for agent in self.agents:
            current_state = states.get(agent.agent_id)
            if current_state is None:
                continue
            next_states[agent.agent_id] = self._update_agent(
                agent,
                current_state,
                states,
                current_scores,
            )
        return next_states

    def _update_agent(
        self,
        agent: Agent,
        current_state: np.ndarray,
        states: Dict[int, np.ndarray],
        score_map: Dict[int, float],
    ) -> np.ndarray:
        observe = self.rng.random() < self.config.velocity
        if observe:
            best_neighbor_state = self._best_neighbor_state(agent.agent_id, states, score_map)
            if best_neighbor_state is not None:
                return self._mimic_state(current_state, best_neighbor_state)
        return self._local_search(agent, current_state, score_map.get(agent.agent_id, 0.0))

    def _best_neighbor_state(
        self,
        agent_id: int,
        states: Dict[int, np.ndarray],
        score_map: Dict[int, float],
    ) -> Optional[np.ndarray]:
        own_score = score_map.get(agent_id, float("-inf"))
        best_state: Optional[np.ndarray] = None
        best_score = own_score
        for neighbor in self.graph.neighbors(agent_id):
            neighbor_score = score_map.get(neighbor, float("-inf"))
            if neighbor_score > best_score:
                best_score = neighbor_score
                best_state = states[neighbor]
        return best_state

    def _mimic_state(
        self,
        current_state: np.ndarray,
        source_state: np.ndarray,
    ) -> np.ndarray:
        new_state = current_state.copy()
        if self.config.error_rate <= 0:
            new_state[:] = source_state
            return new_state
        copy_mask = self.rng.random(self.landscape.N) >= self.config.error_rate
        new_state[copy_mask] = source_state[copy_mask]
        return new_state

    def _local_search(
        self,
        agent: Agent,
        current_state: np.ndarray,
        current_score: float,
    ) -> np.ndarray:
        candidate = current_state.copy()
        if self.config.local_search_scope == "assigned" and agent.bits:
            search_space = agent.bits
        else:
            search_space = list(range(self.landscape.N))
        bit = int(self.rng.choice(search_space))
        candidate[bit] = 1 - candidate[bit]
        new_score = self.landscape.evaluate(candidate)
        if self.config.accept_equal:
            accept = new_score >= current_score
        else:
            accept = new_score > current_score
        if accept:
            return candidate
        return current_state

    def _evaluate_scores(self, states: Dict[int, np.ndarray]) -> Dict[int, float]:
        return {
            agent_id: float(self.landscape.evaluate(state))
            for agent_id, state in states.items()
        }

    def clone_with_graph(self, graph: nx.Graph) -> "SimulationEngine":
        return SimulationEngine(
            landscape=self.landscape,
            agents=self.agents,
            graph=graph,
            config=self.config,
        )

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np


@dataclass
class Agent:
    agent_id: int
    bits: List[int]
    name: Optional[str] = None
    skill: Optional[str] = None
    player_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.name is None:
            self.name = f"Agent{self.agent_id}"
        if self.player_id is None:
            self.player_id = str(self.agent_id)


def create_agents(num_bits: int) -> List[Agent]:
    """Create one-to-one agents for each bit."""
    return [Agent(agent_id=i, bits=[i]) for i in range(num_bits)]


def initialize_states(
    agents: List[Agent],
    num_bits: int,
    seed: Optional[int] = None,
    init: str = "random",
) -> Dict[int, np.ndarray]:
    rng = np.random.default_rng(seed)
    states: Dict[int, np.ndarray] = {}
    for agent in agents:
        if init == "zeros":
            state = np.zeros(num_bits, dtype=np.int8)
        else:
            state = rng.integers(0, 2, size=num_bits, dtype=np.int8)
        states[agent.agent_id] = state
    return states

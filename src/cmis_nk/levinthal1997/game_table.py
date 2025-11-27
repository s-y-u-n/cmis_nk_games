from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from ..common.game_types import GameTableRecord
from ..landscape import NKLandscape
from ..local_search import LocalSearchConfig, LocalSearchEngine
from ..utils import enumerate_coalitions


@dataclass
class LevinthalPlayer:
    player_id: str
    bits: List[int]


class LevinthalGameTableBuilder:
    """Game-table generator using Levinthal-style constrained local search."""

    def __init__(
        self,
        landscape: NKLandscape,
        baseline_state: np.ndarray,
        players: Sequence[LevinthalPlayer],
        search_config: LocalSearchConfig,
        trials: int,
        rng_seed: Optional[int] = None,
        scenario_name: str = "levinthal1997",
    ) -> None:
        self.landscape = landscape
        self.baseline_state = baseline_state.astype(np.int8)
        self.players = list(players)
        self.search_config = search_config
        self.trials = trials
        self.rng = np.random.default_rng(rng_seed)
        self.scenario_name = scenario_name
        self.records: List[GameTableRecord] = []

    def build_table(self, max_size: Optional[int] = None) -> pd.DataFrame:
        self.records.clear()
        coalition_index = 0
        baseline_fitness = float(self.landscape.evaluate(self.baseline_state))
        for coalition in enumerate_coalitions(self.players, max_size):
            member_ids = tuple(player.player_id for player in coalition)
            free_bits = sorted({bit for player in coalition for bit in player.bits})
            if not free_bits:
                mean_value = baseline_fitness
                std_value = 0.0
            else:
                seed = int(self.rng.integers(0, 1_000_000_000))
                engine = LocalSearchEngine(
                    landscape=self.landscape,
                    baseline_state=self.baseline_state,
                    free_bits=free_bits,
                    config=self.search_config,
                    rng_seed=seed,
                )
                results = engine.run_trials(self.trials)
                fitness_values = [res.final_fitness for res in results]
                mean_value = float(np.mean(fitness_values))
                std_value = float(np.std(fitness_values))
            notes = (
                f"scenario={self.scenario_name};N={self.landscape.N};"
                f"K={self.landscape.K};trials={self.trials}"
            )
            self.records.append(
                GameTableRecord(
                    coalition_id=coalition_index,
                    members=member_ids,
                    size=len(member_ids),
                    mean_value=mean_value,
                    std_value=std_value,
                    runs=self.trials,
                    notes=notes,
                )
            )
            coalition_index += 1
        return self.to_dataframe()

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([record.__dict__ for record in self.records])

    def to_csv(self, path: str) -> None:
        df = self.to_dataframe()
        df.to_csv(path, index=False)

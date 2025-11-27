from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from ..landscape import NKLandscape


@dataclass
class ModuleDefinition:
    name: str
    bits: List[int]


class EthirajGameTableBuilder:
    def __init__(
        self,
        landscape: NKLandscape,
        modules: Sequence[ModuleDefinition],
        baseline_state: np.ndarray,
        mature_state: np.ndarray,
        scenario_note: str,
    ) -> None:
        self.landscape = landscape
        self.modules = list(modules)
        self.baseline_state = baseline_state.astype(np.int8)
        self.mature_state = mature_state.astype(np.int8)
        self.scenario_note = scenario_note
        self.baseline_fitness = float(self.landscape.evaluate(self.baseline_state))

    def build_table(self, max_size: Optional[int] = None) -> pd.DataFrame:
        records: List[dict[str, object]] = []
        coalition_id = 0
        for coalition in self._enumerate_coalitions(max_size):
            state = self.baseline_state.copy()
            member_names = tuple(module.name for module in coalition)
            for module in coalition:
                for bit in module.bits:
                    state[bit] = self.mature_state[bit]
            absolute_fitness = float(self.landscape.evaluate(state))
            value = absolute_fitness - self.baseline_fitness
            records.append(
                {
                    "coalition_id": coalition_id,
                    "members": member_names,
                    "size": len(coalition),
                    "v_value": value,
                    "absolute_fitness": absolute_fitness,
                    "baseline_fitness": self.baseline_fitness,
                    "notes": self.scenario_note,
                }
            )
            coalition_id += 1
        return pd.DataFrame(records)

    def _enumerate_coalitions(
        self, max_size: Optional[int]
    ) -> Iterable[Tuple[ModuleDefinition, ...]]:
        yield tuple()
        total = len(self.modules)
        for size in range(1, total + 1):
            if max_size and size > max_size:
                break
            for combo in combinations(self.modules, size):
                yield combo

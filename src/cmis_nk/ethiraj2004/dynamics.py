from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np

from ..landscape import NKLandscape


@dataclass
class EthirajSimulationResult:
    best_state: np.ndarray
    baseline_state: np.ndarray
    history: List[dict[str, float]]


class EthirajFirmPopulation:
    def __init__(
        self,
        landscape: NKLandscape,
        designer_modules: Sequence[Sequence[int]],
        num_firms: int,
        baseline_state: np.ndarray,
        rng_seed: int | None,
    ) -> None:
        self.landscape = landscape
        self.designer_modules = [list(module) for module in designer_modules]
        self.num_firms = num_firms
        self.baseline_state = baseline_state.astype(np.int8)
        self.rng = np.random.default_rng(rng_seed)
        self.states = self.rng.integers(0, 2, size=(num_firms, landscape.N), dtype=np.int8)

    def local_search_step(self) -> None:
        for firm_idx in range(self.num_firms):
            state = self.states[firm_idx]
            for module_bits in self.designer_modules:
                if not module_bits:
                    continue
                bit = int(self.rng.choice(module_bits))
                candidate = state.copy()
                candidate[bit] = 1 - candidate[bit]
                current_fitness = _module_fitness(self.landscape, state, module_bits)
                candidate_fitness = _module_fitness(self.landscape, candidate, module_bits)
                if candidate_fitness > current_fitness:
                    state = candidate
            self.states[firm_idx] = state

    def recombine(self, mode: str) -> None:
        mode_lower = mode.lower()
        if mode_lower == "firm":
            self._recombine_firm_level()
        elif mode_lower == "module":
            self._recombine_module_level()
        elif mode_lower == "hybrid":
            self._recombine_firm_level()
            self._recombine_module_level()
        else:
            return

    def evaluate_all(self) -> np.ndarray:
        return np.array([self.landscape.evaluate(state) for state in self.states])

    def best_state(self) -> np.ndarray:
        scores = self.evaluate_all()
        best_idx = int(np.argmax(scores)) if len(scores) else 0
        return self.states[best_idx].copy()

    def _recombine_firm_level(self) -> None:
        scores = self.evaluate_all()
        if len(scores) == 0:
            return
        best_idx = int(np.argmax(scores))
        donor = self.states[best_idx]
        for firm_idx in range(self.num_firms):
            if firm_idx == best_idx:
                continue
            module_bits = self.designer_modules[self.rng.integers(0, len(self.designer_modules))]
            if not module_bits:
                continue
            self.states[firm_idx, module_bits] = donor[module_bits]

    def _recombine_module_level(self) -> None:
        if not self.designer_modules:
            return
        for module_bits in self.designer_modules:
            if not module_bits:
                continue
            best_idx = self._best_firm_for_module(module_bits)
            donor_bits = self.states[best_idx, module_bits]
            for firm_idx in range(self.num_firms):
                if firm_idx == best_idx:
                    continue
                self.states[firm_idx, module_bits] = donor_bits

    def _best_firm_for_module(self, module_bits: Sequence[int]) -> int:
        best_idx = 0
        best_value = float("-inf")
        for firm_idx in range(self.num_firms):
            value = _module_fitness(self.landscape, self.states[firm_idx], module_bits)
            if value > best_value:
                best_value = value
                best_idx = firm_idx
        return best_idx


def _module_fitness(
    landscape: NKLandscape,
    state: np.ndarray,
    module_bits: Sequence[int],
) -> float:
    if not module_bits:
        return 0.0
    contributions: List[float] = []
    for idx in module_bits:
        local_bits = [idx, *landscape.dependencies[idx]]
        pattern_index = 0
        for bit in local_bits:
            pattern_index = (pattern_index << 1) | int(state[bit])
        contributions.append(float(landscape.tables[idx][pattern_index]))
    return float(np.mean(contributions)) if contributions else 0.0


def run_ethiraj_simulation(
    population: EthirajFirmPopulation,
    rounds: int,
    recombination_interval: int,
    recombination_mode: str,
) -> EthirajSimulationResult:
    history: List[dict[str, float]] = []
    for step in range(rounds):
        population.local_search_step()
        if recombination_interval > 0 and (step + 1) % recombination_interval == 0:
            population.recombine(recombination_mode)
        scores = population.evaluate_all()
        if scores.size:
            history.append(
                {
                    "round": float(step),
                    "mean_fitness": float(np.mean(scores)),
                    "max_fitness": float(np.max(scores)),
                }
            )
    best_state = population.best_state()
    return EthirajSimulationResult(
        best_state=best_state,
        baseline_state=population.baseline_state.copy(),
        history=history,
    )

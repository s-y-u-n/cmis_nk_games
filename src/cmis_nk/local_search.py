from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Sequence

import numpy as np

from .landscape import NKLandscape


@dataclass
class LocalSearchConfig:
    max_steps: int = 250
    stall_limit: int = 50  # patience（改善なし連続ステップ上限）
    noise_accept_prob: float = 0.0
    init_strategy: Literal["random", "baseline", "perturb"] = "random"
    perturb_prob: float = 0.15
    rng_seed: Optional[int] = None


@dataclass
class LocalSearchResult:
    final_state: np.ndarray
    final_fitness: float
    best_fitness: float
    steps: int


class LocalSearchEngine:
    """Levinthal-style constrained hill climbing on an NK landscape."""

    def __init__(
        self,
        landscape: NKLandscape,
        baseline_state: np.ndarray,
        free_bits: Sequence[int],
        config: LocalSearchConfig,
        rng_seed: Optional[int] = None,
    ) -> None:
        if len(baseline_state) != landscape.N:
            raise ValueError("baseline_state length must match landscape.N")
        self.landscape = landscape
        self.baseline_state = baseline_state.astype(np.int8)
        self.free_bits = sorted(set(int(bit) for bit in free_bits))
        self.config = config
        seed = rng_seed if rng_seed is not None else config.rng_seed
        self.rng = np.random.default_rng(seed)

    def run_trials(self, trials: int) -> list[LocalSearchResult]:
        return [self._run_once() for _ in range(trials)]

    def run_with_history(self) -> tuple[LocalSearchResult, list[float]]:
        """1 回のローカル探索を実行し、ベストフィットネスの推移も返す。"""

        if not self.free_bits:
            fitness = float(self.landscape.evaluate(self.baseline_state))
            result = LocalSearchResult(
                final_state=self.baseline_state.copy(),
                final_fitness=fitness,
                best_fitness=fitness,
                steps=0,
            )
            return result, [fitness]
        current_state = self._initial_state()
        current_fitness = float(self.landscape.evaluate(current_state))
        best_state = current_state.copy()
        best_fitness = current_fitness
        history: list[float] = [best_fitness]
        stall_counter = 0
        steps = 0
        while steps < self.config.max_steps and stall_counter < self.config.stall_limit:
            steps += 1
            bit = int(self.rng.choice(self.free_bits))
            candidate_state = current_state.copy()
            candidate_state[bit] = 1 - candidate_state[bit]
            candidate_fitness = float(self.landscape.evaluate(candidate_state))
            improved = candidate_fitness > best_fitness
            accept = improved
            if not accept and self.config.noise_accept_prob > 0.0:
                if self.rng.random() < self.config.noise_accept_prob:
                    accept = True
            if accept:
                current_state = candidate_state
                current_fitness = candidate_fitness
                if improved:
                    best_fitness = candidate_fitness
                    best_state = candidate_state.copy()
                    stall_counter = 0
                else:
                    stall_counter += 1
            else:
                stall_counter += 1
            history.append(best_fitness)
        result = LocalSearchResult(
            final_state=current_state,
            final_fitness=best_fitness,
            best_fitness=best_fitness,
            steps=steps,
        )
        return result, history

    def _run_once(self) -> LocalSearchResult:
        if not self.free_bits:
            fitness = float(self.landscape.evaluate(self.baseline_state))
            return LocalSearchResult(
                final_state=self.baseline_state.copy(),
                final_fitness=fitness,
                best_fitness=fitness,
                steps=0,
            )
        current_state = self._initial_state()
        current_fitness = float(self.landscape.evaluate(current_state))
        best_state = current_state.copy()
        best_fitness = current_fitness
        stall_counter = 0
        steps = 0
        while steps < self.config.max_steps and stall_counter < self.config.stall_limit:
            steps += 1
            bit = int(self.rng.choice(self.free_bits))
            candidate_state = current_state.copy()
            candidate_state[bit] = 1 - candidate_state[bit]
            candidate_fitness = float(self.landscape.evaluate(candidate_state))
            # Levinthal 仕様: 「これまでのベスト」を基準に改善判定
            improved = candidate_fitness > best_fitness
            accept = improved
            if not accept and self.config.noise_accept_prob > 0.0:
                if self.rng.random() < self.config.noise_accept_prob:
                    accept = True
            if accept:
                current_state = candidate_state
                current_fitness = candidate_fitness
                if improved:
                    best_fitness = candidate_fitness
                    best_state = candidate_state.copy()
                    stall_counter = 0
                else:
                    stall_counter += 1
            else:
                stall_counter += 1
        return LocalSearchResult(
            final_state=current_state,
            # 仕様上の「最終フィットネス」は探索中に到達したベスト値とみなす
            final_fitness=best_fitness,
            best_fitness=best_fitness,
            steps=steps,
        )

    def _initial_state(self) -> np.ndarray:
        state = self.baseline_state.copy()
        if self.config.init_strategy == "baseline":
            return state
        if self.config.init_strategy == "perturb":
            for bit in self.free_bits:
                if self.rng.random() < self.config.perturb_prob:
                    state[bit] = 1 - state[bit]
            return state
        # default random
        state[self.free_bits] = self.rng.integers(0, 2, size=len(self.free_bits), dtype=np.int8)
        return state

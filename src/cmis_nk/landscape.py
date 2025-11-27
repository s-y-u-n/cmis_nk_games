from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import numpy as np


SkillProfile = Dict[str, Tuple[float, float]]
ConflictPairs = Set[Tuple[int, int]]


def _bits_from_int(value: int, width: int) -> List[int]:
    return [int(bool((value >> shift) & 1)) for shift in reversed(range(width))]


@dataclass
class NKLandscape:
    """NK landscape with optional skill and conflict biases."""

    N: int
    K: int
    dependencies: List[List[int]]
    tables: List[np.ndarray]
    skill_profile: Optional[SkillProfile] = None
    bit_skills: Optional[Dict[int, str]] = None
    conflict_pairs: Optional[ConflictPairs] = None

    def __post_init__(self) -> None:
        if len(self.dependencies) != self.N:
            raise ValueError("dependencies must have length N")
        if len(self.tables) != self.N:
            raise ValueError("tables must have length N")

    @classmethod
    def from_random(
        cls,
        N: int,
        K: int,
        seed: Optional[int] = None,
        dependencies: Optional[List[List[int]]] = None,
        skill_profile: Optional[SkillProfile] = None,
        bit_skills: Optional[Dict[int, str]] = None,
        conflict_pairs: Optional[Iterable[Tuple[int, int]]] = None,
    ) -> "NKLandscape":
        rng = np.random.default_rng(seed)
        deps = dependencies or cls._generate_dependencies(N, K, rng)
        tables = []
        normalized_conflicts: Optional[ConflictPairs] = None
        if conflict_pairs:
            normalized_conflicts = {
                tuple(sorted(pair)) for pair in conflict_pairs if pair[0] != pair[1]
            }
        for bit_idx in range(N):
            table = cls._generate_table(
                bit_idx,
                deps[bit_idx],
                K,
                rng,
                skill_profile,
                bit_skills,
                normalized_conflicts,
            )
            tables.append(table)
        return cls(
            N=N,
            K=K,
            dependencies=deps,
            tables=tables,
            skill_profile=skill_profile,
            bit_skills=bit_skills,
            conflict_pairs=normalized_conflicts,
        )

    @staticmethod
    def _generate_dependencies(N: int, K: int, rng: np.random.Generator) -> List[List[int]]:
        deps: List[List[int]] = []
        for i in range(N):
            choices = list(range(N))
            choices.remove(i)
            dep = list(rng.choice(choices, size=K, replace=False)) if K > 0 else []
            deps.append(dep)
        return deps

    @classmethod
    def _generate_table(
        cls,
        bit_idx: int,
        dep_list: Sequence[int],
        K: int,
        rng: np.random.Generator,
        skill_profile: Optional[SkillProfile],
        bit_skills: Optional[Dict[int, str]],
        conflict_pairs: Optional[ConflictPairs],
    ) -> np.ndarray:
        width = K + 1
        table = np.zeros(2**width, dtype=float)
        local_bits = [bit_idx, *dep_list]
        low, high = cls._skill_range(bit_idx, skill_profile, bit_skills)
        for idx in range(table.size):
            pattern = _bits_from_int(idx, width)
            value = rng.uniform(low, high)
            if cls._has_conflict(pattern, local_bits, conflict_pairs):
                value *= 0.5  # penalize conflicting combinations
            table[idx] = value
        return table

    @staticmethod
    def _skill_range(
        bit_idx: int,
        skill_profile: Optional[SkillProfile],
        bit_skills: Optional[Dict[int, str]],
    ) -> Tuple[float, float]:
        if not skill_profile or not bit_skills:
            return (0.0, 1.0)
        skill = bit_skills.get(bit_idx)
        if not skill:
            return (0.0, 1.0)
        return skill_profile.get(skill, (0.0, 1.0))

    @staticmethod
    def _has_conflict(
        pattern: Sequence[int],
        local_bits: Sequence[int],
        conflict_pairs: Optional[ConflictPairs],
    ) -> bool:
        if not conflict_pairs:
            return False
        bit_value_map = {bit: val for bit, val in zip(local_bits, pattern)}
        for pair in conflict_pairs:
            a, b = pair
            if a in bit_value_map and b in bit_value_map:
                if bit_value_map[a] == 1 and bit_value_map[b] == 1:
                    return True
        return False

    def evaluate(self, state: np.ndarray) -> float:
        if len(state) != self.N:
            raise ValueError("state length must equal N")
        total = 0.0
        for idx in range(self.N):
            local_bits = [idx, *self.dependencies[idx]]
            positions = [state[bit] for bit in local_bits]
            pattern_index = 0
            for bit_val in positions:
                pattern_index = (pattern_index << 1) | int(bit_val)
            total += self.tables[idx][pattern_index]
        return total / self.N

    def random_state(self, rng: Optional[np.random.Generator] = None) -> np.ndarray:
        generator = rng or np.random.default_rng()
        return generator.integers(0, 2, size=self.N, dtype=np.int8)

    def neighbors(self, state: np.ndarray, bit_indices: Sequence[int]) -> List[np.ndarray]:
        """Return one-bit neighbors limited to given bit indices."""
        neighbors = []
        for bit in bit_indices:
            new_state = state.copy()
            new_state[bit] = 1 - new_state[bit]
            neighbors.append(new_state)
        return neighbors

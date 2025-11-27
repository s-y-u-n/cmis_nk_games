from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np

from ..landscape import NKLandscape
from ..utils import split_bits_evenly


def build_true_modules(N: int, module_count: int) -> List[List[int]]:
    return split_bits_evenly(N, module_count)


def build_designer_modules(N: int, designer_count: int) -> List[List[int]]:
    return split_bits_evenly(N, max(1, designer_count))


def build_ethiraj_landscape(
    N: int,
    K: int,
    true_modules: Sequence[Sequence[int]],
    intra_bias: float,
    inter_bias: float,
    seed: int | None,
) -> NKLandscape:
    rng = np.random.default_rng(seed)
    module_map = {}
    for module_idx, bits in enumerate(true_modules):
        for bit in bits:
            module_map[bit] = module_idx
    dependencies: List[List[int]] = []
    for bit in range(N):
        dep = _sample_dependencies(
            bit,
            K,
            module_map,
            true_modules,
            rng,
            intra_bias,
            inter_bias,
        )
        dependencies.append(dep)
    return NKLandscape.from_random(
        N=N,
        K=K,
        seed=seed,
        dependencies=dependencies,
    )


def _sample_dependencies(
    bit: int,
    K: int,
    module_map: dict[int, int],
    modules: Sequence[Sequence[int]],
    rng: np.random.Generator,
    intra_bias: float,
    inter_bias: float,
) -> List[int]:
    if K <= 0:
        return []
    same_module = [b for b in modules[module_map[bit]] if b != bit]
    other_bits = [b for b in range(len(module_map)) if module_map[b] != module_map[bit]]
    deps: List[int] = []
    while len(deps) < K:
        prefer_same = rng.random() < intra_bias and same_module
        if prefer_same:
            candidate = int(rng.choice(same_module))
        else:
            pool = other_bits if other_bits else same_module
            if not pool:
                break
            weights = None
            if pool is other_bits and inter_bias not in (0.0, 1.0):
                weights = None  # uniform
            candidate = int(rng.choice(pool))
        if candidate == bit or candidate in deps:
            continue
        deps.append(candidate)
    while len(deps) < K:
        fallback = rng.integers(0, len(module_map))
        if fallback == bit or fallback in deps:
            continue
        deps.append(int(fallback))
    return deps

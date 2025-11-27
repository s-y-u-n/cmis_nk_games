from __future__ import annotations

from itertools import combinations
from typing import Iterable, Iterator, List, Sequence, Tuple

import numpy as np


def bitstring_to_array(bitstring: str, length: int) -> np.ndarray:
    cleaned = [char for char in str(bitstring) if char in {"0", "1"}]
    if len(cleaned) != length:
        raise ValueError(f"bitstring length {len(cleaned)} does not match expected {length}")
    return np.array([int(ch) for ch in cleaned], dtype=np.int8)


def split_bits_evenly(num_bits: int, groups: int) -> List[List[int]]:
    if groups <= 0:
        raise ValueError("groups must be positive")
    partitions: List[List[int]] = [[] for _ in range(groups)]
    for idx in range(num_bits):
        partitions[idx % groups].append(idx)
    return partitions


def enumerate_coalitions(items: Sequence, max_size: int | None = None) -> Iterator[Tuple]:
    yield tuple()
    total = len(items)
    for size in range(1, total + 1):
        if max_size and size > max_size:
            break
        for combo in combinations(items, size):
            yield combo

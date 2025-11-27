from __future__ import annotations

from itertools import combinations
from pathlib import Path
import re
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


def next_numbered_csv_path(base_dir: Path, prefix: str) -> Path:
    """Return next numbered CSV path like `<prefix>_001.csv` under `base_dir`.

    If no matching files exist, start from 001. Otherwise, use (max existing + 1).
    """

    base_dir.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)\.csv$")
    max_index = 0
    for path in base_dir.glob(f"{prefix}_*.csv"):
        match = pattern.match(path.name)
        if match:
            idx = int(match.group(1))
            if idx > max_index:
                max_index = idx
    next_index = max_index + 1
    filename = f"{prefix}_{next_index:03d}.csv"
    return base_dir / filename

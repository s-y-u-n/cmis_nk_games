from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class GameTableRecord:
    coalition_id: int
    members: Tuple[str, ...]
    size: int
    mean_value: float
    std_value: float
    runs: int
    notes: str = ""

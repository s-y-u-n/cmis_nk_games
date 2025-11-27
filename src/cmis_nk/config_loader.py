from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .simulation import SimulationConfig


@dataclass
class LevinthalSettings:
    max_steps: int
    stall_limit: int
    noise_accept_prob: float
    init_strategy: str
    perturb_prob: float
    baseline_state: str
    players: Optional[List[Dict[str, Any]]]


@dataclass
class EthirajSettings:
    true_modules: int
    designer_modules: int
    players_basis: str
    intra_density: float
    inter_density: float
    firms: int
    rounds: int
    recombination_interval: int
    recombination_mode: str
    baseline_state: str


@dataclass
class ExperimentConfig:
    N: int
    K: int
    scenario_type: str
    network_type: str
    network_params: Dict[str, Any]
    rounds: int
    runs: int
    velocity: float
    error_rate: float
    local_search_scope: str
    protocol: str
    random_seed: Optional[int]
    landscape_seed: Optional[int]
    network_seed: Optional[int]
    max_coalition_size: Optional[int]
    output_path: Path
    levinthal: Optional[LevinthalSettings] = None
    ethiraj: Optional[EthirajSettings] = None

    def to_simulation_config(self) -> SimulationConfig:
        return SimulationConfig(
            rounds=self.rounds,
            velocity=self.velocity,
            error_rate=self.error_rate,
            local_search_scope=self.local_search_scope,  # type: ignore[arg-type]
            rng_seed=self.random_seed,
        )


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    network = raw.get("network", {})
    sim = raw.get("simulation", {})
    game_table = raw.get("game_table", {})
    seeds = raw.get("seeds", {})
    output = raw.get("output", {})
    scenario = raw.get("scenario", {})
    scenario_type = scenario.get("type", "lazer2007").lower()
    levinthal_settings: Optional[LevinthalSettings] = None
    ethiraj_settings: Optional[EthirajSettings] = None
    if scenario_type == "levinthal1997":
        search = raw.get("search", {})
        baseline_state = search.get("baseline_state")
        if baseline_state is None:
            baseline_state = "0" * int(raw["N"])
        players_cfg = search.get("players") or raw.get("players")
        levinthal_settings = LevinthalSettings(
            max_steps=int(search.get("max_steps", 250)),
            stall_limit=int(search.get("stall_limit", 50)),
            noise_accept_prob=float(search.get("noise_accept_prob", 0.0)),
            init_strategy=search.get("init_strategy", "random"),
            perturb_prob=float(search.get("perturb_prob", 0.15)),
            baseline_state=str(baseline_state),
            players=players_cfg,
        )
    if scenario_type == "ethiraj2004":
        eth = raw.get("ethiraj", {})
        baseline_state = eth.get("baseline_state") or ("0" * int(raw["N"]))
        ethiraj_settings = EthirajSettings(
            true_modules=int(eth.get("true_modules", 3)),
            designer_modules=int(eth.get("designer_modules", eth.get("true_modules", 3))),
            players_basis=eth.get("players_basis", "designer"),
            intra_density=float(eth.get("intra_density", 0.8)),
            inter_density=float(eth.get("inter_density", 0.2)),
            firms=int(eth.get("firms", 10)),
            rounds=int(eth.get("rounds", raw.get("rounds", 200))),
            recombination_interval=int(eth.get("recombination_interval", 5)),
            recombination_mode=eth.get("recombination_mode", "module"),
            baseline_state=str(baseline_state),
        )
    return ExperimentConfig(
        N=int(raw["N"]),
        K=int(raw["K"]),
        scenario_type=scenario_type,
        network_type=network.get("type", "LINE"),
        network_params=network.get("params", {}),
        rounds=int(sim.get("rounds", 200)),
        runs=int(game_table.get("runs", 3)),
        velocity=float(sim.get("velocity", 1.0)),
        error_rate=float(sim.get("error_rate", 0.0)),
        local_search_scope=sim.get("local_search_scope", "assigned"),
        protocol=game_table.get("protocol", "average_final_score"),
        random_seed=_maybe_int(seeds.get("random")),
        landscape_seed=_maybe_int(seeds.get("landscape")),
        network_seed=_maybe_int(seeds.get("network")),
        max_coalition_size=_maybe_int(game_table.get("max_coalition_size")),
        output_path=Path(output.get("path", "outputs/tables/lazer2007_baseline.csv")),
        levinthal=levinthal_settings,
        ethiraj=ethiraj_settings,
    )


def _maybe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    return int(value)

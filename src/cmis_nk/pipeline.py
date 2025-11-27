from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from .agents import Agent, create_agents
from .config_loader import ExperimentConfig, LazerSettings, load_experiment_config
from .lazer2007.game_table import (
    AverageFinalScoreProtocol,
    GameTableBuilder,
    GameValueProtocol,
)
from .landscape import NKLandscape
from .levinthal1997 import LevinthalGameTableBuilder, LevinthalPlayer
from .local_search import LocalSearchConfig
from .networks import NetworkFactory
from .simulation import SimulationConfig
from .ethiraj2004 import (
    build_true_modules,
    build_designer_modules,
    build_ethiraj_landscape,
    EthirajFirmPopulation,
    run_ethiraj_simulation,
    EthirajGameTableBuilder,
)
from .ethiraj2004.game_table import ModuleDefinition
from .utils import bitstring_to_array


def protocol_from_name(name: str) -> GameValueProtocol:
    normalized = name.lower()
    if normalized in {"average_final_score", "avg_final"}:
        return AverageFinalScoreProtocol()
    raise ValueError(f"Unsupported protocol: {name}")


def build_landscape(exp_config: ExperimentConfig) -> NKLandscape:
    skill_profile = None
    bit_skills = None
    conflict_pairs = None
    if getattr(exp_config, "lazer", None):
        skill_profile = exp_config.lazer.skill_profile
        bit_skills = exp_config.lazer.bit_skills
        conflict_pairs = exp_config.lazer.conflict_pairs
    return NKLandscape.from_random(
        N=exp_config.N,
        K=exp_config.K,
        seed=exp_config.landscape_seed or exp_config.random_seed,
        skill_profile=skill_profile,
        bit_skills=bit_skills,
        conflict_pairs=conflict_pairs,
    )


def build_agents(exp_config: ExperimentConfig) -> list[Agent]:
    agents = create_agents(exp_config.N)
    if getattr(exp_config, "lazer", None) and exp_config.lazer.bit_skills:
        for agent in agents:
            # プレイヤー = ビット = agent_id と仮定
            bit_idx = agent.bits[0] if agent.bits else agent.agent_id
            agent.skill = exp_config.lazer.bit_skills.get(bit_idx)
    return agents


def build_network(exp_config: ExperimentConfig, num_agents: int):
    factory = NetworkFactory(exp_config.network_type, seed=exp_config.network_seed)
    return factory.build(num_agents, **exp_config.network_params)


def build_simulation_config(exp_config: ExperimentConfig) -> SimulationConfig:
    return exp_config.to_simulation_config()


def run_experiment(
    config_path: str | Path,
    *,
    output_override: str | Path | None = None,
    max_coalition_size: Optional[int] = None,
) -> Tuple[Path, int]:
    exp = load_experiment_config(config_path)
    if exp.scenario_type == "levinthal1997":
        return _run_levinthal_experiment(
            exp, output_override=output_override, max_coalition_size=max_coalition_size
        )
    if exp.scenario_type == "ethiraj2004":
        return _run_ethiraj_experiment(
            exp, output_override=output_override, max_coalition_size=max_coalition_size
        )
    else:
        return _run_lazer_experiment(
            exp, output_override=output_override, max_coalition_size=max_coalition_size
        )


def _run_lazer_experiment(
    exp: ExperimentConfig,
    *,
    output_override: str | Path | None,
    max_coalition_size: Optional[int],
) -> Tuple[Path, int]:
    landscape = build_landscape(exp)
    agents = build_agents(exp)
    graph = build_network(exp, len(agents))
    sim_config = build_simulation_config(exp)
    protocol = protocol_from_name(exp.protocol)

    notes = (
        f"scenario=lazer2007;N={exp.N};K={exp.K};"
        f"rounds={exp.rounds};velocity={exp.velocity};error={exp.error_rate};"
        f"runs={exp.runs};network_type={exp.network_type};"
        f"landscape_seed={exp.landscape_seed};random_seed={exp.random_seed};"
        f"network_seed={exp.network_seed}"
    )

    builder = GameTableBuilder(
        landscape=landscape,
        agents=agents,
        base_graph=graph,
        sim_config=sim_config,
        runs=exp.runs,
        protocol=protocol,
        rng_seed=exp.random_seed,
        notes=notes,
    )
    target_max_size = max_coalition_size or exp.max_coalition_size
    df = builder.build_table(max_size=target_max_size)
    output_path = Path(output_override) if output_override else exp.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    builder.to_csv(str(output_path))
    return output_path, len(df)


def _run_levinthal_experiment(
    exp: ExperimentConfig,
    *,
    output_override: str | Path | None,
    max_coalition_size: Optional[int],
) -> Tuple[Path, int]:
    if not exp.levinthal:
        raise ValueError("Levinthal scenario requires search settings in config")
    landscape = build_landscape(exp)
    baseline_state = bitstring_to_array(exp.levinthal.baseline_state, exp.N)
    players = _build_players(exp)
    search_config = LocalSearchConfig(
        max_steps=exp.levinthal.max_steps,
        stall_limit=exp.levinthal.stall_limit,
        noise_accept_prob=exp.levinthal.noise_accept_prob,
        init_strategy=exp.levinthal.init_strategy,  # type: ignore[arg-type]
        perturb_prob=exp.levinthal.perturb_prob,
        rng_seed=exp.random_seed,
    )
    trials = exp.runs if exp.runs > 0 else 1
    builder = LevinthalGameTableBuilder(
        landscape=landscape,
        baseline_state=baseline_state,
        players=players,
        search_config=search_config,
        trials=trials,
        rng_seed=exp.random_seed,
    )
    target_max_size = max_coalition_size or exp.max_coalition_size
    df = builder.build_table(max_size=target_max_size)
    output_path = Path(output_override) if output_override else exp.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    builder.to_csv(str(output_path))
    return output_path, len(df)


def _run_ethiraj_experiment(
    exp: ExperimentConfig,
    *,
    output_override: str | Path | None,
    max_coalition_size: Optional[int],
) -> Tuple[Path, int]:
    if not exp.ethiraj:
        raise ValueError("Ethiraj scenario requires ethiraj settings in config")
    true_modules = build_true_modules(exp.N, exp.ethiraj.true_modules)
    designer_modules = build_designer_modules(exp.N, exp.ethiraj.designer_modules)
    landscape = build_ethiraj_landscape(
        N=exp.N,
        K=exp.K,
        true_modules=true_modules,
        intra_bias=exp.ethiraj.intra_density,
        inter_bias=exp.ethiraj.inter_density,
        seed=exp.landscape_seed or exp.random_seed,
    )
    baseline_state = bitstring_to_array(exp.ethiraj.baseline_state, exp.N)
    # R ラン分のダイナミクスを独立に回し、それぞれの成熟設計候補 d* を集める
    run_count = exp.runs if exp.runs > 0 else 1
    mature_states: List[np.ndarray] = []
    for run_idx in range(run_count):
        population = EthirajFirmPopulation(
            landscape=landscape,
            designer_modules=designer_modules,
            num_firms=exp.ethiraj.firms,
            baseline_state=baseline_state,
            rng_seed=(exp.random_seed or 0) + run_idx,
        )
        sim_result = run_ethiraj_simulation(
            population=population,
            rounds=exp.ethiraj.rounds,
            recombination_interval=exp.ethiraj.recombination_interval,
            recombination_mode=exp.ethiraj.recombination_mode,
        )
        mature_states.append(sim_result.best_state)
    players_modules = (
        true_modules if exp.ethiraj.players_basis == "true" else designer_modules
    )
    prefix = "T" if exp.ethiraj.players_basis == "true" else "D"
    module_defs = [
        ModuleDefinition(name=f"{prefix}{idx}", bits=list(bits))
        for idx, bits in enumerate(players_modules)
    ]
    builder = EthirajGameTableBuilder(
        landscape=landscape,
        modules=module_defs,
        baseline_state=baseline_state,
        mature_states=mature_states,
        scenario_note=(
            f"scenario=ethiraj2004;true={len(true_modules)};"
            f"designer={len(designer_modules)};basis={exp.ethiraj.players_basis}"
        ),
    )
    target_max_size = max_coalition_size or exp.max_coalition_size
    df = builder.build_table(max_size=target_max_size)
    output_path = Path(output_override) if output_override else exp.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path, len(df)

def _build_players(exp: ExperimentConfig) -> List[LevinthalPlayer]:
    N = exp.N
    players_cfg = exp.levinthal.players if exp.levinthal else None
    players: List[LevinthalPlayer] = []
    if not players_cfg:
        for idx in range(N):
            players.append(LevinthalPlayer(player_id=str(idx), bits=[idx]))
        return players
    for idx, entry in enumerate(players_cfg):
        bits = entry.get("bits") or []
        int_bits = sorted({int(bit) for bit in bits})
        for bit in int_bits:
            if bit < 0 or bit >= N:
                raise ValueError(f"Player bits out of range: {bit} (N={N})")
        player_id = entry.get("id") or str(idx)
        players.append(LevinthalPlayer(player_id=player_id, bits=int_bits))
    return players

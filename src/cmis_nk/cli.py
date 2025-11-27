from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .pipeline import run_experiment, build_landscape
from .config_loader import load_experiment_config
from .visualization import (
    plot_game_table,
    plot_landscape_heatmap,
    plot_module_dependency_graph,
)
from .utils import bitstring_to_array
from .ethiraj2004 import build_true_modules, build_designer_modules, build_ethiraj_landscape


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nk-games",
        description="Generate NK-model game tables and run LF-style simulations",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Execute a simulation using a YAML config and emit a game table CSV",
    )
    run_parser.add_argument(
        "--config",
        default="config/lazer2007_baseline.yml",
        help="Path to experiment config YAML (default: config/lazer2007_baseline.yml)",
    )
    run_parser.add_argument(
        "--output",
        default=None,
        help="Optional override for output CSV path",
    )
    run_parser.add_argument(
        "--max-size",
        type=int,
        default=None,
        help="Limit coalition size evaluated (overrides config max_coalition_size)",
    )
    run_parser.set_defaults(func=_handle_run)

    plot_parser = subparsers.add_parser(
        "plot-table",
        help="Visualize a game table CSV for a given scenario",
    )
    plot_parser.add_argument(
        "--scenario",
        required=True,
        choices=["lazer2007", "levinthal1997", "ethiraj2004"],
        help="Scenario name (lazer2007 / levinthal1997 / ethiraj2004)",
    )
    plot_parser.add_argument(
        "--input",
        required=True,
        help="Path to a game table CSV (e.g., outputs/tables/...csv)",
    )
    plot_parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to save plot PNG (default: same as CSV)",
    )
    plot_parser.set_defaults(func=_handle_plot_table)

    plot_land_parser = subparsers.add_parser(
        "plot-landscape",
        help="Plot an NK landscape cross-section heatmap using a config",
    )
    plot_land_parser.add_argument("--config", required=True, help="Path to config YAML")
    plot_land_parser.add_argument(
        "--x-bits",
        nargs="+",
        type=int,
        default=[0],
        help="Bit indices to sweep along X axis (default: [0])",
    )
    plot_land_parser.add_argument(
        "--y-bits",
        nargs="+",
        type=int,
        default=[1],
        help="Bit indices to sweep along Y axis (default: [1])",
    )
    plot_land_parser.add_argument(
        "--baseline",
        default=None,
        help="Baseline bitstring for fixed bits (default: all zeros)",
    )
    plot_land_parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to save heatmap (default: outputs/figures/<scenario>)",
    )
    plot_land_parser.set_defaults(func=_handle_plot_landscape)

    plot_module_parser = subparsers.add_parser(
        "plot-modules",
        help="Plot module dependency networks for Ethiraj2004 configs",
    )
    plot_module_parser.add_argument("--config", required=True, help="Path to Ethiraj2004 config")
    plot_module_parser.add_argument(
        "--basis",
        choices=["true", "designer", "both"],
        default="both",
        help="Which module basis to plot",
    )
    plot_module_parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to save figures (default: outputs/figures/ethiraj2004)",
    )
    plot_module_parser.set_defaults(func=_handle_plot_modules)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


def _handle_run(args: argparse.Namespace) -> int:
    output_path, rows = run_experiment(
        args.config,
        output_override=args.output,
        max_coalition_size=args.max_size,
    )
    print(f"Saved {rows} coalition rows to {Path(output_path)}")
    return 0


def _handle_plot_table(args: argparse.Namespace) -> int:
    out_path = plot_game_table(args.input, args.scenario, args.output_dir)
    print(f"Saved plot to {out_path}")
    return 0


def _handle_plot_landscape(args: argparse.Namespace) -> int:
    exp = load_experiment_config(args.config)
    scenario = exp.scenario_type
    if scenario == "ethiraj2004":
        if not exp.ethiraj:
            raise ValueError("Ethiraj 設定が見つかりません")
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
    else:
        landscape = build_landscape(exp)
    baseline_bits = args.baseline if args.baseline is not None else "0" * exp.N
    baseline_state = bitstring_to_array(baseline_bits, exp.N)
    output_dir = Path(args.output_dir) if args.output_dir else Path("outputs/figures") / scenario
    out_path = plot_landscape_heatmap(
        landscape,
        args.x_bits,
        args.y_bits,
        baseline_state,
        output_dir,
        scenario,
    )
    print(f"Saved landscape heatmap to {out_path}")
    return 0


def _handle_plot_modules(args: argparse.Namespace) -> int:
    exp = load_experiment_config(args.config)
    if exp.scenario_type != "ethiraj2004" or not exp.ethiraj:
        raise ValueError("plot-modules は scenario.type=ethiraj2004 の設定でのみ使用できます")
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
    output_dir = Path(args.output_dir) if args.output_dir else Path("outputs/figures") / "ethiraj2004"
    saved_paths: list[Path] = []
    if args.basis in {"true", "both"}:
        saved_paths.append(
            plot_module_dependency_graph(
                true_modules,
                landscape.dependencies,
                module_label="T",
                output_dir=output_dir,
                filename="module_network_true.png",
                title="Ethiraj2004: 真のモジュール依存ネットワーク",
            )
        )
    if args.basis in {"designer", "both"}:
        saved_paths.append(
            plot_module_dependency_graph(
                designer_modules,
                landscape.dependencies,
                module_label="D",
                output_dir=output_dir,
                filename="module_network_designer.png",
                title="Ethiraj2004: デザイナーモジュール依存ネットワーク",
            )
        )
    for path in saved_paths:
        print(f"Saved module graph to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

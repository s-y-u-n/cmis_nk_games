from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .pipeline import run_experiment


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


if __name__ == "__main__":
    sys.exit(main())

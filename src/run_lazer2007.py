from __future__ import annotations

import argparse
from pathlib import Path

from cmis_nk.pipeline import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Lazer2007 NK simulation and build game table")
    parser.add_argument(
        "--config",
        default="config/lazer2007_baseline.yml",
        help="Path to experiment config YAML",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Override output CSV path",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=None,
        help="Limit coalition size evaluated",
    )
    args = parser.parse_args()

    output_path, rows = run_experiment(
        args.config,
        output_override=args.output,
        max_coalition_size=args.max_size,
    )
    print(f"Saved {rows} coalition rows to {Path(output_path)}")


if __name__ == "__main__":
    main()

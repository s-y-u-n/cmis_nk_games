# CMIS NK Games

This repository hosts source code, documentation and experiment outputs for the NK model simulations used in organization theory research. Unlike typical software projects, it also stores the reference paper that inspired the experiments and the playbook for turning the model into an iterative game between agents.

## Layout

- `src/` – simulation code, helper libraries, experiment scripts.
- `docs/` – primary references, derivations, and the "how to run as a dynamic game" guide.
- `config/` – parameter files describing landscapes, payoff matrices, and run settings.
- `outputs/` – generated data, plots, logs, and other artifacts (keep under version control only when needed).

## Design Docs

The implementation follows the layered architectures captured in:

- Lazer2007 set: `docs/requirements.md`, `docs/basic_design.md`, `docs/detailed_design.md`
- Levinthal1997 set: `docs/levinthal_requirements.md`, `docs/levinthal_basic_design.md`, `docs/levinthal_detailed_design.md`
- Ethiraj2004 set: `docs/ethiraj_requirements.md`, `docs/ethiraj_basic_design.md`, `docs/ethiraj_detailed_design.md`

Each document maps back to the "NKモデル採用報告書" policy and keeps the specification aligned with the code.

## Running the Lazer2007 Baseline

1. Install the Poetry environment (Python 3.11+):

   ```bash
   poetry install
   ```

2. Execute the baseline pipeline through the CLI (this uses the sub-network coalition protocol):

   ```bash
   poetry run nk-games run --config config/lazer2007_baseline.yml
   ```

   - Use `--output` to override the CSV path.
   - Use `--max-size` to cap coalition sizes without editing the YAML.

The resulting CSV lands in `outputs/tables/lazer2007_baseline.csv` and can be passed directly to Shapley-value calculators.  
For backward compatibility you can also run `poetry run python src/run_lazer2007.py ...`.

### Running the Levinthal1997 Baseline

```bash
poetry install  # if not already done
poetry run nk-games run --config config/levinthal1997_baseline.yml
```

This configuration evaluates all coalitions under the Levinthal constrained-local-search protocol and saves `outputs/tables/levinthal1997_baseline.csv`.

### Running the Ethiraj2004 Baseline

```bash
poetry install  # if not already done
poetry run nk-games run --config config/ethiraj2004_baseline.yml
```

This scenario simulates the modular misperception dynamics and exports `outputs/tables/ethiraj2004_baseline.csv`, where each coalition corresponds to a subset of modules (true or designer basis per config).

## Next Steps

- Drop the original Lazer & Friedman PDF plus HTML slides into `docs/papers/Lazer2007/`.
- Expand `config/` with new scenarios (different networks, skill mixes) and rerun the script to collect comparable tables.
- Add notebooks or tests as analysis needs grow.

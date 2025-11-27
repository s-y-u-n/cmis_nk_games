# 詳細設計（Levinthal 1997 シナリオ）

## 1. LocalSearchConfig / Engine
```text
@dataclass
class LocalSearchConfig:
    max_steps: int
    stall_limit: int
    noise_accept_prob: float
    trials: int
    baseline_state: np.ndarray
    init_strategy: Literal['random','baseline','perturb']
    rng_seed: int | None
```
- `baseline_state`: ビット権限を持たない部分を固定する参照形態。
- `LocalSearchEngine` 引数:
  - `landscape: NKLandscape`
  - `config: LocalSearchConfig`
  - `free_bits: Sequence[int]`
- `run_once(initial_state=None) -> LocalSearchResult`
  1. 初期状態を生成（`random_state` を baseline とマージ）。
  2. 反復：
     - `free_bits` からランダムに 1 ビット選択。
     - トグル案のフィットネスが向上すれば採用。
     - 改善なしの場合 `noise_accept_prob` で採用する場合あり。
     - `stall_counter` と `step` で停止判定。
  3. `LocalSearchResult(final_state, final_fitness, steps_taken)` を返す。

## 2. プレイヤ & 提携評価
```text
@dataclass
class LevinthalCoalitionEvaluator:
    landscape: NKLandscape
    search_config: LocalSearchConfig
    player_bits: dict[int, int]
    trials: int
```
- `player_bits`: プレイヤ ID -> ビット index（拡張で複数ビットも可）。
- `evaluate(coalition: tuple[int, ...]) -> tuple[float, float]`
  - `free_bits = union(player_bits[i] for i in coalition)`
  - `trials` 回 `LocalSearchEngine` を実行。
  - 平均値と標準偏差を返却。
- `baseline_state` への上書き:
  - `non_free_bits` は baseline を保持（= 権限なし）。
  - `free_bits` の初期値のみ乱数で変化可能。

## 3. ゲームテーブル生成
```text
class LevinthalGameTableBuilder:
    def __init__(..., evaluator: LevinthalCoalitionEvaluator, max_size: int | None)
    def build_table() -> pd.DataFrame
```
- `GameTableRecord` を流用し、`notes` に scenario 名、`params` に (N,K,trials,seeds) を JSON 文字列で格納。
- ループ:
  - `yield ()` (空提携) → フィットネスは baseline state の評価。
  - それ以降 `itertools.combinations` で列挙。

## 4. Config 拡張
`ExperimentConfig` へ以下追加:
```text
scenario_type: Literal['lazer2007','levinthal1997']
scenario_params: dict[str, Any]
```
- Levinthal 用追加フィールド：
  - `search`: {max_steps, stall_limit, noise_accept_prob, trials, baseline_state}
  - `players`: optional mapping（デフォルトは 1:1 bit mapping）
- Loader が scenario.type によって検証を切り替える。

## 5. CLI / Pipeline
- `run_experiment` 内で `if exp.scenario_type == 'lazer2007': ... elif == 'levinthal1997': ...`。
- Levinthal ルート：
  - `landscape = NKLandscape.from_random(...)`
  - `baseline_state` 文字列を numpy array に変換（長さ N）。
  - `player_map = default {i: i for i in range(N)}` unless override provided。
  - `LevinthalCoalitionEvaluator` + `LevinthalGameTableBuilder` 実行。
  - 出力 CSV には scenario 名と seeds を note。

## 6. テスト戦略
- `poetry run nk-games run --config config/levinthal1997_baseline.yml`
- 期待: `outputs/tables/levinthal1997_baseline.csv` が生成され、`size=0..N` のエントリを含む。
- 手動チェック: baseline state だけの場合（空提携）は baseline フィットネスに一致する。

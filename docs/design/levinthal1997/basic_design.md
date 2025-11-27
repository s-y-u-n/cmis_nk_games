# 基本設計（Levinthal 1997 シナリオ）

## 1. レイヤ構造
| レイヤ | モジュール | 役割 |
| --- | --- | --- |
| NKランドスケープ | `cmis_nk.landscape` | 既存クラスを再利用。N,K,依存構造を生成し、`evaluate(state)` を提供。 |
| ローカル探索 | `cmis_nk.local_search` | Levinthal 型の制約付き山登りを実装。探索自由度 S、最大ステップ、ノイズ等をパラメータ化。 |
| ゲーム定義 | `cmis_nk.levinthal1997.game_table` | プレイヤ = ビット対応、提携 S のみ探索可とするロジックを持ち、`evaluate_coalition(S)` を提供。 |
| 実験ランナー | `cmis_nk.pipeline` | YAML 設定を読み込み、シナリオ種別（`lazer2007`/`levinthal1997`）に応じて適切なビルダを呼び出す。 |
| 出力 | `cmis_nk.common.game_types` | `GameTableRecord` 形式を再利用し、Levinthal 用のテーブルカラムを拡張（scenario, NK params 等）。 |

## 2. データフロー
1. `load_experiment_config` が YAML を `ExperimentConfig` に読み込む（`scenario.type='levinthal1997'`, `levinthal` セクション等）。
2. `run_experiment` が scenario に応じて分岐。
   - `lazer2007`: Lazer 用 GameTableBuilder を使用。
   - `levinthal1997`: Levinthal 用 `LevinthalGameTableBuilder` を呼び出す。
3. Levinthal モードでは：
   - `NKLandscape` を生成（N, K, landscape_seed に基づき rugged landscape を構築）。
   - プレイヤ ID ↔ ビットは 1:1 対応（`LevinthalPlayer(player_id=str(i), bits=[i])`）を基本とする。
   - 各提携 S に対して `LocalSearchEngine` による制約付きローカル探索を M 回実行し、`v(S)` を推定。
   - 結果を `GameTableRecord` の配列として `pandas.DataFrame` にまとめ、CSV 出力。

## 3. 主要構造
- `LocalSearchConfig`
  - `max_steps`, `stall_limit`（= patience）, `noise_accept_prob`, `init_strategy`, `perturb_prob`, `rng_seed`。
- `LocalSearchEngine`
  - 引数: `landscape: NKLandscape`, `baseline_state: np.ndarray`, `free_bits: Sequence[int]`, `config: LocalSearchConfig`, `rng_seed`（任意）。
  - `run_trials(trials: int) -> list[LocalSearchResult]` が M 回分の制約付きローカル探索を実行。
  - `LocalSearchResult` は `final_state`, `final_fitness`（探索中に到達したベスト値）, `best_fitness`, `steps` を保持。
- `LevinthalGameTableBuilder`
  - 引数: `landscape`, `baseline_state`, `players: Sequence[LevinthalPlayer]`, `search_config`, `trials(M)`, `rng_seed`。
  - `build_table(max_size=None)` で全提携（またはサイズ制限付き）を列挙し、各提携に対し `LocalSearchEngine` を M 回実行して v(S) を推定。
  - `GameTableRecord` を再利用しつつ、`notes` に scenario 名や (N,K,trials) を記録。

## 4. 可視化方針

- ゲームテーブル CSV から |S| vs v(S) のプロットを生成し、「自由ビット数が多いほどどの程度フィットネスが上がるか」を可視化する。
  - タイトル例:「Levinthal1997: 自由ビット集合 S の適応力 v(S)」。
  - x 軸ラベル:「提携サイズ |S|（自由に変更可能なビット数）」。
  - y 軸ラベル:「v(S)（制約付きローカル探索の平均ベストフィットネス）」。
- CLI から `nk-games plot-table --scenario levinthal1997 --input <csv>` を実行することで、
  設計権限のサイズと性能の関係をグラフで確認できるようにする。

## 5. 設定ファイル方針
- `config/levinthal1997_baseline.yml`
  - `scenario.type = levinthal1997`
  - `landscape`: N, K, seeds。
  - `search`: {max_steps, stall_limit, noise_accept_prob, baseline_state（0/1 文字列） 等}。
  - `game_table`: {runs: M}（Levinthal シナリオでは M = runs と解釈）。
- 既存 Lazer config も `scenario.type = lazer2007` を追加して互換性を確保。

## 6. CLI 拡張
- `nk-games run --scenario levinthal1997 ...` も検討したが、YAML 側で scenario を切り替える方式を採用。
- CLI は共通で、内部で `ExperimentConfig.scenario_type` を評価して適切なルートを実行。

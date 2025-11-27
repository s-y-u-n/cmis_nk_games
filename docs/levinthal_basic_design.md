# 基本設計（Levinthal 1997 シナリオ）

## 1. レイヤ構造
| レイヤ | モジュール | 役割 |
| --- | --- | --- |
| NKランドスケープ | `cmis_nk.landscape` | 既存クラスを再利用。N,K,依存構造を生成し、`evaluate(state)` を提供。 |
| ローカル探索 | `cmis_nk.local_search` | Levinthal 型の制約付き山登りを実装。探索自由度 S、最大ステップ、ノイズ等をパラメータ化。 |
| ゲーム定義 | `cmis_nk.levinthal_game` | プレイヤ = ビット対応、提携 S のみ探索可とするロジックを持ち、`evaluate_coalition(S)` を提供。 |
| 実験ランナー | `cmis_nk.pipeline` | YAML 設定を読み込み、シナリオ種別（`lazer2007`/`levinthal1997`）に応じて適切なビルダを呼び出す。 |
| 出力 | `cmis_nk.game_table` | `GameTableRecord` 形式を再利用し、Levinthal 用のテーブルカラムを拡張（scenario, NK params 等）。 |

## 2. データフロー
1. `load_experiment_config` が YAML を `ExperimentConfig` に読み込む（scenario.type, scenario.params を追加）。
2. `run_experiment` が scenario に応じて分岐。
   - `lazer2007`: 既存 `GameTableBuilder` を使用。
   - `levinthal1997`: 新たに `LevinthalGameTableBuilder` を呼び出す。
3. Levinthal モードでは：
   - `NKLandscape` を生成。
   - `LevinthalPlayerMapping` がプレイヤ ID ↔ ビットを定義。
   - `LevinthalCoalitionEvaluator` が M 回の初期化＋ローカル探索を実施し `v(S)` を算出。
   - 結果を `pandas.DataFrame` にまとめて CSV 出力。

## 3. 主要構造
- `LocalSearchConfig`
  - `max_steps`, `stall_steps`, `noise_accept_prob`, `initial_state`, `baseline_state` など。
- `LocalSearchEngine`
  - `run(free_bits: Sequence[int]) -> LocalSearchResult`
  - `LocalSearchResult` が `final_state`, `final_fitness`, `history` を保持。
- `LevinthalGameTableBuilder`
  - `build_table()` で全提携を列挙。
  - 各提携に対し M 回 `LocalSearchEngine` を実行し平均値を計算。
  - 既存 `GameTableRecord` を再利用しつつ `notes` に scenario 名や seeds を記録。

## 4. 設定ファイル方針
- `config/levinthal1997_baseline.yml`
  - `scenario.type = levinthal1997`
  - `landscape`: N, K, seeds。
  - `search`: max_steps, stall_steps, trials(M), baseline_state（0/1 文字列）等。
  - `game_table`: runs/trials -> M。
- 既存 Lazer config も `scenario.type = lazer2007` を追加して互換性を確保。

## 5. CLI 拡張
- `nk-games run --scenario levinthal1997 ...` も検討したが、YAML 側で scenario を切り替える方式を採用。
- CLI は共通で、内部で `ExperimentConfig.scenario_type` を評価して適切なルートを実行。

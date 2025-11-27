# 基本設計

## 1. レイヤ構造とモジュール対応
| レイヤ | モジュール | 役割 |
| --- | --- | --- |
| A: NKランドスケープ | `cmis_nk.landscape` | NKLandscape クラスで環境生成・スコア評価を提供。skill/conflict フックを保持。 |
| B: エージェント/タスク | `cmis_nk.agents` | Agent/TaskAssignment データ構造。プレイヤーID、担当ビット、skill を管理。 |
| C: ネットワーク | `cmis_nk.networks` | NetworkFactory で line/complete/random/small-world グラフを生成。 |
| D: ダイナミクス | `cmis_nk.simulation` | SimulationEngine がエージェント状態を更新し履歴を返す。LFモードをプリセットで提供。 |
| E: ゲームテーブル | `cmis_nk.lazer2007.game_table` | GameTableBuilder が提携列挙、サブネットワーク構築、評価、CSV出力を行う。 |

## 2. データフロー
1. `NKLandscape` が `evaluate(state)` を提供。
2. `Agent` が担当ビット集合と skill 情報を持ち、初期戦略を生成。
3. `NetworkFactory` が `networkx.Graph` を返し、SimulationEngine が隣接情報を参照。
4. `SimulationEngine.run()` がランドスケープとネットワークを参照してラウンド更新、`SimulationResult` を返却。
5. `GameTableBuilder` がプレイヤー集合から提携を生成、各提携ごとに SimulationEngine を初期化し v(S) を計算、`pandas.DataFrame`/CSV に変換。

## 3. 拡張戦略
- **skill / conflict**: `NKLandscape` に `skill_profile`, `bit_skills`, `conflict_pairs` を設定し random 生成時に反映。
- **別論文設定**: 設定 JSON/YAML を `config/` に保存し、読み込んで `ScenarioConfig` へパースするユーティリティを追加予定。
- **ゲーム評価指標**: `GameValueProtocol` 抽象クラスを `game_table` に導入し、平均スコア・ベストスコアなどを切り替え可能にする。

## 4. 主要クラス概要
- `NKLandscape`:
  - 属性: `N`, `K`, `dependencies`, `tables`, `skill_profile`, `bit_skills`, `conflict_pairs`。
  - メソッド: `from_random(...)`, `evaluate(state)`, `best_neighbor(state, idx)` など。
- `Agent`:
  - 属性: `agent_id`, `name`, `bits`, `skill`, `player_id`。
  - メソッド: `initialize_state(N, seed)`。
- `SimulationEngine`:
  - 引数: `landscape`, `agents`, `graph`, `velocity`, `error_rate`, `rounds`, `rng`。
  - メソッド: `run(metric='mean_final')`。
  - 結果: `SimulationResult`（履歴、最良スコア、最終スコア、raw states）。
- `GameTableBuilder`:
  - 引数: `landscape`, `base_agents`, `base_graph`, `protocol`, `rounds`, `runs`。
  - メソッド: `evaluate_coalition(coalition_agents)`, `build_table()`, `to_csv(path)`。

## 5. 外部 I/F
- `config/*.yml` にケース設定を保存（N,K,network_type,etc）。
- CLI/Notebook から `scripts/run_lazer2007.py`（後続タスク）を経由してテーブル生成できる構成を想定。

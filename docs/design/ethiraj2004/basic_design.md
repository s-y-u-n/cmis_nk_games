# 基本設計（Ethiraj & Levinthal 2004 シナリオ）

## 1. モジュール構成とデータモデル
| レイヤ | モジュール | 役割 |
| --- | --- | --- |
| 真の構造 | `cmis_nk.ethiraj.landscape` | モジュール密度を指定した依存行列と局所貢献テーブルを生成。|
| デザイナー視点 | `cmis_nk.ethiraj.designer` | K 個の想定モジュールを生成し、モジュール性能 F_k を計算する。|
| ダイナミクス | `cmis_nk.ethiraj.dynamics` | L 社 × K モジュールの局所探索＋リコンビネーションを駆動。|
| ゲーム化 | `cmis_nk.ethiraj.game_table` | ベースライン d⁰ と成熟設計 d* から v(S) を算出。|
| CLI/統合 | `cmis_nk.pipeline` | scenario=ethiraj2004 を読み取り、上記コンポーネントを組み合わせて CSV を出力。|

## 2. 流れ
1. **ランドスケープ生成**: N, M, intra_density, inter_density, seeds を入力して `EthirajLandscape` (NKLandscape を再利用しつつモジュール毎に依存先を制御)。
2. **デザイナー視点**: K と分割方法（等分 or 設定ファイル）に従って `DesignerModules` を構築。
3. **初期化**: L 社分の設計行列 D ∈ {0,1}^{L×N} を乱数で生成。d⁰ はゼロベクトル or 設定で指定。
4. **ラウンド**: for t in 1..T:
   - 各企業が各モジュールごとにビットをランダム選択 → toggle → F_k 改善なら採用。
   - 既定頻度でリコンビネーション（firm/module/hybrid）を適用。
   - 履歴を蓄積（平均性能など）。
5. **スナップショット取得**: 終了時刻（または指定ラウンド）で各モジュールの最良企業を記録し、成熟設計 d* を決定（例: 全体性能が最大の企業）。
6. **ゲームテーブル**: プレイヤ＝モジュール集合 P を定義し、すべての S ⊆ P に対して d^S を構築し F(d^S)、v(S) を計算。

## 3. 主要クラス概要
- `EthirajLandscapeConfig`: N, M, intra_density, inter_density, seed。
- `EthirajLandscapeFactory`: `build()` -> `NKLandscape` + `module_assignments`。
- `DesignerModules`:
  - 属性: `designer_modules` (List[List[int]]), `true_modules`。
  - メソッド: `module_fitness(state, module_idx)`.
- `FirmPopulation`:
  - 属性: `states` (np.ndarray shape (L, N)), `performance_history`.
  - メソッド: `local_search_step()`, `recombine(strategy)`.
- `EthirajGameTableBuilder`:
  - 引数: `landscape`, `players_modules` (List[List[int]]), `baseline_state`, `mature_state`.
  - `build_table()` returns DataFrame with `v_value`, `absolute_fitness`, `notes`.

## 4. Config 項目
```yaml
scenario:
  type: ethiraj2004
  players: true_modules | designer_modules
landscape:
  M: 3
  intra_density: 0.8
  inter_density: 0.2
firms:
  count: 12
  rounds: 200
  recombination: module_level
  recombination_interval: 5
```

## 5. CLI 連携
- `ExperimentConfig` に `ethiraj` セクションを追加。
- `run_experiment` が scenario.type を判定し `run_ethiraj_experiment()` を呼ぶ。
- 出力ファイル: `outputs/tables/ethiraj2004_baseline.csv`。

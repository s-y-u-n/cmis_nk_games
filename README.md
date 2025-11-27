# CMIS NK Games

組織論で用いられる NK モデルを、複数の代表的な論文（Lazer2007 / Levinthal1997 / Ethiraj2004）に沿って実装し、
協力ゲームのゲームテーブル v(S) を生成するための実験基盤です。論文 PDF やモデリングスライド、設計書、ソースコードを
同一リポジトリ内で管理し、「仕様 ⇔ 実装 ⇔ 実験結果」が一望できる構成になっています。

## ディレクトリ構成

- `src/` – Python 実装（NK ランドスケープ、シナリオ別ダイナミクス、ゲームテーブル生成、CLI）。
- `docs/` – 論文 PDF・modeling.html・設計書などのドキュメント。
  - `docs/papers/` – 各論文の PDF / HTML スライド。
  - `docs/design/<scenario>/` – シナリオ別の要件定義・基本設計・詳細設計。
- `config/` – YAML 形式の実験設定ファイル（N, K, ネットワーク、ラウンド数、runs など）。
- `outputs/` – シミュレーション結果（ゲームテーブル CSV など）。Git 管理からは除外されています。

## 設計書（Design Docs）

実装は、シナリオごとに整理された設計書と 1 対 1 に対応するよう整理されています。

- Lazer2007: `docs/design/lazer2007/requirements.md`, `basic_design.md`, `detailed_design.md`
- Levinthal1997: `docs/design/levinthal1997/requirements.md`, `basic_design.md`, `detailed_design.md`
- Ethiraj2004: `docs/design/ethiraj2004/requirements.md`, `basic_design.md`, `detailed_design.md`

インデックスは `docs/README.md` を参照してください。これらは「NKモデル採用報告書」で定めた方針をコードレベルに落とし込んだもので、
アルゴリズム仕様（ステップ表）とクラス・関数名の対応が明示されています。

## 実行方法（CLI）

まず Poetry 環境をセットアップします（Python 3.11+）。

```bash
poetry install
```

### Lazer2007 ベースライン

```bash
poetry run nk-games run --config config/lazer2007_baseline.yml
```

- ネットワーク構造 × 探索/活用ダイナミクス（Lazer-Friedman 型）を再現し、
  プレイヤ=エージェントの協力ゲーム v(S) を推定します。
- 出力先（自動採番）: `outputs/tables/lazer2007/lazer2007_XXX.csv`
- `--output` で出力パスを直接指定できます。

### Levinthal1997 ベースライン

```bash
poetry run nk-games run --config config/levinthal1997_baseline.yml
```

- NK ランドスケープ上で、提携 S のみに設計自由度を与えた制約付きローカル探索を M 回実行し、
  v(S) = 平均到達フィットネスとしてゲームテーブルを生成します。
- 出力先: `outputs/tables/levinthal1997/levinthal1997_XXX.csv`

### Ethiraj2004 ベースライン

```bash
poetry run nk-games run --config config/ethiraj2004_baseline.yml
```

- モジュール誤認（真のモジュール構造 vs デザイナー構造）を持つ NK モデル上で、複数企業の
  局所探索＋リコンビネーション動学を実行し、成熟設計 d* に基づくモジュール単位のゲームテーブル v(S) を生成します。
- 出力先: `outputs/tables/ethiraj2004/ethiraj2004_XXX.csv`

## 今後の拡張のためのメモ

- `config/` に実験ケース（ネットワークタイプ、skill 差、conflict_pairs など）を追加することで、
  同じフレームワーク上で異なるシナリオ・パラメータのゲームテーブルを容易に比較できます。
- Shapley 値や相互作用指数の計算はこのリポジトリの外側（ノートブック等）で行う想定ですが、
  すべてのテーブルには scenario 名や N,K,seed などのメタ情報が `notes` カラムに埋め込まれているため、
  再現性の高い分析パイプラインが構成できます。

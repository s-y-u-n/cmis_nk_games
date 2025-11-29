# 詳細設計（Ethiraj & Levinthal 2004 シナリオ）

## 1. Config 拡張
```text
@dataclass
class EthirajSettings:
    true_modules: int
    designer_modules: int
    players_basis: Literal['true','designer']
    intra_density: float
    inter_density: float
    firms: int
    rounds: int
    recombination_interval: int
    recombination_mode: Literal['firm','module','hybrid']
    baseline_state: str
```
- `ExperimentConfig.ethiraj: Optional[EthirajSettings]` を追加。
- YAML: `scenario.type=ethiraj2004` と `ethiraj:` セクションを必須とする。

## 2. ランドスケープ生成
- `EthirajLandscapeFactory`:
```python
def build(N, M, intra, inter, seed) -> tuple[NKLandscape, list[list[int]]]
```
  - 各モジュール `M_k` の要素数をできるだけ均等に分配。
  - 依存関係: `K_i` = neighbors sampled prioritizing same module with prob `intra`, otherwise cross-module `inter` density。
  - 各ビットの依存候補から `NKLandscape` を構築（`dependencies`, `tables`）。
  - 戻り値: `NKLandscape`, `true_modules` (list of bit indices per module)。

## 3. デザイナー構造
- `build_designer_modules(N, K)`
  - 均等割り / YAML 指定をサポート。
  - `designer_modules: list[list[int]]`。
  - `players_basis` が `designer` の場合はこちらをプレイヤ集合として使用。

## 4. Dynamics
### Data structures
```python
@dataclass
class EthirajFirmPopulation:
    states: np.ndarray  # shape (L, N)
    module_assignments: list[list[int]]  # designer modules
    landscape: NKLandscape
```
- `module_fitness(state, module_idx)` = 平均 `f_i` over module bits。
- `local_search_step()`:
  1. For each firm ℓ and module D_k:
     - pick `bit` in D_k at random.
     - toggle bit; compute `module_fitness` using landscape (`evaluate_module`).
     - accept if improved.
- `recombine(mode, top_fraction)`:
  - `firm`: rank firms by `F(state)`; pick donors to copy random module.
  - `module`: for each module, select firm with best module fitness and copy module bits into others with prob.
  - `hybrid`: combination of above.

Implementation simplification: use deterministic copy from best firm(s) each interval.

### Simulation run
```python
def run_simulation(population, rounds, recomb_interval, mode) -> EthirajSimulationResult:
    history = []
    for t in range(rounds):
        population.local_search_step()
        if (t+1) % recomb_interval == 0:
            population.recombine(mode)
        history.append(population.metrics())
    return EthirajSimulationResult(best_state, baseline_state, history)
```
- `best_state` = state with highest global fitness.
- `baseline_state` = zeros vector or config-provided string.

## 5. ゲームテーブル
- `EthirajGameTableBuilder`:
```python
class EthirajGameTableBuilder:
    def __init__(landscape, modules, baseline_state, mature_state): ...
    def build_table():
        for coalition in all subsets modules:
            state = baseline_state.copy()
            for module in coalition:
                for bit in module:
                    state[bit] = mature_state[bit]
            F_dS = landscape.evaluate(state)
            v_value = F_dS - baseline_fitness
```
- `GameTableRecord` (from `cmis_nk.common.game_types`) reused with `mean_value = v_value`, `std_value=0`, `notes` storing scenario+module basis。

### 5.1 ゲームテーブル生成フロー（フローチャート）

Ethiraj シナリオにおけるゲームテーブル生成の処理フローを、アルゴリズム的なフローチャートとして整理すると以下のようになる。

```mermaid
flowchart TD
    A["Config 読み込み<br/>N, M, K, L, rounds, players_basis など"] --> B["ランドスケープ生成<br/>NKLandscape, true_modules"]
    B --> C["デザイナーモジュール生成<br/>designer_modules"]
    C --> D["企業集団初期化<br/>EthirajFirmPopulation"]
    D --> E["ダイナミクス実行<br/>run_ethiraj_simulation"]
    E --> F["成熟設計 d* 取得<br/>best_state"]
    A --> G["ベースライン設計 d0 生成<br/>baseline_state"]
    G --> H["F(d0) 計算<br/>baseline_fitness"]
    F --> I["プレイヤーモジュール集合 P を選択<br/>true_modules または designer_modules"]
    H --> J["全提携 C を列挙"]
    I --> J
    J --> K["各提携 C について<br/>状態 dC を構成<br/>d0をコピーし C属モジュール置換"]
    K --> L["F(dC) を評価"]
    L --> M["v(C) = F(dC) - F(d0)"]
    M --> N["GameTableRecord を追加<br/>coalition_id, members, size など"]
    N --> O{"全提携を<br/>処理済みか?"}
    O -->|いいえ| J
    O -->|はい| P["DataFrame に集約し<br/>CSV に保存"]
```

このフローに従うことで、「(d⁰, d*) とプレイヤーモジュール集合 P」から、各提携 C の v(C) を系統的に計算してゲームテーブルを構築する。

### 5.2 ゲームテーブル生成フロー（意味的フローチャート）

同じ処理を、Ethiraj & Levinthal (2004) の「ほぼ分解可能システム＋モジュール誤認」の組織設計ストーリーとして意味的に読み替えたフローチャートは次のとおり。

```mermaid
flowchart TD
    A["ケース設定を決める<br/>製品・組織システムの規模 N、<br/>真のモジュール数 M、<br/>設計者が信じるモジュール数 K、<br/>企業数 L、適応ラウンド数など"] --> B["現実の結合構造を仮定<br/>真のモジュール構造と依存関係を設定"]
    A --> C["設計者が頭の中で描いている<br/>（かもしれない）モジュール分割を設定<br/>K 個のデザイナーモジュール"]

    B --> D["真の結合構造の上で<br/>各ビット組合せに対する性能 F を定義"]
    C --> E["設計者がモジュール単位で<br/>改善・移植を考えるための<br/>『見かけのモジュール構造』が決まる"]

    A --> F["ベースライン設計 d⁰ を決める<br/>＝現行の製品・組織設計"]
    F --> G["d⁰ の性能 F(d⁰) を測る"]

    B --> H["複数企業 L 社を用意し<br/>それぞれに初期設計を割り当てる"]
    C --> H

    H --> I["各企業が『自分のモジュール認識』に基づいて<br/>局所探索を行う<br/>（モジュールごとにレバーを少しずつ変え<br/>性能が良くなれば採用）"]

    I --> J["一定ラウンドごとに<br/>他社のモジュールを真似る／組み合わせる<br/>リコンビネーションを行う"]

    J --> K["十分な期間が経過した後<br/>最も高い性能を達成した企業の設計を<br/>成熟設計 d* とみなす"]

    K --> L["ゲームで評価するプレイヤーモジュール集合 P を決める<br/>（真のモジュールを単位にするか、<br/>設計者の誤認モジュールを単位にするか）"]

    G --> M["P の各モジュール集合 C について<br/>『どのモジュール群を作り直すか』という<br/>投資シナリオを考える"]
    L --> M

    M --> N["ベースライン設計 d⁰ を出発点として<br/>C に属するモジュールだけを<br/>成熟設計 d* の内容に置き換えた設計 d^C を作る"]

    N --> O["d^C の性能 F(d^C) を測る"]

    O --> P["ベースラインからの性能差<br/>v(C) = F(d^C) − F(d⁰) を計算<br/>＝そのモジュール群をきちんと設計し直したときの<br/>期待リターン"]

    P --> Q["モジュール集合 C ごとに<br/>『どの組み合わせを改善すべきか』の<br/>価値をゲームテーブルに記録する"]
```

この意味的フローチャートでは、d⁰ / d* をそれぞれ「現行設計」と「設計者のモジュール認識のもとで長期に適応した設計」として解釈し、  
「どのモジュール集合を優先的に作り直せば、システム性能がどれだけ改善するか」を投資判断の観点から読むことを意図している。

## 6. Pipeline Integration
- Add `_run_ethiraj_experiment(exp)` in `pipeline.py` analogous to other scenario branches.
- Steps:
  1. Build landscape + true modules.
  2. Build designer modules.
  3. Initialize firm population (random states respecting baseline if desired).
  4. Run simulation for `ethiraj.rounds`.
  5. Determine mature state (global best) and baseline state.
  6. Choose player modules (true or designer) for coalition evaluation.
  7. Build `EthirajGameTableBuilder` and export CSV.

## 7. 出力
- Path: `outputs/tables/ethiraj2004_baseline.csv`.
- Notes include scenario name, M/K, recombination_mode, and seeds.
- Optionally store time-series metrics to `outputs/logs/ethiraj2004_baseline_history.csv`.

## 8. 実世界での読み替え

- `true_modules` は、現実の技術システムや組織プロセスの「実際の結合構造」に対応し、`designer_modules` は設計者が頭の中で想定している分割単位を表す。
- ダイナミクスで生成される d⁰ / d* は、それぞれ「ベースライン設計」と「設計者のモジュール認識のもとで長期に適応した設計」として解釈できる。
- ゲームテーブルのプレイヤ（modules）は、現実には「どのモジュール群をちゃんと設計し直せば、全体性能がどれだけ伸びるか」を評価するための単位であり、
  v(S) = F(d^S) − F(d⁰) は、そのモジュール集合 S に対する設計投資の“期待リターン”として読める。

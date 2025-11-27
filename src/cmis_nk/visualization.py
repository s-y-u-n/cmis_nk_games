from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Sequence, List, Dict

import matplotlib.pyplot as plt
import japanize_matplotlib  # noqa: F401  # フォントを日本語対応にする
import pandas as pd
import numpy as np
import networkx as nx


ScenarioType = Literal["lazer2007", "levinthal1997", "ethiraj2004"]


def plot_game_table(
    csv_path: str | Path,
    scenario: ScenarioType,
    output_dir: str | Path | None = None,
) -> Path:
    """ゲームテーブル CSV を読み込み、シナリオ別に基本的な可視化を生成する。

    - x 軸: 提携サイズ |S|
    - y 軸: v(S) または v_value

    実世界の解釈が分かるように、タイトルとラベルをシナリオごとに切り替える。
    """

    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)
    if "size" not in df.columns:
        raise ValueError("CSV に 'size' カラムがありません")

    # v(S) 列名の決定
    if "mean_value" in df.columns:
        value_col = "mean_value"
    elif "v_value" in df.columns:
        value_col = "v_value"
    else:
        raise ValueError("CSV に v(S) を表す列 (mean_value / v_value) が見つかりません")

    # 描画用の基本情報
    grouped = df.groupby("size")[value_col]
    sizes = sorted(grouped.groups.keys())
    means = [grouped.get_group(s).mean() for s in sizes]
    stds = [grouped.get_group(s).std() for s in sizes]

    # シナリオ別のラベル
    if scenario == "lazer2007":
        title = "Lazer2007: エージェント集合 S の探索性能 v(S)"
        ylabel = "v(S)（最終ラウンド平均フィットネス）"
        xlabel = "提携サイズ |S|（参加エージェント数）"
    elif scenario == "levinthal1997":
        title = "Levinthal1997: 自由ビット集合 S の適応力 v(S)"
        ylabel = "v(S)（制約付きローカル探索の平均ベストフィットネス）"
        xlabel = "提携サイズ |S|（自由に変更可能なビット数）"
    elif scenario == "ethiraj2004":
        title = "Ethiraj2004: モジュール集合 S の貢献度 v(S)"
        ylabel = "v(S) = F(d^S) − F(d⁰)"
        xlabel = "提携サイズ |S|（改善されたモジュール数）"
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.errorbar(sizes, means, yerr=stds, fmt="o-", capsize=4)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle=":", alpha=0.4)

    if output_dir is None:
        # テーブルとは別ディレクトリに保存する（scenario ごとの figures 配下）
        output_dir = Path("outputs/figures") / scenario
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{csv_path.stem}_by_size.png"
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_lazer_dynamics(
    history: Sequence[Dict[str, float]],
    output_dir: str | Path,
    label: str = "mean/max",
) -> Path:
    """Lazer2007 用: ラウンドごとの平均・最大スコアの推移をプロットする。"""

    if not history:
        raise ValueError("history が空です")
    rounds = [h["round"] for h in history]
    mean_scores = [h["mean_score"] for h in history]
    max_scores = [h["max_score"] for h in history]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(rounds, mean_scores, label="平均スコア")
    ax.plot(rounds, max_scores, label="最大スコア", linestyle="--")
    ax.set_title("Lazer2007: ネットワーク上の探索/活用ダイナミクス")
    ax.set_xlabel("ラウンド")
    ax.set_ylabel("フィットネス V")
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.4)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "lazer2007_dynamics.png"
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_levinthal_path(
    best_fitness_history: Sequence[float],
    output_dir: str | Path,
) -> Path:
    """Levinthal1997 用: 制約付きローカル探索中のベストフィットネス推移をプロットする。"""

    if not best_fitness_history:
        raise ValueError("best_fitness_history が空です")
    steps = np.arange(len(best_fitness_history))

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(steps, best_fitness_history, label="ベストフィットネス")
    ax.set_title("Levinthal1997: 制約付きローカル探索中のフィットネス推移")
    ax.set_xlabel("ステップ")
    ax.set_ylabel("ベストフィットネス V")
    ax.grid(True, linestyle=":", alpha=0.4)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "levinthal1997_local_search.png"
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_ethiraj_dynamics(
    history: Sequence[Dict[str, float]],
    output_dir: str | Path,
) -> Path:
    """Ethiraj2004 用: マルチ企業ダイナミクスの平均/最大フィットネス推移をプロットする。"""

    if not history:
        raise ValueError("history が空です")
    rounds = [h["round"] for h in history]
    mean_values = [h["mean_fitness"] for h in history]
    max_values = [h["max_fitness"] for h in history]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(rounds, mean_values, label="平均フィットネス")
    ax.plot(rounds, max_values, label="最大フィットネス", linestyle="--")
    ax.set_title("Ethiraj2004: モジュール誤認下での企業集団ダイナミクス")
    ax.set_xlabel("ラウンド")
    ax.set_ylabel("フィットネス V")
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.4)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ethiraj2004_dynamics.png"
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_landscape_heatmap(
    landscape,
    x_bits: Sequence[int],
    y_bits: Sequence[int],
    baseline_state: np.ndarray,
    output_dir: Path,
    scenario: str,
) -> Path:
    """指定したビット群の断面をヒートマップで可視化する。"""

    if not x_bits or not y_bits:
        raise ValueError("x_bits と y_bits は 1 つ以上指定してください")
    if len(baseline_state) != landscape.N:
        raise ValueError("baseline_state の長さが N と一致していません")

    x_levels = 2 ** len(x_bits)
    y_levels = 2 ** len(y_bits)
    heatmap = np.zeros((y_levels, x_levels))

    base = baseline_state.astype(np.int8)
    for xi in range(x_levels):
        for yi in range(y_levels):
            state = base.copy()
            for idx, bit in enumerate(x_bits):
                state[bit] = (xi >> idx) & 1
            for idx, bit in enumerate(y_bits):
                state[bit] = (yi >> idx) & 1
            heatmap[yi, xi] = landscape.evaluate(state)

    x_labels = [format(i, f"0{len(x_bits)}b") for i in range(x_levels)]
    y_labels = [format(i, f"0{len(y_bits)}b") for i in range(y_levels)]

    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(heatmap, origin="lower", cmap="viridis")
    ax.set_xticks(range(x_levels))
    ax.set_xticklabels(x_labels)
    ax.set_yticks(range(y_levels))
    ax.set_yticklabels(y_labels)
    ax.set_xlabel(f"X軸ビット {list(x_bits)} の組み合わせ (2進)" )
    ax.set_ylabel(f"Y軸ビット {list(y_bits)} の組み合わせ (2進)" )
    ax.set_title(f"{scenario}: NKランドスケープ断面")
    fig.colorbar(im, ax=ax, label="フィットネス F(d)")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"landscape_heatmap_{scenario}.png"
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_module_dependency_graph(
    modules: Sequence[Sequence[int]],
    dependencies: Sequence[Sequence[int]],
    module_label: str,
    output_dir: Path,
    filename: str,
    title: str,
) -> Path:
    """モジュール間依存（どのモジュールがどのモジュールに影響するか）を可視化する。"""

    module_map: Dict[int, int] = {}
    for idx, bits in enumerate(modules):
        for bit in bits:
            module_map[bit] = idx
    G = nx.DiGraph()
    for idx in range(len(modules)):
        G.add_node(idx)
    for target_bit, deps in enumerate(dependencies):
        tgt_module = module_map.get(target_bit)
        if tgt_module is None:
            continue
        for dep_bit in deps:
            src_module = module_map.get(dep_bit)
            if src_module is None:
                continue
            if G.has_edge(src_module, tgt_module):
                G[src_module][tgt_module]["weight"] += 1
            else:
                G.add_edge(src_module, tgt_module, weight=1)

    pos = nx.circular_layout(G)
    edge_weights = [G[u][v]["weight"] for u, v in G.edges()]
    edge_widths = [1 + w / 2 for w in edge_weights]

    fig, ax = plt.subplots(figsize=(6, 4))
    nx.draw_networkx_nodes(G, pos, node_color="#fdd835", ax=ax)
    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.7, arrows=True, ax=ax)
    labels = {idx: f"{module_label}{idx}" for idx in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, ax=ax)
    ax.set_title(title)
    ax.axis("off")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / filename
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path

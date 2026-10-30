"""从已有宝藏博弈结果绘制即时收益排序优化图，不重新运行搜索。"""

import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import math
import os
from pathlib import Path
import json
import statistics
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".cache" / "matplotlib"))

from src.visualization.common import BLUE, GRAY, GREEN, INK, LIGHT, ORANGE, configure

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np

ORDERS = ("input", "reverse", "gain")
COLORS = (GRAY, BLUE, ORANGE, GREEN)
LABELS = ("Minimax\n输入顺序", "Alpha-Beta\n输入顺序", "Alpha-Beta\n逆序", "Alpha-Beta\ngain 排序")
CONFIGS = (("minimax", "input"), *(('alpha_beta', order) for order in ORDERS))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def trace_branches(events):
    """根子树的计数取自真实访问事件；根下界由回传值累计更新。"""
    branches, active, alpha = [], None, -math.inf
    for event in events:
        kind, depth = event["event"], event["depth"]
        if kind == "visit" and depth == 1:
            assert active is None
            incoming = event["details"].get("alpha")
            if incoming is not None:
                assert incoming == alpha or (incoming == "-Infinity" and alpha == -math.inf)
            active = {"action": event["state"]["position_a"], "visits": 0, "evaluations": 0}
            branches.append(active)
        if active is not None and depth >= 1:
            active["visits"] += kind == "visit"
            active["evaluations"] += kind == "evaluate"
        if kind == "return" and depth == 1:
            assert active is not None
            alpha = max(alpha, event["details"]["value"])
            active["alpha_after"] = alpha
            active = None
    assert active is None
    return branches


def load_data(root):
    metadata = read_json(root / "metadata.json")
    with (root / "timing_runs.csv").open(encoding="utf-8-sig", newline="") as stream:
        timing = [row for row in csv.DictReader(stream) if row["phase"] == "game"]
    data = {}
    counters = ("nodes_visited", "nodes_expanded", "nodes_generated", "evaluation_calls",
                "cutoff_events", "pruned_branches")
    for depth in (2, 4):
        for algorithm in ("minimax", "alpha_beta"):
            for order in ORDERS:
                folder = root / f"depth_{depth}" / f"{order}_order" / algorithm
                result = read_json(folder / "result.json")
                events = read_json(folder / "trace.json")
                with (folder / "metrics.csv").open(encoding="utf-8-sig", newline="") as stream:
                    rows = list(csv.DictReader(stream))
                assert len(rows) == 1
                row = rows[0]
                counts = {key: int(row[key]) for key in counters}
                repeats = [t for t in timing if int(t["depth_limit"]) == depth
                           and t["move_order"] == order and t["algorithm"] == algorithm]
                assert len(repeats) == int(row["repeat_count"]) == 3
                selected = sorted(repeats, key=lambda t: (float(t["elapsed_seconds"]), int(t["repetition"])))
                selected = selected[1]
                assert selected["is_median"] == "True"
                assert int(selected["repetition"]) == int(row["selected_repetition"])
                assert all(t["collect_trace"] == row["collect_trace"] == "True" for t in repeats)
                assert float(selected["elapsed_seconds"]) == float(row["elapsed_seconds"])
                assert all(int(t[key]) == counts[key] for t in repeats for key in counters)
                assert counts["nodes_visited"] == sum(e["event"] == "visit" for e in events)
                assert counts["evaluation_calls"] == sum(e["event"] == "evaluate" for e in events)
                cuts = [e for e in events if e["event"] == "cutoff"]
                assert len(cuts) == counts["cutoff_events"]
                assert sum(e["details"]["pruned_branches"] for e in cuts) == counts["pruned_branches"]
                assert all(e["details"]["alpha"] >= e["details"]["beta"] for e in cuts)
                expected = metadata["inputs"]["expected"][str(depth)]
                assert result["best_value"] == expected["best_value"] == float(row["best_value"])
                assert result["best_action"] == expected["best_target"]
                branches = trace_branches(events)
                assert len(branches) == 4
                assert 1 + sum(b["visits"] for b in branches) == counts["nodes_visited"]
                assert sum(b["evaluations"] for b in branches) == counts["evaluation_calls"]
                data[depth, algorithm, order] = {
                    **counts, "time_us": float(row["elapsed_seconds"]) * 1e6,
                    "repeats_us": [float(t["elapsed_seconds"]) * 1e6 for t in repeats],
                    "branches": branches, "result": result,
                }
        for key in counters:
            assert len({data[depth, "minimax", order][key] for order in ORDERS}) == 1
    return data


def reduction(baseline, candidate):
    return (baseline - candidate) / baseline * 100


def percent_label(value):
    return str(Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def tidy(ax, ylabel=""):
    ax.set_ylabel(ylabel)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=LIGHT, linewidth=.7)


def workload(data):
    fig, axes = plt.subplots(2, 2, figsize=(12.4, 8), layout="constrained")
    for col, depth in enumerate((2, 4)):
        for row, (key, name) in enumerate((("nodes_visited", "访问节点数"),
                                            ("evaluation_calls", "叶子评价次数"))):
            ax = axes[row, col]
            values = [data[depth, *config][key] for config in CONFIGS]
            patches = ax.bar(range(4), values, color=COLORS, width=.62)
            labels = [str(values[0]), *(f"{n}\n−{percent_label(reduction(values[0], n))}%" for n in values[1:])]
            ax.bar_label(patches, labels=labels, fontsize=10, padding=5, linespacing=1.5)
            ax.set_xticks(range(4), LABELS, fontsize=9)
            ax.set_ylim(0, max(values) * 1.28)
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            tidy(ax, f"H={depth} · {name}")
    return fig


def incremental(data):
    values, deltas = [], []
    for config in CONFIGS[:3]:
        percentages, differences = [], []
        for depth in (2, 4):
            for key in ("nodes_visited", "evaluation_calls"):
                base, gain = data[depth, *config][key], data[depth, "alpha_beta", "gain"][key]
                percentages.append(reduction(base, gain))
                differences.append(base - gain)
        values.append(percentages)
        deltas.append(differences)
    fig, ax = plt.subplots(figsize=(10.6, 4.6), layout="constrained")
    image = ax.imshow(values, cmap="Greens", vmin=0, vmax=50, aspect="auto")
    for row in range(3):
        for col in range(4):
            ax.text(col, row, f"{percent_label(values[row][col])}%\n−{deltas[row][col]} 次",
                    ha="center", va="center", fontsize=13, linespacing=1.7,
                    color="white" if values[row][col] >= 34 else INK)
    ax.set_xticks(range(4), ["H=2\n访问节点", "H=2\n叶子评价", "H=4\n访问节点", "H=4\n叶子评价"])
    ax.set_yticks(range(3), ["Minimax / 输入顺序", "Alpha-Beta / 输入顺序", "Alpha-Beta / 逆序"])
    ax.set_ylabel("gain 方案的比较基线")
    ax.axvline(1.5, color="white", linewidth=3)
    ax.set_xticks(np.arange(-.5, 4, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 3, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.colorbar(image, ax=ax, shrink=.9, label="gain 相对行基线的减少率 (%)")
    return fig


def mechanism(data):
    fig, axes = plt.subplots(2, 2, figsize=(12.6, 8), layout="constrained")
    for col, depth in enumerate((2, 4)):
        ax = axes[0, col]
        for order, color, label, marker in zip(ORDERS, COLORS[1:], ("输入顺序", "逆序", "gain 排序"), ("o", "s", "D")):
            branches = data[depth, "alpha_beta", order]["branches"]
            visits = 1 + np.cumsum([b["visits"] for b in branches])
            alpha = [b["alpha_after"] for b in branches]
            ax.step(visits, alpha, where="post", color=color, linewidth=1.8)
            ax.plot(visits, alpha, marker, color=color, label=label,
                    markersize=10 if order == "input" else 7 if order == "reverse" else 6,
                    markerfacecolor="none" if order == "input" else color,
                    markeredgewidth=1.5)
        ax.set_xlabel("累计访问节点数（含根节点）")
        ax.set_xlim(0, max(data[depth, "alpha_beta", o]["nodes_visited"] for o in ORDERS) + 2)
        ax.set_ylim((-4.8, -.3) if depth == 2 else (-8, 4))
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        tidy(ax, f"H={depth} · 根节点下界 α")
        ax.legend(fontsize=9, loc="lower right")
        ax = axes[1, col]
        for index, ((algorithm, order), color, label) in enumerate(zip(CONFIGS, COLORS, LABELS)):
            counts = {b["action"]: b["visits"] for b in data[depth, algorithm, order]["branches"]}
            positions = np.arange(4) + (index - 1.5) * .19
            patches = ax.bar(positions, [counts[f"T{i}"] for i in range(1, 5)], width=.18,
                             color=color, label=label.replace("\n", " / "))
            ax.bar_label(patches, fontsize=9, padding=3)
        ax.set_xticks(range(4), [f"T{i}" for i in range(1, 5)])
        ax.set_xlabel("根节点的首步目标（按目标对齐）")
        ax.set_ylim(0, max(b["visits"] for b in data[depth, "minimax", "input"]["branches"]) * 1.48)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        tidy(ax, f"H={depth} · 各根子树访问节点数")
        ax.legend(ncols=2, fontsize=8, loc="upper right")
    return fig


def runtime(data):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.3), layout="constrained")
    configs = (*CONFIGS, ("minimax", "gain"))
    names = [label.replace("\n", " / ") for label in LABELS] + ["Minimax / gain（辅助对照）"]
    colors = (*COLORS, GRAY)
    for ax, depth in zip(axes, (2, 4)):
        maximum = max(max(data[depth, *c]["repeats_us"]) for c in configs)
        for index, (config, color) in enumerate(zip(configs, colors)):
            item = data[depth, *config]
            y = 4 - index
            samples = item["repeats_us"]
            ax.hlines(y, min(samples), max(samples), color=color, alpha=.55, linewidth=2)
            ax.scatter(samples, y + np.array([-.10, 0, .10]), c=color, alpha=.6, s=28, zorder=3)
            ax.scatter([statistics.median(samples)], [y], marker="D", c=color,
                       edgecolors="white", linewidths=.7, s=67, zorder=4)
            ax.text(maximum * 1.055, y, f"{item['time_us']:.1f}", ha="left", va="center", fontsize=11)
        ax.axhline(.5, color=LIGHT, linestyle="--", linewidth=1)
        ax.set_yticks(range(4, -1, -1), names, fontsize=9)
        ax.set_ylim(-.55, 5)
        ax.set_xlim(0, maximum * 1.25)
        ax.set_xlabel(f"H={depth} · 博弈搜索耗时 (µs)")
        ax.text(maximum * 1.055, 4.6, "中位数", ha="left", va="center", fontsize=10)
        ax.set_axisbelow(True)
        ax.grid(axis="x", color=LIGHT, linewidth=.7)
        ax.legend(handles=[Line2D([], [], marker="o", linestyle="", color=GRAY, markersize=5, label="三轮原始值"),
                           Line2D([], [], marker="D", linestyle="", color=GRAY, markersize=6, label="中位数"),
                           Line2D([], [], color=GRAY, linewidth=2, label="最小–最大值")],
                  loc="upper left", fontsize=8, ncols=3)
    return fig



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=PROJECT_ROOT / "results/problem4_treasure_game")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "report/figures/gain_order_optimization")
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    if args.dpi < 72:
        parser.error("--dpi must be at least 72")
    root, output = args.results.resolve(), args.output.resolve()
    if output.is_relative_to(root):
        parser.error("output must be outside the input results directory")
    original = fingerprint(root)
    data = load_data(root)
    configure()
    output.mkdir(parents=True, exist_ok=True)
    figures = (("18_gain_search_workload", workload),
               ("19_gain_incremental_reduction", incremental),
               ("20_gain_bound_and_subtree_work", mechanism),
               ("21_gain_runtime_repetitions", runtime))
    for name, render in figures:
        fig = render(data)
        fig.savefig(output / f"{name}.png", dpi=args.dpi, bbox_inches="tight", pad_inches=.16)
        plt.close(fig)
        print(f"Saved {name}.png", flush=True)
    assert original == fingerprint(root), "Input results changed during plotting"
    print("Validated 12 configurations, 36 timing samples and all traces; input results unchanged.")


if __name__ == "__main__":
    main()

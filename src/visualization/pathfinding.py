"""迷宫、加权路径、启发函数与搜索开销图。"""

from heapq import heappop, heappush

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch, Rectangle

from .common import BLUE, GREEN, ORANGE, GRAY, TIME_NOTE, bars, finish, grid, route, style_axis
from .data import Results


def replay_frontier(events: list[dict]) -> list[dict]:
    """用 discover/visit/stale 事件恢复实际优先队列；不重新运行 A*。"""
    queue, best, visited, snapshots = [], {}, [], []
    serial = 0
    current = None

    def save() -> None:
        if current is not None:
            valid = [entry for entry in sorted(queue) if entry[3] == best[entry[2]]]
            snapshots.append({"visited": visited.copy(), "current": current, "frontier": valid})

    for event in events:
        state = tuple(event["state"])
        details = event["details"]
        if event["event"] == "discover":
            best[state] = details["g"]
            heappush(queue, (details["f"], serial, state, details["g"], details["h"]))
            serial += 1
        elif event["event"] in ("visit", "stale"):
            if event["event"] == "visit":
                save()
            entry = heappop(queue)
            if entry[2] != state or entry[3] != details["g"]:
                raise ValueError("A* trace does not preserve priority-queue order")
            if event["event"] == "visit":
                visited.append(state)
                current = state
    save()
    return snapshots


def maze_visits(data: Results):
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.5), layout="constrained")
    cells = data.case(1)["grid"]
    for ax, mode, label in zip(axes, ("zero", "manhattan"), ("h=0", "曼哈顿启发")):
        events = data.read(1, f"astar_{mode}", "trace.json")
        visits = [event["state"] for event in events if event["event"] == "visit"]
        result = data.read(1, f"astar_{mode}", "result.json")
        grid(ax, cells)
        for row, col in visits:
            ax.add_patch(Rectangle((col-.5, row-.5), 1, 1, facecolor="#dcfce7", alpha=.7, zorder=1))
        route(ax, result["path"])
        for index, (row, col) in enumerate(visits, 1):
            ax.text(col+.25, row+.28, str(index), ha="center", va="center", fontsize=9, zorder=5,
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 1, "alpha": .8})
        ax.set_title(f"{label}：访问 {len(visits)} 个节点，最短路径 {int(result['cost'])} 步")
    return finish(fig, "题目一：搜索覆盖、访问顺序与最短路径",
                  "绿色为有效出队节点，角标为访问序号；蓝线为最终路径。访问目标计入访问数，但不展开目标。")


def maze_frontier(data: Results):
    snapshots = replay_frontier(data.read(1, "astar_manhattan", "trace.json"))
    steps = (1, 5, 10, len(snapshots))
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))
    fig.subplots_adjust(left=.035, right=.99, top=.99, bottom=.19, wspace=.25)
    for ax, step in zip(axes, steps):
        snapshot = snapshots[step-1]
        grid(ax, data.case(1)["grid"])
        for row, col in snapshot["visited"]:
            ax.add_patch(Rectangle((col-.5, row-.5), 1, 1, facecolor="#dcfce7", alpha=.8, zorder=1))
        for _, _, (row, col), _, _ in snapshot["frontier"]:
            ax.add_patch(Rectangle((col-.5, row-.5), 1, 1, facecolor="#fef3c7", alpha=.85, zorder=1))
        row, col = snapshot["current"]
        ax.add_patch(Rectangle((col-.48, row-.48), .96, .96, fill=False, edgecolor=BLUE, linewidth=3, zorder=6))
        if step == len(snapshots):
            route(ax, data.summaries[1]["path"])
        queue = snapshot["frontier"]
        peek = f"最小项 {queue[0][2]}：f={queue[0][0]:g}" if queue else "OPEN 已空"
        ax.set_title(f"完成第 {step} 次节点处理\n当前 {snapshot['current']}\n{peek}", fontsize=11)
    fig.legend(handles=[Patch(facecolor="#dcfce7", label="已访问"),
                        Patch(facecolor="#fef3c7", label="OPEN 中的有效候选")],
               loc="lower center", bbox_to_anchor=(.5,.01), ncols=2, fontsize=10)
    return finish(fig, "题目一：A* 优先队列与路径形成的四个时刻",
                  "按保存事件重放队列；先比较 f，再按入队序号打破平局。蓝框为当前处理节点。")


def efficiency(data: Results, number: int):
    rows = [data.metric(number, heuristic=mode) for mode in ("zero", "manhattan")]
    names = ("h=0", "曼哈顿" if number == 1 else "修正曼哈顿")
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), layout="constrained")
    bars(axes[0], ["访问", "展开", "生成候选"],
         {name: [int(row[key]) for key in ("nodes_visited", "nodes_expanded", "nodes_generated")]
          for name, row in zip(names, rows)}, "次数", "节点开销")
    bars(axes[1], ["堆条目峰值", "成功松弛"],
         {name: [int(row[key]) for key in ("frontier_peak", "relaxations")]
          for name, row in zip(names, rows)}, "数量", "队列与路径更新")
    bars(axes[2], list(names), {"搜索耗时": [float(row["elapsed_seconds"])*1e6 for row in rows]},
         "微秒 µs", "本次观测耗时", decimals=1)
    saved = (int(rows[0]["nodes_visited"])-int(rows[1]["nodes_visited"]))/int(rows[0]["nodes_visited"])
    return finish(fig, f"题目{'一' if number == 1 else '二'}：启发函数的搜索开销对照（访问减少 {saved:.1%}）",
                  "生成候选包含重复状态；堆峰值包含尚未弹出的过期项。" + TIME_NOTE)


def weighted_path(data: Results):
    summary = data.summaries[2]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.7), layout="constrained")
    grid(axes[0], data.case(2)["grid"], weighted=True)
    route(axes[0], summary["path"], color=BLUE)
    for index, (row, col) in enumerate(summary["path"]):
        axes[0].text(col+.27, row+.3, f"#{index}", ha="center", fontsize=8, zorder=6,
                     bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})
    axes[0].set_title("最小代价路径；格内数字为进入代价，E=0")
    x = np.arange(len(summary["path"]))
    axes[1].bar(x, summary["step_costs"], color="#cbd5e1", label="本步进入代价")
    axes[1].plot(x, summary["cumulative_costs"], "o-", color=BLUE, label="累计代价 g")
    for index, value in enumerate(summary["cumulative_costs"]):
        axes[1].annotate(str(value), (index, value), xytext=(0, 9), textcoords="offset points",
                         ha="center", fontsize=10, color=BLUE)
    axes[1].set_xticks(x, [f"{i}\n({r},{c})" for i, (r,c) in enumerate(summary["path"])], fontsize=9)
    axes[1].set_xlabel("路径步号与坐标")
    axes[1].set_title("最后一步进入 E：累计代价保持为 7")
    style_axis(axes[1], "代价")
    axes[1].legend(loc="upper left")
    return finish(fig, "题目二：地形权值、路径选择与逐步代价累计",
                  "起点不计进入代价；进入 E 的最后一步为 0。路径有 8 次移动，但总代价为 7。")


def weighted_heuristic(data: Results):
    summary = data.summaries[2]
    path = summary["path"]
    goal = path[-1]
    cells = data.case(2)["grid"]
    if cells[goal[0]][goal[1]] != "E":
        raise ValueError("The zero-goal-cost analysis requires an E goal marker")
    minimum = min(1 if cell == "S" else 0 if cell == "E" else int(cell)
                  for row, values in enumerate(cells) for col, cell in enumerate(values)
                  if cell != "X" and (row, col) != tuple(goal))
    distances = np.array([abs(r-goal[0])+abs(c-goal[1]) for r,c in path])
    corrected = np.maximum(distances-1, 0)*minimum
    true_remaining = summary["cost"]-np.array(summary["cumulative_costs"])
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    x = np.arange(len(path))
    ax.plot(x, distances, "s--", color=ORANGE, label="原始曼哈顿 D")
    ax.plot(x, corrected, "o-", color=BLUE, label=f"修正 h={minimum}×max(D−1,0)")
    ax.plot(x, true_remaining, "x:", color=GREEN, linewidth=2.2,
                 markersize=10, label="最优路径后缀的真实代价 h*")
    ax.set_xticks(x, [f"({r},{c})" for r,c in path], rotation=35, ha="right", fontsize=9)
    ax.set_xlabel("路径上的状态")
    style_axis(ax, "剩余代价 / 启发值")
    ax.legend(fontsize=10)
    return finish(fig, "题目二：终点零代价与启发函数可采纳性",
                  "真实剩余代价由最优路径的后缀计算；曲线只展示该路径，不将局部相等推广为任意地图上的精确估计。")


def figures(data: Results) -> dict:
    return {"01_maze_search": maze_visits(data), "02_maze_frontier": maze_frontier(data),
            "03_maze_efficiency": efficiency(data, 1), "04_weighted_path_cost": weighted_path(data),
            "05_weighted_heuristic": weighted_heuristic(data), "06_weighted_efficiency": efficiency(data, 2)}

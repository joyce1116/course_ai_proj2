"""统一图形样式、地图与统计图绘制工具。"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Rectangle

BLUE, ORANGE, GREEN, RED = "#2563eb", "#d97706", "#15803d", "#dc2626"
INK, GRAY, LIGHT = "#1f2937", "#64748b", "#e2e8f0"
TIME_NOTE = "耗时为开启轨迹后的单次观测，无重复测量或误差区间；不据此推断稳定速度优势。"


def configure() -> str:
    candidates = [Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/simhei.ttf"),
                  Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")]
    family = None
    for path in candidates:
        if path.is_file():
            font_manager.fontManager.addfont(str(path))
            family = font_manager.FontProperties(fname=str(path)).get_name()
            break
    if family is None:
        installed = {font.name for font in font_manager.fontManager.ttflist}
        family = next((name for name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC")
                       if name in installed), None)
    if family is None:
        raise RuntimeError("Install a Chinese font such as Microsoft YaHei or Noto Sans CJK SC")
    plt.rcParams.update({"font.family": family, "font.size": 11, "axes.titlesize": 13,
                         "axes.labelsize": 11, "axes.unicode_minus": False,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titlepad": 12, "figure.facecolor": "white",
                         "savefig.facecolor": "white", "legend.frameon": False})
    return family


def finish(fig, title: str, note: str = ""):
    """保留内部图名和图注，实际标题与分析由 Markdown 承载。"""
    fig.set_label(title)
    fig._report_caption = note
    return fig


def style_axis(ax, ylabel: str = "") -> None:
    ax.set_ylabel(ylabel)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=LIGHT, linewidth=0.7)
    ax.margins(y=0.15)


def bars(ax, labels, series, ylabel: str, title: str, *, decimals: int = 0) -> None:
    x = np.arange(len(labels))
    width = 0.72 / len(series)
    colors = (BLUE, ORANGE, GREEN, RED)
    for index, (name, values) in enumerate(series.items()):
        positions = x - 0.36 + width / 2 + index * width
        patches = ax.bar(positions, values, width, label=name, color=colors[index],
                         edgecolor="white", linewidth=0.7)
        ax.bar_label(patches, fmt=f"%.{decimals}f", padding=3, fontsize=9)
    ax.set_xticks(x, labels)
    ax.set_title(title)
    style_axis(ax, ylabel)
    ax.legend(fontsize=9)


def grid(ax, cells, *, weighted: bool = False, special_cost: int = 1) -> None:
    height, width = len(cells), len(cells[0])
    max_cost = max((cell for row in cells for cell in row if type(cell) is int), default=1)
    for row, values in enumerate(cells):
        for col, cell in enumerate(values):
            blocked = cell == "X"
            value = cell if type(cell) is int else 0 if weighted and cell == "E" else special_cost
            color = "#263444" if blocked else (
                plt.colormaps["YlOrBr"](0.08 + 0.65 * value / max(max_cost, 1))
                if weighted else "#f8fafc")
            ax.add_patch(Rectangle((col-0.5, row-0.5), 1, 1, facecolor=color,
                                   edgecolor="#cbd5e1", linewidth=0.8, zorder=0))
            text = "X" if blocked else str(cell) if cell != "." else ""
            ax.text(col, row, text, ha="center", va="center", fontsize=11,
                    color="white" if blocked else INK, zorder=4)
    ax.set_xlim(-0.5, width-0.5)
    ax.set_ylim(height-0.5, -0.5)
    ax.set_xticks(range(width))
    ax.set_yticks(range(height))
    ax.set_xlabel("列 col")
    ax.set_ylabel("行 row")
    ax.set_aspect("equal")
    for spine in ax.spines.values():
        spine.set_visible(False)


def route(ax, path, *, color: str = BLUE, linewidth: float = 3,
          linestyle: str = "-", label: str | None = None, offset: float = 0) -> None:
    xs = [point[1] + offset for point in path]
    ys = [point[0] + offset for point in path]
    ax.plot(xs, ys, color=color, linewidth=linewidth, linestyle=linestyle,
            label=label, zorder=3, alpha=0.85)
    for start, end in zip(path, path[1:]):
        ax.annotate("", xy=(end[1]+offset, end[0]+offset),
                    xytext=(start[1]+offset, start[0]+offset), zorder=3,
                    arrowprops={"arrowstyle": "-|>", "color": color,
                                "lw": 0.8, "mutation_scale": 10})



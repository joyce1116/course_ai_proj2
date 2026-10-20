"""题目一：四方向、单位移动代价的迷宫寻路。"""

from collections.abc import Sequence

from src.algorithms import SearchResult, astar
from ._grid import Coordinate, GridInput, GridMap


def _cost(cell: str | int) -> int | None:
    if cell == "X":
        return None
    if cell in (".", "S", "E"):
        return 1
    raise ValueError(f"Unknown maze cell: {cell!r}")


def search(
    start: Sequence[int], goal: Sequence[int], grid: GridInput,
    *, heuristic: str = "manhattan", collect_trace: bool = False,
) -> SearchResult[Coordinate]:
    """返回完整搜索结果和统计；坐标采用 (row, col)。"""
    maze = GridMap.from_cells(grid, _cost)
    source, target = maze.require_position(start), maze.require_position(goal)
    return astar(source, lambda point: point == target, maze.successors,
                 maze.heuristic(target, heuristic), collect_trace=collect_trace)


def solve(
    start: Sequence[int], goal: Sequence[int], grid: GridInput,
    *, heuristic: str = "manhattan",
) -> list[Coordinate]:
    """按题目格式返回最短路径；不可达时返回 []。"""
    return search(start, goal, grid, heuristic=heuristic).path


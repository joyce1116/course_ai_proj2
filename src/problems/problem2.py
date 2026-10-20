"""题目二：按进入格子的权值计算路径代价，进入 E 的代价为 0。"""

from collections.abc import Sequence

from src.algorithms import SearchResult, astar
from ._grid import Coordinate, GridInput, GridMap, integer_cost


def _cost(cell: str | int) -> int | None:
    if cell == "X":
        return None
    if cell == "S":
        return 1
    if cell == "E":
        return 0
    return integer_cost(cell)


def search(
    start: Sequence[int], goal: Sequence[int], grid: GridInput,
    *, heuristic: str = "manhattan", collect_trace: bool = False,
) -> SearchResult[Coordinate]:
    """保留路径、总代价、搜索统计及可选的累计 g/h/f 轨迹。"""
    terrain = GridMap.from_cells(grid, _cost)
    source, target = terrain.require_position(start), terrain.require_position(goal)
    return astar(source, lambda point: point == target, terrain.successors,
                 terrain.heuristic(target, heuristic), collect_trace=collect_trace)


def solve(
    start: Sequence[int], goal: Sequence[int], grid: GridInput,
    *, heuristic: str = "manhattan",
) -> int:
    """返回最小整数代价；不可达时返回 -1。起点本身不计进入代价。"""
    result = search(start, goal, grid, heuristic=heuristic)
    return int(result.cost) if result.cost is not None else -1


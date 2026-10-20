"""四邻接地图、输入检查和可采纳的网格启发函数。"""

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass

from src.algorithms import Transition

Coordinate = tuple[int, int]
GridInput = Sequence[Sequence[str | int]]
DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))


def integer_cost(cell: str | int) -> int:
    if isinstance(cell, str) and cell.isdecimal():
        return int(cell)
    if type(cell) is int and cell >= 0:
        return cell
    raise ValueError(f"Expected a nonnegative integer terrain cost, got {cell!r}")


@dataclass(frozen=True)
class GridMap:
    costs: tuple[tuple[int | None, ...], ...]

    @classmethod
    def from_cells(
        cls, cells: GridInput, decode: Callable[[str | int], int | None],
    ) -> "GridMap":
        if not cells or not cells[0]:
            raise ValueError("Grid must not be empty")
        width = len(cells[0])
        if any(len(row) != width for row in cells):
            raise ValueError("Grid must be rectangular")
        return cls(tuple(tuple(decode(cell) for cell in row) for row in cells))

    def require_position(self, point: Sequence[int]) -> Coordinate:
        if len(point) != 2 or any(type(value) is not int for value in point):
            raise ValueError("Position must contain two integer coordinates")
        row, col = point
        if not (0 <= row < len(self.costs) and 0 <= col < len(self.costs[0])):
            raise ValueError(f"Position outside grid: {point!r}")
        if self.costs[row][col] is None:
            raise ValueError(f"Position is blocked: {point!r}")
        return row, col

    def successors(self, point: Coordinate) -> Iterator[Transition[Coordinate]]:
        for dr, dc in DIRECTIONS:
            row, col = point[0] + dr, point[1] + dc
            if 0 <= row < len(self.costs) and 0 <= col < len(self.costs[0]):
                cost = self.costs[row][col]
                if cost is not None:
                    yield Transition((row, col), cost, (row, col))

    def heuristic(self, goal: Coordinate, mode: str) -> Callable[[Coordinate], int]:
        if mode == "zero":
            return lambda _: 0
        if mode != "manhattan":
            raise ValueError("heuristic must be 'zero' or 'manhattan'")
        minimum = min((
            cost for row, values in enumerate(self.costs) for col, cost in enumerate(values)
            if cost is not None and (row, col) != goal
        ), default=0)
        goal_cost = self.costs[goal[0]][goal[1]]
        assert goal_cost is not None

        def estimate(point: Coordinate) -> int:
            distance = abs(point[0] - goal[0]) + abs(point[1] - goal[1])
            # 最后一步单独计目标格代价；题目二的 E 为 0，不能直接用原始距离。
            return 0 if distance == 0 else (distance - 1) * minimum + goal_cost

        return estimate


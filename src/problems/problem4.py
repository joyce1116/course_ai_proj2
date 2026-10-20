"""题目四：A* 两两距离预计算与轮流选择宝藏的博弈搜索。"""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Literal

from src.algorithms import GameMove, SearchResult, alpha_beta, astar, minimax
from ._grid import Coordinate, GridInput, GridMap, integer_cost


@dataclass(frozen=True)
class TreasureState:
    position_a: str
    position_b: str
    remaining: tuple[str, ...]
    score_a: int = 0
    score_b: int = 0
    current_player: Literal["A", "B"] = "A"

    @property
    def utility(self) -> int:
        return self.score_a - self.score_b


class TreasureGame:
    def __init__(
        self, grid: GridInput, treasure_values: Mapping[str, int],
        *, heuristic: str = "manhattan", collect_trace: bool = False,
    ) -> None:
        self.values = dict(treasure_values)
        if any(not isinstance(name, str) or not name or name in ("A", "B", "X") for name in self.values):
            raise ValueError("Treasure labels must be distinct from A, B and X")
        if any(type(value) is not int for value in self.values.values()):
            raise ValueError("Treasure values must be integers")
        self.labels = ("A", "B", *self.values)
        self.heuristic_name = heuristic

        def decode(cell: str | int) -> int | None:
            if cell == "X":
                return None
            if cell in self.labels:
                return 1
            return integer_cost(cell)

        terrain = GridMap.from_cells(grid, decode)
        positions: dict[str, Coordinate] = {}
        for row, cells in enumerate(grid):
            for col, cell in enumerate(cells):
                if cell in self.labels:
                    if cell in positions:
                        raise ValueError(f"Duplicate position marker: {cell}")
                    positions[cell] = (row, col)
        if set(positions) != set(self.labels):
            raise ValueError("Grid must contain A, B and each treasure exactly once")
        self.positions = positions
        self.path_searches: dict[tuple[str, str], SearchResult[Coordinate]] = {}
        self.distances: dict[tuple[str, str], int | None] = {}
        # 全部有向点对分别搜索；一般的进入代价模型不能假定距离对称。
        for source in self.labels:
            for target in self.labels:
                destination = positions[target]
                result = astar(
                    positions[source], lambda point, goal=destination: point == goal,
                    terrain.successors, terrain.heuristic(destination, heuristic),
                    collect_trace=collect_trace,
                )
                self.path_searches[source, target] = result
                self.distances[source, target] = int(result.cost) if result.cost is not None else None
        self.initial_state = TreasureState("A", "B", tuple(self.values))

    def distance_matrix(self) -> list[list[int | None]]:
        """行列均按 labels 排列；不可达用 None 表示。"""
        return [[self.distances[source, target] for target in self.labels] for source in self.labels]

    def successors(self, state: TreasureState) -> Iterator[GameMove[TreasureState]]:
        for target in state.remaining:
            position = state.position_a if state.current_player == "A" else state.position_b
            distance = self.distances[position, target]
            if distance is None:
                continue
            gain = self.values[target] - distance
            remaining = tuple(name for name in state.remaining if name != target)
            # 仅领取本回合选中的宝藏；路径经过其他宝藏或玩家均无额外效果。
            if state.current_player == "A":
                child = TreasureState(target, state.position_b, remaining,
                                      state.score_a + gain, state.score_b, "B")
            else:
                child = TreasureState(state.position_a, target, remaining,
                                      state.score_a, state.score_b + gain, "A")
            yield GameMove(child, target)

    def search(
        self, depth: int, *, algorithm: str = "alpha_beta",
        order: str = "input", collect_trace: bool = False,
    ) -> SearchResult[TreasureState]:
        algorithms = {"minimax": minimax, "alpha_beta": alpha_beta}
        if algorithm not in algorithms:
            raise ValueError("algorithm must be 'minimax' or 'alpha_beta'")
        if order not in ("input", "reverse", "gain"):
            raise ValueError("order must be 'input', 'reverse' or 'gain'")
        order_moves = None
        if order == "reverse":
            order_moves = lambda _state, moves, _max: reversed(moves)
        elif order == "gain":
            order_moves = lambda _state, moves, maximizing: sorted(
                moves, key=lambda move: move.state.utility, reverse=maximizing,
            )
        return algorithms[algorithm](
            self.initial_state, self.successors, lambda state: state.utility,
            lambda state: not state.remaining, max_depth=depth,
            order_moves=order_moves, collect_trace=collect_trace,
        )

    def solve(self, depth: int, *, algorithm: str = "alpha_beta", order: str = "input") -> dict:
        return answer(self.search(depth, algorithm=algorithm, order=order))


def answer(result: SearchResult[TreasureState]) -> dict[str, str | int | None]:
    assert result.value is not None
    return {"best_target": result.best_action, "best_value": int(result.value)}


def solve(
    grid: GridInput, treasure_values: Mapping[str, int], depth: int,
    *, algorithm: str = "alpha_beta",
) -> dict[str, str | int | None]:
    """返回题目规定的 best_target 与 best_value；多次决策可复用 TreasureGame。"""
    return TreasureGame(grid, treasure_values).solve(depth, algorithm=algorithm)


"""Minimax / Alpha-Beta 共用的输入检查、叶子评估和统计口径。"""

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from math import isnan
from typing import Generic

from .models import GameMove, StateT, TraceEvent, record_trace
from .stats import SearchStats


@dataclass
class GameLine(Generic[StateT]):
    value: float
    path: list[StateT]
    actions: list[object]


class GameContext(Generic[StateT]):
    def __init__(
        self,
        algorithm: str,
        successors: Callable[[StateT], Iterable[GameMove[StateT]]],
        evaluate: Callable[[StateT], float],
        is_terminal: Callable[[StateT], bool],
        max_depth: int | None,
        order_moves: Callable[[StateT, tuple[GameMove[StateT], ...], bool], Iterable[GameMove[StateT]]] | None,
        collect_trace: bool,
    ) -> None:
        if max_depth is not None and (type(max_depth) is not int or max_depth < 0):
            raise ValueError("max_depth must be a nonnegative integer or None")
        self.successors = successors
        self.evaluate = evaluate
        self.is_terminal = is_terminal
        self.max_depth = max_depth
        self.order_moves = order_moves
        self.stats = SearchStats(algorithm)
        self.trace: list[TraceEvent[StateT]] | None = [] if collect_trace else None

    def prepare(
        self, state: StateT, depth: int, maximizing: bool, **bounds: float,
    ) -> tuple[list[GameMove[StateT]], GameLine[StateT] | None]:
        stats = self.stats
        stats.nodes_visited += 1
        stats.max_depth = max(stats.max_depth, depth)
        record_trace(self.trace, "visit", state, depth, maximizing=maximizing, **bounds)

        reason = None
        moves: list[GameMove[StateT]] = []
        if self.is_terminal(state):
            reason = "terminal"
        elif self.max_depth is not None and depth >= self.max_depth:
            reason = "depth_limit"
        else:
            stats.nodes_expanded += 1
            moves = list(self.successors(state))
            stats.nodes_generated += len(moves)
            if not moves:
                reason = "no_moves"

        if reason is not None:
            if reason == "depth_limit":
                stats.depth_limit_nodes += 1
            else:
                stats.terminal_nodes += 1
            stats.evaluation_calls += 1
            value = float(self.evaluate(state))
            if isnan(value):
                raise ValueError("evaluation must not be NaN")
            record_trace(self.trace, "evaluate", state, depth, value=value, reason=reason)
            return [], GameLine(value, [state], [])

        if self.order_moves is not None:
            ordered = list(self.order_moves(state, tuple(moves), maximizing))
            if Counter(map(id, ordered)) != Counter(map(id, moves)):
                raise ValueError("order_moves must return a permutation of the original move objects")
            moves = ordered
        return moves, None


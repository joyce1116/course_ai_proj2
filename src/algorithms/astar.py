"""支持外部启发函数、零代价边和状态重新打开的图搜索 A*。"""

from collections.abc import Callable, Hashable, Iterable
from heapq import heappop, heappush
from itertools import count
from math import isfinite
from typing import TypeVar

from .models import SearchResult, TraceEvent, Transition, record_trace
from .stats import SearchStats

StateT = TypeVar("StateT", bound=Hashable)


def _nonnegative_finite(value: float, name: str) -> float:
    value = float(value)
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return value


def astar(
    start: StateT,
    is_goal: Callable[[StateT], bool],
    successors: Callable[[StateT], Iterable[Transition[StateT]]],
    heuristic: Callable[[StateT], float] | None = None,
    *,
    collect_trace: bool = False,
) -> SearchResult[StateT]:
    """返回路径与累计代价；默认 h=0。状态须可哈希且搜索期间不变。

    最优性要求启发值不超过真实剩余代价且目标启发值为 0；允许不一致
    启发函数。回调及启发值须在一次搜索内保持稳定。边代价必须非负有限。
    """
    stats = SearchStats("astar", frontier_peak=1)
    trace: list[TraceEvent[StateT]] | None = [] if collect_trace else None

    with stats.timer():
        def estimate(state: StateT) -> float:
            stats.heuristic_calls += 1
            return _nonnegative_finite(heuristic(state) if heuristic is not None else 0, "heuristic")

        serial = count()
        start_h = estimate(start)
        # 序号打破 f 相同的平局，不要求状态对象可比较。
        frontier = [(start_h, next(serial), start, 0.0, 0, start_h)]
        best_g = {start: 0.0}
        parents: dict[StateT, tuple[StateT, object]] = {}
        expanded: set[StateT] = set()
        record_trace(trace, "discover", start, 0, g=0.0, h=start_h, f=start_h)

        while frontier:
            f, _, state, g, depth, h = heappop(frontier)
            if g != best_g[state]:
                stats.stale_queue_entries += 1
                record_trace(trace, "stale", state, depth, g=g, best_g=best_g[state])
                continue

            stats.nodes_visited += 1
            stats.max_depth = max(stats.max_depth, depth)
            record_trace(trace, "visit", state, depth, g=g, h=h, f=f)
            if is_goal(state):
                if h != 0:
                    raise ValueError("heuristic at a goal must be zero")
                stats.terminal_nodes += 1
                path, actions = [state], []
                while state in parents:
                    state, action = parents[state]
                    path.append(state)
                    actions.append(action)
                path.reverse()
                actions.reverse()
                return SearchResult(
                    "success", stats, path, actions, cost=g, trace=trace if trace is not None else [],
                )

            if state in expanded:
                stats.reopened_nodes += 1
            expanded.add(state)
            stats.nodes_expanded += 1

            for edge in successors(state):
                stats.nodes_generated += 1
                step_cost = _nonnegative_finite(edge.cost, "edge cost")
                candidate_g = _nonnegative_finite(g + step_cost, "path cost")
                if edge.state in best_g:
                    stats.duplicate_states += 1
                    if candidate_g >= best_g[edge.state]:
                        continue

                child_h = estimate(edge.state)
                child_f = _nonnegative_finite(candidate_g + child_h, "priority")
                best_g[edge.state] = candidate_g
                parents[edge.state] = (state, edge.action)
                stats.relaxations += 1
                heappush(frontier, (
                    child_f, next(serial), edge.state, candidate_g, depth + 1, child_h,
                ))
                stats.frontier_peak = max(stats.frontier_peak or 0, len(frontier))
                record_trace(
                    trace, "discover", edge.state, depth + 1,
                    parent=state, action=edge.action, g=candidate_g, h=child_h, f=child_f,
                )

        return SearchResult("no_solution", stats, trace=trace if trace is not None else [])


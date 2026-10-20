"""按给定访问顺序执行的深度优先 Minimax。"""

from collections.abc import Callable, Iterable

from ._game import GameContext, GameLine
from .models import GameMove, SearchResult, StateT, record_trace


def minimax(
    state: StateT,
    successors: Callable[[StateT], Iterable[GameMove[StateT]]],
    evaluate: Callable[[StateT], float],
    is_terminal: Callable[[StateT], bool],
    *,
    max_depth: int | None = None,
    maximizing: bool = True,
    order_moves: Callable[[StateT, tuple[GameMove[StateT], ...], bool], Iterable[GameMove[StateT]]] | None = None,
    collect_trace: bool = False,
) -> SearchResult[StateT]:
    """根深度为 0；evaluate 始终给出 MAX 视角的值，相同值选先访问的动作。

    每层 MAX/MIN 交替。未限制深度时，调用方必须提供有限、无环的博弈树。
    """
    ctx = GameContext("minimax", successors, evaluate, is_terminal, max_depth, order_moves, collect_trace)

    def visit(node: StateT, depth: int, is_max: bool) -> GameLine[StateT]:
        moves, leaf = ctx.prepare(node, depth, is_max)
        if leaf is not None:
            return leaf

        best: GameLine[StateT] | None = None
        for move in moves:
            child = visit(move.state, depth + 1, not is_max)
            if best is None or (child.value > best.value if is_max else child.value < best.value):
                best = GameLine(child.value, [node, *child.path], [move.action, *child.actions])
        assert best is not None
        record_trace(ctx.trace, "return", node, depth, value=best.value)
        return best

    with ctx.stats.timer():
        best = visit(state, 0, maximizing)
        return SearchResult(
            "success", ctx.stats, best.path, best.actions, value=best.value,
            trace=ctx.trace if ctx.trace is not None else [],
        )


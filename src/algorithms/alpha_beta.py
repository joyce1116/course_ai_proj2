"""与 Minimax 使用同一输入接口及计数口径的 Alpha-Beta。"""

from collections.abc import Callable, Iterable
from math import inf

from ._game import GameContext, GameLine
from .models import GameMove, SearchResult, StateT, record_trace


def alpha_beta(
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
    """全窗口搜索；alpha >= beta 时跳过剩余分支，分数含义与 Minimax 一致。"""
    ctx = GameContext("alpha_beta", successors, evaluate, is_terminal, max_depth, order_moves, collect_trace)

    def visit(node: StateT, depth: int, is_max: bool, alpha: float, beta: float) -> GameLine[StateT]:
        moves, leaf = ctx.prepare(node, depth, is_max, alpha=alpha, beta=beta)
        if leaf is not None:
            return leaf

        best: GameLine[StateT] | None = None
        for index, move in enumerate(moves):
            child = visit(move.state, depth + 1, not is_max, alpha, beta)
            if best is None or (child.value > best.value if is_max else child.value < best.value):
                best = GameLine(child.value, [node, *child.path], [move.action, *child.actions])

            if is_max:
                alpha = max(alpha, best.value)
            else:
                beta = min(beta, best.value)
            remaining = len(moves) - index - 1
            if alpha >= beta and remaining:
                ctx.stats.cutoff_events += 1
                ctx.stats.pruned_branches += remaining
                if ctx.trace is not None:
                    record_trace(
                        ctx.trace, "cutoff", node, depth,
                        alpha=alpha, beta=beta, value=best.value, pruned_branches=remaining,
                        pruned_actions=[item.action for item in moves[index + 1:]],
                    )
                break

        assert best is not None
        record_trace(ctx.trace, "return", node, depth, value=best.value, alpha=alpha, beta=beta)
        return best

    with ctx.stats.timer():
        best = visit(state, 0, maximizing, -inf, inf)
        return SearchResult(
            "success", ctx.stats, best.path, best.actions, value=best.value,
            trace=ctx.trace if ctx.trace is not None else [],
        )


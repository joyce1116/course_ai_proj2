"""题目三：根为 MAX、默认从左到右访问的极大极小博弈树。"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite

from src.algorithms import GameMove, SearchResult, alpha_beta, minimax


@dataclass(eq=False)
class TreeNode:
    value: int | float | None = None
    children: list["TreeNode"] = field(default_factory=list)


def tree_from_dict(data: Mapping) -> TreeNode:
    """读取 tree_structure JSON，检查玩家标记与层次交替一致。"""
    def build(node: Mapping, maximizing: bool) -> TreeNode:
        if not isinstance(node, Mapping):
            raise ValueError("Each tree node must be an object")
        player = node.get("is_maximizing_player", maximizing)
        if type(player) is not bool or player != maximizing:
            raise ValueError("Tree player flags must alternate from a MAX root")
        children = node.get("children", [])
        if not isinstance(children, (list, tuple)):
            raise ValueError("children must be a list")
        if children:
            return TreeNode(children=[build(child, not maximizing) for child in children])
        value = node.get("value")
        if type(value) not in (int, float) or not isfinite(value):
            raise ValueError("A leaf must have a finite numeric value")
        return TreeNode(value=value)

    return build(data.get("tree_structure", data), True)


def search(
    root: TreeNode | Mapping, *, algorithm: str = "alpha_beta",
    order: str = "left_to_right", collect_trace: bool = False,
) -> SearchResult[TreeNode]:
    if isinstance(root, Mapping):
        root = tree_from_dict(root)
    algorithms = {"minimax": minimax, "alpha_beta": alpha_beta}
    if algorithm not in algorithms:
        raise ValueError("algorithm must be 'minimax' or 'alpha_beta'")
    if order not in ("left_to_right", "reverse"):
        raise ValueError("order must be 'left_to_right' or 'reverse'")

    def evaluate(node: TreeNode) -> float:
        if type(node.value) not in (int, float) or not isfinite(node.value):
            raise ValueError("A leaf must have a finite numeric value")
        return float(node.value)

    return algorithms[algorithm](
        root,
        lambda node: [GameMove(child, index) for index, child in enumerate(node.children)],
        evaluate, lambda node: not node.children,
        order_moves=(lambda _state, moves, _max: reversed(moves)) if order == "reverse" else None,
        collect_trace=collect_trace,
    )


def solve(root: TreeNode | Mapping) -> int | float:
    """使用从左到右的 Alpha-Beta，返回 MAX 的最佳得分。"""
    value = search(root).value
    assert value is not None
    return int(value) if value.is_integer() else value


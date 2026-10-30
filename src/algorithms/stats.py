"""所有搜索共用的计数、计时、导出和对照接口。"""

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from time import perf_counter_ns
from typing import Iterator


@dataclass
class SearchStats:
    """统计搜索操作；未执行的操作计为 0，不适用的队列峰值为 None。"""

    algorithm: str
    elapsed_seconds: float = 0.0
    nodes_visited: int = 0
    nodes_expanded: int = 0
    nodes_generated: int = 1  # 包含根节点；生成不等于访问。
    terminal_nodes: int = 0
    depth_limit_nodes: int = 0
    evaluation_calls: int = 0
    heuristic_calls: int = 0
    max_depth: int = 0
    frontier_peak: int | None = None
    duplicate_states: int = 0
    relaxations: int = 0
    reopened_nodes: int = 0
    stale_queue_entries: int = 0
    cutoff_events: int = 0
    pruned_branches: int = 0

    @contextmanager
    def timer(self) -> Iterator[None]:
        """累计墙钟时间；包含回调和可选轨迹，不包含导出与对照计算。"""
        started = perf_counter_ns()
        try:
            yield
        finally:
            self.elapsed_seconds += (perf_counter_ns() - started) / 1_000_000_000

    def to_dict(self) -> dict[str, str | int | float | None]:
        """返回可直接用于 JSON 或 CSV 的扁平指标。"""
        return asdict(self)


def compare_stats(baseline: SearchStats, candidate: SearchStats) -> dict[str, float | None]:
    """同输入/深度的对照；减少率可为负，零分母返回 None。"""

    def reduction(before: int, after: int) -> float | None:
        return (before - after) / before if before else None

    return {
        "visited_reduction_ratio": reduction(baseline.nodes_visited, candidate.nodes_visited),
        "expanded_reduction_ratio": reduction(baseline.nodes_expanded, candidate.nodes_expanded),
        "evaluation_reduction_ratio": reduction(baseline.evaluation_calls, candidate.evaluation_calls),
        "time_speedup": (
            baseline.elapsed_seconds / candidate.elapsed_seconds
            if candidate.elapsed_seconds > 0 else None
        ),
    }


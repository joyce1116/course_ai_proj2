"""与具体题目无关的边、结果和可选轨迹结构。"""

from dataclasses import dataclass, field
from typing import Generic, Literal, TypeVar

from .stats import SearchStats

StateT = TypeVar("StateT")


@dataclass(frozen=True)
class Transition(Generic[StateT]):
    state: StateT
    cost: float = 1.0
    action: object = None


@dataclass(frozen=True)
class GameMove(Generic[StateT]):
    state: StateT
    action: object = None


@dataclass
class TraceEvent(Generic[StateT]):
    event: str
    state: StateT
    depth: int
    details: dict[str, object] = field(default_factory=dict)


def record_trace(
    trace: list[TraceEvent[StateT]] | None,
    event: str,
    state: StateT,
    depth: int,
    **details: object,
) -> None:
    if trace is not None:
        trace.append(TraceEvent(event, state, depth, details))


@dataclass
class SearchResult(Generic[StateT]):
    status: Literal["success", "no_solution"]
    stats: SearchStats
    path: list[StateT] = field(default_factory=list)
    actions: list[object] = field(default_factory=list)
    cost: float | None = None
    value: float | None = None
    trace: list[TraceEvent[StateT]] = field(default_factory=list)

    @property
    def best_action(self) -> object:
        return self.actions[0] if self.actions else None

    def metrics(self) -> dict[str, str | int | float | None]:
        """只导出标量；状态、动作和轨迹由后续题目适配器负责序列化。"""
        return {
            **self.stats.to_dict(),
            "status": self.status,
            "path_cost": self.cost,
            "best_value": self.value,
            "solution_depth": len(self.path) - 1 if self.path else None,
        }


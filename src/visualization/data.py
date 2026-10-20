"""读取已有运行产物，不执行搜索或修改实验结果。"""

import csv
import json
from pathlib import Path

NAMES = {1: "problem1_maze", 2: "problem2_weighted_terrain",
         3: "problem3_game_tree", 4: "problem4_treasure_game"}


class Results:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.metadata = {n: self.read(n, "metadata.json") for n in NAMES}
        self.summaries = {n: self.read(n, "summary.json") for n in NAMES}
        self.rows = {}
        for number in NAMES:
            if not self.summaries[number].get("expected_verified"):
                raise ValueError(f"Problem {number} has not passed its expected-output checks")
            with self.path(number, "metrics.csv").open(encoding="utf-8-sig", newline="") as stream:
                self.rows[number] = list(csv.DictReader(stream))

    def path(self, number: int, *parts: str) -> Path:
        return self.root / NAMES[number] / Path(*parts)

    def read(self, number: int, *parts: str):
        return json.loads(self.path(number, *parts).read_text(encoding="utf-8"))

    def case(self, number: int) -> dict:
        return self.metadata[number]["inputs"]

    def select(self, number: int, **filters: object) -> list[dict]:
        return [row for row in self.rows[number]
                if all(row[key] == str(value) for key, value in filters.items())]

    def metric(self, number: int, **filters: object) -> dict:
        rows = self.select(number, **filters)
        if len(rows) != 1:
            raise ValueError(f"Expected one metric row: problem={number}, filters={filters}, count={len(rows)}")
        return rows[0]

    def pv(self, depth: int) -> dict:
        return self.read(4, f"depth_{depth}", "input_order", "minimax", "result.json")

    def root_values(self, depth: int) -> dict[str, float]:
        events = self.read(4, f"depth_{depth}", "input_order", "minimax", "trace.json")
        values = {event["state"]["position_a"]: event["details"]["value"] for event in events
                  if event["event"] == "return" and event["depth"] == 1}
        if set(values) != set(self.case(4)["treasure_values"]):
            raise ValueError("Complete Minimax root-child returns are required")
        if max(values.values()) != self.pv(depth)["best_value"]:
            raise ValueError("Root-child values disagree with the recorded decision")
        return values


def number(row: dict, key: str) -> float:
    return float(row[key])


def tree_trace(root: dict, events: list[dict], reverse: bool = False) -> dict:
    """按 DFS 事件及访问顺序定位节点，避免把内容相同的两个子树混淆。"""
    cursor = 0
    visits, values, cutoffs = {}, {}, {}

    def take(event_name: str, depth: int) -> dict:
        nonlocal cursor
        event = events[cursor]
        if event["event"] != event_name or event["depth"] != depth:
            raise ValueError(f"Unexpected tree trace event at {cursor}: {event}")
        cursor += 1
        return event

    def visit(node: dict, path: tuple[int, ...]) -> None:
        entry = take("visit", len(path))
        if entry["state"]["value"] != node.get("value"):
            raise ValueError("Tree trace does not match the input tree")
        visits[path] = len(visits) + 1
        children = node.get("children", [])
        if not children:
            values[path] = take("evaluate", len(path))["details"]["value"]
            return
        indexes = list(range(len(children)))
        if reverse:
            indexes.reverse()
        for index in indexes:
            visit(children[index], path + (index,))
            if events[cursor]["event"] == "cutoff" and events[cursor]["depth"] == len(path):
                cutoffs[path] = take("cutoff", len(path))["details"]
                break
        values[path] = take("return", len(path))["details"]["value"]

    visit(root, ())
    if cursor != len(events):
        raise ValueError("Unconsumed tree trace events")
    return {"visits": visits, "values": values, "cutoffs": cutoffs}

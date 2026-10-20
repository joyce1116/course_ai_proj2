"""运行题目、校验预期结果并保存答案、性能统计及可选轨迹。"""

import argparse
import hashlib
import json
import platform
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

# 兼容从任意工作目录以脚本路径运行。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.algorithms import SearchResult, compare_stats
from src.problems import problem1, problem2, problem3, problem4
from src.utils.io import save_json, save_metrics

OUTPUT_DIRECTORIES = {
    1: "problem1_maze",
    2: "problem2_weighted_terrain",
    3: "problem3_game_tree",
    4: "problem4_treasure_game",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


class ExperimentRun:
    def __init__(self, output: Path, collect_trace: bool) -> None:
        self.output = output
        self.collect_trace = collect_trace
        self.answers: dict[str, object] = {}
        self.metrics: list[dict] = []
        self.messages: list[str] = []
        self.records: list[tuple[Path, SearchResult, dict]] = []

    def emit(self, message: str) -> None:
        print(message)
        self.messages.append(message)

    def record(self, case_id: str, result: SearchResult, **parameters: object) -> dict:
        if case_id in ("problem1", "problem2"):
            relative = Path(f"astar_{parameters['heuristic']}")
        elif case_id == "problem3":
            relative = Path(str(parameters["move_order"])) / result.stats.algorithm
        elif parameters["phase"] == "distance":
            relative = Path("distance_matrix")
        else:
            relative = (Path(f"depth_{parameters['depth_limit']}")
                        / f"{parameters['move_order']}_order" / result.stats.algorithm)
        row = {
            "case_id": case_id,
            "phase": "search",
            "heuristic": None,
            "depth_limit": None,
            "move_order": None,
            "from_point": None,
            "to_point": None,
            "collect_trace": self.collect_trace,
            "result_directory": relative.as_posix(),
            **result.metrics(),
            "visited_reduction_ratio": None,
            "expanded_reduction_ratio": None,
            "evaluation_reduction_ratio": None,
            "time_speedup": None,
            **parameters,
        }
        self.metrics.append(row)
        self.records.append((relative, result, row))
        if self.collect_trace:
            if parameters.get("phase") == "distance":
                start = quote(str(parameters["from_point"]), safe="")
                goal = quote(str(parameters["to_point"]), safe="")
                trace_path = relative / "traces" / f"{start}_to_{goal}.json"
            else:
                trace_path = relative / "trace.json"
            save_json(self.output / trace_path, result.trace)
        return row

    def run_pathfinding(self, case_id: str, case: dict) -> None:
        module = problem1 if case_id == "problem1" else problem2
        runs = {}
        for heuristic in ("zero", "manhattan"):
            result = module.search(case["start"], case["goal"], case["grid"],
                                   heuristic=heuristic, collect_trace=self.collect_trace)
            require(result.cost == case["expected_cost"], f"{case_id}: unexpected path cost")
            require(bool(result.path) and result.path[0] == tuple(case["start"])
                    and result.path[-1] == tuple(case["goal"]), f"{case_id}: invalid endpoints")
            require(all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
                        for a, b in zip(result.path, result.path[1:])), f"{case_id}: invalid path step")
            row = self.record(case_id, result, heuristic=heuristic)
            if heuristic == "manhattan":
                row.update(compare_stats(runs["zero"].stats, result.stats))
            runs[heuristic] = result
            self.emit(f"{case_id} h={heuristic}: cost={int(result.cost)}, "
                      f"visited={result.stats.nodes_visited}, seconds={result.stats.elapsed_seconds:.6f}")

        result = runs["manhattan"]
        answer = {"path": result.path, "cost": int(result.cost), "expected_verified": True}
        if case_id == "problem2":
            costs = [0]
            for row, col in result.path[1:]:
                cell = case["grid"][row][col]
                costs.append(0 if cell == "E" else 1 if cell == "S" else int(cell))
            cumulative = [0]
            for cost in costs[1:]:
                cumulative.append(cumulative[-1] + cost)
            require(cumulative[-1] == result.cost, "problem2: cumulative cost mismatch")
            answer.update(step_costs=costs, cumulative_costs=cumulative)
        self.answers[case_id] = answer
        self.emit(f"{case_id} path: {result.path}")

    def run_tree(self, case: dict, compare: bool) -> None:
        root = problem3.tree_from_dict(case)
        runs = []
        for order in (("left_to_right", "reverse") if compare else ("left_to_right",)):
            baseline = None
            for algorithm in ("minimax", "alpha_beta"):
                result = problem3.search(root, algorithm=algorithm, order=order,
                                         collect_trace=self.collect_trace)
                require(result.value == case["expected_value"], "problem3: unexpected root value")
                row = self.record("problem3", result, move_order=order)
                if baseline is None:
                    baseline = result
                else:
                    require(result.best_action == baseline.best_action, "problem3: algorithms disagree")
                    row.update(compare_stats(baseline.stats, result.stats))
                value = int(result.value) if result.value.is_integer() else result.value
                runs.append({"algorithm": algorithm, "move_order": order,
                             "best_value": value, "principal_variation": result.actions})
                self.emit(f"problem3 {algorithm} order={order}: value={result.value:g}, "
                          f"visited={result.stats.nodes_visited}, cutoffs={result.stats.cutoff_events}")
        self.answers["problem3"] = {"best_value": runs[0]["best_value"], "runs": runs,
                                    "expected_verified": True}

    def run_treasures(self, case: dict, compare: bool) -> None:
        game = problem4.TreasureGame(case["grid"], case["treasure_values"],
                                     collect_trace=self.collect_trace)
        self.emit("problem4 distance matrix: " + ", ".join(game.labels))
        for label, row in zip(game.labels, game.distance_matrix()):
            self.emit(f"  {label}: {row}")
        for (start, goal), result in game.path_searches.items():
            require(result.status == "success", f"problem4: unreachable point pair {start}, {goal}")
            self.record("problem4", result, phase="distance", heuristic=game.heuristic_name,
                        from_point=start, to_point=goal)

        decisions = []
        for depth in case["depths"]:
            expected = case["expected"][str(depth)]
            for order in (("input", "reverse", "gain") if compare else ("input",)):
                baseline = None
                for algorithm in ("minimax", "alpha_beta"):
                    result = game.search(depth, algorithm=algorithm, order=order,
                                         collect_trace=self.collect_trace)
                    answer = problem4.answer(result)
                    require(answer["best_value"] == expected["best_value"],
                            f"problem4 H={depth}: unexpected utility")
                    if order == "input":
                        require(answer == expected, f"problem4 H={depth}: unexpected first target")
                    row = self.record("problem4", result, phase="game", depth_limit=depth,
                                      move_order=order)
                    if baseline is None:
                        baseline = result
                    else:
                        require(answer == problem4.answer(baseline), "problem4: algorithms disagree")
                        row.update(compare_stats(baseline.stats, result.stats))
                    decisions.append({"algorithm": algorithm, "depth_limit": depth,
                                      "move_order": order, **answer,
                                      "principal_variation": result.actions, "states": result.path})
                    self.emit(f"problem4 H={depth} {algorithm} order={order}: {answer}, "
                              f"visited={result.stats.nodes_visited}, cutoffs={result.stats.cutoff_events}")
        self.answers["problem4"] = {"labels": game.labels, "distance_matrix": game.distance_matrix(),
                                    "decisions": decisions, "expected_verified": True}

    def save(self) -> None:
        summary = next(iter(self.answers.values()), {})
        save_json(self.output / "summary.json", summary)
        groups: dict[Path, list[dict]] = {Path(): self.metrics}
        paths = []
        for relative, result, row in self.records:
            for directory in (relative, *relative.parents):
                if directory != Path():
                    groups.setdefault(directory, []).append(row)
            if row["phase"] == "distance":
                paths.append({"from_point": row["from_point"], "to_point": row["to_point"],
                              "cost": result.cost, "path": result.path})
                continue
            payload = {"algorithm": result.stats.algorithm, "status": result.status}
            if result.stats.algorithm == "astar":
                payload.update(path=result.path, cost=result.cost)
            else:
                payload.update(best_value=result.value, best_action=result.best_action,
                               principal_variation=result.actions)
                if row["case_id"] == "problem4":
                    payload["states"] = result.path
            save_json(self.output / relative / "result.json", payload)
        for relative, rows in groups.items():
            save_metrics(self.output / relative / "metrics.csv", rows)
        if "problem4" in self.answers:
            matrix = summary["distance_matrix"]
            labels = summary["labels"]
            directory = self.output / "distance_matrix"
            save_json(directory / "matrix.json", {"labels": labels, "matrix": matrix})
            save_metrics(directory / "matrix.csv", [
                {"point": label, **dict(zip(labels, values))}
                for label, values in zip(labels, matrix)
            ])
            save_json(directory / "paths.json", paths)
        (self.output / "run.log").write_text("\n".join(self.messages) + "\n", encoding="utf-8")


def prepare_output(root: Path, number: int) -> Path:
    """替换所选题目的已生成结果，保留其他题目的输出。"""
    root = root.resolve()
    output = root / OUTPUT_DIRECTORIES[number]
    require(not output.is_symlink() and output.resolve().parent == root,
            "Result directory must remain directly inside the output root")
    if output.exists():
        metadata = output / "metadata.json"
        require(metadata.is_file(), f"Cannot replace an unmanaged directory: {output}")
        existing = json.loads(metadata.read_text(encoding="utf-8"))
        require(existing.get("case_id") == f"problem{number}",
                f"Result directory belongs to a different case: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=False)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=PROJECT_ROOT / "configs" / "test_cases.json")
    parser.add_argument("--problem", choices=("all", "1", "2", "3", "4"), default="all")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "results",
                        help="结果根目录；所选题目的结果会更新到固定子目录")
    parser.add_argument("--compare", action="store_true", help="增加逆序及收益排序的对照运行")
    parser.add_argument("--trace", action="store_true", help="保存搜索过程轨迹")
    args = parser.parse_args()
    raw_cases = args.cases.read_bytes()
    cases = json.loads(raw_cases.decode("utf-8-sig"))
    now = datetime.now(timezone(timedelta(hours=8)))
    for number in (1, 2, 3, 4):
        if args.problem != "all" and args.problem != str(number):
            continue
        key = f"problem{number}"
        case = cases[key]
        output = prepare_output(args.output, number)
        save_json(output / "metadata.json", {
            "case_id": key, "created_at": now.isoformat(), "python": platform.python_version(),
            "platform": platform.platform(), "input_sha256": hashlib.sha256(raw_cases).hexdigest(),
            "parameters": {"compare": args.compare, "trace": args.trace}, "inputs": case,
        })
        run = ExperimentRun(output, args.trace)
        try:
            if number in (1, 2):
                run.run_pathfinding(key, case)
            elif number == 3:
                run.run_tree(case, args.compare)
            else:
                run.run_treasures(case, args.compare)
            run.emit(f"{key}: all expected results verified.")
            run.emit(f"Results: {output}")
        except Exception as error:
            run.emit(f"FAILED: {error}")
            raise
        finally:
            run.save()
    print("All requested cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

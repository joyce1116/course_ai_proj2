"""将算法结果、博弈状态及轨迹转换为 JSON / CSV 文件。"""

import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from math import isfinite, isnan
from pathlib import Path


def to_jsonable(value: object) -> object:
    if isinstance(value, float) and not isfinite(value):
        if isnan(value):
            raise ValueError("NaN cannot be serialized")
        return "+Infinity" if value > 0 else "-Infinity"
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(data), ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


def save_metrics(path: Path, rows: Sequence[Mapping]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

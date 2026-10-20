# 实验二：搜索算法

实现 **A\*、Minimax、Alpha-Beta、统一统计接口和四道题的输入输出**。
提供统一运行入口，校验预期答案并保存性能数据和可选搜索轨迹。
绘图和正式报告尚未实现。

## 环境与复现

- Python 3.10+；本次验证环境为 Windows / Python 3.13.9。
- 仅使用标准库，`requirements.txt` 暂无第三方依赖。
- 以下命令均在 `D:\course_ai\project2` 目录执行。
- 运行全部题目、访问顺序对照并保存搜索轨迹：

```powershell
python -B -X utf8 scripts/run_all.py --compare --trace
```

该命令生成下文列出的四个题目目录。单独重新运行各题的命令如下：

```powershell
python -B -X utf8 scripts/run_all.py --problem 1 --trace
python -B -X utf8 scripts/run_all.py --problem 2 --trace
python -B -X utf8 scripts/run_all.py --problem 3 --compare --trace
python -B -X utf8 scripts/run_all.py --problem 4 --compare --trace
```

| 命令中的题目编号 | 输出目录 | 运行内容 |
| --- | --- | --- |
| `--problem 1` | `results/problem1_maze/` | 迷宫寻路：零启发与曼哈顿启发 |
| `--problem 2` | `results/problem2_weighted_terrain/` | 加权地形：零启发与修正曼哈顿启发 |
| `--problem 3 --compare` | `results/problem3_game_tree/` | 博弈树：两种算法、从左到右和逆序访问 |
| `--problem 4 --compare` | `results/problem4_treasure_game/` | 距离矩阵、H=2/H=4、两种算法及三种访问顺序 |

`--trace` 保存各次搜索过程；省略时只保存答案、指标和日志。
`--cases` 指定输入 JSON，`--output` 指定结果根目录。例如另存一组结果：

```powershell
python -B -X utf8 scripts/run_all.py --compare --trace --output results_alternative
```

每次运行更新所选题目的固定目录，替换该题已有的生成结果；其他题目保持原样。
目录内的旧轨迹与旧对照方案也会一并清理，避免与本次设置混合。
输出目录已存在时，脚本仅替换具有匹配题目元数据的生成目录。
默认运行题目一、二的零启发与可采纳曼哈顿启发，以及题目三、四的两种博弈算法。
`--compare` 为题目三增加逆序访问，为题目四增加逆序及即时收益排序。
默认输入的校验结果：最短路径 7 步、加权最小代价 7、博弈树得分 5；
宝藏分配 H=2 选择 T2、收益差为 -1，H=4 选择 T3、收益差为 3。

## 目录结构

```text
project2/
├── process.md
├── requirements.txt
├── .gitignore
├── configs/
│   └── test_cases.json         # 四道题的输入和预期结果
├── src/
│   ├── __init__.py
│   ├── algorithms/
│   │   ├── __init__.py         # 公共导入接口
│   │   ├── astar.py
│   │   ├── minimax.py
│   │   ├── alpha_beta.py
│   │   ├── stats.py            # 计数、计时、指标导出和对照计算
│   │   ├── models.py           # 通用边、结果和轨迹类型
│   │   └── _game.py            # 两个博弈算法的共享评估及统计逻辑
│   ├── problems/
│   │   ├── __init__.py
│   │   ├── _grid.py            # 四邻接地图及启发函数
│   │   ├── problem1.py         # 迷宫寻路
│   │   ├── problem2.py         # 加权地形
│   │   ├── problem3.py         # 极大极小博弈树
│   │   └── problem4.py         # 宝藏分配
│   └── utils/
│       ├── __init__.py
│       └── io.py               # JSON、CSV 与状态序列化
├── tests/                     # 预留：后续题目验证
├── scripts/
│   └── run_all.py              # 运行、校验和结果保存
├── results/                   # 自动生成，默认被 Git 忽略
└── report/                    # 预留：报告与最终图片
```

算法层只负责搜索；题目层负责规则和输出适配；脚本读取输入并组织运行；
工具层负责保存数据。保留目录用 `.gitkeep` 占位，不保存临时验证代码。

## 题目接口与规则

`src.problems.problem1` 和 `problem2` 均提供
`solve(start, goal, grid, *, heuristic="manhattan")` 和同参数的 `search(...)`。
`solve` 分别返回坐标路径和整数最小代价；不可达时分别返回 `[]` 和 `-1`。
`search` 返回包含路径、统计和可选轨迹的 `SearchResult`，支持 `collect_trace=True`。
空地图、非矩形地图、无效坐标、障碍上的起终点或非法格子值会抛出 `ValueError`。

题目一每步代价为 1，使用四邻接移动。题目二起点不计进入代价，进入数字格计该格权值，
进入 S 计 1，进入 E 计 0，额外支持 X 障碍和零代价格。两题均支持 `heuristic="zero"`。
设曼哈顿距离为 D，非目标可通行格的最小进入代价为 m，目标进入代价为 c，
使用 `h=0 (D=0)`，否则 `h=(D-1)*m+c`。题目一退化为普通曼哈顿距离，
题目二在 m=1、c=0 时为 `max(D-1, 0)`，避免高估最后一步。

`src.problems.problem3.solve(root)` 接收 `TreeNode` 或包含 `tree_structure` 的字典，
返回最优得分；默认根为 MAX，从左到右使用 Alpha-Beta 搜索。
`tree_from_dict(data)` 解析输入并检查玩家交替标记。
`search(root, algorithm="alpha_beta", order="left_to_right", collect_trace=False)`
提供完整结果，可切换 `algorithm="minimax"` 和 `order="reverse"` 进行对照。

`src.problems.problem4.TreasureGame(grid, treasure_values)` 预计算所有标记点之间的
有向最小代价，`labels` 给出矩阵顺序，`distance_matrix()` 返回距离矩阵。
格子 A、B 和宝藏标记的进入代价均为 1。`path_searches` 保留每对点的 A* 搜索结果，
将路径预计算与博弈开销分别统计，避免重复计入不同深度的比较。

`TreasureState` 记录双方位置、剩余宝藏、双方累计收益和当前玩家。
每次只领取选中的宝藏，收益为宝藏价值减最小移动代价，随后更新该玩家的位置并换人；
经过其他宝藏不自动领取，另一玩家不阻挡路径，已领取宝藏的位置仍可通行。
`game.search(H, algorithm="alpha_beta", order="input")` 搜索至 H 步或宝藏取完，
按当前 `Score_A-Score_B` 评价，返回完整统计。`game.solve(H, ...)` 返回
`{"best_target": ..., "best_value": ...}`。支持 `minimax`、`reverse` 和 `gain` 对照。
距离不可达时矩阵记为 `None`，该宝藏不作为当前玩家的合法动作；无合法动作时直接评价。

## 运行产物

结果按题目、启发函数、访问顺序、深度和算法分目录，不按运行时间建立外层目录。
完整运行后的主要结构如下：

```text
results/
├── problem1_maze/
│   ├── summary.json
│   ├── astar_zero/
│   └── astar_manhattan/
├── problem2_weighted_terrain/
│   ├── summary.json
│   ├── astar_zero/
│   └── astar_manhattan/
├── problem3_game_tree/
│   ├── summary.json
│   ├── left_to_right/
│   │   ├── minimax/
│   │   └── alpha_beta/
│   └── reverse/
│       ├── minimax/
│       └── alpha_beta/
└── problem4_treasure_game/
    ├── summary.json
    ├── distance_matrix/
    │   ├── matrix.json
    │   ├── matrix.csv
    │   ├── paths.json
    │   ├── metrics.csv
    │   └── traces/
    │       ├── A_to_B.json
    │       ├── A_to_T1.json
    │       └── ...
    ├── depth_2/
    │   ├── input_order/
    │   │   ├── minimax/
    │   │   └── alpha_beta/
    │   ├── reverse_order/
    │   │   ├── minimax/
    │   │   └── alpha_beta/
    │   └── gain_order/
    │       ├── minimax/
    │       └── alpha_beta/
    └── depth_4/                # 与 depth_2 相同的三种访问顺序及两种算法
```

每个题目根目录都有以下文件：

- `summary.json`：先查看此文件，汇总该题答案、路径或决策结果。
- `metadata.json`：本次运行时间、环境、输入摘要、参数和该题输入快照。
- `metrics.csv`：该题全部搜索的指标及对照减少率。
- `run.log`：该题的运行输出和校验结果。

每个具体搜索方案目录，例如 `problem1_maze/astar_manhattan/`、
`problem3_game_tree/left_to_right/alpha_beta/` 或
`problem4_treasure_game/depth_4/input_order/alpha_beta/`，都包含：

- `result.json`：本方案的路径、代价或博弈结果。
- `metrics.csv`：本方案的统计指标。
- `trace.json`：本方案的搜索过程，仅在 `--trace` 开启时生成。

各层 `metrics.csv` 汇总本目录及下级方案，因此可以直接在 `depth_2/metrics.csv`
与 `depth_4/metrics.csv` 比较深度，也可以在 `input_order/metrics.csv` 比较两种算法。
`result_directory` 列给出具体方案相对于题目目录的位置。

`distance_matrix/` 单独保存题目四的寻路预计算：`matrix.csv` 可直接查看 6×6 矩阵，
`paths.json` 保存各点对的实际路径，`metrics.csv` 包含全部 36 次 A* 搜索。
其轨迹按起终点命名，如 `A_to_T1.json`，与后续博弈轨迹分开。

`left_to_right` 表示从左到右，`reverse` / `reverse_order` 表示逆序，
`input_order` 表示输入顺序，`gain_order` 表示按即时收益排序。
轨迹中的无限边界以字符串 `+Infinity` / `-Infinity` 表示。

CSV 使用 UTF-8 BOM，便于表格软件读取。JSON 使用标准格式，不写入非标准数值常量。

## A* 接口

```python
from src.algorithms import Transition, astar

graph = {
    "S": [Transition("A", 6, "direct"), Transition("B", 1, "via_b")],
    "B": [Transition("A", 1, "to_a")],
    "A": [Transition("G", 2, "finish")],
}
h = {"S": 4, "B": 3, "A": 2, "G": 0}
result = astar(
    start="S",
    is_goal=lambda state: state == "G",
    successors=lambda state: graph.get(state, []),
    heuristic=h.__getitem__,    # 省略时使用 h=0，也可替换成其他启发函数
    collect_trace=True,
)
assert result.path == ["S", "B", "A", "G"]
assert result.cost == 4
print(result.metrics())
```

- `Transition(state, cost=1.0, action=None)` 表示后继状态、进入代价和动作。
  由题目适配器决定具体代价，算法不内置任何地图规则。
- 状态必须可哈希，参与相等性比较的内容在搜索期间不能变化。
- 使用 `f=g+h` 的最小堆；相同 `f` 按插入顺序访问，不比较状态对象。
  只在严格更小的 `g` 出现时更新父节点和入队，跳过过期堆条目，允许重新展开状态。
- 非负且可采纳的启发函数、目标处 `h=0` 和非负边代价是最优性条件；
  允许启发函数不一致。可采纳性需由调用方结合问题证明，框架无法自动判定。
- 边代价、启发值、累计代价及优先级均须非负有限，否则抛出 `ValueError`。
  代价按浮点数计算；零代价边和零代价环均支持。
- 起点即目标时返回单节点路径、代价 0；搜索耗尽时返回
  `status="no_solution"`、`path=[]`、`cost=None`。
  后续题目适配器可将其映射为题目要求的 `[]` 或 `-1`。
- 有限可达状态图保证耗尽时终止；无限状态空间需要调用方约束。

终点进入代价为 0 时，普通曼哈顿距离可能高估最后一步。
题目适配层按目标格的实际代价构造启发函数。

## Minimax / Alpha-Beta 接口

```python
from src.algorithms import GameMove, alpha_beta, compare_stats, minimax

tree = {"root": ["a", "b"], "a": ["a1", "a2"], "b": ["b1", "b2"]}
scores = {"a1": 4, "a2": 7, "b1": 2, "b2": 9}

def successors(state):
    return [GameMove(child, action=child) for child in tree.get(state, [])]

kwargs = {
    "state": "root",
    "successors": successors,
    "evaluate": scores.__getitem__,
    "is_terminal": lambda state: state in scores,
    "max_depth": 2,
}
baseline = minimax(**kwargs)
pruned = alpha_beta(**kwargs)
assert baseline.value == pruned.value == 4
assert pruned.best_action == "a"
assert baseline.stats.nodes_visited == 7
assert pruned.stats.nodes_visited == 6
print(compare_stats(baseline.stats, pruned.stats))
```

- `GameMove(state, action=None)` 表示后继状态和动作，动作标签用于返回最优首步。
- `evaluate(state)` 始终返回 MAX 视角的数值，包括深度截断时的估值。
  可以使用正负无穷表示必胜/必败；不接受 NaN。
- 根默认为 MAX，可通过 `maximizing=False` 指定 MIN；每步交替玩家。
  支持不平衡树、单分支和无合法动作状态。状态不必可哈希。
- 根深度为 0，`max_depth=H` 表示最多执行 H 次行动。
  真终局优先于深度截断；非终局到达深度限制时直接评估，不生成后继。
  无合法动作也直接评估，因此评价函数须覆盖这些情况。
- `max_depth=None` 搜索到终局，要求博弈展开有限且无环；
  有循环的状态转移应设置有限深度。两个算法使用 Python 递归，适合本实验的小深度搜索。
- 默认保持 `successors` 给出的访问顺序。同值时选择最先访问的动作。
  两个算法均返回最优值和一条相应的主变化路径，不返回完整策略树。
- Alpha-Beta 从 `[-inf, +inf]` 窗口开始，在 `alpha >= beta` 时跳过剩余兄弟分支。
  内部发生剪枝时的回传值可能只是界；根节点的全窗口结果与同设置的 Minimax 相同。

通过同名参数 `order_moves(state, moves, maximizing)` 可以比较不同访问顺序。
回调接收原始 `GameMove` 对象的元组，须返回这些对象的一个完整排列；不能删减、
重复或替换动作。默认不排序。以下回调让两个算法都逆序访问：

```python
def reverse_order(state, moves, maximizing):
    return reversed(moves)

reordered = alpha_beta(**kwargs, order_moves=reverse_order)
assert reordered.value == baseline.value
```

排序回调可以按问题相关的估值排序，为后续拓展实验保留接口。
没有默认排序、缓存或跨次调用复用的搜索状态，便于先建立可解释的基线。

## 统一统计口径

三种算法均返回 `SearchResult`，其中 `stats` 为 `SearchStats`；
`stats.to_dict()` 导出计数，`result.metrics()` 额外导出结果标量。
零值表示该操作没有发生；不适用或没有结果的字段用 `None`。

| 字段 | 口径 |
| --- | --- |
| `algorithm` | `astar`、`minimax` 或 `alpha_beta` |
| `elapsed_seconds` | `perf_counter_ns` 记录的搜索墙钟秒数，包含回调、排序及可选轨迹开销，不含导出 |
| `nodes_visited` | A* 中有效出队次数，排除过期项；博弈中递归进入次数；均含根和终局，重新进入再次计数 |
| `nodes_expanded` | 调用 `successors` 的次数；即使返回空后继也算一次；已识别终局或深度截断不算 |
| `nodes_generated` | 根计 1，加上每次展开产出的直接后继数；包含重复候选和随后被剪掉的直接兄弟 |
| `terminal_nodes` | A* 到达目标的次数；博弈的真终局和无合法动作叶子的次数 |
| `depth_limit_nodes` | 博弈中仅因深度限制而评估的非终局节点数 |
| `evaluation_calls` | 博弈算法调用 `evaluate` 的次数，不含用户排序回调内部自行调用的评价 |
| `heuristic_calls` | A* 计算启发值的次数，包含默认零启发函数，不对未改进的重复候选求值 |
| `max_depth` | 实际访问过的最大深度；根为 0，不等于请求的搜索深度 H |
| `frontier_peak` | A* 堆条目数峰值，包含未弹出的过期项；博弈为 `None`；不是内存字节数 |
| `duplicate_states` | A* 生成后继时已在 `best_g` 中出现的候选数，包含能够改进路径的候选 |
| `relaxations` | A* 成功降低/首次建立后继 g 并入队的次数，不包含初始根入队 |
| `reopened_nodes` | A* 再次展开此前已展开状态的次数 |
| `stale_queue_entries` | A* 弹出并丢弃的过期堆条目数 |
| `cutoff_events` | Alpha-Beta 因界相交且确有剩余兄弟而停止搜索的次数 |
| `pruned_branches` | 上述事件跳过的直接兄弟分支数，不包括未知的后代节点总数 |
| `status` | `success` 或 A* 的 `no_solution` |
| `path_cost` | A* 最终路径的总代价；博弈或无解时为 `None` |
| `best_value` | 博弈根节点的最优估值；A* 为 `None` |
| `solution_depth` | 返回路径的边数；A* 无解时为 `None`；博弈表示返回主变化路径的长度 |

`result.path`、`actions`、`best_action` 提供具体解。它们可能包含任意 Python
对象，因此不混入扁平指标表；后续题目适配层负责保存坐标、目标名称等字段。

**不把剪掉的直接分支数当作节省的节点数。** 两个博弈算法会生成当前层的合法
动作列表，但不会为统计而展开被剪掉的子树。实际节点节省通过完整基线比较：

| `compare_stats(baseline, candidate)` 字段 | 计算方式 |
| --- | --- |
| `visited_reduction_ratio` | `(基线访问数 - 候选访问数) / 基线访问数` |
| `expanded_reduction_ratio` | 同上，使用展开次数 |
| `evaluation_reduction_ratio` | 同上，使用评价函数调用次数 |
| `time_speedup` | `基线耗时 / 候选耗时` |

减少率可以为负；零分母返回 `None`，避免把未定义比率写成 0 或无穷。
所有减少率采用 0–1 的比例，显示为百分比时乘 100。

后续实验记录应在指标行附加输入编号和参数，确保解释节点变化时可以追溯设置：

```python
row = {
    "case_id": "synthetic_tree",
    "depth_limit": 2,
    "move_order": "input_order",
    "heuristic": None,
    "collect_trace": False,
    **pruned.metrics(),
}
```

这种扁平字典可直接传给 `csv.DictWriter` 或 `json.dump`。
深度 H、启发函数名称、访问顺序等是实验参数，由实验调用层命名和记录。
跨输入、不同深度的统计不能直接解释为剪枝收益；比较时保持输入、评价函数、
深度和轨迹开关一致，并只改变所研究的因素。短搜索的单次时间波动较大，
后续性能实验应重复测量并汇总，节点统计则可直接复现。

## 可选搜索轨迹

`collect_trace=True` 将事件保存到 `result.trace`，默认关闭以减少测量干扰。
每个事件有 `event`、`state`、`depth` 和 `details`：

- A* 的 `discover` / `visit` 包含 `g/h/f`，发现事件还包含父状态及动作；
  `stale` 记录被跳过的旧 g 与当前最优 g。
- 博弈的 `visit` 标记 MAX/MIN，Alpha-Beta 同时记录进入时的界；
  `evaluate` 记录终局、无动作或深度截断原因及评价值；`return` 记录回传值。
- Alpha-Beta 的 `cutoff` 记录 `alpha/beta`、回传值、直接跳过的分支数及动作。

轨迹包含原始状态对象；状态在搜索期间须保持稳定，写 JSON 前由后续适配层序列化。
完整轨迹可能较大，性能测试应统一关闭，过程分析再单独开启。

## 实验指标覆盖

| 评分关注点 | 已经提供 | 后续需要完成 |
| --- | --- | --- |
| 三种算法及状态管理 | 通用算法、四道题建模、路径更新、深度限制和剪枝条件 | 更多输入的适用性分析 |
| 搜索效率 | 生成/访问/展开数、时间、队列峰值、启发调用数、两种启发对照 | 重复运行与时间汇总 |
| 剪枝效率与访问顺序 | 两种博弈算法、评价次数、剪枝事件/分支、减少率、深度和顺序对照 | 根据数据解释开销差异 |
| 结果与过程分析 | 路径/代价、最优动作/值、距离矩阵、收益和可选轨迹 | 图表和行为分析 |
| 可复现性 | 标准库环境、运行入口、输入快照、指标口径和结果保存 | 图表自动生成 |
| 创新与拓展 | 外部启发、动作排序和特殊输入的接入点 | 自设场景、缓存等优化及对照证据 |

评分还包含报告结构、深入分析与独立思考，这些需要在后续正式实验和报告中完成，
不能仅凭通用接口或算法验证认定已取得对应分数。

# 实验二：搜索算法

实现 **A\*、Minimax、Alpha-Beta、统一统计接口和四道题的输入输出**。
提供统一运行入口，校验预期答案并保存性能数据和可选搜索轨迹。
提供报告图表生成、逐图数据说明及 PNG 导出；正式报告正文尚未编写。

## 环境与复现

- Python 3.10+；本次验证环境为 Windows / Python 3.13.9。
- 搜索及题目运行仅使用标准库。绘图依赖 Matplotlib 和 NumPy，安装命令为 `python -m pip install -r requirements.txt`。
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

每个计时配置固定运行 3 次，按 `elapsed_seconds` 排序保留中间一轮的完整内容；
耗时相同按轮次排序。题目四的 36 个点对也分别按此规则选择。
`--trace` 保存所选轮次的搜索过程；省略时只保存答案、指标和日志。
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
│   ├── utils/
│       ├── __init__.py
│       └── io.py               # JSON、CSV 与状态序列化
│   └── visualization/          # 图表样式、结果读取、四题制图与逐图说明
├── tests/                     # 预留：后续题目验证
├── scripts/
│   ├── run_all.py              # 运行、校验和结果保存
│   └── plot_results.py         # 从已有结果生成报告图表
├── results/                   # 自动生成，默认被 Git 忽略
└── report/
    └── figures/               # 按四道题分类的 PNG 图表
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
- `timing_runs.csv`：全部三轮的配置、轮次、耗时和必要标量；`is_median` 标记所选轮次。
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
`repeat_count=3` 和 `selected_repetition` 记录重复次数与实际保留轮次。
其他轮次只保留 `timing_runs.csv` 中的标量，不另存路径、完整结果或轨迹。

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
当前运行入口固定测量 3 次并保留中位数轮次，节点统计则可直接复现。

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
| 搜索效率 | 生成/访问/展开数、时间、队列峰值、启发调用数、两种启发对照、3 次测量与中位数轮次 | 根据数据解释开销差异 |
| 剪枝效率与访问顺序 | 两种博弈算法、评价次数、剪枝事件/分支、减少率、深度和顺序对照 | 根据数据解释开销差异 |
| 结果与过程分析 | 路径/代价、最优动作/值、距离矩阵、收益、轨迹及报告图表 | 正文中的解释与讨论 |
| 可复现性 | 运行入口、输入快照、指标口径、中位数轮次完整结果、三轮标量记录及图表生成命令 | 正文中的实验设置说明 |
| 创新与拓展 | 外部启发、动作排序和特殊输入的接入点 | 自设场景、缓存等优化及对照证据 |

评分还包含报告结构、深入分析与独立思考，这些需要在后续正式实验和报告中完成，
不能仅凭通用接口或算法验证认定已取得对应分数。

<!-- report-figures:begin -->
## 报告图表与数据说明

本组共 17 张图，覆盖四道题的结果及过程分析。暂不绘制创新与拓展部分，也不采用收益排序方案。
全部图表读取现有 `results/`，不重新执行搜索，不修改运行结果。每图仅导出 300 dpi PNG，按题目分类保存。
图片不绘制标题、图注或分析性文字。图名、各子图的读法、数据来源、计算口径和结论统一记录在本节。

复现命令（在项目根目录执行）：

```powershell
python -m pip install -r requirements.txt
python -B -X utf8 scripts/plot_results.py
```

绘图支持 `--results` 指定结果根目录、`--output` 指定图表目录、`--process` 指定说明文档、`--dpi` 指定 PNG 分辨率。
重复执行绘图命令更新同名图和本节说明，不产生新的搜索测量。

### 数据使用口径

- 每个计时配置测量 3 次，按 elapsed_seconds 排序取中间一轮；耗时相同按轮次排序。结果、轨迹、计数和耗时均来自选中的同一轮。
- 各题 timing_runs.csv 保留全部三轮的配置、轮次、耗时和必要标量，is_median 标记保留轮次；metrics.csv 的 selected_repetition 可回查该轮。
- 本组全部三轮均开启轨迹；耗时图读取保留轮次，不绘制误差条，不据此声称稳定速度排名。
- 访问、展开、生成分别使用各自计数，不混称为同一节点数；目标计入访问，不再展开。
- 剪枝效果按同深度、同访问顺序的 Minimax 基线计算；直接剪掉的分支数不当作未知子树的节点总数。
- 题目四的两两距离预计算与博弈搜索分开，不能把一次预计算重复加到每组决策中。
- 各首步的精确估值取自完整 Minimax 轨迹；Alpha-Beta 内部的剪枝回传可能只是界。
- 地图与输入从各题 `metadata.json` 的输入快照读取，避免当前配置变化后与旧结果混用。

### 图表索引

| 图号 | 内容 | 报告位置 | 文件 |
| --- | --- | --- | --- |
| 01 | 搜索覆盖与最短路径 | 2. 题目一：迷宫寻路 | [PNG](report/figures/problem1_maze/01_maze_search.png) |
| 02 | 优先队列与搜索过程快照 | 2. 题目一：迷宫寻路 | [PNG](report/figures/problem1_maze/02_maze_frontier.png) |
| 03 | 启发函数的搜索开销 | 2. 题目一：迷宫寻路 | [PNG](report/figures/problem1_maze/03_maze_efficiency.png) |
| 04 | 加权路径与代价累计 | 3. 题目二：加权地形 | [PNG](report/figures/problem2_weighted_terrain/04_weighted_path_cost.png) |
| 05 | 零代价终点与启发可采纳性 | 3. 题目二：加权地形 | [PNG](report/figures/problem2_weighted_terrain/05_weighted_heuristic.png) |
| 06 | 加权地图搜索开销 | 3. 题目二：加权地形 | [PNG](report/figures/problem2_weighted_terrain/06_weighted_efficiency.png) |
| 07 | 完整 Minimax 数值回传 | 4. 题目三：Alpha-Beta 剪枝 | [PNG](report/figures/problem3_game_tree/07_minimax_backup.png) |
| 08 | 两种访问顺序的剪枝位置 | 4. 题目三：Alpha-Beta 剪枝 | [PNG](report/figures/problem3_game_tree/08_alpha_beta_pruning.png) |
| 09 | 算法与访问顺序的开销对照 | 4. 题目三：Alpha-Beta 剪枝 | [PNG](report/figures/problem3_game_tree/09_game_tree_efficiency.png) |
| 10 | 宝藏地图与距离矩阵 | 5. 题目四：综合题 | [PNG](report/figures/problem4_treasure_game/10_treasure_map_matrix.png) |
| 11 | 状态表示与收益更新 | 5. 题目四：综合题 | [PNG](report/figures/problem4_treasure_game/11_treasure_state.png) |
| 12 | 深度改变首步决策 | 5. 题目四：综合题 | [PNG](report/figures/problem4_treasure_game/12_treasure_root_choices.png) |
| 13 | 主变化中的收益演化 | 5. 题目四：综合题 | [PNG](report/figures/problem4_treasure_game/13_treasure_scores.png) |
| 14 | 最优主变化的实际移动路线 | 5. 题目四：综合题 | [PNG](report/figures/problem4_treasure_game/14_treasure_routes.png) |
| 15 | 深度及顺序的搜索效率 | 5. 题目四：综合题 | [PNG](report/figures/problem4_treasure_game/15_treasure_efficiency.png) |
| 16 | 剪枝发生深度与直接分支数 | 5. 题目四：综合题 | [PNG](report/figures/problem4_treasure_game/16_treasure_pruning_depth.png) |
| 17 | 寻路与博弈阶段观测时间 | 5. 题目四：综合题 | [PNG](report/figures/problem4_treasure_game/17_treasure_runtime.png) |

### 图 01：搜索覆盖与最短路径

报告位置：2. 题目一：迷宫寻路。

数据来源与字段：

- [results/problem1_maze/metadata.json](results/problem1_maze/metadata.json)：`inputs.grid、start、goal`。
- [results/problem1_maze/astar_zero/result.json](results/problem1_maze/astar_zero/result.json)：`path、cost`。
- [results/problem1_maze/astar_manhattan/result.json](results/problem1_maze/astar_manhattan/result.json)：`path、cost`。
- [results/problem1_maze/astar_zero/trace.json](results/problem1_maze/astar_zero/trace.json)：`event=visit、state、depth、details.g/h/f`。
- [results/problem1_maze/astar_manhattan/trace.json](results/problem1_maze/astar_manhattan/trace.json)：`event=visit、state、depth、details.g/h/f`。

读图方式：左为 h=0，右为曼哈顿启发。绿色是访问过的状态，角标为访问序号，蓝线是最终最短路径。

计算与筛选：按 visit 事件标访问序号，叠加保存的最终路径。

图的含义：解释最短路径形成及两种启发函数的搜索覆盖差异。

本次结果：两方案均找到 7 步路径；访问数 16→14，减少 12.5%。

解释边界：访问含目标，目标不再展开；生成候选数与访问数口径不同。

### 图 02：优先队列与搜索过程快照

报告位置：2. 题目一：迷宫寻路。

数据来源与字段：

- [results/problem1_maze/metadata.json](results/problem1_maze/metadata.json)：`inputs.grid`。
- [results/problem1_maze/astar_manhattan/trace.json](results/problem1_maze/astar_manhattan/trace.json)：`discover/visit/stale、state、details.g/h/f`。
- [results/problem1_maze/astar_manhattan/result.json](results/problem1_maze/astar_manhattan/result.json)：`path`。

读图方式：从左到右为第 1、5、10、14 次有效访问完成后的状态。绿色为已访问，浅黄为有效 OPEN 候选，蓝框是当前节点，末图蓝线是最终路径。目标出队后仍可有其他 OPEN 候选。

计算与筛选：由事件按入队序号和 f 重放堆；g 与 best_g 不一致的项不计有效 OPEN；截取第 1、5、10、14 次有效访问完成后的状态。

图的含义：展示 OPEN 如何推动搜索，并说明相同 f 的访问顺序。

本次结果：本例曼哈顿方案的 14 次有效出队 f 均为 7，仍会访问多条同优先级分支；终点出队时剩余 OPEN 的最小 f 为 9，无需继续搜索。

解释边界：画面中 OPEN 为有效候选；统计表中的堆峰值还可能包含过期项。

### 图 03：启发函数的搜索开销

报告位置：2. 题目一：迷宫寻路。

数据来源与字段：

- [results/problem1_maze/metrics.csv](results/problem1_maze/metrics.csv)：`heuristic、nodes_visited、nodes_expanded、nodes_generated、frontier_peak、relaxations、elapsed_seconds、collect_trace`。

读图方式：从左到右依次为节点访问/展开/生成、堆峰值与成功松弛、本次观测耗时。蓝色是 h=0，橙色是曼哈顿；耗时柱使用横轴标签区分方案。

计算与筛选：按 heuristic 配对读取两行指标；耗时由秒乘 10^6 转为微秒。

图的含义：比较访问、展开、生成、队列峰值、松弛和本次耗时。

本次结果：访问数 16→14，减少 12.5%，路径长度保持 7。

解释边界：每个配置测量 3 次，保留耗时中位数轮次的完整结果；三轮简要记录见 timing_runs.csv，不据此推断稳定速度优势。

### 图 04：加权路径与代价累计

报告位置：3. 题目二：加权地形。

数据来源与字段：

- [results/problem2_weighted_terrain/metadata.json](results/problem2_weighted_terrain/metadata.json)：`inputs.grid`。
- [results/problem2_weighted_terrain/summary.json](results/problem2_weighted_terrain/summary.json)：`path、cost、step_costs、cumulative_costs`。

读图方式：左侧为地形权值及路线，# 为路径步号；右侧灰柱为本步代价，蓝线为累计 g。起点步号 0 不是一次移动。

计算与筛选：在地图叠加路径步号，以 step_costs 画柱、cumulative_costs 画折线。

图的含义：说明按进入格子计费，展示总代价如何累计。

本次结果：路径有 8 次移动，最后进入 E 的代价为 0，累计总代价为 7。

解释边界：起点位置的 step_cost 为 0，表示未发生进入移动。

### 图 05：零代价终点与启发可采纳性

报告位置：3. 题目二：加权地形。

数据来源与字段：

- [results/problem2_weighted_terrain/metadata.json](results/problem2_weighted_terrain/metadata.json)：`inputs.grid、goal`。
- [results/problem2_weighted_terrain/summary.json](results/problem2_weighted_terrain/summary.json)：`path、cost、cumulative_costs`。

读图方式：横轴按实际最优路径排列状态。橙色为原始 D，蓝色为修正启发，绿色叉号为最优路径后缀的真实代价；本例后两条曲线重合。

计算与筛选：沿已得最优路径计算 D、修正 h=max(D−1,0)×m 和 h*=总代价−当前累计代价。最优路径后缀也是最优路径，故其代价是这些路径状态的真实剩余代价。

图的含义：用终点前一格的反例解释原始曼哈顿为什么可能高估，并说明修正公式。

本次结果：(4,3) 到 E 的真实代价为 0，原始 D=1，构成高估；本例修正启发与所示后缀代价重合。

解释边界：只比较实际最优路径上的状态；修正启发的整体可采纳性来自非负进入代价下界，不来自几处曲线重合。

### 图 06：加权地图搜索开销

报告位置：3. 题目二：加权地形。

数据来源与字段：

- [results/problem2_weighted_terrain/metrics.csv](results/problem2_weighted_terrain/metrics.csv)：`heuristic、nodes_visited、nodes_expanded、nodes_generated、frontier_peak、relaxations、elapsed_seconds、collect_trace`。

读图方式：从左到右依次比较节点次数、堆峰值及松弛、本次耗时；两种参数由图例和横轴标签区分。

计算与筛选：配对读取零启发与修正曼哈顿的指标，秒转微秒。

图的含义：将可采纳性讨论与实测搜索开销连接。

本次结果：访问数 15→11，减少 26.7%，最小代价都为 7。

解释边界：每个配置测量 3 次，保留耗时中位数轮次的完整结果；三轮简要记录见 timing_runs.csv，不据此推断稳定速度优势。

### 图 07：完整 Minimax 数值回传

报告位置：4. 题目三：Alpha-Beta 剪枝。

数据来源与字段：

- [results/problem3_game_tree/metadata.json](results/problem3_game_tree/metadata.json)：`inputs.tree_structure：children、value、is_maximizing_player`。
- [results/problem3_game_tree/left_to_right/minimax/trace.json](results/problem3_game_tree/left_to_right/minimax/trace.json)：`visit/evaluate/return、depth、details.value`。

读图方式：最上方是根，底层是输入叶值。节点内标玩家及回传值；绿色箭头是各节点选中的回传方向。

计算与筛选：按 DFS 深度和原始子节点索引解析事件；各节点用完整 Minimax 回传值标注。

图的含义：说明叶子如何经 MAX/MIN 交替得到根得分。

本次结果：中间 MAX 值为 [5,9,9,2]，MIN 值为 [5,2]，根值为 5。

解释边界：两个内容相同的 [6,9] 子树按不同分支定位，不合并成一个访问。

### 图 08：两种访问顺序的剪枝位置

报告位置：4. 题目三：Alpha-Beta 剪枝。

数据来源与字段：

- [results/problem3_game_tree/metadata.json](results/problem3_game_tree/metadata.json)：`inputs.tree_structure：children、value、is_maximizing_player`。
- [results/problem3_game_tree/left_to_right/alpha_beta/trace.json](results/problem3_game_tree/left_to_right/alpha_beta/trace.json)：`visit/return/cutoff、details.alpha/beta/value/pruned_actions`。
- [results/problem3_game_tree/reverse/alpha_beta/trace.json](results/problem3_game_tree/reverse/alpha_beta/trace.json)：`visit/return/cutoff、details.alpha/beta/value/pruned_actions`。

读图方式：上图从左到右访问，下图每层逆序访问；树的位置固定。# 为访问序号，红色 × 是未访问叶子，橙色节点的 ≥ 数值表示剪枝后的下界。

计算与筛选：按实际顺序解析轨迹、标记访问序号与未访问叶子；剪枝节点的回传注明下界。

图的含义：解释 alpha>=beta 的依据，以及相同开销下剪枝位置仍可不同。

本次结果：从左到右在 alpha=6、beta=5 时跳过叶值 9；逆序在 alpha=9、beta=2 时跳过另一分支的叶值 6；均访问 14 个节点。

解释边界：>=6 等标记为回传界，不是完整子树精确值；不能宣称本例逆序显著减少节点。

### 图 09：算法与访问顺序的开销对照

报告位置：4. 题目三：Alpha-Beta 剪枝。

数据来源与字段：

- [results/problem3_game_tree/metrics.csv](results/problem3_game_tree/metrics.csv)：`algorithm、move_order、nodes_visited、evaluation_calls、elapsed_seconds、collect_trace`。

读图方式：左图访问节点，中图叶子评价次数，右图本次耗时；横轴均比较从左到右和逆序，蓝色 Minimax、橙色 Alpha-Beta。

计算与筛选：按算法和访问顺序分别比较访问、叶子评价和本次微秒耗时。

图的含义：用数据判断剪枝是否减少工作，而不是仅展示相同答案。

本次结果：两种顺序均是 Minimax 15 次访问 / 8 次评价，对应 Alpha-Beta 14 次访问 / 7 次评价。逆序配置保留的中位数轮次耗时为 Minimax 64.2 µs、Alpha-Beta 101.6 µs；3 次测量仍不足以据此分离剪枝管理开销与测量波动。

解释边界：每个配置测量 3 次，保留耗时中位数轮次的完整结果；三轮简要记录见 timing_runs.csv，不据此推断稳定速度优势。

### 图 10：宝藏地图与距离矩阵

报告位置：5. 题目四：综合题。

数据来源与字段：

- [results/problem4_treasure_game/metadata.json](results/problem4_treasure_game/metadata.json)：`inputs.grid、treasure_values`。
- [results/problem4_treasure_game/distance_matrix/matrix.json](results/problem4_treasure_game/distance_matrix/matrix.json)：`labels、matrix`。

读图方式：左侧是原地图，V 为宝藏价值；右侧矩阵按行起点、列终点排列，单元格数字为最小移动代价。

计算与筛选：按 labels 排列热力矩阵，地图格子显示权值、标记和宝藏价值。

图的含义：给出后续 Gain 计算所用的最小移动代价和地图环境。

本次结果：矩阵为 6×6，所有点可达，主对角线为 0。

解释边界：全部有向点对分别搜索；本例的对称矩阵不意味着可在任意进入代价模型中省略反向搜索。

### 图 11：状态表示与收益更新

报告位置：5. 题目四：综合题。

数据来源与字段：

- [results/problem4_treasure_game/metadata.json](results/problem4_treasure_game/metadata.json)：`inputs.treasure_values`。
- [results/problem4_treasure_game/distance_matrix/matrix.json](results/problem4_treasure_game/distance_matrix/matrix.json)：`labels、matrix`。
- [results/problem4_treasure_game/depth_4/input_order/minimax/result.json](results/problem4_treasure_game/depth_4/input_order/minimax/result.json)：`best_action、best_value、principal_variation、states`。

读图方式：左表 s0 是初始状态，s1 是 A 选择 T3 后的状态；右表是该动作的玩家、目标、价值 V、距离 d 和 Gain=V−d。

计算与筛选：用 H=4 主变化的前后两个实际状态，结合矩阵中的 A→T3 距离演示一次更新。

图的含义：说明双方位置、剩余集合、收益和当前玩家怎样共同定义状态。

本次结果：A→T3 的距离 8、价值 7，Gain=-1；A 位置变为 T3，仅移除 T3，再由 B 行动。

解释边界：这是完整主变化的一步示例，不能用即时 Gain 直接替代整个博弈价值。

### 图 12：深度改变首步决策

报告位置：5. 题目四：综合题。

数据来源与字段：

- [results/problem4_treasure_game/metadata.json](results/problem4_treasure_game/metadata.json)：`inputs.treasure_values`。
- [results/problem4_treasure_game/depth_2/input_order/minimax/result.json](results/problem4_treasure_game/depth_2/input_order/minimax/result.json)：`best_action、best_value、principal_variation、states`。
- [results/problem4_treasure_game/depth_4/input_order/minimax/result.json](results/problem4_treasure_game/depth_4/input_order/minimax/result.json)：`best_action、best_value、principal_variation、states`。
- [results/problem4_treasure_game/depth_2/input_order/minimax/trace.json](results/problem4_treasure_game/depth_2/input_order/minimax/trace.json)：`depth=1 的 return、state.position_a、details.value`。
- [results/problem4_treasure_game/depth_4/input_order/minimax/trace.json](results/problem4_treasure_game/depth_4/input_order/minimax/trace.json)：`depth=1 的 return、state.position_a、details.value`。

读图方式：横轴是 A 固定的首步目标，柱高为后续双方最优行动下的 U。蓝色 H=2，橙色 H=4；MAX 在同色柱中选择最大值。

计算与筛选：提取完整 Minimax 根下四个首步的回传值，分别画 H=2 与 H=4；最大者为该深度的首步选择。

图的含义：解释短视决策与四回合决策为什么不同。

本次结果：H=2：T1=-4、T2=-1、T3=-2、T4=-4；H=4：T1=-5、T2=1、T3=3、T4=-7。H=2 只计算双方各一次行动；H=4 纳入后续位置和剩余宝藏，首步 T3 虽即时 Gain=-1，却取得终局 U=3。

解释边界：内部子树估值必须取完整 Minimax；Alpha-Beta 的剪枝返回界不能代替精确分支值。

### 图 13：主变化中的收益演化

报告位置：5. 题目四：综合题。

数据来源与字段：

- [results/problem4_treasure_game/depth_2/input_order/minimax/result.json](results/problem4_treasure_game/depth_2/input_order/minimax/result.json)：`best_action、best_value、principal_variation、states`。
- [results/problem4_treasure_game/depth_4/input_order/minimax/result.json](results/problem4_treasure_game/depth_4/input_order/minimax/result.json)：`best_action、best_value、principal_variation、states`。

读图方式：左图 H=2，右图 H=4。蓝色是 Score_A、橙色是 Score_B、绿色虚线是 U；横轴给出行动玩家、目标及该步 Gain。

计算与筛选：逐状态提取 score_a、score_b，计算 U；相邻状态的单方收益差为该步 Gain。

图的含义：解释负收益动作、剩余宝藏约束和终局收益差的形成。

本次结果：H=2：A 得 2、B 得 3，U=-1；H=4：A 得 -1、B 得 -4，U=3。

解释边界：只展示各自深度下的一条最优主变化，不是所有分支或一棵完整策略树。

### 图 14：最优主变化的实际移动路线

报告位置：5. 题目四：综合题。

数据来源与字段：

- [results/problem4_treasure_game/metadata.json](results/problem4_treasure_game/metadata.json)：`inputs.grid`。
- [results/problem4_treasure_game/distance_matrix/paths.json](results/problem4_treasure_game/distance_matrix/paths.json)：`from_point、to_point、path、cost`。
- [results/problem4_treasure_game/depth_2/input_order/minimax/result.json](results/problem4_treasure_game/depth_2/input_order/minimax/result.json)：`best_action、best_value、principal_variation、states`。
- [results/problem4_treasure_game/depth_4/input_order/minimax/result.json](results/problem4_treasure_game/depth_4/input_order/minimax/result.json)：`best_action、best_value、principal_variation、states`。

读图方式：左图 H=2，右图 H=4。蓝色为 A、橙色为 B，实线是前两步、虚线是后两步；目标旁的圆角标是领取回合编号。

计算与筛选：用主变化每步前的玩家位置和目标查找已保存的 A* 路径，按玩家及回合编号叠加。

图的含义：把博弈动作与地图中的移动连接，说明行动后位置更新。

本次结果：H=2 的领取顺序为 T2→T3；H=4 为 T3→T1→T2→T4。

解释边界：路径可能经过未选择的宝藏，圆角标仅表示实际选中领取的目标。

### 图 15：深度及顺序的搜索效率

报告位置：5. 题目四：综合题。

数据来源与字段：

- [results/problem4_treasure_game/metrics.csv](results/problem4_treasure_game/metrics.csv)：`筛选 phase=game，move_order=input/reverse；algorithm、depth_limit、nodes_visited、nodes_expanded、evaluation_calls`。

读图方式：左上访问次数、右上展开次数、左下评价次数、右下访问减少率。横轴按深度与访问顺序配对；前三图蓝色 Minimax、橙色 Alpha-Beta。

计算与筛选：按深度和顺序配对 Minimax / Alpha-Beta；减少率=(基线访问−剪枝访问)/基线访问。

图的含义：分别比较深度增长和访问顺序对搜索工作的影响。

本次结果：H=2 输入顺序：17→13，减少 23.5%；H=4 输入顺序：65→47，减少 27.7%。

解释边界：不将 36 次距离搜索重复加到每组博弈开销，不将直接剪枝分支数用作节省节点数。

### 图 16：剪枝发生深度与直接分支数

报告位置：5. 题目四：综合题。

数据来源与字段：

- [results/problem4_treasure_game/depth_2/input_order/alpha_beta/trace.json](results/problem4_treasure_game/depth_2/input_order/alpha_beta/trace.json)：`event=cutoff、depth、details.pruned_branches、alpha、beta`。
- [results/problem4_treasure_game/depth_2/reverse_order/alpha_beta/trace.json](results/problem4_treasure_game/depth_2/reverse_order/alpha_beta/trace.json)：`event=cutoff、depth、details.pruned_branches、alpha、beta`。
- [results/problem4_treasure_game/depth_4/input_order/alpha_beta/trace.json](results/problem4_treasure_game/depth_4/input_order/alpha_beta/trace.json)：`event=cutoff、depth、details.pruned_branches、alpha、beta`。
- [results/problem4_treasure_game/depth_4/reverse_order/alpha_beta/trace.json](results/problem4_treasure_game/depth_4/reverse_order/alpha_beta/trace.json)：`event=cutoff、depth、details.pruned_branches、alpha、beta`。
- [results/problem4_treasure_game/metrics.csv](results/problem4_treasure_game/metrics.csv)：`phase=game，algorithm=alpha_beta，move_order=input/reverse；cutoff_events、pruned_branches`。

读图方式：上排 H=2，下排 H=4；左列是各深度的剪枝事件数，右列是跳过的直接分支数。蓝色输入顺序、橙色逆序。

计算与筛选：按 cutoff.depth 分组，分别统计事件数和 details.pruned_branches 之和，并与记录的计数器核对。

图的含义：说明一次剪枝发生的位置也会影响收益，不能只比较剪枝次数。

本次结果：H=4 输入顺序 5 次剪枝、跳过 6 个直接分支、访问 47；逆序 4 次剪枝、跳过 5 个直接分支、访问 46。

解释边界：不遍历未访问子树推算其后代总数；实际节省节点需与同设置 Minimax 对照。

### 图 17：寻路与博弈阶段观测时间

报告位置：5. 题目四：综合题。

数据来源与字段：

- [results/problem4_treasure_game/distance_matrix/matrix.json](results/problem4_treasure_game/distance_matrix/matrix.json)：`labels`。
- [results/problem4_treasure_game/metrics.csv](results/problem4_treasure_game/metrics.csv)：`phase=distance 的全部 36 行，以及 phase=game、move_order=input/reverse；elapsed_seconds、from_point、to_point、algorithm、depth_limit、collect_trace`。

读图方式：左侧热力矩阵是各点对 A* 的中位数轮次微秒耗时；右侧是不同深度、顺序下保留的博弈耗时，蓝色 Minimax、橙色 Alpha-Beta。

计算与筛选：点对中位数轮次耗时画为 6×6 热力图；36 个点对各自保留的耗时求和；博弈阶段按算法、深度和顺序分组，秒转微秒。

图的含义：区分可复用的距离预计算与之后的博弈决策开销。

本次结果：36 个点对各自中位数轮次的 A* 耗时之和为 1.7187 ms。不同深度复用同一组距离；图中未重复计入预计算。

解释边界：每个配置测量 3 次，保留耗时中位数轮次的完整结果；三轮简要记录见 timing_runs.csv，不据此推断稳定速度优势。各点对中位数之和不是预计算总耗时的中位数，也不含建图与文件写入，不能冒充完整程序端到端耗时。

<!-- report-figures:end -->

# 实验二：搜索算法

实现 A*、Minimax 与 Alpha-Beta，完成迷宫寻路、加权地形、博弈树搜索和竞争性宝藏分配。通过启发函数、搜索深度及动作顺序对照，记录正确性、搜索工作量和耗时。提供即时收益排序优化及两组拓展场景。

## 环境与安装

- Python **3.10+**，搜索和结果导出使用标准库。
- 绘图依赖：`matplotlib>=3.9,<4`、`numpy>=1.26,<3`，见 [requirements.txt](requirements.txt)。
- 已验证环境：Windows 11、Python 3.13.9、Matplotlib 3.11.2、NumPy 2.1.3。

以下命令均在仓库根目录、同一 Python 环境中执行：

```shell
python -m pip install -r requirements.txt
```

## 目录结构

源码、配置和图表逐文件说明。搜索结果按代表性配置展开，同结构的深度、访问顺序和场景合并标注。

```text
.
├── .gitignore                             # 缓存、虚拟环境和本地测试的忽略规则
├── README.md                              # 环境、输入、运行与结果说明
├── requirements.txt                       # 绘图依赖及版本范围
├── configs/                               # 实验输入
│   ├── test_cases.json                    # 四题原始输入与预期结果
│   ├── exp2_extension_case_A.json          # 场景 A，宝藏价值为 3/12/4/11
│   └── exp2_extension_case_B.json          # 场景 B，宝藏价值为 13/6/1/12
├── scripts/                               # 命令行入口
│   ├── run_all.py                         # 运行搜索、校验答案并保存三轮记录
│   ├── plot_results.py                    # 生成原始四题的 17 张图
│   └── plot_gain_optimization.py           # 生成即时收益排序的 4 张优化对照图
├── src/                                   # 搜索实现与题目适配
│   ├── __init__.py                        # 源码包入口
│   ├── algorithms/                        # 通用搜索算法
│   │   ├── __init__.py                    # 导出算法、统计和公共类型
│   │   ├── astar.py                       # 优先队列 A*、状态松弛与路径回溯
│   │   ├── minimax.py                     # 完整极大极小递归搜索
│   │   ├── alpha_beta.py                  # 上下界更新与 Alpha-Beta 剪枝
│   │   ├── _game.py                       # 博弈算法共享的终局判断、排序和评价
│   │   ├── models.py                      # 转移边、动作、搜索结果与轨迹事件类型
│   │   └── stats.py                       # 操作计数、搜索计时与基线比较
│   ├── problems/                          # 四题状态和规则
│   │   ├── __init__.py                    # 题目模块包入口
│   │   ├── _grid.py                       # 网格校验、四邻接后继与修正曼哈顿启发
│   │   ├── problem1.py                    # 单位移动代价的迷宫寻路接口
│   │   ├── problem2.py                    # 按进入格权值计费的最小代价寻路接口
│   │   ├── problem3.py                    # 博弈树解析、玩家交替校验与搜索接口
│   │   └── problem4.py                    # 宝藏状态、距离矩阵、收益更新与 gain 排序
│   ├── utils/                             # 结果保存
│   │   ├── __init__.py                    # 序列化工具包入口
│   │   └── io.py                          # 状态序列化与 JSON、CSV 写入
│   └── visualization/                     # 图表生成
│       ├── __init__.py                    # 绘图模块包入口
│       ├── common.py                      # 中文字体、配色、柱状图和地图绘制工具
│       ├── data.py                        # 读取指标、重放轨迹与提取根子树值
│       ├── catalog.py                     # 图号、文件名和输出目录索引
│       ├── export.py                      # 绘图输入文件的 SHA-256 校验
│       ├── pathfinding.py                 # 两类寻路任务的路径、启发与开销图
│       ├── game_tree.py                   # 博弈树数值回传、剪枝位置与效率图
│       └── treasures.py                   # 宝藏地图、状态、决策、收益与剪枝开销图
├── tests/                                 # 本地回归测试
│   ├── .gitkeep                           # 目录占位文件
│   └── test_repeated_runs.py               # 校验三轮执行、中位数选择与完整结果保留
├── results/                               # 搜索结果
│   ├── .gitkeep                           # 目录占位文件
│   ├── problem1_maze/                     # 题目一，展示题目级通用文件
│   │   ├── summary.json                   # 最终答案与校验状态
│   │   ├── metadata.json                  # 输入快照、SHA-256、参数、时间和环境
│   │   ├── metrics.csv                    # 本题各方案选中轮次的指标
│   │   ├── timing_runs.csv                # 全部三轮的标量记录
│   │   ├── run.log                        # 搜索输出与校验日志
│   │   ├── astar_zero/                    # 零启发方案
│   │   │   ├── result.json                # 路径、总代价与求解状态
│   │   │   ├── metrics.csv                # 当前方案的计数与耗时
│   │   │   └── trace.json                 # 入队、访问、松弛等搜索事件
│   │   └── astar_manhattan/               # 曼哈顿启发，文件结构同 astar_zero
│   ├── problem2_weighted_terrain/          # 题目二，结构同题目一
│   ├── problem3_game_tree/                 # 题目三，题目级文件同题目一
│   │   ├── left_to_right/                 # 从左到右访问
│   │   │   ├── metrics.csv                # 本顺序的两种算法指标
│   │   │   ├── minimax/                   # result、metrics、trace 三类文件
│   │   │   └── alpha_beta/                # 同类文件，包含剪枝轨迹
│   │   └── reverse/                       # 逆序访问，结构同 left_to_right
│   ├── problem4_treasure_game/             # 题目四，题目级文件同题目一
│   │   ├── distance_matrix/               # 寻路预计算
│   │   │   ├── matrix.json                # 点名顺序与 6×6 最小代价矩阵
│   │   │   ├── matrix.csv                 # 表格形式的距离矩阵
│   │   │   ├── paths.json                 # 36 个有向点对的实际路径与代价
│   │   │   ├── metrics.csv                # 各点对 A* 搜索指标
│   │   │   └── traces/                    # 点对轨迹，按 起点_to_终点.json 命名
│   │   ├── depth_2/                       # H=2 博弈搜索
│   │   │   ├── metrics.csv                # 本深度全部顺序与算法的指标
│   │   │   ├── input_order/               # 输入顺序
│   │   │   │   ├── metrics.csv            # 本顺序的算法指标
│   │   │   │   ├── minimax/               # 文件结构同 alpha_beta
│   │   │   │   └── alpha_beta/            # Alpha-Beta 搜索结果
│   │   │   │       ├── result.json        # 最优首步、根值、主变化与对应状态
│   │   │   │       ├── metrics.csv        # 计数、耗时与相对 Minimax 的减少率
│   │   │   │       └── trace.json         # 访问、评价、回传与上下界剪枝事件
│   │   │   ├── reverse_order/             # 逆序，结构同 input_order
│   │   │   └── gain_order/                # 即时收益排序，结构同 input_order
│   │   └── depth_4/                       # H=4，结构同 depth_2
│   ├── exp2_extension_case_A/              # 场景 A 结果
│   │   └── problem4_treasure_game/         # 结构同原始题目四
│   ├── exp2_extension_case_B/              # 场景 B，结构同场景 A
│   ├── exp2_extension_comparison.json      # 场景配置、各方案指标与增减率汇总
│   └── exp2_extension_comparison.csv       # 按场景和深度展开的对照表
└── report/                                # 报告素材
    ├── .gitkeep                           # 目录占位文件
    └── figures/                           # 300 dpi PNG 图表
        ├── problem1_maze/                  # 迷宫寻路图表
        │   ├── 01_maze_search.png          # 搜索覆盖与最短路径
        │   ├── 02_maze_frontier.png        # 优先队列与搜索过程快照
        │   └── 03_maze_efficiency.png      # 启发函数对搜索开销的影响
        ├── problem2_weighted_terrain/      # 加权地形图表
        │   ├── 04_weighted_path_cost.png   # 加权路径与逐步代价累计
        │   ├── 05_weighted_heuristic.png   # 原始、修正启发与真实剩余代价
        │   └── 06_weighted_efficiency.png  # 加权地形的搜索开销
        ├── problem3_game_tree/             # 极大极小博弈树图表
        │   ├── 07_minimax_backup.png       # Minimax 数值回传过程
        │   ├── 08_alpha_beta_pruning.png   # 两种访问顺序的剪枝位置
        │   └── 09_game_tree_efficiency.png # 算法与访问顺序的开销对照
        ├── problem4_treasure_game/         # 宝藏分配图表
        │   ├── 10_treasure_map_matrix.png  # 宝藏地图与距离矩阵
        │   ├── 11_treasure_state.png       # 博弈状态与单步收益更新
        │   ├── 12_treasure_root_choices.png # 两种深度的根动作回传值
        │   ├── 13_treasure_scores.png      # 主变化中的收益演化
        │   ├── 14_treasure_routes.png      # 最优主变化的实际移动路线
        │   ├── 15_treasure_efficiency.png  # 深度与顺序的搜索效率
        │   ├── 16_treasure_pruning_depth.png # 剪枝深度与直接分支数
        │   └── 17_treasure_runtime.png     # 寻路与博弈阶段的观测耗时
        └── gain_order_optimization/        # 即时收益排序优化图表
            ├── 18_gain_search_workload.png # gain 与三个对照组的搜索工作量
            ├── 19_gain_incremental_reduction.png # 相对各基线的增量节省
            ├── 20_gain_bound_and_subtree_work.png # 根下界建立与子树访问量
            └── 21_gain_runtime_repetitions.png # 三轮耗时、中位数与观测范围
```

## 输入与实验设置

输入由 `configs/` 中的 JSON 提供。坐标使用从 0 开始的 `[row, col]`，网格按四邻接移动，`X` 表示障碍。

| 配置键 | 主要字段 | 对照设置 |
| --- | --- | --- |
| `problem1` | `start`、`goal`、`grid`、`expected_cost` | A* 比较零启发与曼哈顿距离，`expected_path` 为参考路径 |
| `problem2` | `start`、`goal`、`grid`、`expected_cost` | 按进入格子计费，E 代价为 0，比较零启发与修正曼哈顿启发 |
| `problem3` | `tree_structure`、`expected_value` | 节点用 `children`、叶子用 `value`，根为 MAX，比较两种算法及正序/逆序 |
| `problem4` | `grid`、`treasure_values`、`depths`、`expected` | H=2/4，比较 Minimax 与 Alpha-Beta 及输入顺序、逆序、`gain` 排序 |

题目四先用 A* 计算 6×6 有向最小代价矩阵，再交替搜索 A、B 的行动。每步收益为宝藏价值减移动代价，评价为 `U=Score_A−Score_B`。H 计行动步数，根深度为 0。每回合领取选中的一个宝藏，双方位置和已领取宝藏的位置均可通行。

`gain` 在每个展开节点按后继效用排序：MAX 降序、MIN 升序，等价于优先尝试当前玩家即时收益较大的动作。各方案共享相同的合法动作与评价函数。搜索顺序由输入和排序规则确定，同值时选择先访问的动作。

## 运行与绘图

先运行四题及全部顺序对照，保存轨迹，再生成图片：

```shell
python -B -X utf8 scripts/run_all.py --compare --trace
python -B -X utf8 scripts/plot_results.py
python -B -X utf8 scripts/plot_gain_optimization.py
```

| 参数 | 用途 |
| --- | --- |
| `--problem 1/2/3/4` | 选择题目，默认运行全部 |
| `--cases PATH` | 指定输入 JSON，默认 `configs/test_cases.json` |
| `--compare` | 为题目三增加逆序，为题目四增加逆序和 gain，两种博弈算法始终参与 |
| `--trace` | 保存搜索轨迹，供上述两套绘图读取 |
| `--output DIR` | 指定结果根目录，默认 `results/` |

重复运行会更新所选题目的结果目录。用 `--output` 指定新的结果根目录，可保存另一组测量。绘图读取结果并更新同名 PNG，默认 300 dpi，可用 `--dpi` 修改。

两套图形布局对应原始样例。`plot_results.py --results` 接收包含四题的结果根目录，`plot_gain_optimization.py --results` 接收题目四目录。两者均支持 `--output` 指定图片目录。

运行成功以 `All requested cases passed.` 结束。原始样例应得到：

| 题目 | 预期结果 |
| --- | --- |
| 迷宫寻路 | 返回一条 7 步最短路径，总代价 7 |
| 加权地形 | 最小总代价 7，当前返回路径为 8 步 |
| 博弈树 | 根节点最优值 5 |
| 宝藏分配 | H=2：T2、U=−1，H=4：T3、U=3 |

## 拓展场景复现

A、B 沿用原始地图和规则，宝藏价值取下表中的两组设置。配置的顶层键为 `problem4`，运行命令指定 `--problem 4`：

```shell
python -B -X utf8 scripts/run_all.py --problem 4 --compare --trace --cases configs/exp2_extension_case_A.json --output results/exp2_extension_case_A
python -B -X utf8 scripts/run_all.py --problem 4 --compare --trace --cases configs/exp2_extension_case_B.json --output results/exp2_extension_case_B
```

| 场景 | T1/T2/T3/T4 价值 | H=2 访问节点：输入 AB → gain AB | H=4 访问节点：输入 AB → gain AB |
| --- | --- | --- | --- |
| A | 3 / 12 / 4 / 11 | 14 → 11 | 46 → 31 |
| B | 13 / 6 / 1 / 12 | 11 → 13 | 38 → 47 |

A 的最优结果为 H=2：T2、U=7，H=4：T2、U=14。B 为 H=2：T1、U=1，H=4：T1、T2 并列最优，U=6，不同访问顺序可以返回不同的最优首步。

跨场景数据见 [汇总 JSON](results/exp2_extension_comparison.json) 和 [汇总 CSV](results/exp2_extension_comparison.csv)。两份文件保存本次跨场景对照的汇总快照。以上命令生成各场景的独立结果，场景重跑后的跨场景汇总需单独更新。

## 输出与指标口径

先查看题目目录的 `summary.json` 获取答案，再通过 `metrics.csv` 比较方案。`timing_runs.csv` 保留三轮记录，`is_median` 标记选中轮次。各层 `metrics.csv` 汇总当前目录及下级方案，`result_directory` 指向具体方案目录。

- **重复与计时**：每个配置运行 3 次，答案、计数、耗时和轨迹统一选自耗时中位数轮次。`elapsed_seconds` 记录搜索过程，覆盖排序、回调和可选轨迹。距离预计算与博弈搜索分别计时，结果导出在搜索结束后执行。
- **计数**：`nodes_visited` 为有效出队或递归进入次数，含根和终局。`nodes_expanded` 为生成后继的次数。`evaluation_calls` 统计博弈叶子评价，动作排序通过后继状态的 utility 取值。
- **剪枝**：`cutoff_events` 记录跳过剩余兄弟的剪枝事件，`pruned_branches` 记录跳过的直接兄弟分支数。实际节点节省量由完整 Minimax 与 Alpha-Beta 的访问数之差计算。
- **对照**：Alpha-Beta 的减少率以同深度、同顺序 Minimax 为基线。拓展汇总的 `change_ratio=(gain−baseline)/baseline`，负数表示减少。

## 核验与结果解读

运行器自动核对路径代价、根值和同顺序算法结果，绘图脚本通过文件哈希核验结果文件的完整性。修改输入时同步维护 `expected` 等预期字段，校验差异通过异常和 `run.log` 定位。

搜索工作量通过节点访问数和评价次数比较，耗时作为三轮实测的辅助指标。场景 A 中 gain 减少访问，场景 B 中 gain 增加访问，展示了宝藏价值分布对排序与剪枝的影响。博弈搜索采用递归展开，搜索规模随深度增长。H=2 的 U 对应双方各行动一次后的局面，H=4 的 U 对应四回合终局。

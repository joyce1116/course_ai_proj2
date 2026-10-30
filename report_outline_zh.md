# 实验二报告撰写大纲与图表安排

依据：已通读《实验二要求_new.pdf》全部 17 页，重点对照第 16 页报告要求和第 17 页评分细则，并核对本项目的算法实现、实验配置、现有 17 张 PNG、metrics.csv、result.json 和 trace.json。本文件是撰写大纲，不是已完成的实验报告，也不新增实验结论。

## 一、整体结构与篇幅安排

建议采用“目标与设计 → 四题结果及分析 → 创新与拓展 → 总结”的结构，把解释算法行为的内容放在对应题目中。PDF 第 16 页列出的“图表展示与独立思考”适合贯穿全文，不必单独设一个重复汇总结果的章节。

| 章节 | 建议小节 | 建议篇幅，不含封面 | 核心图表 |
| --- | --- | --- | --- |
| 1 实验目标、算法设计与实验设置 | 1.1 目标；1.2 A*；1.3 Minimax 与 Alpha-Beta；1.4 设置与统计口径 | 1.5～2 页 | 可选一张紧凑的设置表 |
| 2 题目一：迷宫寻路 | 2.1 建模与路径；2.2 启发函数对照及过程解释 | 1～1.5 页 | 图 01 |
| 3 题目二：加权地形 | 3.1 代价累计；3.2 启发可采纳性；3.3 性能对照 | 1.5～2 页 | 图 04、05 |
| 4 题目三：博弈树求值与剪枝 | 4.1 数值回传；4.2 剪枝过程；4.3 顺序与开销 | 1.5～2 页 | 图 08 |
| 5 题目四：宝藏分配综合实验 | 5.1 距离矩阵；5.2 状态；5.3 深度与收益；5.4 剪枝效率；5.5 阶段耗时 | 3～4 页 | 图 10、12、13、15、16；一张状态表 |
| 6 创新与拓展 | 6.1 已有收益排序；6.2 待补充的自设场景 | 1～1.5 页 | 一张排序对照表；新增实验完成后再决定图表 |
| 7 总结与局限 | 回答实验目标，概括适用条件和数据边界 | 0.5 页 | 不新增图表 |

篇幅合计约 10～14 页，具体取决于字号和图片排版。这是编辑建议，PDF 没有规定报告页数。正文推荐 9 张现有图：01、04、05、08、10、12、13、15、16；建议的小表主要是状态表和收益排序对照表，设置表可改成短段落。

使用数据时：图片是主要证据，正文只提炼支撑分析的少量数值；不要粘贴完整 CSV。下文列出的 CSV 是核对来源，并不表示都需要转成表格。对于逐步路径、内部节点回传和按深度分组的剪枝，实际数据源是 JSON，不能强行把只记录汇总指标的 CSV 说成图中全部信息的来源。

## 二、各章节详细大纲

### 1 实验目标、算法设计与实验设置

#### 1.1 实验目标与任务联系

用一段话交代三件事：

1. 用 A* 求解单位代价和加权网格的最小代价路径，并比较零启发与有信息的启发函数。
2. 用 Minimax 作基线，检验 Alpha-Beta 在保持根节点决策价值一致的前提下怎样减少搜索工作。
3. 用预计算的最短移动代价连接寻路与宝藏博弈，研究搜索深度和访问顺序对决策及开销的影响。

不重复整份题目，不在这里展示每题运行截图。各题结果会在后文逐项验证。

#### 1.2 A* 的设计与实际实现

说明：

- 状态为 `(row, col)`，合法动作只有上下左右；邻居枚举顺序实际为上、右、下、左。
- `g(n)` 是已知最优到达代价，`h(n)` 是剩余代价下界，`f(n)=g(n)+h(n)`。
- 最小堆按 `f` 排序，同 `f` 按入队序号排序。不要把本项目的平局规则写成“优先更小的 h”或“优先更大的 g”。
- 用 `best_g` 判断是否发现更优路径，用父节点记录回溯最终路径；堆中的旧条目出队时跳过。
- 实现允许更优路径重新打开已展开状态；本次样例的重新打开计数为 0，不必为了说明通用能力扩写成长篇代码介绍。
- 在目标有效出队时结束，而不是在第一次发现目标时结束。
- 可采纳性及各题进入代价的差异是后文分析重点；此处只建立共同框架。

可用很短的伪代码表达“出队 → 判目标 → 展开 → 松弛 → 入队”，不放完整源码。

实现参考：[astar.py](../src/algorithms/astar.py)、[_grid.py](../src/problems/_grid.py)。

#### 1.3 Minimax 与 Alpha-Beta 的共同框架

先给 Minimax 的递推式：终止或深度到限时返回评价值；MAX 取最大子值；MIN 取最小子值。明确评价始终站在 A/MAX 的视角，根深度为 0，每执行一次动作深度加 1。

接着说明 `alpha` 是 MAX 已有可保证的下界，`beta` 是 MIN 已有可保证的上界；MAX 更新 alpha，MIN 更新 beta，当 `alpha >= beta` 且还有未访问分支时跳过剩余分支。解释被剪枝分支不可能改变祖先当前选择，而不只给一个判断条件。

说明两算法共用后继生成、评价函数、终止条件及计数方式，控制对照变量；相同价值时保留先访问动作，因此不同顺序可能产生不同的等价主变化。

复杂度如需保留，用两句话概括：完整 Minimax 最坏为 O(b^H)，Alpha-Beta 最坏仍相同，良好排序可显著减少访问；本实验宝藏数量逐层递减，应结合实际计数分析，不能机械套用固定分支数。

实现参考：[minimax.py](../src/algorithms/minimax.py)、[alpha_beta.py](../src/algorithms/alpha_beta.py)、[_game.py](../src/algorithms/_game.py)。

#### 1.4 实验设置、控制变量和统计口径

交代输入来自 [test_cases.json](../configs/test_cases.json)，包括两张 5×5 地图、给定博弈树和 7×7 宝藏地图。记录中的环境是 Python 3.13.9、Windows 11；不补写没有记录的 CPU 型号。

建议用一小段或一张小表说明对照组：

| 对照对象 | 改变的变量 | 保持相同的条件 |
| --- | --- | --- |
| 题一、题二 A* | `zero` / `manhattan` | 地图、端点、邻居顺序、平局规则 |
| 题三 | Minimax / Alpha-Beta；从左到右 / 每层逆序 | 树结构、叶值、根玩家 |
| 题四 | 算法；H=2 / H=4；input / reverse | 地图、价值、规则、距离矩阵 |
| 拓展排序 | input / reverse / gain | 同一深度、评价函数和终止条件 |

必须讲清的统计口径：

- `nodes_visited`：A* 的有效出队或博弈递归访问次数；不是所有入队数或不同状态总数。
- `nodes_expanded`：实际生成后继的节点次数。A* 目标计入访问，但不再展开。
- `nodes_generated`：包含根和生成候选，可能包含重复状态；博弈实现一次性构造当前节点的全部后继，生成不等于递归访问。
- `evaluation_calls`：博弈叶子评价次数；H=2 的叶子通常由深度截断产生，H=4 的叶子为宝藏取完的终局。
- `cutoff_events` 是剪枝事件数，`pruned_branches` 是跳过的直接兄弟分支数，二者都不是节省的后代节点总数。
- 每组计时执行 3 次，选择按 `elapsed_seconds` 排序的中间一轮，保留该轮结果、统计与轨迹；不能写成“平均耗时”。
- 当前结果均启用 `collect_trace=True`。算法计时包含搜索回调及轨迹记录，不含结果导出和绘图。微秒级时间只作本次观测，不能据此宣称稳定加速。

数据来源：各题的 `metadata.json`、`metrics.csv`；全部轮次在各题 `timing_runs.csv`。这里无需展示这些 CSV 的原始内容。

### 2 题目一：迷宫寻路

#### 2.1 状态建模、最短路径与形成过程

交代墙不可通行、每步代价 1，路径包含起点和终点。给出成功结果为 7 次移动、8 个坐标；坐标已在图上可见时，不另列完整坐标表。

结合访问角标与最终路径解释：A* 不是只沿最终蓝线前进，而是维护多条候选路径；当找到更低 g 时更新父节点，最终回溯形成蓝线。以图中的一两个转弯说明绕开障碍即可。

**正文图：** [01_maze_search.png](figures/problem1_maze/01_maze_search.png)。

**对应 CSV：** [题一 metrics.csv](../results/problem1_maze/metrics.csv)，筛选 `heuristic=zero/manhattan`，核对 `path_cost`、`nodes_visited`、`nodes_expanded`。实际路径来自各自 `astar_*/result.json`，访问角标来自 `astar_*/trace.json`。

若正文需要更完整的队列过程，可将 [02_maze_frontier.png](figures/problem1_maze/02_maze_frontier.png) 作为备选；默认不再加入，以免与图 01 重复。

#### 2.2 启发函数对照与“改善为什么有限”

直接在正文写出：两方案路径代价均为 7；访问数从 16 降到 14，减少 12.5%；展开数从 15 降到 13；本次中位数轮次耗时为 112.2 μs 和 107.0 μs。数值无需另做一张性能表。

分析不能止于“曼哈顿更准确”：本例曼哈顿方案的 14 次有效出队都满足 f=7，多个分支处于相同优先级，按入队序号打破平局，仍访问了不在最终路径上的格子。因此启发函数减少了一些无关访问，但没有把搜索压缩到 8 个路径节点。堆峰值仍同为 3，说明访问减少不代表每项内存指标都下降。

在目标出队时，剩余有效 OPEN 的最小 f 已是 9，无需继续搜索。若写最优性理由，应结合启发下界和目标出队条件，不能仅凭“路径看起来最短”。

这些信息已可由图 01、现有性能图及文字共同表达，默认不插入 [03_maze_efficiency.png](figures/problem1_maze/03_maze_efficiency.png)。图 03 的直接来源也是题一 `metrics.csv`；需要更直观的性能展示时，可将其列为额外备选图。

### 3 题目二：加权地形

#### 3.1 进入代价、路径选择与 g 的累计

先写清 `c(u,v)=cost(v)`；起点不收取进入代价，终点 E 的进入代价为 0。将题一的“最少步数”与本题的“最小总代价”联系起来：选择依据是累计地形代价，而不只是格子数。

结合图说明最优路径绕开高权值地形，进行了 8 次移动，但仅前 7 次进入代价为 1，最后一步进入 E 为 0，所以总代价为 7。累计 g 是 `0,1,2,3,4,5,6,7,7`。图已给出全部路径步号和累计曲线，不再新增逐步 CSV 表。

**正文图：** [04_weighted_path_cost.png](figures/problem2_weighted_terrain/04_weighted_path_cost.png)。

**对应 CSV：** [题二 metrics.csv](../results/problem2_weighted_terrain/metrics.csv) 只能核对 `path_cost=7`、`solution_depth=8`。逐步进入代价和累计曲线的直接来源是 [summary.json](../results/problem2_weighted_terrain/summary.json) 的 `path`、`step_costs`、`cumulative_costs`，没有逐步代价 CSV。

#### 3.2 零代价终点与启发函数可采纳性

这是本题分析重点，建议按“反例 → 修正 → 下界证明 → 图中验证”的顺序写。

1. 定义 D 为到目标的曼哈顿距离。原始 `h=D` 在这里不能保证可采纳：位于 (4,3) 时，D=1，但一步进入 E 的真实剩余代价为 0，发生高估；起点 D=8 也超过真实最优代价 7。
2. 本项目实际使用的是修正曼哈顿，不是原始 D。本样例的非终点最小进入代价 m=1，因此 `h(n)=m·max(D(n)-1,0)`。
3. 对非目标节点，一条到 E 的路线至少有 D 步，最后一步免费，其余至少 D−1 次进入非终点且每次代价不低于 m，故上述 h 是剩余代价下界；目标 h=0。这里只需一段证明，不必列全地图状态表。
4. 当前最优路径上的修正 h 与真实后缀代价重合，可以作为本样例的直观验证；不能由这条路径上的相等推断任意节点、任意地图都能精确估计。
5. 若其他非终点允许零代价，m 可能为 0，此下界仍安全，但启发引导会减弱。这个边界可以放在一两句话中，为拓展章节作铺垫。

**正文图：** [05_weighted_heuristic.png](figures/problem2_weighted_terrain/05_weighted_heuristic.png)。

**对应 CSV：** 无直接 CSV。图中三条曲线由题二 `summary.json` 的最优路径及累计代价、`metadata.json` 的网格和目标计算；`metrics.csv` 不记录每个路径状态的 h 或真实后缀代价。不要为满足“有 CSV”而另造表格。

#### 3.3 修正启发的搜索开销

正文提炼：h=0 与修正曼哈顿都得到总代价 7；访问 15→11，减少 26.67%；展开 14→10；生成候选 47→32；堆峰值 10→9；本次耗时 118.9→99.8 μs。

解释修正启发保留了正确的代价下界，同时减少低价值区域的访问。不要把“当前样例耗时更低”推广成普遍稳定的时间优势，也不要把不同地图上 12.5% 与 26.67% 的差异完全归因于是否加权。

这些数据已在 [06_weighted_efficiency.png](figures/problem2_weighted_terrain/06_weighted_efficiency.png) 中展示，默认只提取关键值写入正文，不再插一张图或一张重复表。其直接 CSV 为题二 `metrics.csv`。

### 4 题目三：博弈树求值与 Alpha-Beta 剪枝

#### 4.1 完整 Minimax 的数值回传

按配置和 PDF 第 10～12 页的 JSON/构建代码介绍实际搜索结构：两个内容相同的 [6,9] 分支，在左右两个 MIN 下各有一次出现。按树展开后有 15 个节点、8 个叶子评价，不按 6 个叶子误算。

用一行回传链配合图 08 的树结构即可：底部四个 MAX 的精确值为 `[5,9,9,2]`，上一层 MIN 为 `[5,2]`，根 MAX 为 5。

已有 [07_minimax_backup.png](figures/problem3_game_tree/07_minimax_backup.png) 可以作为备选，但它与图 08 的树结构重复，默认不加入正文。直接数据源是 `left_to_right/minimax/trace.json`，计数来源是题三 `metrics.csv`。

#### 4.2 用具体界值说明剪枝依据

**正文图：** [08_alpha_beta_pruning.png](figures/problem3_game_tree/08_alpha_beta_pruning.png)，上半为从左到右，下半为每层逆序。

围绕图中的实际事件分析：

- 从左到右：左 MIN 已有可取值 5，后续 MAX 先见到 6，得到 alpha=6、beta=5。该 MAX 只可能返回不小于 6 的值，MIN 已有 5，故其剩余叶子 9 不会改善 MIN 的选择，可以跳过。
- 每层逆序：右 MIN 先得到 2，后续 MAX 先见到 9，得到 alpha=9、beta=2，跳过该分支的另一个叶子 6。
- 图中剪枝 MAX 的 `≥6` 或 `≥9` 是当时返回的下界。不能把 `≥6` 改写成“该完整子树的精确值为 6”；完整子树精确值可由无剪枝 Minimax 得知为 9。

**对应 CSV：** [题三 metrics.csv](../results/problem3_game_tree/metrics.csv)，按 `algorithm`、`move_order` 读取访问、评价、剪枝统计。两次具体 alpha/beta、剪枝位置和被跳过叶子的直接来源分别为：

- [left_to_right/alpha_beta/trace.json](../results/problem3_game_tree/left_to_right/alpha_beta/trace.json)
- [reverse/alpha_beta/trace.json](../results/problem3_game_tree/reverse/alpha_beta/trace.json)

#### 4.3 顺序对开销的影响与时间现象

正文写出：两种顺序下，Minimax 都访问 15、评价 8；Alpha-Beta 都访问 14、评价 7。访问减少 6.67%，评价减少 12.5%，根值均为 5。结论应为“剪枝位置不同，但这个样例的节省量相同”，不能宣称逆序显著提高效率。

补充本次从左到右的耗时：Minimax 26.6 μs，Alpha-Beta 32.6 μs；逆序分别为 64.2、101.6 μs。少访问一个叶子带来的收益较小，维护上下界、轨迹及运行波动都可能影响时间。现有 3 次测量不足以将这些因素分开，只能确认本例工作量减少而记录耗时没有降低。

不必再插 [09_game_tree_efficiency.png](figures/problem3_game_tree/09_game_tree_efficiency.png) 或重复计数表，正文已有足够证据。该图的直接来源是题三 `metrics.csv`，全轮计时在 `timing_runs.csv`。

### 5 题目四：竞争环境下的宝藏分配

这是综合题，也是最适合体现设计和独立分析的部分，篇幅应略多于前三题。

#### 5.1 A* 距离预计算与问题分解

说明地图上的 A、B 和四个宝藏共 6 个关键点，按行起点、列终点形成 6×6 最小移动代价矩阵。当前实现分别计算 36 个有向点对，包括 6 个自身到自身的零距离搜索；博弈阶段复用这个矩阵，不为每条博弈边重新运行 A*。

**正文图：** [10_treasure_map_matrix.png](figures/problem4_treasure_game/10_treasure_map_matrix.png)。地图和矩阵已有完整标注，不再复制一张 6×6 数值表。

**对应 CSV：** [distance_matrix/matrix.csv](../results/problem4_treasure_game/distance_matrix/matrix.csv) 是距离数值的直接 CSV；绘图程序实际读取等价 `matrix.json`。每个点对的搜索开销另在 [distance_matrix/metrics.csv](../results/problem4_treasure_game/distance_matrix/metrics.csv)。

正文挑两个差异说明地理位置的影响：A→T2=4、A→T3=8；B→T3=4、B→T2=8。宝藏价值不能单独决定选择，必须减去当前位置的移动代价。

可以用一句话解释矩阵对称：本题关键点的进入代价均为 1，四邻接连通关系可逆，所以关键点间路径反转的总成本相同；一般进入代价模型若两端代价不同，不能直接套用对称性。

#### 5.2 博弈状态、动作与状态更新

明确状态表示：`s=(position_a, position_b, remaining, score_a, score_b, current_player)`；位置用关键点标签表示并关联坐标，remaining 记录尚未领取的宝藏。

推荐一张 6 行小表：字段、含义、初始值。相比插入整张 [11_treasure_state.png](figures/problem4_treasure_game/11_treasure_state.png)，原生表格更紧凑，也方便调整中文字段说明；二者择一。

动作选择一个剩余且可达的宝藏；计算 `Gain=V−d`；更新行动方位置与累计收益，删除仅本回合选中的宝藏，切换玩家。终止为剩余集合为空，或搜索深度达到 H；评价始终为 `U=score_a−score_b`。

用正文给一个实际更新：初始 A 选择 T3，d=8、V=7，Gain=−1；状态变为 A 在 T3、B 仍在 B，剩余 T1/T2/T4，收益为 (−1,0)，轮到 B。

必须写清三条规则：经过其他宝藏不自动领取；已领取位置仍可通行；另一玩家不阻挡寻路。它们也说明预计算距离能够跨博弈状态复用。

**数据来源：** [problem4.py](../src/problems/problem4.py) 的 `TreasureState` 和 `successors`；[H=4 输入顺序 Minimax 结果](../results/problem4_treasure_game/depth_4/input_order/minimax/result.json) 中 `states`。这里无状态字段 CSV，不需新增。

#### 5.3 H=2 与 H=4 的首步差异及收益形成

先检验两算法在同深度得到相同首步和根值：H=2 选 T2、U=−1；H=4 选 T3、U=3。H=2 是双方各行动一次后的截断评价，仍有两个宝藏未领取；H=4 才是四个宝藏取完的终局价值。

**正文图之一：** [12_treasure_root_choices.png](figures/problem4_treasure_game/12_treasure_root_choices.png)。

图上四个固定首步分支值依次为：H=2 时 `[-4,-1,-2,-4]`；H=4 时 `[-5,1,3,-7]`，目标顺序为 T1/T2/T3/T4。这些已标在图上，不再复制成 4×2 表。

**对应 CSV：** [题四 metrics.csv](../results/problem4_treasure_game/metrics.csv) 中 `phase=game` 的 `depth_limit`、`algorithm`、`best_value` 可核对根值。最优首步在对应 `result.json`；四个内部首步的精确回传值来自：

- [H=2 input_order/minimax/trace.json](../results/problem4_treasure_game/depth_2/input_order/minimax/trace.json)，筛选 `event=return, depth=1`
- [H=4 input_order/minimax/trace.json](../results/problem4_treasure_game/depth_4/input_order/minimax/trace.json)，同样筛选

这些四分支值无直接 CSV；必须用完整 Minimax 回传，不能将 Alpha-Beta 中可能只是上下界的内部返回值当作精确柱值。

**正文图之二：** [13_treasure_scores.png](figures/problem4_treasure_game/13_treasure_scores.png)。

结合主变化解释“为什么”：

- H=2：A→T2，Gain=6−4=2；B→T3，Gain=7−4=3，当前 U=2−3=−1。
- H=4 的输入顺序主变化：A→T3，Gain=7−8=−1；B→T1，Gain=9−8=1；A 从 T3→T2，Gain=6−6=0；B 从 T1→T4，Gain=7−12=−5。终局 Score_A=−1、Score_B=−4，因此 U=3。
- T3 的即时收益虽为负，却改变了剩余宝藏和双方后续位置；完整博弈中，A 的目标是最大化收益差，不是保证自己的绝对收益为正。首步选 T2 的完整分支值只有 1，而选 T3 为 3。
- 此处展示一条最优主变化即可。H=4 逆序下存在等值序列 T3→T2→T1→T4，根价值仍为 3，不应把等价序列不同当成算法冲突。

**对应数据：** 图 13 无逐步收益 CSV，直接使用 `depth_2/input_order/minimax/result.json` 和 `depth_4/input_order/minimax/result.json` 的 `states`、`principal_variation`；题四 `metrics.csv` 只能核对最终 best_value。

默认不再插入 [14_treasure_routes.png](figures/problem4_treasure_game/14_treasure_routes.png)。若希望直观看到 A 的首步路线经过 T2 却仅领取 T3，可将它作为备选；路径直接来源为 [distance_matrix/paths.json](../results/problem4_treasure_game/distance_matrix/paths.json)，同样不是 CSV。

#### 5.4 深度、顺序与剪枝效率

**正文图之一：** [15_treasure_efficiency.png](figures/problem4_treasure_game/15_treasure_efficiency.png)。

按“固定深度比较算法 → 固定算法比较顺序 → 深度增长”分析：

- H=2：Minimax 访问 17；Alpha-Beta 输入顺序访问 13，减少 23.53%；逆序访问 16，减少 5.88%。
- H=4：Minimax 访问 65；Alpha-Beta 输入顺序访问 47，减少 27.69%；逆序访问 46，减少 29.23%。
- 输入顺序并非在所有深度都优于逆序。排序影响较好界值建立的时机，深度变化会改变分支估值和可剪枝结构。
- Minimax 的 17 与 65 可由 `1+4+12` 和 `1+4+12+24+24` 解释：每取一个宝藏，后继分支数减少 1。这比泛泛写“深度越大节点越多”更能体现理解。
- H=2 时两算法展开数都为 5，而访问和评价数下降；实现先生成当前节点所有候选，之后才递归访问，所以剪枝不一定减少已经完成的后继生成。H=4 可跳过更深子树，展开数也会减少。

**正文图之二：** [16_treasure_pruning_depth.png](figures/problem4_treasure_game/16_treasure_pruning_depth.png)。

用它专门回答“为什么不能只比较剪枝次数”：H=4 输入顺序有 5 次剪枝，跳过 6 个直接分支，却访问 47；逆序只有 4 次剪枝、跳过 5 个直接分支，反而访问 46。

结合深度解释：输入顺序的事件分布为深度 1 一次、深度 2 四次；逆序为深度 1 两次、深度 2 两次。在这棵树中，深度 1 跳过一个子分支对应的完整剩余子树有 5 个节点，而深度 2 跳过一个子分支有 2 个节点。因此输入顺序实际省下 `2×5+4×2=18` 个访问，逆序省下 `3×5+2×2=19`，对应 65−47 与 65−46。这个子树大小解释来自已知剩余宝藏的展开结构，不是把直接分支计数冒充后代总数。

**对应 CSV：** 两图共同使用题四 [metrics.csv](../results/problem4_treasure_game/metrics.csv)，筛选 `phase=game`，正文基础对照取 `move_order=input/reverse`，字段为 `nodes_visited`、`nodes_expanded`、`evaluation_calls`、`cutoff_events`、`pruned_branches`。图 16 的逐深度分布不在 CSV，直接来源为四个 `depth_{2,4}/{input,reverse}_order/alpha_beta/trace.json` 的 `cutoff` 事件。

图 15、16 已足够，不再列一张包含所有指标的重复表。收益排序 gain 留到第 6 章，用于讨论优化的增量效果。

#### 5.5 寻路预计算与博弈阶段的时间边界

用一小段收束，不必再插一整张计时热力图。可以提取：36 个点对各自中位数轮次的 A* 搜索耗时之和为 1.7187 ms；H=4 输入顺序下，Minimax 和 Alpha-Beta 博弈阶段的观测耗时分别为 178.2 μs、170.3 μs。

分析：距离矩阵可跨不同算法、深度和顺序复用；当前小规模博弈的搜索耗时很短，预计算也是需要关注的成本。但上述 1.7187 ms 是各点对中位数之和，不是完整预计算总耗时的中位数，更不是包含建图、文件写入和绘图的程序总耗时。

来源为题四 `metrics.csv` 中 `phase=distance/game` 的 `elapsed_seconds`，完整轮次在 `timing_runs.csv`。这些信息已在 [17_treasure_runtime.png](figures/problem4_treasure_game/17_treasure_runtime.png) 中可视化；默认将关键结果写进正文即可。若教师偏好完整时间图，再加入图 17。

### 6 创新与拓展

本节与“基础部分已有结果”分开处理。目前发现项目已有 gain 排序实现及对应结果，具备一个可使用的优化对照；但现有数据不能替代尚未完成的自设场景实验，也不能保证创新评分。下面区分可直接写的内容与待补充的内容。

#### 6.1 利用已有数据：即时收益排序改进 Alpha-Beta

说明动机：输入顺序和逆序都不利用局面价值；尝试优先搜索对当前行动方更有利的动作，尽早收紧界值。

准确描述实际规则：MAX 按子状态 U 降序，MIN 按子状态 U 升序。在当前规则下，两者都等价于优先选择当前行动方即时 Gain 较大的动作；不要误写成“MIN 按自己的 Gain 升序”。排序只改变搜索顺序，不改变合法动作、终局条件或评价函数。

**建议使用一张小表。** 现有图 15、16、17 都只覆盖 input/reverse，没有 gain，因此这里是需要从 CSV 提取额外信息的地方。

| H | 顺序 | Minimax 访问 | Alpha-Beta 访问 | Alpha-Beta 评价 | 相对同设置 Minimax 的访问减少率 |
| --- | --- | ---: | ---: | ---: | ---: |
| 2 | input | 17 | 13 | 8 | 23.53% |
| 2 | reverse | 17 | 16 | 11 | 5.88% |
| 2 | gain | 17 | 11 | 6 | 35.29% |
| 4 | input | 65 | 47 | 16 | 27.69% |
| 4 | reverse | 65 | 46 | 16 | 29.23% |
| 4 | gain | 65 | 37 | 12 | 43.08% |

**CSV：** [题四 metrics.csv](../results/problem4_treasure_game/metrics.csv)，筛选 `phase=game`，按 `depth_limit`、`move_order`、`algorithm` 提取；最优首步再核对对应 `gain_order/*/result.json`。

分析写四点即可：

1. 根值与首步保持一致：H=2 为 T2/−1，H=4 为 T3/3，优化没有改变当前样例的决策结果。
2. H=2 相对 input 的 Alpha-Beta 访问从 13 降至 11，额外减少 15.38%；H=4 从 47 降至 37，额外减少 21.28%。这些“相对 input 的增量减少率”不能与表中“相对 Minimax 的减少率”混用。
3. 即时 Gain 排序是为剪枝寻找更好的访问顺序，并不意味着最终按即时 Gain 进行贪心决策。H=4 最优首步 T3 即时收益为负，本身就说明这一区别。
4. 工作量改善不保证耗时同步降低：H=4 input 的 Alpha-Beta 为 170.3 μs，而 gain 为 214.1 μs。排序本身有成本，且短时测量有波动；现有数据只支持当前样例节点与评价数减少，不能宣称稳定时间加速或普遍最优排序。

#### 6.2 待补充的自设场景：验证适用条件或边界

用户说明创新与拓展尚未完成，此处只预留结构，不写成已完成实验。若后续只补一组，建议围绕已有 gain 排序，改变四个宝藏的价值而保持地图和规则不变，比较 input/reverse/gain：这样距离矩阵可复用，对照变量明确。

写作结构为：

- 研究问题：即时收益排序在收益相近、收益差异较大或短期收益与长期位置收益冲突时，是否仍能改善剪枝？
- 实验设置：事先指定若干价值配置，固定 H=4、地图、规则和评价函数；不只筛选对 gain 有利的配置。
- 检验正确性：各排序的 Alpha-Beta 根值与完整 Minimax 相同；等值最优首步不同要区分正常平局与错误。
- 记录数据：配置、顺序、根值、访问数、评价次数、相对基线减少率；若分析时间，另采用足够多轮重复并明确轨迹开关，不能混用当前带轨迹结果。
- 分析适用条件：何时即时排序能较早建立强界，何时即时 Gain 不代表深层收益、排序收益减弱或成本抵消。

**图片/CSV：尚无对应产物，不预填路径，不编造结果。** 后续数据少时用一张关键结果表即可，不必为每个配置单独画图。收益排序 6.1 的已有样例不重复充当 6.2 的新场景数据。

如果本次先只写基础报告，则保留本节标题和待补内容即可。第 2～5 章的零启发、算法、深度和顺序对照仍属于已有基础分析，不必统一挪进拓展章节。

### 7 总结与局限

用约半页回答四个问题，每个问题一两句：

1. 启发函数怎样在不改变最优解的前提下减少搜索？结合题一、二，而非重复所有指标。
2. 启发函数为何必须匹配代价规则？点明题二 E=0 的反例与修正。
3. 搜索深度和访问顺序分别影响什么？在相同规则和深度下，顺序主要影响剪枝效率；深度改变当前纳入考虑的未来，因此可能改变首步。
4. 实验结论适用到哪里？当前为给定小规模样例、带轨迹计时和有限重复；gain 改善了已有样例的访问工作量，自设场景若未完成就不作跨场景推广。

不再堆一张总表，不新增结果图。创新章节尚未验证的方案只能写成后续方向。

## 三、现有图片的最终取舍清单

下面路径都相对于项目根目录 `D:/course_ai/project2/`；本文件内链接相对于 `report/`。编号是已有文件编号，正式报告可按正文顺序重新编号。

| 现有图 | 建议 | 图像路径 | CSV 与实际数据源 |
| --- | --- | --- | --- |
| 01 | 正文：题一 | `report/figures/problem1_maze/01_maze_search.png` | `results/problem1_maze/metrics.csv` 核对计数；路径/序号为 `astar_*/result.json`、`trace.json` |
| 02 | 备选：需要更细队列过程时使用 | `report/figures/problem1_maze/02_maze_frontier.png` | 无队列快照 CSV；`astar_manhattan/trace.json` 重放 |
| 03 | 默认省略，关键值写正文 | `report/figures/problem1_maze/03_maze_efficiency.png` | `results/problem1_maze/metrics.csv` |
| 04 | 正文：题二 | `report/figures/problem2_weighted_terrain/04_weighted_path_cost.png` | `results/problem2_weighted_terrain/metrics.csv` 仅总量；逐步值为 `summary.json` |
| 05 | 正文：题二 | `report/figures/problem2_weighted_terrain/05_weighted_heuristic.png` | 无直接 CSV；`summary.json`、`metadata.json` 计算 |
| 06 | 默认省略，关键值写正文 | `report/figures/problem2_weighted_terrain/06_weighted_efficiency.png` | `results/problem2_weighted_terrain/metrics.csv` |
| 07 | 默认省略，用回传链结合图 08 | `report/figures/problem3_game_tree/07_minimax_backup.png` | `results/problem3_game_tree/metrics.csv` 仅计数；回传为 `left_to_right/minimax/trace.json` |
| 08 | 正文：题三 | `report/figures/problem3_game_tree/08_alpha_beta_pruning.png` | `results/problem3_game_tree/metrics.csv` 及两顺序 `alpha_beta/trace.json` |
| 09 | 默认省略，关键值写正文 | `report/figures/problem3_game_tree/09_game_tree_efficiency.png` | `results/problem3_game_tree/metrics.csv` |
| 10 | 正文：题四 | `report/figures/problem4_treasure_game/10_treasure_map_matrix.png` | `results/problem4_treasure_game/distance_matrix/matrix.csv`；地图为 metadata |
| 11 | 改为原生状态字段小表 | `report/figures/problem4_treasure_game/11_treasure_state.png` | 无状态 CSV；`depth_4/input_order/minimax/result.json` |
| 12 | 正文：题四 | `report/figures/problem4_treasure_game/12_treasure_root_choices.png` | `results/problem4_treasure_game/metrics.csv` 仅根值；四分支值为两深度的 `input_order/minimax/trace.json` |
| 13 | 正文：题四 | `report/figures/problem4_treasure_game/13_treasure_scores.png` | 无逐步收益 CSV；两深度 `input_order/minimax/result.json` 的 states |
| 14 | 备选：强调经过不领取时使用 | `report/figures/problem4_treasure_game/14_treasure_routes.png` | 无路线 CSV；`distance_matrix/paths.json` 和主变化 result |
| 15 | 正文：题四 | `report/figures/problem4_treasure_game/15_treasure_efficiency.png` | `results/problem4_treasure_game/metrics.csv`，`phase=game`，input/reverse |
| 16 | 正文：题四，深入分析证据 | `report/figures/problem4_treasure_game/16_treasure_pruning_depth.png` | 同题 metrics 为汇总；逐深度来自四个 `alpha_beta/trace.json` |
| 17 | 默认省略，关键时间写正文 | `report/figures/problem4_treasure_game/17_treasure_runtime.png` | `results/problem4_treasure_game/metrics.csv`，distance/game 两阶段 |

## 四、撰写时要守住的结论边界

- 不把题二 `manhattan` 参数误称为原始曼哈顿距离，实际实现考虑了终点 E=0。
- 不把 H=2 的 U=−1 当作四回合完整游戏的终局输赢。
- 不把 Alpha-Beta 的内部剪枝回传界当作全部首步分支的精确估值。
- 不声称题三逆序减少了更多访问，两个顺序都访问 14。
- 不把“剪枝事件更多”“直接分支更多”直接等同于“省下节点更多”。
- 不把重复 3 次保留中位数写成平均值，不把轨迹计时写成纯算法无记录开销。
- 不把各点对中位数之和写成端到端总耗时。
- 不因路径经过 T2 就认为已经领取 T2；不因 A 的最终自身得分为负就认为 U 不可能为正。
- 不把已有 gain 样例的工作量减少写成跨场景普遍加速，也不把尚未完成的拓展写成已验证结果。

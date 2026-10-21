"""图号、数据字段、计算口径与报告含义。"""

from dataclasses import dataclass
from pathlib import Path

from .common import TIME_NOTE
from .data import Results


@dataclass
class FigureSpec:
    identifier: str
    folder: str
    title: str
    section: str
    inputs: list[tuple[Path,str]]
    calculation: str
    meaning: str
    finding: str
    limitation: str = ""
    reading: str = ""


def specifications(data:Results)->list[FigureSpec]:
    def ref(n,path,fields):
        return data.path(n,path),fields
    def metric(n,fields):
        return ref(n,"metrics.csv",fields)
    def meta(n,fields="inputs"):
        return ref(n,"metadata.json",fields)
    def summary(n,fields):
        return ref(n,"summary.json",fields)
    def saved(n,**filters):
        a=int(data.metric(n,**filters,algorithm="minimax")["nodes_visited"])
        b=int(data.metric(n,**filters,algorithm="alpha_beta")["nodes_visited"])
        return f"{a}→{b}，减少 {(a-b)/a:.1%}"
    def astar_saved(n):
        a=int(data.metric(n,heuristic="zero")["nodes_visited"])
        b=int(data.metric(n,heuristic="manhattan")["nodes_visited"])
        return f"{a}→{b}，减少 {(a-b)/a:.1%}"
    time_limit=TIME_NOTE
    path_inputs=lambda n:[meta(n,"inputs.grid、start、goal"),
        ref(n,"astar_zero/result.json","path、cost"),ref(n,"astar_manhattan/result.json","path、cost"),
        ref(n,"astar_zero/trace.json","event=visit、state、depth、details.g/h/f"),
        ref(n,"astar_manhattan/trace.json","event=visit、state、depth、details.g/h/f")]
    search_fields="heuristic、nodes_visited、nodes_expanded、nodes_generated、frontier_peak、relaxations、elapsed_seconds、collect_trace"
    tree_input=meta(3,"inputs.tree_structure：children、value、is_maximizing_player")
    pv_inputs=[ref(4,f"depth_{h}/input_order/minimax/result.json","best_action、best_value、principal_variation、states")
               for h in (2,4)]
    trace_inputs=[ref(4,f"depth_{h}/{order}_order/alpha_beta/trace.json",
                     "event=cutoff、depth、details.pruned_branches、alpha、beta")
                  for h in (2,4) for order in ("input","reverse")]
    root_findings="；".join(f"H={h}："+"、".join(f"{k}={v:g}" for k,v in data.root_values(h).items())
                            for h in (2,4))
    precompute_ms=sum(float(row["elapsed_seconds"]) for row in data.select(4,phase="distance"))*1000
    reverse_minimax_us=float(data.metric(3,algorithm="minimax",move_order="reverse")["elapsed_seconds"])*1e6
    reverse_alpha_beta_us=float(data.metric(3,algorithm="alpha_beta",move_order="reverse")["elapsed_seconds"])*1e6
    specs = [
        FigureSpec("01_maze_search","problem1_maze","搜索覆盖与最短路径","2. 题目一：迷宫寻路",
            path_inputs(1),"按 visit 事件标访问序号，叠加保存的最终路径。",
            "解释最短路径形成及两种启发函数的搜索覆盖差异。",
            "两方案均找到 7 步路径；访问数 "+astar_saved(1)+"。",
            "访问含目标，目标不再展开；生成候选数与访问数口径不同。"),
        FigureSpec("02_maze_frontier","problem1_maze","优先队列与搜索过程快照","2. 题目一：迷宫寻路",
            [meta(1,"inputs.grid"),ref(1,"astar_manhattan/trace.json","discover/visit/stale、state、details.g/h/f"),
             ref(1,"astar_manhattan/result.json","path")],
            "由事件按入队序号和 f 重放堆；g 与 best_g 不一致的项不计有效 OPEN；截取第 1、5、10、14 次有效访问完成后的状态。",
            "展示 OPEN 如何推动搜索，并说明相同 f 的访问顺序。",
            "本例曼哈顿方案的 14 次有效出队 f 均为 7，仍会访问多条同优先级分支；终点出队时剩余 OPEN 的最小 f 为 9，无需继续搜索。",
            "画面中 OPEN 为有效候选；统计表中的堆峰值还可能包含过期项。"),
        FigureSpec("03_maze_efficiency","problem1_maze","启发函数的搜索开销","2. 题目一：迷宫寻路",
            [metric(1,search_fields)],"按 heuristic 配对读取两行指标；耗时由秒乘 10^6 转为微秒。",
            "比较访问、展开、生成、队列峰值、松弛和本次耗时。",
            "访问数 "+astar_saved(1)+"，路径长度保持 7。",time_limit),
        FigureSpec("04_weighted_path_cost","problem2_weighted_terrain","加权路径与代价累计","3. 题目二：加权地形",
            [meta(2,"inputs.grid"),summary(2,"path、cost、step_costs、cumulative_costs")],
            "在地图叠加路径步号，以 step_costs 画柱、cumulative_costs 画折线。",
            "说明按进入格子计费，展示总代价如何累计。",
            "路径有 8 次移动，最后进入 E 的代价为 0，累计总代价为 7。",
            "起点位置的 step_cost 为 0，表示未发生进入移动。"),
        FigureSpec("05_weighted_heuristic","problem2_weighted_terrain","零代价终点与启发可采纳性","3. 题目二：加权地形",
            [meta(2,"inputs.grid、goal"),summary(2,"path、cost、cumulative_costs")],
            "沿已得最优路径计算 D、修正 h=max(D−1,0)×m 和 h*=总代价−当前累计代价。最优路径后缀也是最优路径，故其代价是这些路径状态的真实剩余代价。",
            "用终点前一格的反例解释原始曼哈顿为什么可能高估，并说明修正公式。",
            "(4,3) 到 E 的真实代价为 0，原始 D=1，构成高估；本例修正启发与所示后缀代价重合。",
            "只比较实际最优路径上的状态；修正启发的整体可采纳性来自非负进入代价下界，不来自几处曲线重合。"),
        FigureSpec("06_weighted_efficiency","problem2_weighted_terrain","加权地图搜索开销","3. 题目二：加权地形",
            [metric(2,search_fields)],"配对读取零启发与修正曼哈顿的指标，秒转微秒。",
            "将可采纳性讨论与实测搜索开销连接。",
            "访问数 "+astar_saved(2)+"，最小代价都为 7。",time_limit),
        FigureSpec("07_minimax_backup","problem3_game_tree","完整 Minimax 数值回传","4. 题目三：Alpha-Beta 剪枝",
            [tree_input,ref(3,"left_to_right/minimax/trace.json","visit/evaluate/return、depth、details.value")],
            "按 DFS 深度和原始子节点索引解析事件；各节点用完整 Minimax 回传值标注。",
            "说明叶子如何经 MAX/MIN 交替得到根得分。",
            "中间 MAX 值为 [5,9,9,2]，MIN 值为 [5,2]，根值为 5。",
            "两个内容相同的 [6,9] 子树按不同分支定位，不合并成一个访问。"),
        FigureSpec("08_alpha_beta_pruning","problem3_game_tree","两种访问顺序的剪枝位置","4. 题目三：Alpha-Beta 剪枝",
            [tree_input]+[ref(3,f"{order}/alpha_beta/trace.json","visit/return/cutoff、details.alpha/beta/value/pruned_actions")
                           for order in ("left_to_right","reverse")],
            "按实际顺序解析轨迹、标记访问序号与未访问叶子；剪枝节点的回传注明下界。",
            "解释 alpha>=beta 的依据，以及相同开销下剪枝位置仍可不同。",
            "从左到右在 alpha=6、beta=5 时跳过叶值 9；逆序在 alpha=9、beta=2 时跳过另一分支的叶值 6；均访问 14 个节点。",
            ">=6 等标记为回传界，不是完整子树精确值；不能宣称本例逆序显著减少节点。"),
        FigureSpec("09_game_tree_efficiency","problem3_game_tree","算法与访问顺序的开销对照","4. 题目三：Alpha-Beta 剪枝",
            [metric(3,"algorithm、move_order、nodes_visited、evaluation_calls、elapsed_seconds、collect_trace")],
            "按算法和访问顺序分别比较访问、叶子评价和本次微秒耗时。",
            "用数据判断剪枝是否减少工作，而不是仅展示相同答案。",
            "两种顺序均是 Minimax 15 次访问 / 8 次评价，对应 Alpha-Beta 14 次访问 / 7 次评价。"
            f"逆序配置保留的中位数轮次耗时为 Minimax {reverse_minimax_us:.1f} µs、Alpha-Beta {reverse_alpha_beta_us:.1f} µs；"
            "3 次测量仍不足以据此分离剪枝管理开销与测量波动。",time_limit),
        FigureSpec("10_treasure_map_matrix","problem4_treasure_game","宝藏地图与距离矩阵","5. 题目四：综合题",
            [meta(4,"inputs.grid、treasure_values"),ref(4,"distance_matrix/matrix.json","labels、matrix")],
            "按 labels 排列热力矩阵，地图格子显示权值、标记和宝藏价值。",
            "给出后续 Gain 计算所用的最小移动代价和地图环境。",
            "矩阵为 6×6，所有点可达，主对角线为 0。",
            "全部有向点对分别搜索；本例的对称矩阵不意味着可在任意进入代价模型中省略反向搜索。"),
        FigureSpec("11_treasure_state","problem4_treasure_game","状态表示与收益更新","5. 题目四：综合题",
            [meta(4,"inputs.treasure_values"),ref(4,"distance_matrix/matrix.json","labels、matrix"),pv_inputs[1]],
            "用 H=4 主变化的前后两个实际状态，结合矩阵中的 A→T3 距离演示一次更新。",
            "说明双方位置、剩余集合、收益和当前玩家怎样共同定义状态。",
            "A→T3 的距离 8、价值 7，Gain=-1；A 位置变为 T3，仅移除 T3，再由 B 行动。",
            "这是完整主变化的一步示例，不能用即时 Gain 直接替代整个博弈价值。"),
        FigureSpec("12_treasure_root_choices","problem4_treasure_game","深度改变首步决策","5. 题目四：综合题",
            [meta(4,"inputs.treasure_values")]+pv_inputs+
            [ref(4,f"depth_{h}/input_order/minimax/trace.json","depth=1 的 return、state.position_a、details.value") for h in (2,4)],
            "提取完整 Minimax 根下四个首步的回传值，分别画 H=2 与 H=4；最大者为该深度的首步选择。",
            "解释短视决策与四回合决策为什么不同。",root_findings+
            "。H=2 只计算双方各一次行动；H=4 纳入后续位置和剩余宝藏，首步 T3 虽即时 Gain=-1，却取得终局 U=3。",
            "内部子树估值必须取完整 Minimax；Alpha-Beta 的剪枝返回界不能代替精确分支值。"),
        FigureSpec("13_treasure_scores","problem4_treasure_game","主变化中的收益演化","5. 题目四：综合题",
            pv_inputs,"逐状态提取 score_a、score_b，计算 U；相邻状态的单方收益差为该步 Gain。",
            "解释负收益动作、剩余宝藏约束和终局收益差的形成。",
            "H=2：A 得 2、B 得 3，U=-1；H=4：A 得 -1、B 得 -4，U=3。",
            "只展示各自深度下的一条最优主变化，不是所有分支或一棵完整策略树。"),
        FigureSpec("14_treasure_routes","problem4_treasure_game","最优主变化的实际移动路线","5. 题目四：综合题",
            [meta(4,"inputs.grid"),ref(4,"distance_matrix/paths.json","from_point、to_point、path、cost")]+pv_inputs,
            "用主变化每步前的玩家位置和目标查找已保存的 A* 路径，按玩家及回合编号叠加。",
            "把博弈动作与地图中的移动连接，说明行动后位置更新。",
            "H=2 的领取顺序为 T2→T3；H=4 为 T3→T1→T2→T4。",
            "路径可能经过未选择的宝藏，圆角标仅表示实际选中领取的目标。"),
        FigureSpec("15_treasure_efficiency","problem4_treasure_game","深度及顺序的搜索效率","5. 题目四：综合题",
            [metric(4,"筛选 phase=game，move_order=input/reverse；algorithm、depth_limit、nodes_visited、nodes_expanded、evaluation_calls")],
            "按深度和顺序配对 Minimax / Alpha-Beta；减少率=(基线访问−剪枝访问)/基线访问。",
            "分别比较深度增长和访问顺序对搜索工作的影响。",
            "H=2 输入顺序："+saved(4,phase="game",depth_limit=2,move_order="input")+
            "；H=4 输入顺序："+saved(4,phase="game",depth_limit=4,move_order="input")+"。",
            "不将 36 次距离搜索重复加到每组博弈开销，不将直接剪枝分支数用作节省节点数。"),
        FigureSpec("16_treasure_pruning_depth","problem4_treasure_game","剪枝发生深度与直接分支数","5. 题目四：综合题",
            trace_inputs+[metric(4,"phase=game，algorithm=alpha_beta，move_order=input/reverse；cutoff_events、pruned_branches")],
            "按 cutoff.depth 分组，分别统计事件数和 details.pruned_branches 之和，并与记录的计数器核对。",
            "说明一次剪枝发生的位置也会影响收益，不能只比较剪枝次数。",
            "H=4 输入顺序 5 次剪枝、跳过 6 个直接分支、访问 47；逆序 4 次剪枝、跳过 5 个直接分支、访问 46。",
            "不遍历未访问子树推算其后代总数；实际节省节点需与同设置 Minimax 对照。"),
        FigureSpec("17_treasure_runtime","problem4_treasure_game","寻路与博弈阶段观测时间","5. 题目四：综合题",
            [ref(4,"distance_matrix/matrix.json","labels"),
             metric(4,"phase=distance 的全部 36 行，以及 phase=game、move_order=input/reverse；elapsed_seconds、from_point、to_point、algorithm、depth_limit、collect_trace")],
            "点对中位数轮次耗时画为 6×6 热力图；36 个点对各自保留的耗时求和；博弈阶段按算法、深度和顺序分组，秒转微秒。",
            "区分可复用的距离预计算与之后的博弈决策开销。",
            f"36 个点对各自中位数轮次的 A* 耗时之和为 {precompute_ms:.4f} ms。不同深度复用同一组距离；图中未重复计入预计算。",
            time_limit+"各点对中位数之和不是预计算总耗时的中位数，也不含建图与文件写入，不能冒充完整程序端到端耗时。"),
    ]
    readings = {
        "01_maze_search": "左为 h=0，右为曼哈顿启发。绿色是访问过的状态，角标为访问序号，蓝线是最终最短路径。",
        "02_maze_frontier": "从左到右为第 1、5、10、14 次有效访问完成后的状态。绿色为已访问，浅黄为有效 OPEN 候选，蓝框是当前节点，末图蓝线是最终路径。目标出队后仍可有其他 OPEN 候选。",
        "03_maze_efficiency": "从左到右依次为节点访问/展开/生成、堆峰值与成功松弛、本次观测耗时。蓝色是 h=0，橙色是曼哈顿；耗时柱使用横轴标签区分方案。",
        "04_weighted_path_cost": "左侧为地形权值及路线，# 为路径步号；右侧灰柱为本步代价，蓝线为累计 g。起点步号 0 不是一次移动。",
        "05_weighted_heuristic": "横轴按实际最优路径排列状态。橙色为原始 D，蓝色为修正启发，绿色叉号为最优路径后缀的真实代价；本例后两条曲线重合。",
        "06_weighted_efficiency": "从左到右依次比较节点次数、堆峰值及松弛、本次耗时；两种参数由图例和横轴标签区分。",
        "07_minimax_backup": "最上方是根，底层是输入叶值。节点内标玩家及回传值；绿色箭头是各节点选中的回传方向。",
        "08_alpha_beta_pruning": "上图从左到右访问，下图每层逆序访问；树的位置固定。# 为访问序号，红色 × 是未访问叶子，橙色节点的 ≥ 数值表示剪枝后的下界。",
        "09_game_tree_efficiency": "左图访问节点，中图叶子评价次数，右图本次耗时；横轴均比较从左到右和逆序，蓝色 Minimax、橙色 Alpha-Beta。",
        "10_treasure_map_matrix": "左侧是原地图，V 为宝藏价值；右侧矩阵按行起点、列终点排列，单元格数字为最小移动代价。",
        "11_treasure_state": "左表 s0 是初始状态，s1 是 A 选择 T3 后的状态；右表是该动作的玩家、目标、价值 V、距离 d 和 Gain=V−d。",
        "12_treasure_root_choices": "横轴是 A 固定的首步目标，柱高为后续双方最优行动下的 U。蓝色 H=2，橙色 H=4；MAX 在同色柱中选择最大值。",
        "13_treasure_scores": "左图 H=2，右图 H=4。蓝色是 Score_A、橙色是 Score_B、绿色虚线是 U；横轴给出行动玩家、目标及该步 Gain。",
        "14_treasure_routes": "左图 H=2，右图 H=4。蓝色为 A、橙色为 B，实线是前两步、虚线是后两步；目标旁的圆角标是领取回合编号。",
        "15_treasure_efficiency": "左上访问次数、右上展开次数、左下评价次数、右下访问减少率。横轴按深度与访问顺序配对；前三图蓝色 Minimax、橙色 Alpha-Beta。",
        "16_treasure_pruning_depth": "上排 H=2，下排 H=4；左列是各深度的剪枝事件数，右列是跳过的直接分支数。蓝色输入顺序、橙色逆序。",
        "17_treasure_runtime": "左侧热力矩阵是各点对 A* 的中位数轮次微秒耗时；右侧是不同深度、顺序下保留的博弈耗时，蓝色 Minimax、橙色 Alpha-Beta。",
    }
    for spec in specs:
        spec.reading = readings[spec.identifier]
    return specs

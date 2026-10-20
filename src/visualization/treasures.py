"""宝藏地图、决策差异、收益演化与剪枝开销图。"""

import matplotlib.pyplot as plt
import numpy as np

from .common import BLUE,ORANGE,GREEN,GRAY,TIME_NOTE,bars,finish,grid,route,style_axis
from .data import Results


def map_matrix(data:Results):
    matrix=data.read(4,"distance_matrix","matrix.json")
    values=np.array(matrix["matrix"])
    labels=matrix["labels"]
    fig,axes=plt.subplots(1,2,figsize=(13.5,6.3),layout="constrained")
    cells=data.case(4)["grid"]
    grid(axes[0],cells,weighted=True)
    for row,cells_row in enumerate(cells):
        for col,cell in enumerate(cells_row):
            if cell in data.case(4)["treasure_values"]:
                axes[0].text(col,row+.28,f"V={data.case(4)['treasure_values'][cell]}",ha="center",fontsize=8,zorder=5)
    axes[0].set_title("地图、障碍和宝藏价值；标记格进入代价为 1")
    im=axes[1].imshow(values,cmap="Blues",vmin=0,vmax=values.max())
    for row in range(len(labels)):
        for col in range(len(labels)):
            axes[1].text(col,row,str(values[row,col]),ha="center",va="center",
                         color="white" if values[row,col]>values.max()*.55 else "#111827",fontsize=12)
    axes[1].set_xticks(range(len(labels)),labels)
    axes[1].set_yticks(range(len(labels)),labels)
    axes[1].set_xlabel("终点")
    axes[1].set_ylabel("起点")
    axes[1].set_title("A* 计算的 6×6 最小移动代价矩阵")
    fig.colorbar(im,ax=axes[1],shrink=.8,label="最小移动代价")
    return finish(fig,"题目四：地图与两两最小代价",
                  "36 个有向点对分别计算；经过宝藏不自动领取，玩家不阻挡路径。矩阵与之后的博弈搜索分别统计。")


def state_model(data:Results):
    pv=data.pv(4)
    initial,following=pv["states"][:2]
    target=pv["principal_variation"][0]
    matrix=data.read(4,"distance_matrix","matrix.json")
    distance=matrix["matrix"][matrix["labels"].index(initial["position_a"])][matrix["labels"].index(target)]
    value=data.case(4)["treasure_values"][target]
    gain=following["score_a"]-initial["score_a"]
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout="constrained",
                          gridspec_kw={"width_ratios":[1.5,1]})
    for ax in axes:
        ax.axis("off")
    fields=("position_a","position_b","remaining","score_a","score_b","current_player")
    def display(state,key):
        return ", ".join(state[key]) if key=="remaining" else str(state[key])
    table=axes[0].table(cellText=[[key,display(initial,key),display(following,key)] for key in fields],
                        colLabels=["state","s0","s1"],colWidths=[.34,.36,.30],
                        cellLoc="center",bbox=[0,.06,1,.88])
    payoff=axes[1].table(cellText=[["player",initial["current_player"]],["target",target],
                                 ["V",value],["d",distance],["Gain",gain]],
                         colLabels=["action","value"],cellLoc="center",bbox=[.04,.16,.92,.68])
    for current in (table,payoff):
        current.auto_set_font_size(False)
        current.set_fontsize(11)
        for (row,col),cell in current.get_celld().items():
            cell.set_edgecolor("#cbd5e1")
            cell.set_facecolor("#dbeafe" if row==0 else "white")
    return finish(fig,"题目四：博弈状态与收益更新",
                  "位置以标记名称表示并关联地图坐标；每次只删除选中的宝藏，到达深度限制时按当前 U 评价。")


def root_choices(data:Results):
    labels=list(data.case(4)["treasure_values"])
    series={f"H={depth}":[data.root_values(depth)[label] for label in labels] for depth in (2,4)}
    fig,ax=plt.subplots(figsize=(11,5.5),layout="constrained")
    bars(ax,labels,series,"最坏应对下的收益差 U","固定首步后，MIN 最优应对得到的分支值")
    ax.axhline(0,color=GRAY,linewidth=.8)
    ax.margins(y=.3)
    return finish(fig,"题目四：搜索深度改变首步决策的原因",
                  "所有柱值均取自无剪枝 Minimax 的根子节点完整回传；不使用 Alpha-Beta 中可能只是界的内部返回值。")


def score_evolution(data:Results):
    fig,axes=plt.subplots(1,2,figsize=(14,5.5),layout="constrained")
    for ax,depth in zip(axes,(2,4)):
        pv=data.pv(depth)
        states=pv["states"]
        x=np.arange(len(states))
        score_a=[state["score_a"] for state in states]
        score_b=[state["score_b"] for state in states]
        utility=[a-b for a,b in zip(score_a,score_b)]
        ax.plot(x,score_a,"o-",color=BLUE,label="Score_A")
        ax.plot(x,score_b,"s-",color=ORANGE,label="Score_B")
        ax.plot(x,utility,"D--",color=GREEN,linewidth=2,label="U=Score_A−Score_B")
        labels=["初始"]
        for index,target in enumerate(pv["principal_variation"]):
            before,after=states[index:index+2]
            player=before["current_player"]
            key="score_a" if player=="A" else "score_b"
            gain=after[key]-before[key]
            labels.append(f"{player}→{target}\nGain={gain:+d}")
        for index,value in enumerate(utility):
            ax.annotate(str(value),(index,value),xytext=(0,9),textcoords="offset points",ha="center",color=GREEN)
        ax.set_xticks(x,labels,fontsize=9)
        ax.set_xlabel("主变化中的行动顺序")
        ax.axhline(0,color=GRAY,linewidth=.8)
        ax.set_title(f"H={depth}：首步 {pv['best_action']}，最终 U={pv['best_value']:g}")
        style_axis(ax,"累计收益 / 收益差")
        ax.legend(fontsize=9)
    return finish(fig,"题目四：两种搜索深度的收益演化",
                  "曲线对应各自深度下的一条最优主变化，不代表完整策略树；负 Gain 仍可能是必须执行的最优选择。")


def movement_routes(data:Results):
    paths={(item["from_point"],item["to_point"]):item["path"]
           for item in data.read(4,"distance_matrix","paths.json")}
    fig,axes=plt.subplots(1,2,figsize=(13,7),layout="constrained")
    for ax,depth in zip(axes,(2,4)):
        pv=data.pv(depth)
        grid(ax,data.case(4)["grid"],weighted=True)
        for index,target in enumerate(pv["principal_variation"]):
            before=pv["states"][index]
            player=before["current_player"]
            start=before["position_a" if player=="A" else "position_b"]
            color=BLUE if player=="A" else ORANGE
            path=paths[start,target]
            route(ax,path,color=color,linestyle="-" if index<2 else "--",linewidth=2.7,
                  label=f"第 {index+1} 步 {player}：{start}→{target}")
            row,col=path[-1]
            ax.text(col+.28,row+.28,str(index+1),ha="center",va="center",color=color,fontsize=10,zorder=6,
                    bbox={"boxstyle":"circle,pad=.12","facecolor":"white","edgecolor":color})
        ax.set_title(f"H={depth} 的最优主变化移动路线")
        ax.legend(loc="upper center",bbox_to_anchor=(.5,-.11),ncols=2,fontsize=8)
    return finish(fig,"题目四：由两两 A* 路径组成的行动路线",
                  "蓝色为 A，橙色为 B；实线为前两步，虚线为后两步；圆角标为本回合实际领取的宝藏。")


def search_efficiency(data:Results):
    configs=[(depth,order) for depth in (2,4) for order in ("input","reverse")]
    labels=[f"H={depth}\n{'输入顺序' if order=='input' else '逆序'}" for depth,order in configs]
    fig,axes=plt.subplots(2,2,figsize=(13,8),layout="constrained")
    for ax,key,title in zip(axes.flat[:3],("nodes_visited","nodes_expanded","evaluation_calls"),
                            ("访问节点数","展开节点数","叶子评价次数")):
        series={name:[int(data.metric(4,phase="game",algorithm=algorithm,depth_limit=depth,move_order=order)[key])
                      for depth,order in configs]
                for algorithm,name in (("minimax","Minimax"),("alpha_beta","Alpha-Beta"))}
        bars(ax,labels,series,"次数",title)
    ratios=[]
    for depth,order in configs:
        baseline=int(data.metric(4,phase="game",algorithm="minimax",depth_limit=depth,move_order=order)["nodes_visited"])
        candidate=int(data.metric(4,phase="game",algorithm="alpha_beta",depth_limit=depth,move_order=order)["nodes_visited"])
        ratios.append(100*(baseline-candidate)/baseline)
    bars(axes[1,1],labels,{"相对同设置 Minimax":ratios},"访问减少率 %","剪枝实际节省的访问量",decimals=1)
    return finish(fig,"题目四：深度与访问顺序对搜索开销的影响",
                  "仅比较同深度、同顺序的两种算法；全部为博弈阶段统计，不包含距离矩阵预计算。")


def pruning_depths(data:Results):
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout="constrained")
    for row,depth in enumerate((2,4)):
        indexes=list(range(1,depth))
        event_series,branch_series={},{}
        for order,label in (("input","输入顺序"),("reverse","逆序")):
            events=data.read(4,f"depth_{depth}",f"{order}_order","alpha_beta","trace.json")
            cuts=[event for event in events if event["event"]=="cutoff"]
            counts=[sum(event["depth"]==level for event in cuts) for level in indexes]
            branches=[sum(event["details"]["pruned_branches"] for event in cuts if event["depth"]==level)
                      for level in indexes]
            metric=data.metric(4,phase="game",algorithm="alpha_beta",depth_limit=depth,move_order=order)
            if sum(counts)!=int(metric["cutoff_events"]) or sum(branches)!=int(metric["pruned_branches"]):
                raise ValueError("Cutoff trace does not match recorded counters")
            event_series[label],branch_series[label]=counts,branches
        labels=[f"深度 {level}" for level in indexes]
        bars(axes[row,0],labels,event_series,f"H={depth} 剪枝事件数",f"H={depth}：剪枝事件发生位置")
        bars(axes[row,1],labels,branch_series,f"H={depth} 跳过的直接分支数",f"H={depth}：跳过的直接兄弟分支")
    return finish(fig,"题目四：剪枝发生深度与直接跳过的分支",
                  "同一次剪枝可能省去大小不同的子树；直接分支数不能当成节省的后代节点总数。根深度为 0。")


def runtime_phases(data:Results):
    labels=data.read(4,"distance_matrix","matrix.json")["labels"]
    times=np.array([[float(data.metric(4,phase="distance",from_point=a,to_point=b)["elapsed_seconds"])*1e6
                     for b in labels] for a in labels])
    fig,axes=plt.subplots(1,2,figsize=(14,5.8),layout="constrained")
    im=axes[0].imshow(times,cmap="YlGnBu",vmin=0)
    for row in range(len(labels)):
        for col in range(len(labels)):
            axes[0].text(col,row,f"{times[row,col]:.1f}",ha="center",va="center",fontsize=8,
                         color="white" if times[row,col]>.55*times.max() else "#111827")
    axes[0].set_xticks(range(len(labels)),labels)
    axes[0].set_yticks(range(len(labels)),labels)
    axes[0].set_xlabel("终点")
    axes[0].set_ylabel("起点")
    axes[0].set_title(f"距离矩阵的 36 次 A* 计时\n搜索时间之和 {times.sum():.1f} µs")
    fig.colorbar(im,ax=axes[0],shrink=.8,label="微秒 µs")
    configs=[(depth,order) for depth in (2,4) for order in ("input","reverse")]
    series={name:[float(data.metric(4,phase="game",algorithm=algorithm,depth_limit=depth,move_order=order)["elapsed_seconds"])*1e6
                  for depth,order in configs] for algorithm,name in (("minimax","Minimax"),("alpha_beta","Alpha-Beta"))}
    bars(axes[1],[f"H={depth}\n{'输入顺序' if order=='input' else '逆序'}" for depth,order in configs],
         series,"微秒 µs","复用距离矩阵后的博弈阶段",decimals=1)
    return finish(fig,"题目四：寻路预计算与博弈搜索的观测时间",
                  TIME_NOTE+"左侧求和不含建图和文件写入；右侧不重复计入预计算。")


def figures(data:Results)->dict:
    return {"10_treasure_map_matrix":map_matrix(data),"11_treasure_state":state_model(data),
            "12_treasure_root_choices":root_choices(data),"13_treasure_scores":score_evolution(data),
            "14_treasure_routes":movement_routes(data),"15_treasure_efficiency":search_efficiency(data),
            "16_treasure_pruning_depth":pruning_depths(data),"17_treasure_runtime":runtime_phases(data)}

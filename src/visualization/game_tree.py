"""由完整回传及剪枝事件绘制博弈树，不把剪枝界当作精确值。"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from .common import BLUE,GREEN,ORANGE,RED,GRAY,TIME_NOTE,bars,finish
from .data import Results,tree_trace


def layout(root:dict)->tuple[dict,dict]:
    positions,nodes={},{}
    leaf=0
    def walk(node,path):
        nonlocal leaf
        nodes[path]=node
        children=node.get("children",[])
        if children:
            xs=[walk(child,path+(i,)) for i,child in enumerate(children)]
            x=sum(xs)/len(xs)
        else:
            x=leaf
            leaf+=1
        positions[path]=(x,len(path))
        return x
    walk(root,())
    return positions,nodes


def draw_tree(ax,root:dict,parsed:dict,*,show_order:bool=False,backup:bool=False):
    positions,nodes=layout(root)
    visited,values,cuts=parsed["visits"],parsed["values"],parsed["cutoffs"]
    for path,(x,y) in positions.items():
        if not path: continue
        parent=path[:-1]
        xp,yp=positions[parent]
        color=GRAY if path in visited else RED
        width=1.2
        if backup and parent in values:
            siblings=[parent+(i,) for i in range(len(nodes[parent]["children"]))]
            best=(max if len(parent)%2==0 else min)(values[item] for item in siblings)
            if values[path]==best:
                color,width=GREEN,2
        ax.annotate("",xy=(xp,yp+.27) if backup else (x,y-.27),
                    xytext=(x,y-.27) if backup else (xp,yp+.27),
                    arrowprops={"arrowstyle":"-|>" if backup else "-","color":color,"lw":width,
                                "linestyle":"-" if path in visited else "--"},zorder=1)
    for path,(x,y) in positions.items():
        node=nodes[path]
        children=node.get("children",[])
        active=path in visited
        color="#eff6ff" if len(path)%2==0 else "#f0fdf4"
        edge=BLUE if len(path)%2==0 else GREEN
        if path in cuts:
            color,edge="#fff7ed",ORANGE
        if not active:
            color,edge="#fff1f2",RED
        patch=FancyBboxPatch((x-.36,y-.25),.72,.5,boxstyle="round,pad=.025",
                             facecolor=color,edgecolor=edge,linewidth=1.3,zorder=3)
        ax.add_patch(patch)
        value=values.get(path,node.get("value"))
        if children:
            bound=("≥" if len(path)%2==0 else "≤") if path in cuts else ""
            label=("MAX" if len(path)%2==0 else "MIN")+f"\n{bound}{value:g}"
        else:
            label=f"{value:g}"
        ax.text(x,y,label,ha="center",va="center",fontsize=10,color=GRAY if not active else "#111827",zorder=4)
        if show_order and active:
            ax.text(x,y-.37,f"#{visited[path]}",ha="center",fontsize=8,color=GRAY)
        if not active:
            ax.text(x+.43,y-.23,"×",ha="center",va="center",color=RED,fontsize=17)
    ax.set_xlim(-.65,7.65)
    ax.set_ylim(3.5,-.6)
    ax.axis("off")
    return nodes


def minimax_backup(data:Results):
    root=data.case(3)["tree_structure"]
    parsed=tree_trace(root,data.read(3,"left_to_right","minimax","trace.json"))
    fig,ax=plt.subplots(figsize=(13.5,6),layout="constrained")
    draw_tree(ax,root,parsed,backup=True)
    return finish(fig,"题目三：完整 Minimax 的数值回传",
                  "树上数值来自完整 Minimax 轨迹；绿色箭头标出各节点选中的回传分支。两个 [6,9] 子树分别访问。")


def pruning(data:Results):
    root=data.case(3)["tree_structure"]
    fig,axes=plt.subplots(2,1,figsize=(14,10),layout="constrained")
    for ax,order,label in zip(axes,("left_to_right","reverse"),("从左到右","每层逆序")):
        parsed=tree_trace(root,data.read(3,order,"alpha_beta","trace.json"),reverse=order=="reverse")
        draw_tree(ax,root,parsed,show_order=True)
        ax.set_title(f"{label}：访问 {len(parsed['visits'])} 个节点，根值 {parsed['values'][()]:g}",fontweight="bold")
    return finish(fig,"题目三：相同节点开销，不同剪枝位置",
                  "# 为实际访问序号；红色节点未访问；≥ 标记剪枝后的下界，不能误当完整子树精确值。")


def efficiency(data:Results):
    fig,axes=plt.subplots(1,3,figsize=(14,4.8),layout="constrained")
    orders=("left_to_right","reverse")
    for ax,key,title,ylabel,scale,decimals in zip(axes,
            ("nodes_visited","evaluation_calls","elapsed_seconds"),
            ("访问节点数","叶子评价次数","本次观测耗时"),("节点","次数","微秒 µs"),
            (1,1,1e6),(0,0,1)):
        series={name:[float(data.metric(3,algorithm=algorithm,move_order=order)[key])*scale
                      for order in orders] for algorithm,name in (("minimax","Minimax"),("alpha_beta","Alpha-Beta"))}
        bars(ax,["从左到右","每层逆序"],series,ylabel,title,decimals=decimals)
    return finish(fig,"题目三：算法与访问顺序的开销对照",
                  "本例两种顺序均剪掉 1 个叶子，访问量均从 15 降至 14。"+TIME_NOTE)


def figures(data:Results)->dict:
    return {"07_minimax_backup":minimax_backup(data),"08_alpha_beta_pruning":pruning(data),
            "09_game_tree_efficiency":efficiency(data)}

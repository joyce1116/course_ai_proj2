"""逐图数据文件、计算口径和报告说明导出。"""

import hashlib
import os
from pathlib import Path

from .catalog import FigureSpec

DOC_BEGIN = "<!-- report-figures:begin -->"
DOC_END = "<!-- report-figures:end -->"


def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path:Path,root:Path)->str:
    return os.path.relpath(path.resolve(),root.resolve()).replace("\\","/")


def document(path:Path,specs:list[FigureSpec],output:Path,dpi:int)->None:
    root=path.parent
    def link(target,label=None):
        name=relative(target,root)
        return f"[{label or name}]({name})"
    lines=[DOC_BEGIN,"## 报告图表与数据说明","",
           f"本组共 {len(specs)} 张图，覆盖四道题的结果及过程分析。暂不绘制创新与拓展部分，也不采用收益排序方案。",
           f"全部图表读取现有 `results/`，不重新执行搜索，不修改运行结果。每图仅导出 {dpi} dpi PNG，按题目分类保存。",
           "图片不绘制标题、图注或分析性文字。图名、各子图的读法、数据来源、计算口径和结论统一记录在本节。","",
           "复现命令（在项目根目录执行）：","","```powershell",
           "python -m pip install -r requirements.txt",
           "python -B -X utf8 scripts/plot_results.py","```","",
           "绘图支持 `--results` 指定结果根目录、`--output` 指定图表目录、`--process` 指定说明文档、`--dpi` 指定 PNG 分辨率。",
           "重复执行绘图命令更新同名图和本节说明，不产生新的搜索测量。","",
           "### 数据使用口径","",
           "- 原始运行对每个配置只测量 1 次，且开启轨迹；耗时图仅记录本次观测，不绘制虚构误差条，不据此声称稳定速度排名。",
           "- 访问、展开、生成分别使用各自计数，不混称为同一节点数；目标计入访问，不再展开。",
           "- 剪枝效果按同深度、同访问顺序的 Minimax 基线计算；直接剪掉的分支数不当作未知子树的节点总数。",
           "- 题目四的两两距离预计算与博弈搜索分开，不能把一次预计算重复加到每组决策中。",
           "- 各首步的精确估值取自完整 Minimax 轨迹；Alpha-Beta 内部的剪枝回传可能只是界。",
           "- 地图与输入从各题 `metadata.json` 的输入快照读取，避免当前配置变化后与旧结果混用。","",
           "### 图表索引","","| 图号 | 内容 | 报告位置 | 文件 |","| --- | --- | --- | --- |"]
    for spec in specs:
        png=output/spec.folder/f"{spec.identifier}.png"
        lines.append(f"| {spec.identifier[:2]} | {spec.title} | {spec.section} | {link(png,'PNG')} |")
    for spec in specs:
        lines += ["",f"### 图 {spec.identifier[:2]}：{spec.title}","",
                  f"报告位置：{spec.section}。","","数据来源与字段：",""]
        for file,fields in spec.inputs:
            lines.append(f"- {link(file)}：`{fields}`。")
        lines += ["","读图方式："+spec.reading,
                  "","计算与筛选："+spec.calculation,"","图的含义："+spec.meaning,
                  "","本次结果："+spec.finding]
        if spec.limitation:
            lines += ["","解释边界："+spec.limitation]
    lines += ["",DOC_END]
    block="\n".join(lines)
    existing=path.read_text(encoding="utf-8") if path.exists() else ""
    if DOC_BEGIN in existing and DOC_END in existing:
        before,rest=existing.split(DOC_BEGIN,1)
        _,after=rest.split(DOC_END,1)
        updated=before+block+after
    else:
        updated=existing.rstrip()+"\n\n"+block+"\n"
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(updated,encoding="utf-8")

"""读取已有实验产物，生成报告图表并更新逐图说明。"""

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT=Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0,str(PROJECT_ROOT))
os.environ.setdefault("MPLCONFIGDIR",str(PROJECT_ROOT/".cache"/"matplotlib"))

from src.visualization import game_tree,pathfinding,treasures
from src.visualization.catalog import specifications
from src.visualization.common import configure
from src.visualization.data import Results
from src.visualization.export import digest,document

import matplotlib.pyplot as plt


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results",type=Path,default=PROJECT_ROOT/"results")
    parser.add_argument("--output",type=Path,default=PROJECT_ROOT/"report"/"figures")
    parser.add_argument("--process",type=Path,default=PROJECT_ROOT/"process.md")
    parser.add_argument("--dpi",type=int,default=300)
    args=parser.parse_args()
    if args.dpi<72:
        parser.error("--dpi must be at least 72")
    data=Results(args.results)
    original={path:digest(path) for path in data.root.rglob("*") if path.is_file()}
    specs=specifications(data)
    configure()
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    figures={}
    for module in (pathfinding,game_tree,treasures):
        batch=module.figures(data)
        if figures.keys() & batch.keys():
            raise ValueError("Duplicate figure identifiers")
        figures.update(batch)
    if set(figures)!={spec.identifier for spec in specs}:
        raise ValueError("Figure catalog and render functions do not match")
    for spec in specs:
        fig=figures[spec.identifier]
        for ax in fig.axes:
            for location in ("left","center","right"):
                ax.set_title("",loc=location)
        directory=output/spec.folder
        directory.mkdir(parents=True,exist_ok=True)
        png=directory/f"{spec.identifier}.png"
        fig.savefig(png,dpi=args.dpi,bbox_inches="tight",pad_inches=.16)
        plt.close(fig)
        print(f"Saved {spec.identifier}: {directory.name}",flush=True)
    current={path:digest(path) for path in data.root.rglob("*") if path.is_file()}
    if current!=original:
        raise RuntimeError("Input results changed during plotting")
    document(args.process.resolve(),specs,output,args.dpi)
    print(f"Generated {len(specs)} PNG figures; data files unchanged.")
    print(f"Figures: {output}")
    print(f"Documentation: {args.process.resolve()}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())

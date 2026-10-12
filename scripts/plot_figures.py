#!/usr/bin/env python3
"""Render retained rational coverage/noise data; no model or oracle is rerun."""
import argparse
import csv
import json
import shutil
from fractions import Fraction
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]


def read_rows(path, delimiter=","):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def canvas(width, height, box, fontsize=8):
    """Canvas and axis geometry in PDF points, measured in the original PDF."""
    fig = plt.figure(figsize=(width / 72, height / 72))
    left, bottom, axis_width, axis_height = box
    ax = fig.add_axes([left / width, bottom / height,
                       axis_width / width, axis_height / height])
    ax.tick_params(direction="in", length=2.5, width=.4, pad=3,
                   labelsize=fontsize)
    for spine in ax.spines.values():
        spine.set_linewidth(.4)
    ax.set_axisbelow(True)
    return fig, ax


def save(fig, name, output, paper_figures):
    output.mkdir(parents=True, exist_ok=True)
    target = output / (name + ".pdf")
    fig.savefig(target, format="pdf", metadata={"Creator": None,
                                               "Producer": None,
                                               "CreationDate": None,
                                               "ModDate": None})
    plt.close(fig)
    if paper_figures is not None:
        paper_figures.mkdir(parents=True, exist_ok=True)
        if target.resolve() != (paper_figures / target.name).resolve():
            shutil.copyfile(target, paper_figures / target.name)
    print(json.dumps({"asset": target.name,
                      "size_bp": [round(v * 72, 5) for v in fig.get_size_inches()]}))


def configure_fonts():
    # Discover Windows fonts without a machine-specific absolute path.
    import os
    windows_fonts = Path(os.environ.get("WINDIR", "")) / "Fonts"
    for name in ("times.ttf", "timesi.ttf", "timesbd.ttf"):
        path = windows_fonts / name
        if path.is_file():
            font_manager.fontManager.addfont(path)
    for family in ("Times New Roman", "Liberation Serif", "STIXGeneral"):
        try:
            path = font_manager.findfont(
                font_manager.FontProperties(family=family),
                fallback_to_default=False)
            break
        except ValueError:
            continue
    else:
        raise RuntimeError("Install a Times-family font.")
    plt.rcParams.update({
        "font.family": family, "font.size": 8,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "pdf.use14corefonts": False, "text.usetex": False,
        "mathtext.fontset": "custom", "mathtext.rm": family,
        "mathtext.it": family + ":italic", "mathtext.bf": family + ":bold",
        "mathtext.fallback": None, "axes.unicode_minus": True,
        "axes.labelpad": 5, "legend.fontsize": 8,
    })
    print(json.dumps({"font_family": family, "font_file": path}))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "results/sensitivity")
    parser.add_argument("--output", type=Path, default=ROOT / "figures")
    parser.add_argument("--paper-figures", type=Path)
    args = parser.parse_args()
    configure_fonts()
    coverage = read_rows(args.data / "coverage_slice.csv")
    if len(coverage) != 13 or Fraction(coverage[4]["exact"]) != Fraction(13, 16):
        raise ValueError("Unexpected retained coverage slice.")
    fig, ax = canvas(245, 181, (33.84, 27, 206.22849, 123.37852))
    xs = [int(row["rank"]) for row in coverage]
    ax.plot(xs, [float(Fraction(row["exact"])) for row in coverage],
            color="black", linewidth=.65, marker="o", markersize=3.6,
            label=r"Exact $M(r,1,3)/2^r$")
    ax.plot(xs, [float(Fraction(row["union"])) for row in coverage],
            color=".4", linewidth=.65, linestyle=(0, (3, 2)), marker="s",
            markersize=3.6, label="Summed volume")
    # The original source keeps ranks 11/12 in the data but clips the view to 10.
    ax.set(xlim=(0, 10), ylim=(0, 1.04), xticks=[0, 2, 4, 6, 8, 10],
           yticks=[0, .2, .4, .6, .8, 1], xlabel=r"Residual rank $r$",
           ylabel="Covered fraction")
    ax.set_yticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1"])
    ax.xaxis.label.set_size(8.4682)
    ax.yaxis.label.set_size(8.4682)
    ax.grid(True, color=".75", linewidth=.35)
    legend = ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.04),
                       fontsize=8.4682, frameon=True, fancybox=False,
                       edgecolor="black", facecolor="white", framealpha=1,
                       borderaxespad=0, labelspacing=.2, borderpad=.3)
    legend.get_frame().set_linewidth(.4)
    save(fig, "coverage", args.output, args.paper_figures)
    noise = read_rows(args.data / "noise_sweep.csv")
    points = [{key: Fraction(row[key]) for key in ("eta", "full", "coset", "oracle")}
              for row in noise]
    if len(points) != 17 or any(
        point["eta"] != Fraction(i, 16) or point["full"] != Fraction(5, 8)
        or point["coset"] != Fraction(7, 16) + Fraction(3, 8)*abs(point["eta"]-Fraction(1, 2))
        or point["coset"] != point["oracle"]
        for i, point in enumerate(points)
    ):
        raise ValueError("Retained noise coordinates differ from the running example.")
    fig, ax = canvas(241, 193, (29.873, 26.475, 206.22852, 123.37544))
    eta = [float(point["eta"]) for point in points]
    ax.plot(eta, [float(point["full"]) for point in points],
            color=".4", linewidth=.65, linestyle=(0, (3, 2)),
            label="Full-channel")
    ax.plot(eta, [float(point["coset"]) for point in points],
            color="black", linewidth=.65, marker="o", markersize=4.1844,
            markerfacecolor="white", markeredgewidth=.65, label="Coset")
    ax.plot(eta, [float(point["oracle"]) for point in points],
            color="black", linestyle="none", marker="x", markersize=3.3872,
            markeredgewidth=.65, label="Oracle")
    ax.set(xlim=(0, 1), ylim=(.4, .65), xticks=[0, .25, .5, .75, 1],
           yticks=[.4, .5, .6], xlabel=r"Crossover probability $\eta$",
           ylabel="Eventual success")
    ax.set_xticklabels(["0", "0.25", "0.5", "0.75", "1"])
    ax.xaxis.label.set_size(8.4682)
    ax.yaxis.label.set_size(8.4682)
    ax.grid(True, color=".75", linewidth=.35)
    legend = ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.034),
                       fontsize=8.4682, frameon=True, fancybox=False,
                       edgecolor="black", facecolor="white", framealpha=1,
                       borderaxespad=0, labelspacing=.3, borderpad=.4,
                       handlelength=1.9)
    legend.get_frame().set_linewidth(.4)
    save(fig, "noise-python", args.output, args.paper_figures)
    print(json.dumps({"coverage_rows": len(coverage), "noise_rows": len(points)}))


if __name__ == "__main__":
    main()

"""
Simple base charts for the Q4-Q6 sketches. We print these and draw the interaction
(controls, hover boxes, filters) on top by hand.

Run from the repo root: python3 scripts/question-specific/plot-q4-q6.py
Saves one PNG per question and a printable PDF (A4, one chart per page) to ../q4-q6-figures/,
outside the repo for now. The sketches go into the report once they are scanned.
"""

from pathlib import Path
from textwrap import fill

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

DATA = Path("src/data")
OUT_DIR = Path("../q4-q6-figures")
A4 = (11.69, 8.27)  # landscape, inches

# The empty top part of each page is for drawing controls
GRADE_COLORS = {"A": "#4e79a7", "B": "#f28e2b", "C": "#e15759", "": "white"}
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})


def read(name):
    return pd.read_csv(DATA / name, keep_default_na=False)


def q4():
    branches = read("q4-branches.csv")
    branches = branches[branches["in_sample"]]
    fig, ax = plt.subplots(figsize=A4)
    chains = ["Dunkin", "Starbucks", "McDonald's"]
    for row, chain in enumerate(chains):
        grades = branches[branches["chain"] == chain]["grade"]
        for col, grade in enumerate(["A", "B", "C", ""]):
            n = (grades == grade).sum()
            # dots in rows of 20 inside each grade column, with the count above them
            xs = [col * 25 + i % 20 for i in range(n)]
            ys = [row * 30 + i // 20 for i in range(n)]
            ax.scatter(xs, ys, s=10, color=GRADE_COLORS[grade], edgecolors="none" if grade else "gray", linewidths=.7)
            ax.text(col * 25 - .5, row * 30 - 2, n, fontsize=10)
    ax.set_xticks([9.5, 34.5, 59.5, 84.5], ["A", "B", "C", "No A/B/C yet"])
    ax.xaxis.tick_top()
    ax.set_yticks([12, 42, 72], [f"{c}\n(n = {(branches['chain'] == c).sum()})" for c in chains])
    ax.set_ylim(90, -5)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.subplots_adjust(top=.7, bottom=.08, left=.15, right=.95)
    return fig


def q5():
    codes = read("q5-code-summary.csv").head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=A4)
    labels = codes["code"] + "  " + codes["label"]
    ax.barh(labels, codes["critical"], color="#e15759", edgecolor="white", hatch="//", label="Critical")
    ax.barh(labels, codes["not_critical"], left=codes["critical"], color="#bab0ac", label="Not Critical")
    ax.set_xlabel("Number of citations")
    ax.xaxis.set_major_formatter("{x:,.0f}")
    ax.legend(loc="lower right", frameon=False)
    fig.subplots_adjust(top=.7, bottom=.1, left=.38, right=.95)
    return fig


def q6():
    city = read("q6-pest-summary.csv").set_index("pest").loc["any_pest", "pct_inspections"]
    fig, axes = plt.subplots(1, 2, figsize=A4)
    for ax, (name, field, title) in zip(axes, [("q6-by-nta.csv", "nta_name", "Neighborhood"),
                                               ("q6-by-cuisine.csv", "cuisine", "Cuisine")]):
        top = read(name)
        top = top[top["compare"]].head(8).sort_values("any_pest_pct")
        ax.scatter(top["any_pest_pct"], [fill(g, 24) for g in top[field]], color="#4e79a7", s=50)
        ax.axvline(city, color="gray", linestyle="--", linewidth=.8)
        ax.set_xlim(0, 100)
        ax.set_xlabel("% of inspections with mice, roaches or flies")
        ax.set_title(title)
        ax.text(city + 1, 7.3, f"citywide {city:.0f}%", fontsize=9)
    fig.subplots_adjust(top=.68, bottom=.1, left=.2, right=.97, wspace=.75)
    return fig


OUT_DIR.mkdir(parents=True, exist_ok=True)
with PdfPages(OUT_DIR / "Q4-Q6_print.pdf") as pdf:
    for name, make in [("Q4_chain_grades", q4), ("Q5_violation_frequency", q5), ("Q6_pest_rates", q6)]:
        fig = make()
        fig.savefig(OUT_DIR / f"{name}.png", dpi=150)
        pdf.savefig(fig)
        plt.close(fig)
        print(f"Wrote {OUT_DIR / name}.png")
print(f"Wrote {OUT_DIR / 'Q4-Q6_print.pdf'}")

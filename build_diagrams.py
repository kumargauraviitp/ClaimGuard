"""
Generate diagrams (PNG) for the ClaimGuard research presentation.
All charts are produced from the project's real artifacts so the slides
are faithful to the codebase.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

OUT = os.path.join(os.path.dirname(__file__), "ppt_assets")
os.makedirs(OUT, exist_ok=True)

# ClaimGuard palette (deep navy + teal + accent amber/red)
NAVY   = "#0B1F3A"
TEAL   = "#0E7C86"
AMBER  = "#E8A33D"
RED    = "#C0392B"
GREEN  = "#27AE60"
SLATE  = "#5D6D7E"
LIGHT  = "#F4F6F8"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": NAVY,
    "axes.linewidth": 0.8,
    "text.color": NAVY,
})

# ------------------------------------------------------------------
# 1) CLASS IMBALANCE (donut)
# ------------------------------------------------------------------
def class_imbalance():
    fig, ax = plt.subplots(figsize=(5.2, 5.2), dpi=200)
    sizes = [14497, 923]
    labels = ["Legitimate\n14,497 (94.0%)", "Fraudulent\n923 (6.0%)"]
    colors = [TEAL, RED]
    wedges, _ = ax.pie(sizes, colors=colors, startangle=90,
                       wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2))
    ax.text(0, 0.12, "15,420", ha="center", va="center",
            fontsize=26, fontweight="bold", color=NAVY)
    ax.text(0, -0.16, "total claims", ha="center", va="center",
            fontsize=12, color=SLATE)
    ax.legend(wedges, labels, loc="center", bbox_to_anchor=(0.5, -0.08),
              ncol=2, frameon=False, fontsize=10)
    ax.set_aspect("equal")
    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "imbalance.png"), bbox_inches="tight",
                facecolor="white")
    plt.close(fig)

# ------------------------------------------------------------------
# 2) MODEL LEADERBOARD (grouped bar — Precision / Recall / F1)
# ------------------------------------------------------------------
def model_leaderboard():
    models = ["CTGAN+\nLightGBM", "CTGAN+\nXGBoost", "SMOTE+\nLightGBM"]
    precision = [0.319, 0.309, 0.371]
    recall    = [0.209, 0.202, 0.141]
    f1        = [0.253, 0.244, 0.204]

    x = np.arange(len(models))
    w = 0.26
    fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
    b1 = ax.bar(x - w, precision, w, label="Precision", color=NAVY)
    b2 = ax.bar(x,     recall,    w, label="Recall",    color=TEAL)
    b3 = ax.bar(x + w, f1,        w, label="F1",        color=AMBER)
    ax.set_ylabel("Score")
    ax.set_title("Stage-2 tuned models on the held-out test set", pad=12)
    ax.set_xticks(x); ax.set_xticklabels(models)
    ax.set_ylim(0, 0.46)
    ax.legend(frameon=False, ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, -0.12))
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for bars in (b1, b2, b3):
        for bar in bars:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.008,
                    f"{bar.get_height():.2f}", ha="center", fontsize=8,
                    color=NAVY)
    sns_despine(ax)
    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "leaderboard.png"), bbox_inches="tight",
                facecolor="white")
    plt.close(fig)

# ------------------------------------------------------------------
# 3) SAMPLER TRADE-OFF (SMOTE vs CTGAN) — FPR vs Recall
# ------------------------------------------------------------------
def sampler_tradeoff():
    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=200)
    # points: (fpr, recall, label, color)
    pts = [
        (0.0152, 0.141, "SMOTE+LightGBM\n(low FPR)", NAVY),
        (0.0285, 0.209, "CTGAN+LightGBM\n(best composite)", TEAL),
        (0.0287, 0.202, "CTGAN+XGBoost", AMBER),
        (0.0341, 0.209, "SMOTE+XGBoost", SLATE),
    ]
    for fpr, rec, lab, col in pts:
        ax.scatter(fpr, rec, s=240, color=col, zorder=3, edgecolor="white", linewidth=1.5)
        ax.annotate(lab, (fpr, rec), xytext=(8, 8), textcoords="offset points",
                    fontsize=9, color=NAVY)
    ax.set_xlabel("False Positive Rate  (lower = better)")
    ax.set_ylabel("Recall on fraud  (higher = better)")
    ax.set_title("Operating-point trade-off across samplers", pad=12)
    ax.set_xlim(0, 0.05); ax.set_ylim(0.10, 0.24)
    ax.grid(linestyle=":", alpha=0.4)
    sns_despine(ax)
    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "tradeoff.png"), bbox_inches="tight",
                facecolor="white")
    plt.close(fig)

# ------------------------------------------------------------------
# 4) RISK-TIER GAUGE — business thresholds
# ------------------------------------------------------------------
def risk_tiers():
    fig, ax = plt.subplots(figsize=(9, 2.4), dpi=200)
    tiers = [("Low", 0, 30, GREEN), ("Medium", 30, 65, AMBER),
             ("High", 65, 80, "#E67E22"), ("Critical", 80, 100, RED)]
    for name, lo, hi, col in tiers:
        ax.barh(0, hi-lo, left=lo, color=col, height=0.5,
                edgecolor="white", linewidth=1.5)
        ax.text((lo+hi)/2, 0, name, ha="center", va="center",
                color="white", fontweight="bold", fontsize=11)
        ax.text(lo, -0.5, f"{lo}%", ha="center", fontsize=9, color=SLATE)
    ax.text(100, -0.5, "100%", ha="center", fontsize=9, color=SLATE)
    ax.set_xlim(0, 100); ax.set_ylim(-0.9, 0.7)
    ax.axis("off")
    ax.set_title("Risk-tier assignment from adjusted fraud probability",
                 fontsize=12, color=NAVY, pad=6)
    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "tiers.png"), bbox_inches="tight",
                facecolor="white")
    plt.close(fig)

# ------------------------------------------------------------------
# 5) PIPELINE FLOW (horizontal)
# ------------------------------------------------------------------
def pipeline_flow():
    fig, ax = plt.subplots(figsize=(11.5, 2.2), dpi=200)
    steps = [
        ("Claim\nsubmitted", LIGHT),
        ("ML model\nbase prob", "#D6E4E5"),
        ("Bayesian\nrule engine", "#CFE8D8"),
        ("Risk\ntier", AMBER),
        ("SHAP + LLM\nexplanation", TEAL),
        ("Investigator\nUI", NAVY),
    ]
    n = len(steps)
    box_w, box_h, gap = 1.5, 1.1, 0.45
    total = n*box_w + (n-1)*gap
    x0 = (12 - total) / 2
    for i, (label, col) in enumerate(steps):
        x = x0 + i*(box_w+gap)
        box = FancyBboxPatch((x, 0), box_w, box_h,
                             boxstyle="round,pad=0.02,rounding_size=0.12",
                             linewidth=1.2, edgecolor=NAVY, facecolor=col)
        ax.add_patch(box)
        txtcol = "white" if col in (NAVY, TEAL, AMBER) else NAVY
        ax.text(x+box_w/2, box_h/2, label, ha="center", va="center",
                fontsize=9.5, fontweight="bold", color=txtcol)
        if i < n-1:
            ax.annotate("", xy=(x+box_w+gap-0.02, box_h/2),
                        xytext=(x+box_w+0.02, box_h/2),
                        arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.6))
    ax.set_xlim(0, 12); ax.set_ylim(-0.4, 1.6)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "pipeline.png"), bbox_inches="tight",
                facecolor="white")
    plt.close(fig)

# ------------------------------------------------------------------
# 6) MULTI-AGENT GRAPH
# ------------------------------------------------------------------
def multi_agent():
    fig, ax = plt.subplots(figsize=(9.5, 6.4), dpi=200)

    def node(x, y, label, col, w=1.7, h=0.62, fs=8.5):
        box = FancyBboxPatch((x-w/2, y-h/2), w, h,
                             boxstyle="round,pad=0.02,rounding_size=0.1",
                             linewidth=1.2, edgecolor=NAVY, facecolor=col)
        ax.add_patch(box)
        txtc = "white" if col in (NAVY, TEAL, AMBER, RED) else NAVY
        ax.text(x, y, label, ha="center", va="center", fontsize=fs,
                fontweight="bold", color=txtc)
        return (x, y, w, h)

    def arrow(a, b, rad=0.0, col=NAVY, ls="-"):
        ax.annotate("", xy=(b[0], b[1]), xytext=(a[0], a[1]),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=1.3,
                                    linestyle=ls,
                                    connectionstyle=f"arc3,rad={rad}"))

    # Parallel fan-out row
    fan_y = 5.3
    fan = [
        (1.4, fan_y, "Claim\nAgent", TEAL),
        (3.4, fan_y, "Prediction\nAgent", TEAL),
        (5.4, fan_y, "SHAP\nAgent", TEAL),
        (7.4, fan_y, "Knowledge\nAgent", TEAL),
        (9.4, fan_y, "Policy\nAgent", TEAL),
    ]
    for x, y, lab, col in fan:
        node(x, y, lab, col, w=1.7, h=0.6, fs=8)
    # History agent above
    node(5.4, 6.25, "History Agent", TEAL, w=1.7, h=0.5, fs=8)
    arrow((5.4, 6.0), (5.4, 5.62), col=TEAL)

    # Orchestrator
    node(5.4, 4.2, "Parallel Orchestrator (fan-out)", NAVY, w=4.2, h=0.55, fs=9)
    for x, y, lab, col in fan:
        arrow((5.4, 3.95), (x, y-0.32), rad=(x-5.4)*0.05, col=TEAL, ls="--")

    # Synthesizers
    node(2.4, 3.0, "Contradiction\nAgent", AMBER, w=2.0, h=0.62)
    node(5.4, 3.0, "Risk\nAgent", AMBER, w=1.8, h=0.62)
    node(8.4, 3.0, "Recommendation\nAgent", AMBER, w=2.2, h=0.62)
    arrow((5.4, 3.95), (2.4, 3.33))
    arrow((5.4, 3.95), (5.4, 3.33))
    arrow((5.4, 3.95), (8.4, 3.33))

    # Reflection
    node(5.4, 1.9, "Reflection Agent", NAVY, w=2.4, h=0.55, fs=9)
    arrow((2.4, 2.68), (5.4, 2.18), rad=-0.1)
    arrow((5.4, 2.68), (5.4, 2.18))
    arrow((8.4, 2.68), (5.4, 2.18), rad=0.1)

    # Report -> QA loop
    node(3.0, 0.8, "Report\nAgent", "#1F618D", w=1.9, h=0.62)
    node(7.8, 0.8, "QA Agent", RED, w=1.9, h=0.62)
    arrow((4.6, 1.62), (3.0, 1.12), rad=-0.08)
    arrow((3.7, 0.8), (6.85, 0.8))
    # QA fail loop
    arrow((7.8, 1.12), (3.0, 1.12), rad=0.28, col=RED, ls=(0,(4,3)))
    ax.text(5.4, 1.55, "QA fail → rewrite", ha="center", fontsize=7.5,
            color=RED, style="italic")
    # QA pass
    arrow((7.8, 0.48), (9.6, 0.1))
    node(10.1, 0.1, "Human\nreview", GREEN, w=1.6, h=0.6, fs=8)
    arrow((10.1, 0.4), (10.1, -0.3))
    node(10.1, -0.65, "Store", NAVY, w=1.4, h=0.5, fs=8)

    ax.set_xlim(-0.2, 11.2); ax.set_ylim(-1.1, 6.8)
    ax.axis("off")
    ax.set_title("LangGraph multi-agent investigation pipeline (12 agents)",
                 fontsize=12, color=NAVY, pad=8)
    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "agents.png"), bbox_inches="tight",
                facecolor="white")
    plt.close(fig)

# ------------------------------------------------------------------
# 7) EXPLAINABILITY LAYERS
# ------------------------------------------------------------------
def explain_layers():
    fig, ax = plt.subplots(figsize=(10, 4.6), dpi=200)
    layers = [
        ("Layer 1 — Deterministic", "SHAP Tree-Explainer + label humanizer\n(no AI, fully reproducible)", LIGHT, NAVY),
        ("Layer 2 — Generative", "LLM (Llama-3.3-70B) narrative\n2–3 sentence plain-English summary", "#D6E4E5", NAVY),
        ("Layer 3 — Rule flags", "Bayesian multiplicative rules\n+ human-readable reasons", "#CFE8D8", NAVY),
    ]
    for i, (title, body, col, txtc) in enumerate(layers):
        x = 0.5 + i*3.6
        box = FancyBboxPatch((x, 1.0), 3.2, 2.6,
                             boxstyle="round,pad=0.02,rounding_size=0.15",
                             linewidth=1.4, edgecolor=NAVY, facecolor=col)
        ax.add_patch(box)
        ax.text(x+1.6, 3.2, title, ha="center", fontsize=11,
                fontweight="bold", color=txtc)
        ax.text(x+1.6, 2.05, body, ha="center", va="center",
                fontsize=9.5, color=txtc)
        if i < 2:
            ax.annotate("", xy=(x+3.55, 2.3), xytext=(x+3.25, 2.3),
                        arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.6))
    ax.set_xlim(0, 11.5); ax.set_ylim(0, 4.4)
    ax.axis("off")
    ax.set_title("Three-layer explainability stack", fontsize=12,
                 color=NAVY, pad=6)
    plt.tight_layout()
    fig.savefig(os.path.join(OUT, "explainability.png"), bbox_inches="tight",
                facecolor="white")
    plt.close(fig)

def sns_despine(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

if __name__ == "__main__":
    class_imbalance()
    model_leaderboard()
    sampler_tradeoff()
    risk_tiers()
    pipeline_flow()
    multi_agent()
    explain_layers()
    print("Diagrams written to", OUT)
    for f in sorted(os.listdir(OUT)):
        print("  ", f)

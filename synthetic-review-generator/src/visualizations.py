"""Generate charts for quality & comparison reports"""

import os
import json
import csv
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)


# ---------- helpers ----------

def _ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _load_csv(csv_path):
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        r["review_index"] = int(r["review_index"])
        r["attempt"] = int(r["attempt"])
        r["rating"] = float(r["rating"])
        r["word_count"] = int(r["word_count"])
        r["passed"] = r["passed"].lower() == "true"
        r["generation_time_sec"] = float(r["generation_time_sec"])
    return pd.DataFrame(rows)


# ---------- charts ----------

def rating_distribution(real, synth, out_dir, ts):
    path = os.path.join(out_dir, f"rating_distribution_{ts}.png")

    ratings = sorted({r["rating"] for r in real + synth})
    real_counts = [sum(r["rating"] == x for r in real) for x in ratings]
    synth_counts = [sum(r["rating"] == x for r in synth) for x in ratings]

    fig, ax = plt.subplots()
    x = range(len(ratings))
    w = 0.35

    ax.bar([i - w / 2 for i in x], real_counts, w, label="Real")
    ax.bar([i + w / 2 for i in x], synth_counts, w, label="Synthetic")

    ax.set(title="Rating Distribution", xlabel="Rating", ylabel="Count")
    ax.set_xticks(list(x))
    ax.set_xticklabels(ratings)
    ax.legend()

    return _save(fig, path)


def generation_attempts(df, out_dir, ts):
    path = os.path.join(out_dir, f"generation_attempts_{ts}.png")

    counts = df[df.passed].attempt.value_counts().sort_index()

    fig, ax = plt.subplots()
    ax.bar(counts.index, counts.values)
    ax.set(title="Passed Reviews by Attempt", xlabel="Attempt", ylabel="Count")

    return _save(fig, path)


def model_performance(df, out_dir, ts):
    path = os.path.join(out_dir, f"model_performance_{ts}.png")

    passed = df[df.passed]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    passed.model.value_counts().plot.pie(
        autopct="%1.1f%%", ax=axes[0], title="Reviews per Model"
    )

    passed.groupby("model").generation_time_sec.mean().plot.barh(
        ax=axes[1], title="Avg Generation Time (s)"
    )

    success = passed.groupby("model").size() / df.groupby("model").size() * 100
    success.plot.barh(ax=axes[2], title="Success Rate (%)", xlim=(0, 100))

    return _save(fig, path)


def failed_metrics(df, out_dir, ts):
    path = os.path.join(out_dir, f"failed_metrics_{ts}.png")

    failed = df[~df.passed]
    fig, ax = plt.subplots()

    if failed.empty:
        ax.text(0.5, 0.5, "No Failed Reviews", ha="center", va="center")
        ax.axis("off")
    else:
        failed.failed_metric.value_counts().plot.barh(ax=ax)
        ax.set(title="Failed Metrics", xlabel="Failures")

    return _save(fig, path)


# ---------- public API ----------

def generate_all_charts(csv_path, synthetic_path, real_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    ts = _ts()

    with open(real_path) as f:
        real = json.load(f)
    with open(synthetic_path) as f:
        synth = json.load(f)

    df = _load_csv(csv_path)

    return {
        "rating_distribution": rating_distribution(real, synth, output_dir, ts),
        "generation_attempts": generation_attempts(df, output_dir, ts),
        "model_performance": model_performance(df, output_dir, ts),
        "failed_metrics": failed_metrics(df, output_dir, ts),
    }

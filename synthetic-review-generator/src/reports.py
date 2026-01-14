"""Report generation utilities"""

import csv
import json
import os
from collections import Counter
from datetime import datetime

from visualizations import (
    generate_all_charts,
    rating_distribution,
)


# =========================
# Helpers
# =========================

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def _avg(values, precision=2):
    return round(sum(values) / len(values), precision) if values else 0

REPO_ROOT = "/synthetic-review-generator"


def _md_image(path: str) -> str:
    """Convert filesystem path to markdown-compatible repo path"""
    return f"{REPO_ROOT}/{path.lstrip('/')}"



def generate_quality_report(
    csv_path,
    report_path=None,
    include_charts=False,
    synthetic_path=None,
    real_path=None,
):
    """Generate quality report from CSV log"""

    attempts = passed = 0
    ratings, word_counts = [], []
    failed_metrics = {}
    review_ids = set()

    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            attempts += 1
            review_ids.add(int(row["review_index"]))

            if row["passed"].lower() == "true":
                passed += 1
                ratings.append(float(row["rating"]))
                word_counts.append(int(row["word_count"]))
            else:
                metric = row.get("failed_metric", "unknown")
                failed_metrics[metric] = failed_metrics.get(metric, 0) + 1

    total_reviews = len(review_ids)
    skipped = total_reviews - passed
    success_rate = (passed / total_reviews * 100) if total_reviews else 0

    lines = [
        "# Synthetic Reviews Quality Report",
        f"Generated: {_now()}",
        "",
        "## Summary Statistics",
        "",
        f"- Total reviews attempted: {total_reviews}",
        f"- Total attempts (retries): {attempts}",
        f"- Passed quality: {passed}",
        f"- Skipped: {skipped}",
        f"- Success rate: {success_rate:.1f}%",
        "",
    ]

    if ratings:
        lines += [
            "## Review Metrics",
            "",
            f"- Avg rating: {_avg(ratings)}",
            f"- Min rating: {min(ratings)}",
            f"- Max rating: {max(ratings)}",
            f"- Avg word count: {_avg(word_counts, 1)}",
            f"- Min words: {min(word_counts)}",
            f"- Max words: {max(word_counts)}",
            "",
        ]

    if failed_metrics:
        lines += ["## Failed Metrics", ""]
        lines += [
            f"- {m}: {c}"
            for m, c in sorted(failed_metrics.items(), key=lambda x: x[1], reverse=True)
        ]
        lines.append("")

    # Charts
    if include_charts and synthetic_path and real_path:
        charts_dir = "reports/charts"
        _ensure_dir(charts_dir)

        charts = generate_all_charts(
            csv_path,
            synthetic_path,
            real_path,
            charts_dir,
        )

        lines += [
    "## Visualizations",
    "",
    f"![Rating Distribution]({_md_image(charts['rating_distribution'])})",
    ""
    f"![Generation Attempts]({_md_image(charts['generation_attempts'])})",
    "",
    f"![Model Performance]({_md_image(charts['model_performance'])})",
    "",
    f"![Failed Metrics]({_md_image(charts['failed_metrics'])})",
    "",
]


    if not report_path:
        _ensure_dir("reports")
        report_path = f"reports/quality_report_{_ts()}.md"

    report_text = "\n".join(lines)

    with open(report_path, "w") as f:
        f.write(report_text)

    return report_path, report_text




def generate_comparison_report(
    real_path,
    synthetic_path,
    report_path=None,
    include_charts=False,
):
    """Compare real vs synthetic reviews"""

    with open(real_path) as f:
        real = json.load(f)
    with open(synthetic_path) as f:
        synthetic = json.load(f)

    def analyze(reviews):
        ratings = [r["rating"] for r in reviews]
        words = [len(r["review_text"].split()) for r in reviews]
        titles = [r["title"] for r in reviews]

        return {
            "count": len(reviews),
            "avg_rating": _avg(ratings),
            "min_rating": min(ratings) if ratings else 0,
            "max_rating": max(ratings) if ratings else 0,
            "avg_words": _avg(words, 1),
            "min_words": min(words) if words else 0,
            "max_words": max(words) if words else 0,
            "top_title_words": Counter(" ".join(titles).split()).most_common(10),
        }

    real_stats = analyze(real)
    synth_stats = analyze(synthetic)

    lines = [
        "# Real vs Synthetic Comparison",
        f"Generated: {_now()}",
        "",
        "## Counts",
        f"- Real: {real_stats['count']}",
        f"- Synthetic: {synth_stats['count']}",
        "",
        "## Ratings",
        f"- Avg: Real={real_stats['avg_rating']}, Synthetic={synth_stats['avg_rating']}",
        f"- Min: Real={real_stats['min_rating']}, Synthetic={synth_stats['min_rating']}",
        f"- Max: Real={real_stats['max_rating']}, Synthetic={synth_stats['max_rating']}",
        "",
        "## Word Counts",
        f"- Avg: Real={real_stats['avg_words']}, Synthetic={synth_stats['avg_words']}",
        f"- Min: Real={real_stats['min_words']}, Synthetic={synth_stats['min_words']}",
        f"- Max: Real={real_stats['max_words']}, Synthetic={synth_stats['max_words']}",
        "",
        "## Top Title Words",
        f"- Real: {real_stats['top_title_words']}",
        f"- Synthetic: {synth_stats['top_title_words']}",
        "",
    ]

    if include_charts:
        charts_dir = "reports/charts"
        _ensure_dir(charts_dir)

        chart_path = rating_distribution(
            real,
            synthetic,
            charts_dir,
            _ts(),
        )

        lines += [
        "## Visualization",
        "",
        f"![Rating Distribution Comparison]({_md_image(chart_path)})",
        "",
    ]


    if not report_path:
        _ensure_dir("reports")
        report_path = f"reports/comparison_{_ts()}.md"

    report_text = "\n".join(lines)

    with open(report_path, "w") as f:
        f.write(report_text)

    return report_path, report_text

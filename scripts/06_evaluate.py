"""
Step 6 - Evaluation.

Computes, for every approach that has a results/predictions/<name>.jsonl
file (produced by scripts 03/04/05), on the same test set:
  1. Detection recall
  2. Correction accuracy (primary metric)
  3. Per-error-type correction accuracy breakdown
  4. False positive rate / overcorrection
  5. Speed (sentences/sec, from the *_stats.txt written by each corrector)

Also runs an exact McNemar test (paired, on the same common-subset errors)
between every pair of approaches to check whether a correction-accuracy
difference is statistically significant rather than noise.

Output:
    results/results.csv               (fair comparison, common subset)
    results/results_full_coverage.csv (each approach's own full coverage, if partial)
    results/significance.csv          (pairwise exact McNemar test p-values)
    results/summary.md
    results/charts/overall_accuracy.png
    results/charts/per_error_type.png
"""
import itertools
import json
import sys
from math import comb
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import is_word, tokenize_with_spans
from errors_lib import ERROR_TYPES

ROOT = Path(__file__).parent.parent
TEST_SET_PATH = ROOT / "data" / "test" / "test_set.jsonl"
PRED_DIR = ROOT / "results" / "predictions"
CHARTS_DIR = ROOT / "results" / "charts"
RESULTS_CSV = ROOT / "results" / "results.csv"
SUMMARY_MD = ROOT / "results" / "summary.md"
SIGNIFICANCE_CSV = ROOT / "results" / "significance.csv"

APPROACH_LABELS = {
    "norvig": "Dictionary + Edit Distance",
    "ngram": "N-gram Reranking",
    "llm": "LLM Zero-shot",
    "llm_fewshot": "LLM Few-shot",
}


def load_jsonl(path: Path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def read_speed(name: str):
    stats_path = PRED_DIR / f"{name}_stats.txt"
    if not stats_path.exists():
        return None
    for line in stats_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Sentences/sec:") or line.startswith("Sentences/sec (new calls only):"):
            value = line.split(":", 1)[1].strip()
            return float(value) if value != "None" else None
    return None


def get_indices(name: str, n_test: int) -> list:
    indices_path = PRED_DIR / f"{name}_indices.json"
    if indices_path.exists():
        return json.loads(indices_path.read_text(encoding="utf-8"))
    return list(range(n_test))


def evaluate_approach(name: str, test_set, restrict_to: set = None):
    preds = load_jsonl(PRED_DIR / f"{name}.jsonl")
    indices = get_indices(name, len(test_set))
    by_index = dict(zip(indices, preds))
    if restrict_to is not None:
        by_index = {i: p for i, p in by_index.items() if i in restrict_to}
    test_set = [test_set[i] for i in sorted(by_index)]
    preds = [by_index[i] for i in sorted(by_index)]
    assert len(preds) == len(test_set)

    total_errors = 0
    detected = 0
    correct = 0
    per_type_total = {t: 0 for t in ERROR_TYPES}
    per_type_correct = {t: 0 for t in ERROR_TYPES}
    changed_correct_words = 0
    total_correct_words = 0

    for rec, pred in zip(test_set, preds):
        changes_by_idx = {c["index"]: c["to"] for c in pred["changes"]}
        error_idx = {e["index"]: e for e in rec["errors"]}

        for idx, err in error_idx.items():
            total_errors += 1
            per_type_total[err["type"]] += 1
            if idx in changes_by_idx:
                detected += 1
                if changes_by_idx[idx].lower() == err["orig_word"].lower():
                    correct += 1
                    per_type_correct[err["type"]] += 1

        tws = tokenize_with_spans(rec["corrupted"])
        for idx, (tok, _, _) in enumerate(tws):
            if not is_word(tok) or idx in error_idx:
                continue
            total_correct_words += 1
            if idx in changes_by_idx:
                changed_correct_words += 1

    row = {
        "approach": APPROACH_LABELS.get(name, name),
        "detection_recall": detected / total_errors,
        "correction_accuracy": correct / total_errors,
        "false_positive_rate": (changed_correct_words / total_correct_words) if total_correct_words else 0.0,
        "sentences_per_sec": read_speed(name),
    }
    for t in ERROR_TYPES:
        row[f"acc_{t}"] = (per_type_correct[t] / per_type_total[t]) if per_type_total[t] else float("nan")
    return row


def correctness_vector(name: str, test_set, common_indices) -> list:
    """Per-injected-error correct/incorrect booleans, in a canonical order shared
    across approaches (sentences then errors-within-sentence, both index-sorted)
    so two approaches' vectors line up error-for-error for a paired test."""
    preds = load_jsonl(PRED_DIR / f"{name}.jsonl")
    by_index = dict(zip(get_indices(name, len(test_set)), preds))
    vec = []
    for i in sorted(common_indices):
        rec = test_set[i]
        changes_by_idx = {c["index"]: c["to"] for c in by_index[i]["changes"]}
        for err in sorted(rec["errors"], key=lambda e: e["index"]):
            idx = err["index"]
            vec.append(idx in changes_by_idx and changes_by_idx[idx].lower() == err["orig_word"].lower())
    return vec


def mcnemar_exact_p(b: int, c: int) -> float:
    """Two-sided exact McNemar test p-value from the two discordant-pair counts."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def pairwise_significance(available, test_set, common_indices) -> pd.DataFrame:
    vectors = {name: correctness_vector(name, test_set, common_indices) for name in available}
    rows = []
    for a, b in itertools.combinations(available, 2):
        va, vb = vectors[a], vectors[b]
        a_only = sum(1 for x, y in zip(va, vb) if x and not y)
        b_only = sum(1 for x, y in zip(va, vb) if not x and y)
        p = mcnemar_exact_p(a_only, b_only)
        rows.append({
            "approach_a": APPROACH_LABELS.get(a, a),
            "approach_b": APPROACH_LABELS.get(b, b),
            "a_only_correct": a_only,
            "b_only_correct": b_only,
            "p_value": p,
            "significant_at_0.05": p < 0.05,
        })
    return pd.DataFrame(rows)


def make_charts(df: pd.DataFrame):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(df["approach"], df["correction_accuracy"], color="#4C72B0")
    ax.set_ylabel("Correction accuracy")
    ax.set_title("Overall correction accuracy by approach")
    ax.set_ylim(0, 1)
    for i, v in enumerate(df["correction_accuracy"]):
        ax.text(i, v + 0.02, f"{v:.2f}", ha="center")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "overall_accuracy.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    n_types = len(ERROR_TYPES)
    n_approaches = len(df)
    width = 0.8 / n_approaches
    x = range(n_types)
    for i, (_, row) in enumerate(df.iterrows()):
        values = [row[f"acc_{t}"] for t in ERROR_TYPES]
        offsets = [xi + i * width for xi in x]
        ax.bar(offsets, values, width=width, label=row["approach"])
    ax.set_xticks([xi + width * (n_approaches - 1) / 2 for xi in x])
    ax.set_xticklabels(ERROR_TYPES)
    ax.set_ylabel("Correction accuracy")
    ax.set_title("Per-error-type correction accuracy")
    ax.set_ylim(0, 1)
    ax.legend()
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "per_error_type.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = range(len(df))
    width = 0.35
    ax.bar([xi - width / 2 for xi in x], df["detection_recall"], width=width, label="Detection recall", color="#4C72B0")
    ax.bar([xi + width / 2 for xi in x], df["correction_accuracy"], width=width, label="Correction accuracy", color="#DD8452")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["approach"], rotation=15, ha="right")
    ax.set_ylabel("Share of injected errors")
    ax.set_title("Detection recall vs. correction accuracy")
    ax.set_ylim(0, 1)
    ax.legend()
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "detection_vs_accuracy.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(df["approach"], df["false_positive_rate"], color="#C44E52")
    ax.set_ylabel("False positive rate")
    ax.set_title("Overcorrection: originally-correct words changed")
    for i, v in enumerate(df["false_positive_rate"]):
        ax.text(i, v + max(df["false_positive_rate"]) * 0.02, f"{v:.3f}", ha="center")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "false_positive_rate.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(df["approach"], df["sentences_per_sec"], color="#55A868")
    ax.set_yscale("log")
    ax.set_ylabel("Sentences / sec (log scale)")
    ax.set_title("Speed by approach")
    for i, v in enumerate(df["sentences_per_sec"]):
        ax.text(i, v * 1.15, f"{v:.2f}", ha="center")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "speed_comparison.png", dpi=150)
    plt.close(fig)


def main():
    test_set = load_jsonl(TEST_SET_PATH)
    available = [name for name in APPROACH_LABELS if (PRED_DIR / f"{name}.jsonl").exists()]
    if not available:
        sys.exit(f"No prediction files found in {PRED_DIR}. Run 03/04/05 first.")

    per_approach_indices = {name: set(get_indices(name, len(test_set))) for name in available}
    common_indices = set.intersection(*per_approach_indices.values())
    partial = any(len(idx) != len(test_set) for idx in per_approach_indices.values())

    display_cols = ["approach", "detection_recall", "correction_accuracy", "false_positive_rate", "sentences_per_sec"]
    type_cols = ["approach"] + [f"acc_{t}" for t in ERROR_TYPES]

    common_rows = [evaluate_approach(name, test_set, restrict_to=common_indices) for name in available]
    df_common = pd.DataFrame(common_rows)
    df_common.to_csv(RESULTS_CSV, index=False)
    md_table = df_common[display_cols].to_markdown(index=False, floatfmt=".3f")
    md_type_table = df_common[type_cols].to_markdown(index=False, floatfmt=".3f")

    summary = (
        "# Evaluation summary\n\n"
        f"Common test subset used for comparison: {len(common_indices)} sentences "
        f"(every approach below is scored on this exact same subset).\n\n"
        "## Overall metrics\n\n" + md_table + "\n\n"
        "## Per-error-type correction accuracy\n\n" + md_type_table + "\n"
    )

    if partial:
        full_rows = [evaluate_approach(name, test_set) for name in available]
        df_full = pd.DataFrame(full_rows)
        df_full.insert(1, "n_sentences", [len(per_approach_indices[name]) for name in available])
        full_csv = PRED_DIR.parent / "results_full_coverage.csv"
        df_full.to_csv(full_csv, index=False)
        md_full = df_full[["approach", "n_sentences"] + display_cols[1:]].to_markdown(index=False, floatfmt=".3f")
        summary += (
            "\n## Supplementary: each approach's own full coverage\n\n"
            "Not a like-for-like comparison (different sample sizes) - included for reference only. "
            "See the common-subset table above for the fair comparison.\n\n" + md_full + "\n"
        )

    if len(available) >= 2:
        df_sig = pairwise_significance(available, test_set, common_indices)
        df_sig.to_csv(SIGNIFICANCE_CSV, index=False)
        md_sig = df_sig.to_markdown(index=False, floatfmt=".4f")
        summary += (
            "\n## Pairwise significance (exact McNemar test on correction accuracy)\n\n"
            "Paired test over the same common-subset errors: `a_only_correct` / "
            "`b_only_correct` are errors only one approach got right (discordant "
            "pairs); p < 0.05 means the accuracy difference is unlikely to be chance.\n\n"
            + md_sig + "\n"
        )

    print(summary)
    SUMMARY_MD.write_text(summary, encoding="utf-8")

    make_charts(df_common)
    print(f"\nSaved: {RESULTS_CSV}, {SUMMARY_MD}, {CHARTS_DIR}/overall_accuracy.png, {CHARTS_DIR}/per_error_type.png")
    if len(available) >= 2:
        print(f"Also saved: {SIGNIFICANCE_CSV}")


if __name__ == "__main__":
    main()

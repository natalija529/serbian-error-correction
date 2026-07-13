"""
Step 7 - Error analysis.

Extracts qualitative examples for the report from the same predictions
06_evaluate.py scores:
  (a) errors only the LLM corrected (Norvig and n-gram both wrong)
  (b) errors the n-gram model fixed but Norvig didn't (value of context)
  (c) errors every available approach failed on
  (d) LLM overcorrections (changed a word that was not actually an injected error)

Output:
    results/error_analysis.md
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import is_word, tokenize_with_spans

ROOT = Path(__file__).parent.parent
TEST_SET_PATH = ROOT / "data" / "test" / "test_set.jsonl"
PRED_DIR = ROOT / "results" / "predictions"
OUT_PATH = ROOT / "results" / "error_analysis.md"

N_PER_CATEGORY = 10


def load_jsonl(path: Path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def load_predictions(name: str, test_set):
    path = PRED_DIR / f"{name}.jsonl"
    if not path.exists():
        return None
    preds = load_jsonl(path)
    indices_path = PRED_DIR / f"{name}_indices.json"
    if indices_path.exists():
        indices = json.loads(indices_path.read_text(encoding="utf-8"))
    else:
        indices = list(range(len(test_set)))
        
    by_index = {idx: pred for idx, pred in zip(indices, preds)}
    return by_index


def changes_map(pred):
    return {c["index"]: c["to"] for c in pred["changes"]} if pred else {}


def is_correct(pred, idx, orig_word):
    cm = changes_map(pred)
    return idx in cm and cm[idx].lower() == orig_word.lower()


def fmt_example(n, rec, *fields):
    lines = [f"**Example {n}**", "", f"- corrupted: `{rec['corrupted']}`", f"- original: `{rec['original']}`"]
    for label, value in fields:
        lines.append(f"- {label}: {value}")
    lines.append("")
    return "\n".join(lines)


def main():
    test_set = load_jsonl(TEST_SET_PATH)
    norvig = load_predictions("norvig", test_set)
    ngram = load_predictions("ngram", test_set)
    llm = load_predictions("llm", test_set)

    available = [d for d in (norvig, ngram, llm) if d is not None]
    common_indices = sorted(set.intersection(*(set(d) for d in available))) if available else []
    print(f"Common subset across all available approaches: {len(common_indices)} sentences")

    sections = {"a": [], "b": [], "c": [], "d": []}

    for i in common_indices:
        rec = test_set[i]
        norvig_pred = norvig.get(i) if norvig else None
        ngram_pred = ngram.get(i) if ngram else None
        llm_pred = llm.get(i) if llm else None

        for err in rec["errors"]:
            idx, orig_word = err["index"], err["orig_word"]
            norvig_ok = is_correct(norvig_pred, idx, orig_word) if norvig_pred else None
            ngram_ok = is_correct(ngram_pred, idx, orig_word) if ngram_pred else None
            llm_ok = is_correct(llm_pred, idx, orig_word) if llm_pred else None

            if llm_ok and norvig_ok is False and ngram_ok is False and len(sections["a"]) < N_PER_CATEGORY:
                sections["a"].append(fmt_example(
                    len(sections["a"]) + 1, rec,
                    ("error", f"`{err['bad_word']}` → should be `{orig_word}` (type: {err['type']})"),
                    ("LLM predicted", f"`{llm_pred['predicted']}`"),
                ))

            if ngram_ok and norvig_ok is False and len(sections["b"]) < N_PER_CATEGORY:
                norvig_to = changes_map(norvig_pred).get(idx, "(unchanged)")
                sections["b"].append(fmt_example(
                    len(sections["b"]) + 1, rec,
                    ("error", f"`{err['bad_word']}` → should be `{orig_word}` (type: {err['type']})"),
                    ("Norvig predicted", f"`{norvig_to}`"),
                    ("N-gram predicted", f"`{orig_word}`"),
                ))

            all_checked = [x for x in (norvig_ok, ngram_ok, llm_ok) if x is not None]
            if all_checked and all(x is False for x in all_checked) and len(sections["c"]) < N_PER_CATEGORY:
                preds_str = ", ".join(
                    f"{name}=`{changes_map(p).get(idx, '(unchanged)')}`"
                    for name, p in (("norvig", norvig_pred), ("ngram", ngram_pred), ("llm", llm_pred)) if p
                )
                sections["c"].append(fmt_example(
                    len(sections["c"]) + 1, rec,
                    ("error", f"`{err['bad_word']}` → should be `{orig_word}` (type: {err['type']})"),
                    ("predictions", preds_str),
                ))

        if llm_pred and len(sections["d"]) < N_PER_CATEGORY:
            error_idx = {e["index"] for e in rec["errors"]}
            tws = tokenize_with_spans(rec["corrupted"])
            for c in llm_pred["changes"]:
                idx = c["index"]
                if idx in error_idx or idx >= len(tws) or not is_word(tws[idx][0]):
                    continue
                sections["d"].append(fmt_example(
                    len(sections["d"]) + 1, rec,
                    ("LLM changed correct word", f"`{tws[idx][0]}` → `{c['to']}`"),
                    ("LLM predicted", f"`{llm_pred['predicted']}`"),
                ))
                break

    titles = {
        "a": "(a) Cases only the LLM got right",
        "b": "(b) Cases the n-gram model fixed but Approach 1 (Norvig) got wrong",
        "c": "(c) Cases everything failed on",
        "d": "(d) LLM overcorrections (changed an originally-correct word)",
    }
    lines = ["# Error analysis\n"]
    for key in ("a", "b", "c", "d"):
        lines.append(f"## {titles[key]}\n")
        if not sections[key]:
            lines.append("_No examples found (approach predictions may be missing)._\n")
        else:
            lines.extend(sections[key])
        lines.append("")

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    for key in ("a", "b", "c", "d"):
        print(f"{titles[key]}: {len(sections[key])} examples")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()

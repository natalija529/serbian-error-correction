"""
Step 2 - Synthetic error generation (test set).

Takes the held-out clean sentences (data/test/holdout_sentences.txt, which
were never used to build the dictionary/n-gram models) and injects
realistic errors: diacritic stripping, keyboard-adjacent substitution,
deletion, insertion, and adjacent-character transposition.

Output:
    data/test/test_set.jsonl
    data/test/test_set_stats.txt   (error-type distribution, counts)
"""
import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import RANDOM_SEED, is_word, tokenize_with_spans
from errors_lib import ERROR_TYPES, can_apply, corrupt_word

ROOT = Path(__file__).parent.parent
TEST_DIR = ROOT / "data" / "test"
HOLDOUT_PATH = TEST_DIR / "holdout_sentences.txt"
OUTPUT_PATH = TEST_DIR / "test_set.jsonl"
STATS_PATH = TEST_DIR / "test_set_stats.txt"

MIN_WORD_LEN = 3


def eligible_words(tokens_with_spans):
    return [
        (idx, tok, start, end)
        for idx, (tok, start, end) in enumerate(tokens_with_spans)
        if is_word(tok) and len(tok) >= MIN_WORD_LEN
    ]


def sample_error_count(rng: random.Random, avg_errors: float, max_errors: int, n_eligible: int) -> int:
    count = 0
    remaining = avg_errors
    while count < max_errors and count < n_eligible:
        p = min(remaining, 1.0)
        if p <= 0 or rng.random() >= p:
            break
        count += 1
        remaining -= 1.0
    return count


def choose_error_type(candidate_words, type_counts: Counter, total_assigned: int, rng: random.Random) -> str:
    applicable = sorted({t for _, w, _, _ in candidate_words for t in ERROR_TYPES if can_apply(w, t)})
    target_share = 1.0 / len(ERROR_TYPES)
    deficits = {t: target_share * total_assigned - type_counts[t] for t in applicable}
    best = max(deficits.values())
    best_types = [t for t, d in deficits.items() if d == best]
    return rng.choice(best_types)


def generate_error(sentence: str, tokens_with_spans, used_indices: set, type_counts: Counter,
                    total_assigned: int, rng: random.Random):
    candidates = [c for c in eligible_words(tokens_with_spans) if c[0] not in used_indices]
    if not candidates:
        return None
    error_type = choose_error_type(candidates, type_counts, total_assigned, rng)
    compatible = [c for c in candidates if can_apply(c[1], error_type)]
    idx, word, start, end = rng.choice(compatible)
    bad_word = corrupt_word(word, error_type, rng)
    return {
        "idx": idx, "start": start, "end": end,
        "orig_word": word, "bad_word": bad_word, "type": error_type, "index": idx,
    }


def main():
    parser = argparse.ArgumentParser(description="Step 2: generate synthetic error test set")
    parser.add_argument("--num-sentences", type=int, default=2000)
    parser.add_argument("--avg-errors", type=float, default=1.0, help="average injected errors per sentence")
    parser.add_argument("--max-errors", type=int, default=3, help="cap on errors within a single sentence")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()

    with open(HOLDOUT_PATH, encoding="utf-8") as f:
        sentences = [line.rstrip("\n") for line in f if line.strip()]

    rng = random.Random(args.seed)
    rng.shuffle(sentences)
    sentences = sentences[: args.num_sentences]

    type_counts = Counter()
    total_assigned = 0
    records = []
    skipped_no_eligible = 0

    for sentence in sentences:
        tws = tokenize_with_spans(sentence)
        elig = eligible_words(tws)
        if not elig:
            skipped_no_eligible += 1
            continue

        n_errors = sample_error_count(rng, args.avg_errors, args.max_errors, len(elig))
        if n_errors == 0:
            records.append({"corrupted": sentence, "original": sentence, "errors": []})
            continue

        used_indices = set()
        errors = []
        for _ in range(n_errors):
            err = generate_error(sentence, tws, used_indices, type_counts, total_assigned, rng)
            if err is None:
                break
            used_indices.add(err["idx"])
            type_counts[err["type"]] += 1
            total_assigned += 1
            errors.append(err)

        errors.sort(key=lambda e: e["start"])
        corrupted = sentence
        offset = 0
        clean_errors = []
        for err in errors:
            s, e = err["start"] + offset, err["end"] + offset
            corrupted = corrupted[:s] + err["bad_word"] + corrupted[e:]
            offset += len(err["bad_word"]) - (err["end"] - err["start"])
            clean_errors.append({
                "orig_word": err["orig_word"], "bad_word": err["bad_word"],
                "type": err["type"], "index": err["index"],
            })

        records.append({"corrupted": corrupted, "original": sentence, "errors": clean_errors})

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    n_with_errors = sum(1 for r in records if r["errors"])
    total_errors = sum(len(r["errors"]) for r in records)
    stats_lines = [
        f"Sentences generated: {len(records)}",
        f"Sentences with >=1 injected error: {n_with_errors}",
        f"Sentences skipped (no eligible word >= {MIN_WORD_LEN} chars): {skipped_no_eligible}",
        f"Total injected errors: {total_errors}",
        f"Average errors/sentence: {total_errors / len(records):.3f}",
        "Error type distribution:",
    ]
    for t in ERROR_TYPES:
        c = type_counts[t]
        pct = 100 * c / total_errors if total_errors else 0
        stats_lines.append(f"  {t:14s} {c:5d}  ({pct:.1f}%)")

    stats_text = "\n".join(stats_lines)
    print(stats_text)
    with open(STATS_PATH, "w", encoding="utf-8") as f:
        f.write(stats_text + "\n")


if __name__ == "__main__":
    main()

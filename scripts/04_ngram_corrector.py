"""
Step 4 - Approach 2: N-gram language model reranking.

Detection and candidate generation are identical to Approach 1 (same
frequency dictionary, same tiered edit-distance / diacritic-restoration
candidate generator) so the comparison against Approach 1 isolates the
effect of adding bigram context. The only difference: candidates are
scored with score = log P(candidate | previous word) + log P(next word |
candidate) (stupid-backoff bigram model) instead of raw unigram frequency.

Usage:
    python scripts/04_ngram_corrector.py

Output:
    data/processed/bigram_model.json   (cached unigram+bigram counts)
    results/predictions/ngram.jsonl
    results/predictions/ngram_stats.txt
"""
import argparse
import json
import sys
import time
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from common import is_word, tokenize_with_spans
from corrector_lib import correct_word, get_candidates, is_known, load_freq_dict, match_case
from ngram_lib import BigramScorer, build_bigram_model, get_context, load_bigram_model, save_bigram_model

ROOT = Path(__file__).parent.parent
TRAIN_PATH = ROOT / "data" / "processed" / "train_sentences.txt"
FREQ_PATH = ROOT / "data" / "processed" / "word_freq.json"
BIGRAM_PATH = ROOT / "data" / "processed" / "bigram_model.json"
TEST_SET_PATH = ROOT / "data" / "test" / "test_set.jsonl"
PRED_DIR = ROOT / "results" / "predictions"
PRED_PATH = PRED_DIR / "ngram.jsonl"
STATS_PATH = PRED_DIR / "ngram_stats.txt"


def get_scorer():
    if BIGRAM_PATH.exists():
        print(f"Loading cached bigram model from {BIGRAM_PATH}")
        unigrams, bigrams = load_bigram_model(BIGRAM_PATH)
    else:
        print("Building bigram model from training corpus...")
        unigrams, bigrams = build_bigram_model(TRAIN_PATH)
        save_bigram_model(unigrams, bigrams, BIGRAM_PATH)
    print(f"Bigram model: {len(unigrams)} unigram types, {sum(len(v) for v in bigrams.values())} bigram types")
    return BigramScorer(unigrams, bigrams)


def correct_word_ngram(word: str, prev_word: str, next_word: str, freq, scorer, min_count: int):
    candidates = get_candidates(word, freq, min_count)
    if not candidates:
        return word, False
    best = max(candidates, key=lambda c: scorer.score(c, prev_word, next_word))
    corrected = match_case(best, word)
    return corrected, corrected != word


def correct_sentence(sentence: str, freq, scorer, min_count: int):
    tws = tokenize_with_spans(sentence)
    changes = []
    offset = 0
    predicted = sentence
    for idx, (tok, start, end) in enumerate(tws):
        if not is_word(tok):
            continue
        if is_known(tok, freq, min_count):
            continue
        prev_word, next_word = get_context(tws, idx)
        corrected, changed = correct_word_ngram(tok, prev_word, next_word, freq, scorer, min_count)
        if changed:
            s, e = start + offset, end + offset
            predicted = predicted[:s] + corrected + predicted[e:]
            offset += len(corrected) - (end - start)
            changes.append({"index": idx, "from": tok, "to": corrected})
    return predicted, changes


def main():
    parser = argparse.ArgumentParser(description="Step 4: n-gram reranking corrector")
    parser.add_argument("--min-count", type=int, default=1)
    args = parser.parse_args()

    freq = load_freq_dict(FREQ_PATH) if FREQ_PATH.exists() else None
    if freq is None:
        sys.exit("word_freq.json not found - run scripts/03_norvig_corrector.py first to build it.")
    scorer = get_scorer()

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        test_set = [json.loads(line) for line in f]

    PRED_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    predictions = []
    for rec in tqdm(test_set, desc="N-gram correcting"):
        predicted, changes = correct_sentence(rec["corrupted"], freq, scorer, args.min_count)
        predictions.append({"predicted": predicted, "changes": changes})
    elapsed = time.time() - start_time

    with open(PRED_PATH, "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    sps = len(test_set) / elapsed if elapsed > 0 else float("inf")
    stats = (
        f"Sentences: {len(test_set)}\n"
        f"Elapsed: {elapsed:.2f}s\n"
        f"Sentences/sec: {sps:.2f}\n"
        f"min_count threshold: {args.min_count}\n"
    )
    print(stats)
    with open(STATS_PATH, "w", encoding="utf-8") as f:
        f.write(stats)


if __name__ == "__main__":
    main()

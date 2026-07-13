"""
Step 3 - Approach 1: Dictionary + edit distance (Norvig-style corrector).

Detection rule: a word is flagged as an error if it is not "known" (does not
appear in the training-corpus frequency dictionary at or above min-count).
This approach therefore cannot detect real-word errors (note for the report).

Output:
    data/processed/word_freq.json           (cached frequency dictionary)
    results/predictions/norvig.jsonl
    results/predictions/norvig_stats.txt
"""
import argparse
import json
import sys
import time
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from common import is_word, tokenize_with_spans
from corrector_lib import build_freq_dict, correct_word, is_known, load_freq_dict, save_freq_dict

ROOT = Path(__file__).parent.parent
TRAIN_PATH = ROOT / "data" / "processed" / "train_sentences.txt"
FREQ_PATH = ROOT / "data" / "processed" / "word_freq.json"
TEST_SET_PATH = ROOT / "data" / "test" / "test_set.jsonl"
PRED_DIR = ROOT / "results" / "predictions"
PRED_PATH = PRED_DIR / "norvig.jsonl"
STATS_PATH = PRED_DIR / "norvig_stats.txt"


def get_freq_dict():
    if FREQ_PATH.exists():
        print(f"Loading cached frequency dictionary from {FREQ_PATH}")
        return load_freq_dict(FREQ_PATH)
    print("Building frequency dictionary from training corpus...")
    freq = build_freq_dict(TRAIN_PATH)
    save_freq_dict(freq, FREQ_PATH)
    print(f"Vocabulary size: {len(freq)} word types")
    return freq


def correct_sentence(sentence: str, freq, min_count: int):
    tws = tokenize_with_spans(sentence)
    changes = []
    offset = 0
    predicted = sentence
    for idx, (tok, start, end) in enumerate(tws):
        if not is_word(tok):
            continue
        if is_known(tok, freq, min_count):
            continue
        corrected, changed = correct_word(tok, freq, min_count)
        if changed:
            s, e = start + offset, end + offset
            predicted = predicted[:s] + corrected + predicted[e:]
            offset += len(corrected) - (end - start)
            changes.append({"index": idx, "from": tok, "to": corrected})
    return predicted, changes


def main():
    parser = argparse.ArgumentParser(description="Step 3: Norvig-style corrector")
    parser.add_argument("--min-count", type=int, default=1, help="minimum frequency to count a word as known")
    args = parser.parse_args()

    freq = get_freq_dict()

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        test_set = [json.loads(line) for line in f]

    PRED_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    predictions = []
    for rec in tqdm(test_set, desc="Norvig correcting"):
        predicted, changes = correct_sentence(rec["corrupted"], freq, args.min_count)
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

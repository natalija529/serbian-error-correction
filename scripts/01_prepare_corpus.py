"""
Step 1 - Corpus collection.

Downloads a Serbian sentence corpus (Leipzig Corpora Collection, Wikipedia
2021, 1M sentences), cleans it, transliterates any Cyrillic to Latin,
tokenizes, deduplicates, and splits off a held-out set of sentences that are
NEVER used for building the dictionary / n-gram models. The held-out set is
the raw material for the synthetic test set generated in Step 2.

The source is already one sentence per line, so no custom sentence
segmentation is needed here (unlike a raw article/dump export).

Usage:
    python scripts/01_prepare_corpus.py

Outputs:
    data/raw/srp_wikipedia_2021_1M.tar.gz   (downloaded archive, cached)
    data/processed/train_sentences.txt      (clean sentences for training)
    data/processed/corpus_stats.txt         (token/sentence counts)
    data/test/holdout_sentences.txt         (~2000 sentences never used in training)
"""
import argparse
import random
import re
import sys
import tarfile
from pathlib import Path

import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from common import RANDOM_SEED, cyrillic_to_latin, has_cyrillic, is_word, normalize_whitespace, tokenize

ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
TEST_DIR = ROOT / "data" / "test"

CORPUS_NAME = "srp_wikipedia_2021_1M"
CORPUS_URL = f"https://downloads.wortschatz-leipzig.de/corpora/{CORPUS_NAME}.tar.gz"

HOLDOUT_SIZE = 2000
MIN_TOKENS_PER_SENTENCE = 4
MAX_TOKENS_PER_SENTENCE = 60


def download_corpus(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"[1/5] Archive already downloaded: {dest}")
        return dest
    print(f"[1/5] Downloading {url}")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(dest, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=dest.name) as bar:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
                bar.update(len(chunk))
    return dest


def extract_sentences_file(archive_path: Path, extract_dir: Path) -> Path:
    sentences_name = f"{CORPUS_NAME}-sentences.txt"
    target = extract_dir / sentences_name
    if target.exists():
        print(f"[2/5] Already extracted: {target}")
        return target
    print(f"[2/5] Extracting {sentences_name} from archive")
    with tarfile.open(archive_path, "r:gz") as tar:
        member = next(m for m in tar.getmembers() if m.name.endswith("sentences.txt"))
        member.name = sentences_name  # flatten path
        tar.extract(member, path=extract_dir)
    return target


def clean_sentences(raw_path: Path):
    """Yield cleaned, transliterated sentences from a Leipzig '<id>\\t<sentence>' file."""
    seen = set()
    with open(raw_path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t", 1)
            if len(parts) != 2:
                continue
            sent = parts[1]
            sent = normalize_whitespace(sent)
            # Drop leading list/citation markers (e.g. "; ", "• ") left over from Wikipedia markup.
            sent = re.sub(r"^[;•\-–*\s]+", "", sent).strip()
            if not sent:
                continue
            if has_cyrillic(sent):
                sent = cyrillic_to_latin(sent)
            tokens = tokenize(sent)
            n_words = sum(1 for t in tokens if is_word(t))
            if n_words < MIN_TOKENS_PER_SENTENCE or len(tokens) > MAX_TOKENS_PER_SENTENCE:
                continue
            if n_words / len(tokens) < 0.6:
                continue
            key = sent.lower()
            if key in seen:
                continue
            seen.add(key)
            yield sent


def main():
    parser = argparse.ArgumentParser(description="Step 1: prepare Serbian training corpus")
    parser.add_argument("--holdout-size", type=int, default=HOLDOUT_SIZE)
    parser.add_argument("--limit", type=int, default=None, help="cap number of cleaned sentences (for quick testing)")
    args = parser.parse_args()

    archive_path = download_corpus(CORPUS_URL, RAW_DIR / f"{CORPUS_NAME}.tar.gz")
    sentences_path = extract_sentences_file(archive_path, RAW_DIR)

    print("[3/5] Cleaning, transliterating, deduplicating sentences")
    sentences = []
    for sent in tqdm(clean_sentences(sentences_path), desc="cleaning"):
        sentences.append(sent)
        if args.limit and len(sentences) >= args.limit:
            break

    print(f"[4/5] Splitting off {args.holdout_size} held-out sentences (seed={RANDOM_SEED})")
    rng = random.Random(RANDOM_SEED)
    indices = list(range(len(sentences)))
    rng.shuffle(indices)
    holdout_idx = set(indices[: args.holdout_size])

    holdout_sentences = [sentences[i] for i in sorted(holdout_idx)]
    train_sentences = [sentences[i] for i in range(len(sentences)) if i not in holdout_idx]

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    train_path = PROCESSED_DIR / "train_sentences.txt"
    holdout_path = TEST_DIR / "holdout_sentences.txt"

    with open(train_path, "w", encoding="utf-8") as f:
        f.write("\n".join(train_sentences) + "\n")
    with open(holdout_path, "w", encoding="utf-8") as f:
        f.write("\n".join(holdout_sentences) + "\n")

    train_tokens = sum(len(tokenize(s)) for s in train_sentences)
    train_words = sum(sum(1 for t in tokenize(s) if is_word(t)) for s in train_sentences)

    stats = (
        f"Total cleaned sentences: {len(sentences)}\n"
        f"Training sentences: {len(train_sentences)}\n"
        f"Held-out sentences: {len(holdout_sentences)}\n"
        f"Training tokens (incl. punctuation): {train_tokens}\n"
        f"Training word tokens: {train_words}\n"
    )
    print("[5/5] Done.\n" + stats)
    with open(PROCESSED_DIR / "corpus_stats.txt", "w", encoding="utf-8") as f:
        f.write(stats)


if __name__ == "__main__":
    main()

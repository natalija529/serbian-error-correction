"""
Bigram language model with stupid backoff, used by Approach 2 to rerank
the same candidates Approach 1 generates.

Smoothing choice: stupid backoff (Brants et al., 2007) rather than
Katz/Kneser-Ney — it needs no held-out discount fitting, is O(1) per
lookup, and is standard practice for this kind of large-n, CPU-only n-gram
setup. Sentence boundaries are modeled with explicit <s> / </s> tokens so
the first/last word in a sentence still gets one-sided bigram context.
"""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import is_word, tokenize

BOS, EOS = "<s>", "</s>"
ALPHA = 0.4  
ADD_K = 1.0 


def build_bigram_model(train_path: Path):
    unigrams = Counter()
    bigrams = defaultdict(Counter)
    with open(train_path, encoding="utf-8") as f:
        for line in f:
            words = [t.lower() for t in tokenize(line) if is_word(t)]
            if not words:
                continue
            seq = [BOS] + words + [EOS]
            for w in seq:
                unigrams[w] += 1
            for w1, w2 in zip(seq, seq[1:]):
                bigrams[w1][w2] += 1
    return unigrams, bigrams


def save_bigram_model(unigrams: Counter, bigrams: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"unigrams": unigrams, "bigrams": {w1: dict(counter) for w1, counter in bigrams.items()}}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def load_bigram_model(path: Path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return Counter(data["unigrams"]), data["bigrams"]


class BigramScorer:
    def __init__(self, unigrams: Counter, bigrams: dict):
        self.unigrams = unigrams
        self.bigrams = bigrams
        self.total = sum(unigrams.values())
        self.vocab_size = len(unigrams)

    def unigram_prob(self, w: str) -> float:
        return (self.unigrams.get(w, 0) + ADD_K) / (self.total + ADD_K * self.vocab_size)

    def bigram_prob(self, w1: str, w2: str) -> float:
        c1 = self.unigrams.get(w1, 0)
        c12 = self.bigrams.get(w1, {}).get(w2, 0)
        if c1 > 0 and c12 > 0:
            return c12 / c1
        return ALPHA * self.unigram_prob(w2)

    def score(self, candidate: str, prev_word: str, next_word: str) -> float:
        """log P(candidate | prev) + log P(next | candidate), context on both sides."""
        s = 0.0
        if prev_word is not None:
            s += math.log(self.bigram_prob(prev_word, candidate))
        if next_word is not None:
            s += math.log(self.bigram_prob(candidate, next_word))
        if prev_word is None and next_word is None:
            s = math.log(self.unigram_prob(candidate))
        return s


def get_context(tokens_with_spans, idx: int):
    """Nearest preceding/following word tokens (lowercased) around position idx, else BOS/EOS."""
    prev_word = BOS
    for j in range(idx - 1, -1, -1):
        tok = tokens_with_spans[j][0]
        if is_word(tok):
            prev_word = tok.lower()
            break
    next_word = EOS
    for j in range(idx + 1, len(tokens_with_spans)):
        tok = tokens_with_spans[j][0]
        if is_word(tok):
            next_word = tok.lower()
            break
    return prev_word, next_word

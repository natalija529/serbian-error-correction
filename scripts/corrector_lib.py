"""
Shared building blocks for Approach 1 (Norvig-style) and Approach 2
(n-gram reranking) correctors: frequency dictionary I/O, the Serbian
edit-distance candidate generator, and the dedicated diacritic-restoration
candidate generator.
"""
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import is_word, tokenize

SERBIAN_ALPHABET = "abcčćdđefghijklmnoprsštuvzž"


def build_freq_dict(train_path: Path) -> Counter:
    freq = Counter()
    with open(train_path, encoding="utf-8") as f:
        for line in f:
            for tok in tokenize(line):
                if is_word(tok):
                    freq[tok.lower()] += 1
    return freq


def save_freq_dict(freq: Counter, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(freq, f, ensure_ascii=False)


def load_freq_dict(path: Path) -> Counter:
    with open(path, encoding="utf-8") as f:
        return Counter(json.load(f))



def edits1(word: str, alphabet: str = SERBIAN_ALPHABET) -> set:
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in alphabet]
    inserts = [L + c + R for L, R in splits for c in alphabet]
    return set(deletes + transposes + replaces + inserts)


def edits2(word: str, alphabet: str = SERBIAN_ALPHABET) -> set:
    return {e2 for e1 in edits1(word, alphabet) for e2 in edits1(e1, alphabet)}



_CHAR_OPTIONS = {
    "c": ["c", "č", "ć"], "C": ["C", "Č", "Ć"],
    "s": ["s", "š"], "S": ["S", "Š"],
    "z": ["z", "ž"], "Z": ["Z", "Ž"],
}


def diacritic_candidates(word: str, max_candidates: int = 2000) -> set:
    groups = []
    i = 0
    while i < len(word):
        pair = word[i:i + 2]
        if pair.lower() == "dj":
            dj_char = "Đ" if pair[0].isupper() else "đ"
            groups.append([pair, dj_char])
            i += 2
        else:
            groups.append(_CHAR_OPTIONS.get(word[i], [word[i]]))
            i += 1

    candidates = set()
    for combo in itertools.product(*groups):
        candidates.add("".join(combo))
        if len(candidates) >= max_candidates:
            break
    candidates.discard(word)
    return candidates



def is_known(word: str, freq: Counter, min_count: int = 1) -> bool:
    return freq.get(word.lower(), 0) >= min_count


def known(words, freq: Counter, min_count: int = 1) -> set:
    return {w for w in words if freq.get(w, 0) >= min_count}


def match_case(candidate: str, original: str) -> str:
    if original.isupper() and len(original) > 1:
        return candidate.upper()
    if original[:1].isupper():
        return candidate[:1].upper() + candidate[1:]
    return candidate


def candidate_tiers(word: str, freq: Counter, min_count: int = 1, alphabet: str = SERBIAN_ALPHABET):
    """Yield successive tiers of known candidates, most authentic/cheap first."""
    lower = word.lower()
    yield known([lower], freq, min_count)
    yield known(diacritic_candidates(lower), freq, min_count)
    yield known(edits1(lower, alphabet), freq, min_count)
    yield known(edits2(lower, alphabet), freq, min_count)
    combined = set()
    for c in diacritic_candidates(lower):
        combined |= edits1(c, alphabet)
    yield known(combined, freq, min_count)


def get_candidates(word: str, freq: Counter, min_count: int = 1, alphabet: str = SERBIAN_ALPHABET) -> set:
    """First non-empty tier of known candidates (lowercase), or {} if none found."""
    for tier in candidate_tiers(word, freq, min_count, alphabet):
        if tier:
            return tier
    return set()


def correct_word(word: str, freq: Counter, min_count: int = 1, alphabet: str = SERBIAN_ALPHABET):
    """Return (corrected_word, changed) preserving the input's capitalization."""
    candidates = get_candidates(word, freq, min_count, alphabet)
    if not candidates:
        return word, False
    best = max(candidates, key=lambda w: freq.get(w, 0))
    corrected = match_case(best, word)
    return corrected, corrected != word

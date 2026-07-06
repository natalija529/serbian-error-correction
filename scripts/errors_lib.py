"""
Error-injection primitives for Step 2 (synthetic test set generation):
a Serbian QWERTZ adjacency map and five corruption functions, one per
error type in instructions.md.
"""
import random

# --- Serbian (Latin) QWERTZ keyboard adjacency ------------------------------
# Approximate row layout of a Serbian Latin keyboard, letter rows only (the
# digit row is excluded so a typo can never turn a word into an alphanumeric
# token, which would fall outside the word tokenizer downstream). Vertical
# neighbors are derived by proportional column alignment across rows of
# different lengths.
_ROWS = [
    "qwertzuiopšđ",
    "asdfghjklčć",
    "yxcvbnm",
]


def _build_adjacency() -> dict:
    adjacency = {ch: set() for row in _ROWS for ch in row}
    for r, row in enumerate(_ROWS):
        for i, ch in enumerate(row):
            if i > 0:
                adjacency[ch].add(row[i - 1])
            if i < len(row) - 1:
                adjacency[ch].add(row[i + 1])
            for other_r in (r - 1, r + 1):
                if 0 <= other_r < len(_ROWS):
                    other = _ROWS[other_r]
                    j = round(i * (len(other) - 1) / (len(row) - 1)) if len(row) > 1 else 0
                    for jj in (j - 1, j, j + 1):
                        if 0 <= jj < len(other):
                            adjacency[ch].add(other[jj])
            adjacency[ch].discard(ch)
    return adjacency


KEY_ADJACENCY = _build_adjacency()

DIACRITIC_MAP = {
    "č": "c", "ć": "c", "š": "s", "ž": "z", "đ": "dj",
    "Č": "C", "Ć": "C", "Š": "S", "Ž": "Z", "Đ": "Dj",
}

ERROR_TYPES = ["diacritic", "substitution", "deletion", "insertion", "transposition"]


def diacritic_positions(word: str) -> list:
    return [i for i, ch in enumerate(word) if ch in DIACRITIC_MAP]


def can_apply(word: str, error_type: str) -> bool:
    if error_type == "diacritic":
        return len(diacritic_positions(word)) > 0
    if error_type == "transposition":
        return len(word) >= 2 and any(word[i] != word[i + 1] for i in range(len(word) - 1))
    if error_type in ("substitution", "insertion"):
        return any(ch.lower() in KEY_ADJACENCY and KEY_ADJACENCY[ch.lower()] for ch in word)
    if error_type == "deletion":
        return len(word) >= 3
    return False


def apply_diacritic(word: str, rng: random.Random) -> str:
    positions = diacritic_positions(word)
    k = rng.randint(1, len(positions))
    chosen = set(rng.sample(positions, k))
    return "".join(DIACRITIC_MAP[ch] if i in chosen and ch in DIACRITIC_MAP else ch for i, ch in enumerate(word))


def apply_substitution(word: str, rng: random.Random) -> str:
    candidates = [i for i, ch in enumerate(word) if ch.lower() in KEY_ADJACENCY and KEY_ADJACENCY[ch.lower()]]
    i = rng.choice(candidates)
    ch = word[i]
    neighbor = rng.choice(sorted(KEY_ADJACENCY[ch.lower()]))
    if ch.isupper():
        neighbor = neighbor.upper()
    return word[:i] + neighbor + word[i + 1:]


def apply_deletion(word: str, rng: random.Random) -> str:
    i = rng.randrange(len(word))
    return word[:i] + word[i + 1:]


def apply_insertion(word: str, rng: random.Random) -> str:
    candidates = [i for i, ch in enumerate(word) if ch.lower() in KEY_ADJACENCY and KEY_ADJACENCY[ch.lower()]]
    i = rng.choice(candidates)
    ch = word[i]
    neighbor = rng.choice(sorted(KEY_ADJACENCY[ch.lower()]))
    if ch.isupper():
        neighbor = neighbor.upper()
    pos = i + rng.randint(0, 1)
    return word[:pos] + neighbor + word[pos:]


def apply_transposition(word: str, rng: random.Random) -> str:
    candidates = [i for i in range(len(word) - 1) if word[i] != word[i + 1]]
    i = rng.choice(candidates)
    chars = list(word)
    chars[i], chars[i + 1] = chars[i + 1], chars[i]
    return "".join(chars)


APPLY_FN = {
    "diacritic": apply_diacritic,
    "substitution": apply_substitution,
    "deletion": apply_deletion,
    "insertion": apply_insertion,
    "transposition": apply_transposition,
}


def corrupt_word(word: str, error_type: str, rng: random.Random, max_attempts: int = 5) -> str:
    """Apply error_type to word, retrying if the result happens to equal the input."""
    for _ in range(max_attempts):
        result = APPLY_FN[error_type](word, rng)
        if result != word:
            return result
    return result

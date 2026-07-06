"""Shared utilities: Cyrillic->Latin transliteration, tokenization, RNG seed."""
import re

RANDOM_SEED = 42

# --- Serbian Cyrillic -> Latin transliteration -----------------------------
# Digraphs must be handled before single letters (Љ->Lj/LJ, Њ->Nj/NJ, Џ->Dž/DŽ).
_DIGRAPHS = {
    "Љ": "Lj", "љ": "lj",
    "Њ": "Nj", "њ": "nj",
    "Џ": "Dž", "џ": "dž",
}

_SINGLE = {
    "А": "A", "а": "a", "Б": "B", "б": "b", "В": "V", "в": "v",
    "Г": "G", "г": "g", "Д": "D", "д": "d", "Ђ": "Đ", "ђ": "đ",
    "Е": "E", "е": "e", "Ж": "Ž", "ж": "ž", "З": "Z", "з": "z",
    "И": "I", "и": "i", "Ј": "J", "ј": "j", "К": "K", "к": "k",
    "Л": "L", "л": "l", "М": "M", "м": "m", "Н": "N", "н": "n",
    "О": "O", "о": "o", "П": "P", "п": "p", "Р": "R", "р": "r",
    "С": "S", "с": "s", "Т": "T", "т": "t", "Ћ": "Ć", "ћ": "ć",
    "У": "U", "у": "u", "Ф": "F", "ф": "f", "Х": "H", "х": "h",
    "Ц": "C", "ц": "c", "Ч": "Č", "ч": "č", "Ш": "Š", "ш": "š",
}

_CYRILLIC_CHARS = set(_DIGRAPHS) | set(_SINGLE)

_ALL_MAP = {**_DIGRAPHS, **_SINGLE}
_CYR_PATTERN = re.compile("|".join(re.escape(k) for k in sorted(_ALL_MAP, key=len, reverse=True)))


def has_cyrillic(text: str) -> bool:
    return any(ch in _CYRILLIC_CHARS for ch in text)


def cyrillic_to_latin(text: str) -> str:
    """Transliterate Serbian Cyrillic to Latin, handling lj/nj/dž digraph casing."""
    return _CYR_PATTERN.sub(lambda m: _ALL_MAP[m.group(0)], text)


# --- Tokenization -----------------------------------------------------------
# Words: letters (incl. Serbian Latin diacritics), digits, and internal
# apostrophes/hyphens. Everything else (punctuation) is its own token.
_TOKEN_RE = re.compile(r"[A-Za-zčćšžđČĆŠŽĐ0-9]+(?:[-'][A-Za-zčćšžđČĆŠŽĐ0-9]+)*|[^\sA-Za-zčćšžđČĆŠŽĐ0-9]")


def tokenize(text: str) -> list:
    return _TOKEN_RE.findall(text)


def tokenize_with_spans(text: str) -> list:
    """Return list of (token, start, end) so a token can be spliced back in place."""
    return [(m.group(0), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_word(token: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-zčćšžđČĆŠŽĐ]+(?:[-'][A-Za-zčćšžđČĆŠŽĐ]+)*", token))

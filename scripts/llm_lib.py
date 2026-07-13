"""
Small provider-swappable LLM client interface for Step 5, using raw HTTP
(`requests`) so no extra SDK dependency is required. API keys are read from
environment variables only - never hardcoded.
"""
import difflib
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from common import tokenize


def load_dotenv(path: Path = None):
    """Minimal .env loader: sets os.environ from KEY=VALUE lines, without overriding existing env vars."""
    path = path or Path(__file__).parent.parent / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_dotenv()


class LLMClient:
    def complete(self, prompt: str) -> str:
        raise NotImplementedError


class AnthropicClient(LLMClient):
    def __init__(self, model=None):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
        self.url = "https://api.anthropic.com/v1/messages"

    def complete(self, prompt: str) -> str:
        resp = requests.post(
            self.url,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=(10, 30),
        )
        if resp.status_code == 429:
            raise RateLimitError(resp.headers.get("retry-after"))
        resp.raise_for_status()
        data = resp.json()
        return "".join(block.get("text", "") for block in data.get("content", []))


class OpenAIClient(LLMClient):
    def __init__(self, model=None):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.url = "https://api.openai.com/v1/chat/completions"

    def complete(self, prompt: str) -> str:
        resp = requests.post(
            self.url,
            headers={"Authorization": f"Bearer {self.api_key}", "content-type": "application/json"},
            json={"model": self.model, "messages": [{"role": "user", "content": prompt}]},
            timeout=(10, 30),
        )
        if resp.status_code == 429:
            raise RateLimitError(resp.headers.get("retry-after"))
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


class GroqClient(LLMClient):
    """OpenAI-compatible chat completions API, free tier, serving open-weight models."""

    def __init__(self, model=None):
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set")
        self.model = model or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def complete(self, prompt: str) -> str:
        resp = requests.post(
            self.url,
            headers={"Authorization": f"Bearer {self.api_key}", "content-type": "application/json"},
            json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
            timeout=(10, 30),
        )
        if resp.status_code == 429:
            raise RateLimitError(resp.headers.get("retry-after"))
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


class RateLimitError(Exception):
    def __init__(self, retry_after=None):
        self.retry_after = float(retry_after) if retry_after else None
        super().__init__(f"rate limited, retry_after={retry_after}")


def get_client(provider: str) -> LLMClient:
    if provider == "anthropic":
        return AnthropicClient()
    if provider == "openai":
        return OpenAIClient()
    if provider == "groq":
        return GroqClient()
    raise ValueError(f"unknown provider: {provider}")


PROMPT_TEMPLATE = (
    "Ispravi isključivo pravopisne i tipografske greške u sledećoj rečenici "
    "(dijakritike, tipfelere). Ne menjaj stil, reči ni red reči osim da ispraviš greške. "
    "Odgovori isključivo ispravljenom rečenicom - bez uvoda, objašnjenja, navodnika ili napomena.\n\n"
    "Rečenica: {sentence}\n"
    "Ispravljena rečenica:"
)

FEWSHOT_EXAMPLES = [
    ("Ovo je jako lep dan za setnju.", "Ovo je jako lep dan za šetnju."),
    ("Necu moci da dodjem sutra na sastanak.", "Neću moći da dođem sutra na sastanak."),
    ("On je najbolji ucenik u razredu.", "On je najbolji učenik u razredu."),
]


def build_prompt(sentence: str, fewshot: bool = False) -> str:
    if not fewshot:
        return PROMPT_TEMPLATE.format(sentence=sentence)
    examples = "\n\n".join(
        f"Rečenica: {bad}\nIspravljena rečenica: {good}" for bad, good in FEWSHOT_EXAMPLES
    )
    return (
        "Ispravi isključivo pravopisne i tipografske greške u rečenici "
        "(dijakritike, tipfelere). Ne menjaj stil, reči ni red reči osim da ispraviš greške. "
        "Odgovori isključivo ispravljenom rečenicom - bez uvoda, objašnjenja, navodnika ili napomena.\n\n"
        f"Primeri:\n{examples}\n\n"
        f"Rečenica: {sentence}\n"
        "Ispravljena rečenica:"
    )


_PREAMBLE_RE = None


def clean_response(text: str) -> str:
    import re
    global _PREAMBLE_RE
    if _PREAMBLE_RE is None:
        _PREAMBLE_RE = re.compile(
            r"^(ispravljena rečenica|ispravna verzija|ispravna rečenica|odgovor|rečenica)\s*[:\-]\s*",
            re.IGNORECASE,
        )
    text = text.strip()
    text = text.splitlines()[0].strip() if text else text
    text = _PREAMBLE_RE.sub("", text).strip()
    if text.startswith('"') and text.endswith('"') and len(text) > 1:
        text = text[1:-1].strip()
    return text


def sentence_key(sentence: str) -> str:
    return hashlib.sha256(sentence.encode("utf-8")).hexdigest()


def load_cache(cache_path: Path) -> dict:
    if cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict, cache_path: Path):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache_path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    tmp.replace(cache_path)


def align_changes(corrupted: str, llm_sentence: str) -> dict:
    """Map corrupted-sentence token index -> replacement text, via difflib opcodes.

    'replace' blocks of equal length map index-for-index; ragged edits (the
    model rephrased/added/removed words) are attributed to the first affected
    index on a best-effort basis - this is what the false_positive_rate metric
    picks up as an overcorrection.
    """
    corrupted_tokens = tokenize(corrupted)
    llm_tokens = tokenize(llm_sentence)
    sm = difflib.SequenceMatcher(
        a=[t.lower() for t in corrupted_tokens], b=[t.lower() for t in llm_tokens], autojunk=False
    )
    changes = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        corrupted_slice = corrupted_tokens[i1:i2]
        llm_slice = llm_tokens[j1:j2]
        if not corrupted_slice:
            continue  
        if len(corrupted_slice) == len(llm_slice):
            for k in range(len(corrupted_slice)):
                changes[i1 + k] = llm_slice[k]
        else:
            joined = " ".join(llm_slice)
            changes[i1] = joined
            for k in range(1, len(corrupted_slice)):
                changes[i1 + k] = ""
    return changes


def call_with_retry(client: LLMClient, prompt: str, max_retries: int = 5, base_delay: float = 1.0) -> str:
    for attempt in range(max_retries):
        try:
            t0 = time.time()
            result = client.complete(prompt)
            print(f"  [call_with_retry] attempt {attempt} ok in {time.time()-t0:.2f}s", flush=True)
            return result
        except RateLimitError as e:
            wait = e.retry_after or base_delay * (2 ** attempt)
            print(f"  [call_with_retry] attempt {attempt} RateLimitError retry_after={e.retry_after} -> sleeping {wait}s", flush=True)
            time.sleep(wait)
        except requests.RequestException as e:
            print(f"  [call_with_retry] attempt {attempt} RequestException: {type(e).__name__}: {e}", flush=True)
            if attempt == max_retries - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
    raise RuntimeError("exhausted retries")

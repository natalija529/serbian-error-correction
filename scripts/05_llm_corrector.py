"""
Step 5 - Approach 3: Large Language Model (zero-shot / few-shot).

Sends each corrupted test sentence to an LLM API with a zero-shot prompt
asking for the corrected sentence only. Responses are cached to disk keyed
by sentence text so a resumed/re-run never re-queries an already-answered
sentence (this step costs money and time).

The LLM's free-form output is aligned back to the corrupted sentence's
tokens with difflib to figure out which words changed and where -
"replace" blocks of equal length map cleanly index-for-index; ragged
edits (the model added/removed/merged words - "overcorrection" territory)
are attributed to the first affected index on a best-effort basis, which
the false_positive_rate metric in 06_evaluate.py picks up as
overcorrection.

Usage:
    export ANTHROPIC_API_KEY=...            # or OPENAI_API_KEY
    python scripts/05_llm_corrector.py --provider anthropic
    python scripts/05_llm_corrector.py --provider anthropic --fewshot --subset-size 300

Output:
    data/test/llm_cache/<provider>_<model>.json   (raw response cache, resumable)
    results/predictions/llm.jsonl (or llm_fewshot.jsonl)
    results/predictions/llm_stats.txt (or llm_fewshot_stats.txt)
    results/predictions/llm_indices.json (subset line indices into test_set.jsonl)
"""
import argparse
import json
import sys
import time
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from common import RANDOM_SEED, tokenize
from llm_lib import (
    align_changes, build_prompt, call_with_retry, clean_response, get_client,
    load_cache, save_cache, sentence_key,
)

ROOT = Path(__file__).parent.parent
TEST_SET_PATH = ROOT / "data" / "test" / "test_set.jsonl"
CACHE_DIR = ROOT / "data" / "test" / "llm_cache"
PRED_DIR = ROOT / "results" / "predictions"


def main():
    parser = argparse.ArgumentParser(description="Step 5: LLM zero-shot/few-shot corrector")
    parser.add_argument("--provider", choices=["anthropic", "openai", "groq"], default="groq")
    parser.add_argument("--fewshot", action="store_true", help="use the few-shot prompt variant")
    parser.add_argument("--subset-size", type=int, default=None, help="limit to N sentences (bonus few-shot run)")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--rate-limit-delay", type=float, default=0.2, help="seconds to sleep between requests")
    args = parser.parse_args()

    client = get_client(args.provider)
    name = "llm_fewshot" if args.fewshot else "llm"
    cache_path = CACHE_DIR / f"{args.provider}_{client.model}_{name}.json"
    cache = load_cache(cache_path)

    with open(TEST_SET_PATH, encoding="utf-8") as f:
        test_set = [json.loads(line) for line in f]

    indices = list(range(len(test_set)))
    if args.subset_size and args.subset_size < len(test_set):
        # Take a prefix rather than reshuffling, so a subset run reuses whatever
        # is already cached from a prior full/partial run in the same order.
        indices = indices[: args.subset_size]

    n_cached = sum(1 for i in indices if sentence_key(test_set[i]["corrupted"]) in cache)
    print(f"Provider={args.provider} model={client.model} fewshot={args.fewshot}")
    print(f"Sentences to process: {len(indices)} ({n_cached} already cached)")

    progress_path = CACHE_DIR / f"{args.provider}_{client.model}_{name}_progress.json"

    start_time = time.time()
    n_new_calls = 0
    for i in tqdm(indices, desc="Querying LLM"):
        sentence = test_set[i]["corrupted"]
        key = sentence_key(sentence)
        if key in cache:
            continue
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        progress_path.write_text(
            json.dumps({"index": i, "sentence": sentence, "started_at": time.time()}), encoding="utf-8"
        )
        prompt = build_prompt(sentence, fewshot=args.fewshot)
        raw = call_with_retry(client, prompt)
        cache[key] = raw
        n_new_calls += 1
        if n_new_calls % 5 == 0:
            save_cache(cache, cache_path)
        time.sleep(args.rate_limit_delay)
    save_cache(cache, cache_path)
    elapsed = time.time() - start_time

    PRED_DIR.mkdir(parents=True, exist_ok=True)
    predictions = []
    for i in indices:
        sentence = test_set[i]["corrupted"]
        raw = cache[sentence_key(sentence)]
        predicted = clean_response(raw)
        changes_map = align_changes(sentence, predicted)
        changes = [{"index": idx, "from": tokenize(sentence)[idx] if idx < len(tokenize(sentence)) else "",
                    "to": to} for idx, to in changes_map.items()]
        predictions.append({"predicted": predicted, "changes": changes})

    pred_path = PRED_DIR / f"{name}.jsonl"
    with open(pred_path, "w", encoding="utf-8") as f:
        for p in predictions:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    with open(PRED_DIR / f"{name}_indices.json", "w", encoding="utf-8") as f:
        json.dump(indices, f)

    sps = len(indices) / elapsed if elapsed > 0 and n_new_calls > 0 else None
    stats = (
        f"Sentences: {len(indices)}\n"
        f"New API calls this run: {n_new_calls}\n"
        f"Elapsed (new calls only): {elapsed:.2f}s\n"
        f"Sentences/sec (new calls only): {sps if sps is None else f'{sps:.2f}'}\n"
        f"Provider: {args.provider}, model: {client.model}, fewshot: {args.fewshot}\n"
    )
    print(stats)
    with open(PRED_DIR / f"{name}_stats.txt", "w", encoding="utf-8") as f:
        f.write(stats)


if __name__ == "__main__":
    main()

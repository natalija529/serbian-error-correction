# Evaluation summary

Common test subset used for comparison: 800 sentences (every approach below is scored on this exact same subset).

## Overall metrics

| approach                   |   detection_recall |   correction_accuracy |   false_positive_rate |   sentences_per_sec |
|:---------------------------|-------------------:|----------------------:|----------------------:|--------------------:|
| Dictionary + Edit Distance |              0.796 |                 0.680 |                 0.017 |              94.980 |
| N-gram Reranking           |              0.796 |                 0.719 |                 0.017 |              94.650 |
| LLM Zero-shot              |              0.964 |                 0.805 |                 0.024 |               0.230 |

## Per-error-type correction accuracy

| approach                   |   acc_diacritic |   acc_substitution |   acc_deletion |   acc_insertion |   acc_transposition |
|:---------------------------|----------------:|-------------------:|---------------:|----------------:|--------------------:|
| Dictionary + Edit Distance |           0.619 |              0.662 |          0.381 |           0.906 |               0.831 |
| N-gram Reranking           |           0.625 |              0.725 |          0.469 |           0.912 |               0.863 |
| LLM Zero-shot              |           0.875 |              0.731 |          0.781 |           0.831 |               0.806 |

## Supplementary: each approach's own full coverage

Not a like-for-like comparison (different sample sizes) - included for reference only. See the common-subset table above for the fair comparison.

| approach                   |   n_sentences |   detection_recall |   correction_accuracy |   false_positive_rate |   sentences_per_sec |
|:---------------------------|--------------:|-------------------:|----------------------:|----------------------:|--------------------:|
| Dictionary + Edit Distance |          2000 |              0.800 |                 0.689 |                 0.019 |              94.980 |
| N-gram Reranking           |          2000 |              0.800 |                 0.728 |                 0.019 |              94.650 |
| LLM Zero-shot              |           800 |              0.964 |                 0.805 |                 0.024 |               0.230 |

## Pairwise significance (exact McNemar test on correction accuracy)

Paired test over the same common-subset errors: `a_only_correct` / `b_only_correct` are errors only one approach got right (discordant pairs); p < 0.05 means the accuracy difference is unlikely to be chance.

| approach_a                 | approach_b       |   a_only_correct |   b_only_correct |   p_value | significant_at_0.05   |
|:---------------------------|:-----------------|-----------------:|-----------------:|----------:|:----------------------|
| Dictionary + Edit Distance | N-gram Reranking |                7 |               38 |    0.0000 | True                  |
| Dictionary + Edit Distance | LLM Zero-shot    |               90 |              190 |    0.0000 | True                  |
| N-gram Reranking           | LLM Zero-shot    |               97 |              166 |    0.0000 | True                  |

# Evaluation summary

Common test subset used for comparison: 2000 sentences (every approach below is scored on this exact same subset).

## Overall metrics

| approach                   |   detection_recall |   correction_accuracy |   false_positive_rate |   sentences_per_sec |
|:---------------------------|-------------------:|----------------------:|----------------------:|--------------------:|
| Dictionary + Edit Distance |              0.800 |                 0.689 |                 0.019 |              94.980 |
| N-gram Reranking           |              0.800 |                 0.728 |                 0.019 |              94.650 |
| LLM Zero-shot              |              0.942 |                 0.781 |                 0.024 |               2.520 |

## Per-error-type correction accuracy

| approach                   |   acc_diacritic |   acc_substitution |   acc_deletion |   acc_insertion |   acc_transposition |
|:---------------------------|----------------:|-------------------:|---------------:|----------------:|--------------------:|
| Dictionary + Edit Distance |           0.667 |              0.698 |          0.393 |           0.912 |               0.775 |
| N-gram Reranking           |           0.670 |              0.760 |          0.468 |           0.917 |               0.825 |
| LLM Zero-shot              |           0.830 |              0.700 |          0.750 |           0.830 |               0.795 |

## Pairwise significance (exact McNemar test on correction accuracy)

Paired test over the same common-subset errors: `a_only_correct` / `b_only_correct` are errors only one approach got right (discordant pairs); p < 0.05 means the accuracy difference is unlikely to be chance.

| approach_a                 | approach_b       |   a_only_correct |   b_only_correct |   p_value | significant_at_0.05   |
|:---------------------------|:-----------------|-----------------:|-----------------:|----------:|:----------------------|
| Dictionary + Edit Distance | N-gram Reranking |               14 |               92 |    0.0000 | True                  |
| Dictionary + Edit Distance | LLM Zero-shot    |              249 |              433 |    0.0000 | True                  |
| N-gram Reranking           | LLM Zero-shot    |              266 |              372 |    0.0000 | True                  |

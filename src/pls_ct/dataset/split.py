"""Split QA examples into train/val/test **by trial** (no trial leakage).

The thesis split 85/15 by row (per question), so the same trial could land in both
train and test across different questions. Here we split on ``trial_name`` so every
example for a trial stays in one split. Deterministic given a seed.
"""

from __future__ import annotations

import random


def split_by_trial(
    examples: list[dict],
    *,
    seed: int = 42,
    ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
) -> dict[str, list[dict]]:
    """Return {"train", "val", "test"} with disjoint trials.

    Ratios apply to the number of *trials* (not examples) and must sum to ~1.0.
    With very few trials, val/test may be empty; train is always filled first.
    """
    if not abs(sum(ratios) - 1.0) < 1e-6:
        raise ValueError(f"ratios must sum to 1.0, got {ratios} -> {sum(ratios)}")

    trials = sorted({ex["trial_name"] for ex in examples})
    rng = random.Random(seed)
    rng.shuffle(trials)

    n = len(trials)
    n_train = int(round(ratios[0] * n))
    n_val = int(round(ratios[1] * n))
    # Guard against rounding overflow; test takes the remainder.
    n_train = min(n_train, n)
    n_val = min(n_val, n - n_train)

    train_trials = set(trials[:n_train])
    val_trials = set(trials[n_train : n_train + n_val])
    # Remaining trials (trials[n_train + n_val:]) fall through to the test bucket.

    buckets: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for ex in examples:
        name = ex["trial_name"]
        if name in train_trials:
            buckets["train"].append(ex)
        elif name in val_trials:
            buckets["val"].append(ex)
        else:
            buckets["test"].append(ex)
    return buckets

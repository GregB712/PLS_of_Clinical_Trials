"""Training data preparation (pure, testable — no ML deps).

Turns QA examples into (input_text, target_text) pairs for seq2seq fine-tuning, using the
same prompt as inference so train/serve match. Also provides a leakage check across splits
and simple dataset statistics.
"""

from __future__ import annotations

from pls_ct.models.generative import build_prompt


def to_training_pairs(examples: list[dict]) -> list[dict[str, str]]:
    """input_text = inference prompt (context+question); target_text = plain-language answer."""
    pairs = []
    for ex in examples:
        answer = (ex.get("answer") or "").strip()
        if not answer:
            continue
        pairs.append(
            {
                "input_text": build_prompt(ex["context"], ex["question"]),
                "target_text": answer,
            }
        )
    return pairs


def find_leakage(splits: dict[str, list[dict]]) -> dict[str, set[str]]:
    """Return {"train∩test": {...}, ...} of trials shared between splits. Empty = clean."""
    trial_sets = {
        name: {ex["trial_name"] for ex in rows} for name, rows in splits.items()
    }
    names = list(trial_sets)
    overlaps: dict[str, set[str]] = {}
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            shared = trial_sets[a] & trial_sets[b]
            if shared:
                overlaps[f"{a}∩{b}"] = shared
    return overlaps


def assert_no_leakage(splits: dict[str, list[dict]]) -> None:
    overlaps = find_leakage(splits)
    if overlaps:
        raise ValueError(f"trial leakage across splits: {overlaps}")


def dataset_stats(examples: list[dict]) -> dict[str, int]:
    return {
        "n_examples": len(examples),
        "n_trials": len({ex["trial_name"] for ex in examples}),
        "n_questions": len({ex["question"] for ex in examples}),
    }

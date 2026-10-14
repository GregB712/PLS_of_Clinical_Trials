"""Seq2seq fine-tuning runner (OPTIONAL, GPU-gated).

Requires the ``[ml]`` extra (and ``[peft]`` for LoRA). CPU works but is slow; a GPU is
used automatically when present. This module is **not exercised by automated tests** (no
model downloads / GPU in CI) — its pure, testable parts live in ``dataprep.py``. It is the
reproducible path to reproduce/extend the thesis fine-tuning; run it deliberately.

Default base model is an encoder-decoder (e.g. ``google/flan-t5-base``) because the task is
abstractive — unlike the thesis's extractive DistilBERT (see docs/PROJECT_AUDIT.md).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pls_ct.device import resolve_device
from pls_ct.training.dataprep import assert_no_leakage, to_training_pairs


@dataclass
class FinetuneConfig:
    base_model: str = "google/flan-t5-base"
    epochs: int = 3
    learning_rate: float = 3e-4
    batch_size: int = 8
    max_input_len: int = 1024
    max_target_len: int = 256
    use_lora: bool = False
    seed: int = 42
    early_stopping_patience: int = 2


def _require_ml():
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Fine-tuning needs the ML extra. Install it with:\n    pip install -e '.[ml]'"
            "\n(add '.[peft]' for LoRA)."
        ) from exc


def finetune_seq2seq(
    splits: dict[str, list[dict]],
    *,
    output_dir: str | Path,
    cfg: FinetuneConfig | None = None,
) -> dict:
    """Fine-tune an encoder-decoder on train/val splits; save checkpoint + metadata.json.

    Returns the metadata dict. Raises if the ML extra is missing or splits leak trials.
    """
    cfg = cfg or FinetuneConfig()
    assert_no_leakage(splits)  # fail fast on contaminated splits
    _require_ml()

    import torch
    from datasets import Dataset
    from transformers import (
        AutoModelForSeq2SeqLM,
        AutoTokenizer,
        DataCollatorForSeq2Seq,
        EarlyStoppingCallback,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
        set_seed,
    )

    set_seed(cfg.seed)
    device = resolve_device()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(cfg.base_model)
    model = AutoModelForSeq2SeqLM.from_pretrained(cfg.base_model)

    if cfg.use_lora:
        from peft import LoraConfig, TaskType, get_peft_model

        model = get_peft_model(
            model, LoraConfig(task_type=TaskType.SEQ_2_SEQ_LM, inference_mode=False)
        )

    def _prep(rows: list[dict]) -> Dataset:
        pairs = to_training_pairs(rows)
        ds = Dataset.from_list(pairs)

        def tok(batch):
            model_inputs = tokenizer(
                batch["input_text"], max_length=cfg.max_input_len, truncation=True
            )
            labels = tokenizer(
                text_target=batch["target_text"], max_length=cfg.max_target_len, truncation=True
            )
            model_inputs["labels"] = labels["input_ids"]
            return model_inputs

        return ds.map(tok, batched=True, remove_columns=ds.column_names)

    train_ds = _prep(splits["train"])
    eval_ds = _prep(splits.get("val") or splits.get("test") or [])

    args = Seq2SeqTrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=cfg.epochs,
        learning_rate=cfg.learning_rate,
        per_device_train_batch_size=cfg.batch_size,
        per_device_eval_batch_size=cfg.batch_size,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        predict_with_generate=True,
        fp16=(device == "cuda"),
        seed=cfg.seed,
        report_to=[],
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        # transformers>=5 renamed the Trainer's `tokenizer` arg to `processing_class`.
        processing_class=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
        callbacks=[EarlyStoppingCallback(early_stopping_patience=cfg.early_stopping_patience)],
    )

    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    from pls_ct.evaluation.benchmark import software_versions

    metadata = {
        "base_model": cfg.base_model,
        "config": asdict(cfg),
        "device": device,
        "versions": software_versions(),
        "torch": torch.__version__,
        "n_train": len(train_ds),
        "n_eval": len(eval_ds),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata

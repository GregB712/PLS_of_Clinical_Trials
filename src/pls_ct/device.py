"""CPU-first, GPU-automatic device selection.

Per the project constraint: everything must run on CPU, and use a GPU automatically
when one is present. ``torch`` is an optional dependency, so this module must import
and resolve to ``"cpu"`` even when torch is not installed.
"""

from __future__ import annotations

import os

_VALID = {"cpu", "cuda", "mps"}


def resolve_device(override: str | None = None) -> str:
    """Return the device string to use.

    Resolution order: explicit ``override`` arg → ``PLS_DEVICE`` env → CUDA → MPS → CPU.
    An override of ``"auto"`` (or ``None``) means auto-detect. Any explicit valid value
    is honored as-is (so a user can force CPU even with a GPU present).
    """
    choice = (override or os.environ.get("PLS_DEVICE") or "auto").lower()
    if choice in _VALID:
        return choice
    # "auto" (or anything unrecognized) → detect.
    return _detect()


def _detect() -> str:
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def n_gpu_layers_for(device: str) -> int:
    """How many layers to offload for a GGUF/llama.cpp model given the device.

    ``-1`` offloads all layers to the GPU; ``0`` keeps everything on CPU.
    """
    return -1 if device in {"cuda", "mps"} else 0

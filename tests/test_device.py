"""Tests for CPU-first / GPU-automatic device resolution (no torch required)."""

import pls_ct.device as device


def test_explicit_override_honored():
    assert device.resolve_device("cpu") == "cpu"
    assert device.resolve_device("cuda") == "cuda"
    assert device.resolve_device("mps") == "mps"


def test_env_override_honored(monkeypatch):
    monkeypatch.setenv("PLS_DEVICE", "cpu")
    assert device.resolve_device() == "cpu"


def test_auto_without_torch_is_cpu(monkeypatch):
    monkeypatch.delenv("PLS_DEVICE", raising=False)

    # Simulate torch missing by making the import inside _detect fail.
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "torch":
            raise ImportError("no torch")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert device.resolve_device("auto") == "cpu"


def test_n_gpu_layers_mapping():
    assert device.n_gpu_layers_for("cuda") == -1
    assert device.n_gpu_layers_for("mps") == -1
    assert device.n_gpu_layers_for("cpu") == 0

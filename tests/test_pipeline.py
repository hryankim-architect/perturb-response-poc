"""End-to-end pipeline + audit-chain smoke tests."""

from __future__ import annotations

import json
from pathlib import Path

from perturbresp import audit, pipeline


def test_pipeline_runs_and_scores(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AUDIT_HOST", raising=False)
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)

    result = pipeline.run_pipeline("smoke", tmp_path / "artifacts", n_perturbations=30, seed=0)
    m = result["metrics"]
    assert m["program_recovery_f1"] > 0.8
    assert m["feature_signal_lift"] > 0.2

    payload = json.loads(Path(result["artifact_path"]).read_text())
    assert "effect_recovery" in payload and "heldout_prediction" in payload


def test_audit_chain_valid_after_pipeline(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AUDIT_HOST", raising=False)
    pipeline.run_pipeline("smoke", tmp_path / "artifacts", n_perturbations=20, seed=0)
    ok, n, first_bad = audit.verify()
    assert ok, f"audit chain invalid at {first_bad}"
    assert n >= 2

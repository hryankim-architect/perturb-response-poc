"""Held-out perturbation response-prediction invariants."""

from __future__ import annotations

from perturbresp import predict, synth


def test_model_beats_mean_baseline_on_heldout() -> None:
    s = synth.generate(n_perturbations=40, seed=0)
    res = predict.heldout_prediction(s, n_splits=5, seed=0)
    # the feature->response model generalizes to unseen perturbations and
    # clearly beats predicting the average training response
    assert res["model_mean_corr"] > 0.4, res
    assert res["feature_signal_lift"] > 0.2, res


def test_prediction_is_deterministic() -> None:
    s = synth.generate(n_perturbations=24, seed=2)
    a = predict.heldout_prediction(s, n_splits=4, seed=1)
    b = predict.heldout_prediction(s, n_splits=4, seed=1)
    assert a["model_mean_corr"] == b["model_mean_corr"]

"""Held-out perturbation response prediction.

The harder, more useful task: can we predict the transcriptional response of a
perturbation the model has *never seen*? We learn a linear map from a
perturbation's feature embedding to its observed mean response delta (ridge
regression), train it on a subset of perturbations, and predict the response of
held-out perturbations. Success is measured by the correlation between predicted
and observed held-out response vectors.

A "mean baseline" (predict every held-out perturbation as the average training
response) is reported alongside, so the feature→response signal is shown to
matter rather than asserted.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold

from perturbresp import effect
from perturbresp.synth import PerturbScreen


def _row_correlation(a: np.ndarray, b: np.ndarray) -> float:
    if a.std() < 1e-12 or b.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def heldout_prediction(
    screen: PerturbScreen, *, n_splits: int = 5, seed: int = 0, alpha: float = 1.0
) -> dict:
    """Leave-out-perturbation CV of feature->response prediction.

    Returns mean per-perturbation correlation for the ridge model and a
    mean-response baseline, plus their difference (the feature-signal lift).
    """
    obs = effect.observed_delta(screen)          # n_pert x genes (targets)
    feats = screen.features                       # n_pert x n_features (inputs)
    n = obs.shape[0]

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    model_cors: list[float] = []
    baseline_cors: list[float] = []
    for tr, te in kf.split(np.arange(n)):
        ridge = Ridge(alpha=alpha)
        ridge.fit(feats[tr], obs[tr])
        pred = ridge.predict(feats[te])
        mean_resp = obs[tr].mean(axis=0)
        for j, ti in enumerate(te):
            model_cors.append(_row_correlation(pred[j], obs[ti]))
            baseline_cors.append(_row_correlation(mean_resp, obs[ti]))

    model_mean = float(np.mean(model_cors))
    base_mean = float(np.mean(baseline_cors))
    return {
        "model_mean_corr": model_mean,
        "mean_baseline_corr": base_mean,
        "feature_signal_lift": model_mean - base_mean,
        "n_perturbations": n,
    }

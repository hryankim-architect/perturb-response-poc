"""Regression guard for the interpretability headline.

`scripts/interpret_perturb.py` reports the importance-recovery Spearman as an
across-seed *distribution* (not a single cherry-picked seed), because the true
per-feature importances are near-flat and the rank correlation swings with the
seed. These tests pin that headline so it cannot silently drift, and document why
seed 0 alone would be misleading.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge

from perturbresp import effect, synth

N_PERTURBATIONS = 40
ALPHA = 1.0  # matches interpret_perturb.py / predict.heldout_prediction


def _per_feature_importance(feats: np.ndarray, target: np.ndarray) -> np.ndarray:
    ridge = Ridge(alpha=ALPHA)
    ridge.fit(feats, target)
    return np.abs(np.atleast_2d(ridge.coef_)).sum(axis=0)


def _recovery_spearman(seed: int) -> float:
    sc = synth.generate(n_perturbations=N_PERTURBATIONS, seed=seed)
    return float(spearmanr(
        _per_feature_importance(sc.features, effect.observed_delta(sc)),
        _per_feature_importance(sc.features, sc.true_delta),
    )[0])


def test_importance_recovery_distribution_is_stable() -> None:
    rhos = [_recovery_spearman(s) for s in range(10)]
    mean = sum(rhos) / len(rhos)
    assert 0.88 <= mean <= 0.96, mean        # pins the reported ~0.93 headline
    assert min(rhos) >= 0.80                  # no seed collapses
    assert 0.97 <= max(rhos) <= 1.0           # seed 0 (~0.976) is the top of the range


def test_seed0_is_the_top_not_the_mean() -> None:
    # Documents why the repo reports the distribution: seed 0 is the maximum, well
    # above the across-seed mean — quoting it alone would be a cherry-pick.
    rhos = [_recovery_spearman(s) for s in range(10)]
    assert round(_recovery_spearman(0), 3) == 0.976
    assert _recovery_spearman(0) >= max(rhos) - 1e-9


def test_true_importances_are_near_flat() -> None:
    # The reason the ranking is a weak test: the ground-truth importances are
    # barely separated (max/min ~1.2 over 8 features).
    sc = synth.generate(n_perturbations=N_PERTURBATIONS, seed=0)
    imp_true = _per_feature_importance(sc.features, sc.true_delta)
    assert len(imp_true) == 8
    assert 1.1 <= float(imp_true.max() / imp_true.min()) <= 1.4

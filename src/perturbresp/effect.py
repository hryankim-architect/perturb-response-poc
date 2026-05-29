"""Perturbation effect recovery: differential expression vs control.

For each perturbation, the observed response is the mean expression difference
between its cells and the control cells. We recover the perturbation's response
*program* (its set of strongly-shifted genes) by thresholding that observed
delta, and score recovery against the synthetic ground-truth program. We also
rank perturbations by overall effect size (the L2 norm of the observed delta).
"""

from __future__ import annotations

import numpy as np

from perturbresp.synth import PerturbScreen


def observed_delta(screen: PerturbScreen) -> np.ndarray:
    """Mean expression shift vs control, per perturbation (n_perturbations x genes)."""
    ctrl_mean = screen.expr[screen.perturbation == "control"].mean(axis=0)
    out = np.zeros((len(screen.pert_ids), screen.expr.shape[1]))
    for i, pid in enumerate(screen.pert_ids):
        out[i] = screen.expr[screen.perturbation == pid].mean(axis=0) - ctrl_mean
    return out


def recovered_program(delta_row: np.ndarray, *, top_k: int) -> set[int]:
    """Top-k strongest-shifted gene indices for one perturbation."""
    return set(np.argsort(-np.abs(delta_row))[:top_k].tolist())


def program_recovery_f1(screen: PerturbScreen, obs: np.ndarray) -> float:
    """Mean F1 between recovered and ground-truth response programs across perturbations."""
    f1s = []
    for i in range(len(screen.pert_ids)):
        true_idx = set(np.flatnonzero(screen.true_delta[i]).tolist())
        if not true_idx:
            continue
        pred_idx = recovered_program(obs[i], top_k=len(true_idx))
        tp = len(true_idx & pred_idx)
        prec = tp / len(pred_idx) if pred_idx else 0.0
        rec = tp / len(true_idx)
        f1s.append(0.0 if (prec + rec) == 0 else 2 * prec * rec / (prec + rec))
    return float(np.mean(f1s)) if f1s else 0.0


def effect_size_ranking(obs: np.ndarray) -> np.ndarray:
    """Per-perturbation effect size = L2 norm of the observed delta."""
    return np.linalg.norm(obs, axis=1)


def effect_ranking_spearman(screen: PerturbScreen, obs: np.ndarray) -> float:
    """Spearman correlation between observed and ground-truth effect-size rankings."""
    from scipy.stats import spearmanr

    true_eff = np.linalg.norm(screen.true_delta, axis=1)
    obs_eff = effect_size_ranking(obs)
    rho, _ = spearmanr(true_eff, obs_eff)
    return float(rho)

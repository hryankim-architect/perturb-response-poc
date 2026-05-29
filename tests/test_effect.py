"""Perturbation effect-recovery invariants."""

from __future__ import annotations

from perturbresp import effect, synth


def test_observed_delta_shape() -> None:
    s = synth.generate(n_perturbations=10, n_genes=120, seed=1)
    obs = effect.observed_delta(s)
    assert obs.shape == (10, 120)


def test_program_recovery_is_high() -> None:
    s = synth.generate(n_perturbations=40, seed=0)
    obs = effect.observed_delta(s)
    f1 = effect.program_recovery_f1(s, obs)
    assert f1 > 0.8, f1


def test_effect_ranking_tracks_truth() -> None:
    s = synth.generate(n_perturbations=40, seed=0)
    obs = effect.observed_delta(s)
    rho = effect.effect_ranking_spearman(s, obs)
    assert rho > 0.8, rho

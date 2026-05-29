"""Synthetic Perturb-seq generator invariants."""

from __future__ import annotations

import numpy as np

from perturbresp import synth


def test_generate_is_deterministic() -> None:
    a = synth.generate(n_perturbations=10, seed=5)
    b = synth.generate(n_perturbations=10, seed=5)
    assert np.array_equal(a.expr, b.expr)
    assert np.array_equal(a.true_delta, b.true_delta)


def test_shapes_and_control_block() -> None:
    s = synth.generate(n_perturbations=12, n_genes=100, cells_per_pert=20, n_control=200, seed=1)
    assert len(s.pert_ids) == 12
    assert s.true_delta.shape == (12, 100)
    assert (s.perturbation == "control").sum() == 200
    assert s.n_cells == 200 + 12 * 20


def test_response_programs_are_sparse() -> None:
    s = synth.generate(n_perturbations=8, n_genes=200, seed=2, program_sparsity=20)
    for i in range(len(s.pert_ids)):
        assert np.count_nonzero(s.true_delta[i]) == 20


def test_perturbed_cells_shift_from_control() -> None:
    s = synth.generate(n_perturbations=6, seed=3)
    ctrl_mean = s.expr[s.perturbation == "control"].mean(axis=0)
    p0 = s.expr[s.perturbation == s.pert_ids[0]].mean(axis=0)
    # the perturbed mean differs from control along the program genes
    prog = np.flatnonzero(s.true_delta[0])
    assert np.abs(p0[prog] - ctrl_mean[prog]).mean() > 0.1

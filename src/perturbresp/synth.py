"""Deterministic synthetic Perturb-seq generator.

Fabricates a single-cell perturbation screen with a *known* ground truth so
effect recovery and response prediction can be scored offline and reproducibly.
No real data is used.

Design
------
- A pool of **perturbations**, each with a low-dimensional **feature embedding**
  (e.g. a stand-in for target-pathway membership). Perturbations with similar
  features induce similar response programs — which is what makes generalization
  to *held-out* perturbations possible.
- Each perturbation has a **ground-truth response program**: a sparse vector of
  per-gene expression shifts (up/down) derived linearly from its features, so a
  model that learns the feature→response map can predict unseen perturbations.
- **Cells**: a block of control cells (no shift) plus, per perturbation, a block
  of perturbed cells (control baseline + the perturbation's program + noise).

Everything derives from one integer seed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class PerturbScreen:
    expr: np.ndarray              # cells x genes (log-normalized)
    perturbation: np.ndarray      # cells, perturbation id per cell ("control" or "pNNN")
    pert_ids: list[str]           # ordered perturbation ids (excludes control)
    features: np.ndarray          # n_perturbations x n_features embedding
    true_delta: np.ndarray        # n_perturbations x genes ground-truth response program
    genes: list[str]
    meta: dict = field(default_factory=dict)

    @property
    def n_cells(self) -> int:
        return self.expr.shape[0]


def generate(
    n_perturbations: int = 40,
    n_genes: int = 200,
    n_features: int = 8,
    cells_per_pert: int = 30,
    n_control: int = 300,
    *,
    seed: int = 0,
    program_sparsity: int = 20,
    noise: float = 0.5,
) -> PerturbScreen:
    """Generate a synthetic Perturb-seq screen with ground-truth response programs."""
    rng = np.random.default_rng(seed)
    genes = [f"g{j:03d}" for j in range(n_genes)]

    # perturbation feature embeddings
    features = rng.normal(0.0, 1.0, size=(n_perturbations, n_features))

    # a shared feature->gene response basis: response delta = features @ W
    # W is sparse per output gene so programs are interpretable + sparse-ish
    w = rng.normal(0.0, 1.0, size=(n_features, n_genes))
    # sparsify: keep only `program_sparsity` strongest genes per perturbation
    raw_delta = features @ w
    true_delta = np.zeros_like(raw_delta)
    for i in range(n_perturbations):
        idx = np.argsort(-np.abs(raw_delta[i]))[:program_sparsity]
        true_delta[i, idx] = raw_delta[i, idx]
    # scale to a sensible magnitude
    true_delta = true_delta / (np.abs(true_delta).max() + 1e-9) * 2.0

    pert_ids = [f"p{n:03d}" for n in range(n_perturbations)]

    # baseline control expression profile
    base = rng.normal(3.0, 0.4, size=n_genes)

    rows = []
    labels = []
    # control cells
    ctrl = base + rng.normal(0.0, noise, size=(n_control, n_genes))
    rows.append(ctrl)
    labels.extend(["control"] * n_control)
    # perturbed cells
    for i, pid in enumerate(pert_ids):
        block = base + true_delta[i] + rng.normal(0.0, noise, size=(cells_per_pert, n_genes))
        rows.append(block)
        labels.extend([pid] * cells_per_pert)

    expr = np.clip(np.vstack(rows), 0.0, None)
    perturbation = np.array(labels, dtype=object)

    return PerturbScreen(
        expr=expr, perturbation=perturbation, pert_ids=pert_ids,
        features=features, true_delta=true_delta, genes=genes,
        meta={"seed": seed, "n_perturbations": n_perturbations, "n_genes": n_genes},
    )

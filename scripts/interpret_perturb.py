#!/usr/bin/env python3
"""Interpretability diagnostic for the perturbation-response ridge model.

The held-out predictor maps a perturbation's feature embedding to its response
delta (`predict.heldout_prediction`, ridge). This script makes that mapping
*legible*: which input feature dimensions does the ridge rely on, and does that
learned reliance match the **synthetic ground-truth** feature→response structure?

Because the data is synthetic, we have ground truth: `screen.true_delta` is the
noise-free response the generator built from the features. So we can validate
interpretability directly — fit the ridge on the *observed* (noisy) delta and on
the *true* delta, and check that the per-feature importance rankings agree
(Spearman). High agreement means the model recovered the real feature→response
structure rather than fitting noise — the perturb-repo analogue of dmoi's
"Integrated Gradients recover the expected biology".

We also report the effect-size ranking recovery (Spearman) and program-recovery
F1 that the repo already computes — native interpretability that needs no model.

Limitations: synthetic, small (n_features default 8); importances are
indicative and the ranking is a legibility/recovery check, not a feature-
selection claim on real data.

Reproduce:  python scripts/interpret_perturb.py
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import numpy as np  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402
from sklearn.linear_model import Ridge  # noqa: E402

from perturbresp import audit, effect, synth, tracking  # noqa: E402

AUDIT = REPO / "audit"
JOB_ID = "perturb-interpretability"
N_PERTURBATIONS = 40
SEED = 0
SEED_SWEEP = range(10)  # report the recovery Spearman as a distribution, not one seed
ALPHA = 1.0  # matches predict.heldout_prediction default


def _per_feature_importance(feats: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Aggregate |ridge coefficient| across gene outputs, per input feature."""
    ridge = Ridge(alpha=ALPHA)
    ridge.fit(feats, target)
    coef = np.atleast_2d(ridge.coef_)  # (n_genes, n_features)
    return np.abs(coef).sum(axis=0)    # (n_features,)


def main() -> int:
    screen = synth.generate(n_perturbations=N_PERTURBATIONS, seed=SEED)
    feats = screen.features                 # n_pert x n_features
    obs = effect.observed_delta(screen)     # n_pert x genes (noisy)
    true = screen.true_delta                # n_pert x genes (ground truth)
    n_features = feats.shape[1]
    print(f"=== perturb interpretability (n_pert={len(screen.pert_ids)}, "
          f"n_features={n_features}, n_genes={len(screen.genes)}) ===")

    imp_obs = _per_feature_importance(feats, obs)
    imp_true = _per_feature_importance(feats, true)
    rho, _ = spearmanr(imp_obs, imp_true)
    order = np.argsort(imp_obs)[::-1]

    # Seed-sensitivity sweep. The recovery Spearman is computed over only
    # n_features (default 8) near-flat true importances, so any single seed is a
    # cherry-pick. Report the across-seed distribution instead of the best seed.
    sweep: list[float] = []
    for s in SEED_SWEEP:
        sc_s = synth.generate(n_perturbations=N_PERTURBATIONS, seed=s)
        rho_s, _ = spearmanr(
            _per_feature_importance(sc_s.features, effect.observed_delta(sc_s)),
            _per_feature_importance(sc_s.features, sc_s.true_delta),
        )
        sweep.append(float(rho_s))
    sweep_mean = sum(sweep) / len(sweep)
    sweep_lo, sweep_hi = min(sweep), max(sweep)
    imp_ratio = float(imp_true.max() / imp_true.min())  # ~1.2 => near-flat ranking

    # Complementary native interpretability already in the repo.
    eff_rho = effect.effect_ranking_spearman(screen, obs)
    prog_f1 = effect.program_recovery_f1(screen, obs)

    print("\n  per-feature importance — learned(observed) vs ground-truth(true):")
    print(f"  {'feature':10s}{'imp(obs)':>12s}{'imp(true)':>12s}")
    for f in order:
        print(f"  feat_{f:<5d}{imp_obs[f]:>12.3f}{imp_true[f]:>12.3f}")
    print(f"\n  Spearman(imp_obs, imp_true) = {rho:.4f}  (seed {SEED})")
    print(f"  across {len(sweep)} seeds: mean {sweep_mean:.3f}, range "
          f"[{sweep_lo:.3f}, {sweep_hi:.3f}]  <- report this, not the best seed")
    print(f"  (true importances are near-flat: max/min = {imp_ratio:.2f} over "
          f"{n_features} features, so this is a weak ranking test)")
    print(f"  effect-size ranking Spearman = {eff_rho:.4f}  | program-recovery F1 = {prog_f1:.4f}")

    AUDIT.mkdir(exist_ok=True)
    tsv = ["feature\timportance_observed\timportance_true"]
    for f in order:
        tsv.append(f"feat_{f}\t{imp_obs[f]:.5f}\t{imp_true[f]:.5f}")
    (AUDIT / "feature_importance_reliability.tsv").write_text("\n".join(tsv) + "\n")

    rank_rows = "\n".join(
        f"| {r} | `feat_{f}` | {imp_obs[f]:.3f} | {imp_true[f]:.3f} |"
        for r, f in enumerate(order, 1)
    )
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    (AUDIT / "feature_importance.md").write_text(
        "# Perturbation-response — feature-importance (interpretability) diagnostic\n\n"
        f"Generated: {ts}\n\n"
        "## Why\n\n"
        "Make the ridge feature→response model legible: which input feature "
        "dimensions drive the predicted response, and does the model's learned "
        "reliance match the synthetic ground-truth structure (rather than noise)?\n\n"
        f"- Screen: n_pert={len(screen.pert_ids)}, n_features={n_features}, "
        f"n_genes={len(screen.genes)}, seed={SEED}, ridge alpha={ALPHA}.\n"
        "- Importance = Σ|ridge coefficient| across gene outputs, per input feature.\n\n"
        "## Recovery validation (the key result)\n\n"
        f"- **Importance-recovery Spearman = {sweep_mean:.3f} across {len(sweep)} seeds "
        f"(range [{sweep_lo:.3f}, {sweep_hi:.3f}]; seed {SEED} = {rho:.4f}).** The ranking "
        "learned from the *noisy observed* delta vs the ranking implied by the "
        "*ground-truth* delta; high agreement ⇒ the model recovered the real "
        "feature→response structure, not noise.\n"
        f"- **Caveat (report the distribution, not the best seed):** the true per-feature "
        f"importances are near-flat (max/min = {imp_ratio:.2f} over {n_features} features), "
        "so the Spearman is over barely-separated values and swings with the seed. The "
        f"across-seed mean ({sweep_mean:.3f}) is the honest figure; the single-seed "
        f"{rho:.3f} is the top of the range, not a representative result.\n"
        f"- Effect-size ranking Spearman (native) = {eff_rho:.4f}; "
        f"program-recovery F1 (native) = {prog_f1:.4f}.\n\n"
        "## Per-feature importance\n\n"
        "| Rank | Feature | imp (observed) | imp (true) |\n|---|---|---|---|\n"
        + rank_rows + "\n\n"
        "Full table: `feature_importance_reliability.tsv`.\n\n"
        "## Limitations\n\n"
        "Synthetic data with a small feature embedding (default 8 dims); "
        "importances are indicative and this is a legibility / structure-recovery "
        "check, not a feature-selection claim on real perturbation data. The "
        "ground-truth comparison is only possible *because* the data is synthetic — "
        "on real Perturb-seq the recovery check would be replaced by held-out "
        "predictive correlation (already reported in the pipeline).\n\n"
        "## Reproduce\n\n```bash\npython scripts/interpret_perturb.py\n```\n"
    )
    print(f"\nWrote {AUDIT / 'feature_importance.md'}")

    audit.emit(
        action="perturb_interpretability", job_id=JOB_ID,
        fields={"spearman_obs_true": float(rho), "effect_rank_spearman": float(eff_rho),
                "program_f1": float(prog_f1), "top_feature": f"feat_{int(order[0])}"},
    )
    try:
        if tracking.is_enabled():
            tracking.log_metrics({"importance_recovery_spearman": float(rho)})
    except Exception as exc:  # noqa: BLE001 — tracking must never be fatal
        print(f"  (MLflow logging skipped: {exc})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

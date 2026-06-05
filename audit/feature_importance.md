# Perturbation-response — feature-importance (interpretability) diagnostic

Generated: 2026-06-02T20:58:11Z

## Why

Make the ridge feature→response model legible: which input feature dimensions drive the predicted response, and does the model's learned reliance match the synthetic ground-truth structure (rather than noise)?

- Screen: n_pert=40, n_features=8, n_genes=200, seed=0, ridge alpha=1.0.
- Importance = Σ|ridge coefficient| across gene outputs, per input feature.

## Recovery validation (the key result)

- **Spearman(importance_observed, importance_true) = 0.9762** — the ranking learned from the *noisy observed* delta vs the ranking implied by the *ground-truth* delta. High agreement ⇒ the model recovered the real feature→response structure, not noise.
- Effect-size ranking Spearman (native) = 0.9861; program-recovery F1 (native) = 0.9887.

## Per-feature importance

| Rank | Feature | imp (observed) | imp (true) |
|---|---|---|---|
| 1 | `feat_5` | 10.627 | 9.418 |
| 2 | `feat_0` | 9.666 | 8.448 |
| 3 | `feat_6` | 9.466 | 8.606 |
| 4 | `feat_3` | 9.117 | 8.300 |
| 5 | `feat_4` | 9.049 | 7.962 |
| 6 | `feat_1` | 8.926 | 7.894 |
| 7 | `feat_2` | 8.900 | 7.835 |
| 8 | `feat_7` | 8.609 | 7.778 |

Full table: `feature_importance_reliability.tsv`.

## Limitations

Synthetic data with a small feature embedding (default 8 dims); importances are indicative and this is a legibility / structure-recovery check, not a feature-selection claim on real perturbation data. The ground-truth comparison is only possible because the data is synthetic — on real Perturb-seq the recovery check would be replaced by held-out predictive correlation (already reported in the pipeline).

## Reproduce

```bash
python scripts/interpret_perturb.py
```

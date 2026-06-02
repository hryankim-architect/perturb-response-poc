# Architecture

One Python process, three method modules, three substrate hooks, the same
house style as the rest of the capability-portrait portfolio.

## Control flow

```
                make run / scripts/run_lab.sh
                          │
                          ▼
              perturbresp.pipeline.run_pipeline
                          │
        ┌─────────────────┼──────────────────────────────┐
        ▼                 ▼                               ▼
  audit.emit         tracking.run        synth.generate → effect.observed_delta
 (NDJSON +         (MLflow active run,    → program F1 / effect ranking
  optional POST)    no-op if unset)       → predict.heldout_prediction
                          │
                          ▼
              artifacts/<name>.json  (effect recovery + held-out prediction)
```

## Method modules

| Module | Responsibility |
|---|---|
| `synth.py` | Deterministic Perturb-seq screen: control + perturbed cells, a per-perturbation feature embedding, and a ground-truth response program derived linearly + sparsely from the features (so feature→response generalization is learnable). |
| `effect.py` | Per-perturbation mean expression shift vs control; recover the response program by thresholding (F1 vs ground truth); rank perturbations by effect-size L2 norm (Spearman vs ground truth). |
| `predict.py` | Ridge regression mapping perturbation features → response delta, evaluated by leave-out-perturbation cross-validation; reports model correlation, a mean-response baseline, and their difference. |

## Why two tasks (and why the held-out one matters)

Recovering a *seen* perturbation's program is just differential expression vs
control, easy, and a useful sanity check (F1 ≈ 0.99 here). The task that
actually tests a model is predicting the response of a perturbation it has never
seen. By deriving the synthetic response programs linearly from a perturbation
feature embedding, the screen has *learnable cross-perturbation structure*, and
the leave-out-perturbation CV measures whether a model captures it. Reporting the
mean-response baseline alongside keeps the claim honest: the feature signal is
shown to lift correlation from ~0.04 to ~0.60, not asserted.

## Substrate integration

| Channel | Module | Env var | Behaviour when unset |
|---|---|---|---|
| Audit | `audit` | `AUDIT_HOST` | local NDJSON only (source of truth) |
| MLflow | `tracking` | `MLFLOW_TRACKING_URI` | no-op |
| Canary | `canary` | `PERTURBRESP_CANARY_FIXTURE` | uses the bundled fixture |

The canary asserts the core invariant (DE recovers the ground-truth program
above a floor F1) in well under a second.

## What this architecture intentionally avoids

No deep generative model (CPA / scGen / GEARS), no GPU, no graph priors, and no
real Perturb-seq file formats. The point is a transparent, deterministic linear
baseline with measurable invariants, runnable on a laptop.

# Architecture

One Python process. Three analysis modules. Three optional substrate hooks.

## Control flow

```
make run  (or  scripts/run_lab.sh)
  |
  v
perturbresp.pipeline.run_pipeline
  |
  +-- audit.emit          writes to audit/local-demo.ndjson;
  |                       POSTs to http://$AUDIT_HOST/events if set
  |
  +-- tracking.run        opens an MLflow run; silently skips if
  |                       MLFLOW_TRACKING_URI is not set
  |
  +-- synth.generate
        |
        v
      effect.observed_delta   --> program recovery F1 + effect-size Spearman
        |
        v
      predict.heldout_prediction  --> ridge CV correlation vs mean baseline
        |
        v
      artifacts/<name>.json
```

## Method modules

| Module | Responsibility |
|---|---|
| `synth.py` | Builds a deterministic synthetic Perturb-seq screen: control cells, perturbed cells, a per-perturbation feature embedding, and ground-truth sparse response programs derived linearly from those features so that cross-perturbation generalization is learnable. |
| `effect.py` | Computes per-perturbation mean expression shift vs control. Recovers the response program by thresholding the shift (F1 vs ground truth). Ranks perturbations by effect-size L2 norm (Spearman vs ground truth). |
| `predict.py` | Fits a ridge regression from perturbation features to response delta. Evaluates with leave-out-perturbation cross-validation. Reports model correlation, a mean-response baseline, and the lift between them. |

## Why two tasks, and why the held-out one matters

Recovering a seen perturbation's program is straightforward differential expression vs control. It is a useful sanity check (F1 ≈ 0.99 here) but tells you little about generalization. The harder task is predicting the response for a perturbation the model has not seen during training. The synthetic screen is designed to make this solvable: response programs are derived linearly from the feature embedding, so cross-perturbation structure is real and learnable. Leave-out-perturbation CV measures whether a model finds it. Reporting the mean-response baseline alongside the ridge result shows the feature signal concretely (correlation lifts from ~0.04 to ~0.60 in the synthetic demo) rather than just asserting it.

## Audit ledger mechanics

Each pipeline run appends one NDJSON entry to `audit/local-demo.ndjson`. The entry's `prev_hash` field holds the SHA-256 of the previous entry's canonical JSON encoding (keys sorted, no extra whitespace). The first entry in an empty ledger uses 64 zero hex digits as a sentinel. Replaying the chain with `audit.verify()` detects any gap or modification. The local file is the source of truth; the remote POST to `AUDIT_HOST` is best-effort and pipeline-non-fatal.

## Substrate hooks at a glance

| Channel | Module | Env var | When unset |
|---|---|---|---|
| Audit log | `audit` | `AUDIT_HOST` | writes local NDJSON only |
| Experiment tracking | `tracking` | `MLFLOW_TRACKING_URI` | skipped silently |
| Invariant check | `canary` | `PERTURBRESP_CANARY_FIXTURE` | uses the bundled fixture |

The canary re-runs differential expression on the fixture data and asserts that program-recovery F1 clears a minimum threshold. It completes in well under a second and runs in CI on every push.

## Deliberate omissions

No deep generative model (CPA, scGen, GEARS), no GPU requirement, no graph priors, and no real Perturb-seq file formats (AnnData h5ad). This is a transparent, deterministic linear baseline with measurable invariants. It runs on a laptop with `make install && make run`.

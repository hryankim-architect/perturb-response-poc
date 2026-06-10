# `perturb-response-poc`

![ci](https://github.com/hryankim-architect/perturb-response-poc/actions/workflows/ci.yml/badge.svg)

> **One principle, applied here.** Pick the smallest, most interpretable representation that could carry the signal; measure it against an honest baseline; report the verdict faithfully — whether the compact choice wins, ties, or loses. *That last step is why AI safety is needed: knowing a capability is real rather than a flattering benchmark.*
>
> In this repo: **representation** a low-dim perturbation embedding → ridge map → **baseline** a mean-response baseline (nonlinear GEARS/CPA is the named next step) → **verdict** linear *suffices for now*: held-out perturbation corr 0.60 vs 0.05 (lift +0.55).

> All data is synthetic and deterministically generated. No patient data and no proprietary code or parameters are present in this repository.

**What this shows**: the perturbation-biology axis of single-cell analysis
(Perturb-seq style), (1) **effect recovery**, recovering each perturbation's
transcriptional response program (its differentially expressed genes vs control)
and ranking perturbations by effect size; and (2) **held-out perturbation
response prediction**, learning a map from a perturbation's features to its mean
expression-shift and predicting the response of perturbations *held out of
training*, scored against a mean-response baseline so the signal is shown rather
than asserted.

**Reproducibility**: `make run` produces the metrics artifact in seconds, no
network and no GPU. Everything is seeded.

**Substrate**: every run appends to a NDJSON log whose entries are linked by SHA-256. MLflow tracking is skipped when no server is set, and a canary smoke test is polled daily by the lab monitor.

**Context**: GEARS, CPA, and scGen apply methods in this class to real Perturb-seq screens. This repo implements a transparent **linear baseline** on synthetic data. See [`docs/what-is-out-of-scope.md`](docs/what-is-out-of-scope.md).

---

## The capability, in one diagram

```
 synthetic Perturb-seq screen (control + perturbed cells; per-perturbation
 ground-truth response program + perturbation feature embedding)
        │
        ├── effect.observed_delta  → per-perturbation mean shift vs control →
        │     program recovery (F1 vs ground truth) + effect-size ranking
        │
        └── predict.heldout_prediction → ridge map (perturbation features →
              response delta), leave-out-perturbation CV → correlation on
              UNSEEN perturbations vs a mean-response baseline
```

## Demo results (synthetic, seed 0; 40 perturbations, 200 genes)

| Metric | Value |
|---|---|
| Program recovery F1 (DE vs ground-truth response program) | **0.989** |
| Effect-size ranking Spearman (vs ground truth) | **0.986** |
| Held-out perturbation response correlation, **ridge model** | **0.598** |
| Held-out perturbation response correlation, mean baseline | 0.045 |
| Feature-signal lift (model − baseline) | **+0.553** |

Reading: recovering a *seen* perturbation's program from differential
expression is easy (F1 ≈ 0.99). The meaningful claim is the **held-out** task,
predicting the response of perturbations the model never trained on. There the
linear feature→response model reaches 0.60 correlation versus 0.05 for a mean
baseline, so the feature signal clearly generalizes; a 0.60 correlation is a
modest number for a hard task, not a solved problem. These describe
*this synthetic dataset*, not a real-screen benchmark.

## Quickstart

```bash
make install     # uv sync, or pip install -e ".[dev]"
make run         # -> artifacts/demo.json
make test        # pytest
make lint        # ruff
make canary      # deterministic program-recovery check
```

## Layout

```
.
├── README.md
├── LICENSE                      # MIT
├── Makefile
├── pyproject.toml               # [perturb] extra = scanpy/anndata
├── data/manifest.yaml           # public Perturb-seq datasets + methods targeted
├── src/perturbresp/
│   ├── synth.py                 # deterministic Perturb-seq screen + ground-truth programs
│   ├── effect.py                # DE vs control: program recovery F1 + effect ranking
│   ├── predict.py               # ridge feature->response, leave-out-perturbation CV
│   ├── pipeline.py              # CLI entry; audit + MLflow shape
│   └── audit.py / tracking.py / canary.py   # shared substrate
└── docs/
    ├── architecture.md
    ├── what-is-out-of-scope.md
    └── release-notes/v0.1.md
```

## Interpretability

`scripts/interpret_perturb.py` (→ `audit/feature_importance.md`) makes the ridge
feature→response model legible: per-feature importance is the aggregated
\|coefficient\| across gene outputs. Because the data is synthetic we can validate
it against ground truth — the importance ranking learned from the *noisy observed*
delta matches the ranking implied by the *true* generative delta at **Spearman
0.93 on average across 10 seeds (range 0.86–0.98; seed 0 = 0.976)**, evidence the
model recovered the real feature→response structure rather than fitting noise.
Reported as a distribution on purpose: the true per-feature importances are
near-flat (max/min ≈ 1.2 over 8 features), so the rank correlation swings with the
seed and a single value would be a cherry-pick. Alongside the native
effect-size-ranking Spearman 0.986 and program-recovery F1 0.989. Synthetic and
small (8-dim embedding), so this is a legibility / structure-recovery check, not a
feature-selection claim on real data.

## On real data

The demo is synthetic; the code is written against a real-data shape. To adapt:
load a Perturb-seq screen (control + perturbed cells, perturbation labels) and a
perturbation feature embedding (e.g. target-pathway membership or a gene
embedding; install `pip install -e ".[perturb]"` for scanpy / anndata), then
`effect.observed_delta` and `predict.heldout_prediction`. The public methods this
baselines against are catalogued in [`data/manifest.yaml`](data/manifest.yaml).

## License

MIT. See [`LICENSE`](LICENSE).

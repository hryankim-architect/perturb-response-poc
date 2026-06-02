# What is out of scope

The anti-scope-creep ledger. This repo's value is being small, complete, and
honest about what it is and is not.

## Hard boundaries

- **No proprietary material and no patient data.** The screen, perturbation
  features, and response programs are synthetic and deterministically generated.
- **A transparent linear baseline, not a deep model.** GEARS, CPA, and scGen are
  the published deep / graph-based methods for this task; this repo implements a
  ridge feature→response baseline from scratch and does not vendor them.

## Default out-of-scope items

- **Deep / generative perturbation models** (autoencoders, graph neural nets,
  latent-space arithmetic). The ridge baseline is the legible method used here.
- **Perturbation combinations / epistasis** (predicting double-perturbation
  responses from singles). Single perturbations only in v0.1.
- **Real Perturb-seq file formats** (AnnData h5ad) and the `[perturb]` stack
  (scanpy / anndata), documented as the real-data path, not exercised in the
  synthetic demo.
- **Guide / MOI / knockdown-efficiency modeling.** Each perturbation is treated
  as a clean label; real screens have variable guide efficiency and multiplicity.
- **Statistical-power / benchmark claims.** The reported F1, Spearman, and
  held-out correlation describe the synthetic demo only; they are an existence
  proof that the method runs end to end, not a real-screen benchmark.

## How to add an item

Open a PR that adds the item here with a one-sentence reason and a link to the
proposing issue. The friction is intentional.

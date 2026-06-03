"""perturbresp: a Perturb-seq style perturbation-response proof of concept.

A clean-room demonstration of two core tasks in single-cell perturbation biology:

- **perturbation effect recovery** — for each perturbation, recover its
  transcriptional response program (the differentially expressed genes vs
  control) and rank perturbations by effect size;
- **held-out perturbation response prediction** — learn a map from a
  perturbation's features to its mean expression-shift, and predict the response
  of perturbations held out of training (generalization to unseen perturbations).

Everything runs on synthetic, deterministically-generated data with a known
ground truth. No patient data and no proprietary code or parameters are present.
See the README honest-scope preamble and ``docs/what-is-out-of-scope.md``.
"""

__version__ = "0.1.0"

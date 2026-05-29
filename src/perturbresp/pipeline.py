"""End-to-end pipeline: synthetic screen -> effect recovery -> held-out prediction.

House-style shape: audit_start -> tracking_start -> body -> tracking_end ->
audit_end. The body generates a synthetic Perturb-seq screen, recovers each
perturbation's response program by differential expression vs control, ranks
perturbations by effect size, and runs leave-out-perturbation prediction of the
feature->response map. Deterministic given the seed.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click

from perturbresp import audit, effect, predict, synth, tracking


def _run_id(name: str) -> str:
    return f"{name}-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"


def run_pipeline(
    run_name: str,
    out_dir: Path,
    *,
    n_perturbations: int = 40,
    seed: int = 0,
) -> dict[str, Any]:
    """Generate -> effect recovery -> held-out prediction -> artifact."""
    out_dir.mkdir(parents=True, exist_ok=True)
    job_id = _run_id(run_name)

    audit.emit(action="pipeline_start", job_id=job_id,
               fields={"n_perturbations": n_perturbations, "seed": seed})

    metrics: dict[str, float] = {}
    with tracking.run(name=job_id, experiment="perturbresp"):
        screen = synth.generate(n_perturbations=n_perturbations, seed=seed)

        obs = effect.observed_delta(screen)
        f1 = effect.program_recovery_f1(screen, obs)
        eff_rho = effect.effect_ranking_spearman(screen, obs)
        pred = predict.heldout_prediction(screen, n_splits=5, seed=seed)

        metrics["program_recovery_f1"] = f1
        metrics["effect_ranking_spearman"] = eff_rho
        metrics["heldout_model_corr"] = pred["model_mean_corr"]
        metrics["heldout_baseline_corr"] = pred["mean_baseline_corr"]
        metrics["feature_signal_lift"] = pred["feature_signal_lift"]
        tracking.log_metrics(metrics)

    artifact = {
        "run_name": run_name,
        "job_id": job_id,
        "n_cells": int(screen.n_cells),
        "n_perturbations": n_perturbations,
        "n_genes": len(screen.genes),
        "effect_recovery": {"program_f1": f1, "effect_ranking_spearman": eff_rho},
        "heldout_prediction": pred,
    }
    artifact_path = out_dir / f"{run_name}.json"
    with artifact_path.open("w", encoding="utf-8") as fh:
        json.dump(artifact, fh, indent=2, sort_keys=True)

    audit.emit(action="pipeline_end", job_id=job_id, fields={
        "artifact_path": str(artifact_path),
        "program_recovery_f1": f1,
        "heldout_model_corr": pred["model_mean_corr"],
    })
    return {"job_id": job_id, "artifact_path": str(artifact_path), "metrics": metrics}


@click.group()
def cli() -> None:
    """perturbresp perturbation-response pipeline (synthetic Perturb-seq POC)."""


@cli.command()
@click.option("--manifest", type=click.Path(path_type=Path), default=Path("data/manifest.yaml"))
@click.option("--out", type=click.Path(file_okay=False, path_type=Path), default=Path("data"))
def fetch(manifest: Path, out: Path) -> None:
    """No-op for the synthetic demo: the screen is generated, not downloaded."""
    click.echo(json.dumps(
        {"status": "synthetic-demo", "note": "Perturb-seq screen is generated deterministically; "
         "see data/manifest.yaml for the public datasets the method targets",
         "manifest": str(manifest), "out": str(out)}, indent=2))


@cli.command()
@click.option("--name", default="demo")
@click.option("--out", type=click.Path(file_okay=False, path_type=Path), default=Path("artifacts"))
@click.option("--perturbations", default=40, type=int)
@click.option("--seed", default=0, type=int)
def run(name: str, out: Path, perturbations: int, seed: int) -> None:
    """Run the end-to-end pipeline."""
    result = run_pipeline(name, out, n_perturbations=perturbations, seed=seed)
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    cli()

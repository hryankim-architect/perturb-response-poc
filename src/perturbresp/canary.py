"""Deterministic canary smoke test.

Probed daily by the ``lab_semantic_check.py`` runner. Contract:
completes in well under 30 s, deterministic, exit 0 on success / non-zero on any
deviation, no external services required.

The check generates a tiny synthetic screen and asserts the central invariant:
differential expression vs control recovers each perturbation's ground-truth
response program above a floor F1.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from perturbresp import audit, effect, synth, tracking

DEFAULT_FIXTURE = Path("tests/fixtures/canary.json")
EXPECTED_KEYS = {"name", "tier", "min_f1"}


def _load_fixture(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"canary fixture not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def check() -> dict[str, Any]:
    fixture_path = Path(os.environ.get("PERTURBRESP_CANARY_FIXTURE", str(DEFAULT_FIXTURE)))
    fixture = _load_fixture(fixture_path)
    missing = EXPECTED_KEYS - set(fixture.keys())
    if missing:
        return {"ok": False, "reason": f"fixture missing keys: {sorted(missing)}"}

    job_id = f"canary-{fixture['name']}"
    audit.emit(action="canary_start", job_id=job_id, fields={"tier": fixture["tier"]})

    screen = synth.generate(n_perturbations=12, n_genes=120, seed=3)
    obs = effect.observed_delta(screen)
    f1 = effect.program_recovery_f1(screen, obs)
    ok = f1 >= float(fixture["min_f1"])

    with tracking.run(name=job_id, experiment="canary"):
        tracking.log_metric("program_recovery_f1", f1)

    audit.emit(action="canary_end", job_id=job_id, fields={"ok": ok, "f1": f1})
    return {"ok": ok, "job_id": job_id, "program_recovery_f1": f1,
            "min_required": float(fixture["min_f1"])}


def main() -> int:
    result = check()
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())

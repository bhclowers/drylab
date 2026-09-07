"""Validate drylab.gc against GasChromatographySimulator.jl as oracle.

The oracle is the Julia package itself (MIT; Leppert, JOSS 5(55), 2391),
driven by ``dump_golden_gc.jl`` at tight solver tolerances (Vern9,
abstol 1e-10, reltol 1e-8) over 162 isothermal cases — 3 columns x
3 carrier gases x 3 temperatures x 3 pressure pairs (including a vacuum
outlet) x 2 stationary phases, 8 solutes each — writing ``golden_gc.json``.
A pre-generated dump ships with the repo so this script needs no Julia
runtime; regenerate with::

    julia dump_golden_gc.jl        # needs GasChromatographySimulator.jl

Tolerances are MEASURED, not aspirational (session 2026-08-05):

* hold-up time tM: bit-identical to the oracle's closed form -> 1e-14;
* peak width tau_R: <= 1.0e-15 observed -> 1e-12. The oracle's
  ``dtau2/dz`` integrand is polynomial in z, which any Runge-Kutta method
  integrates exactly, so both sides are exact here;
* retention time tR: <= 6.7e-9 observed -> 1e-8. This residual is the
  ORACLE'S solver error on the square-root integrand ``dt/dz`` at
  reltol 1e-8; the Python side is closed-form (exact).

The Python solutes come from the VENDORED table in ``drylab.gc``, not
from the oracle's CSV, so a transcription error in the vendored parameters
would fail here — the comparison validates the data as well as the physics.

Exit status 0 if everything agrees, 1 otherwise with each failure named.

Usage:  python compare_gc.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drylab.gc import (
    GCColumn,
    GCConditions,
    holdup_time,
    simulate_solute,
    solutes_for_phase,
)

TOL_TM = 1e-14
TOL_TR = 1e-8
TOL_TAU = 1e-12

failures: list[str] = []
values = 0


def check(label: str, got: float, expected: float, tol: float) -> None:
    global values
    values += 1
    if not math.isfinite(got):
        failures.append(f"{label}: non-finite value {got!r}")
        return
    rel = abs(got - expected) / abs(expected)
    if rel > tol:
        failures.append(f"{label}: got {got!r}, expected {expected!r} "
                        f"(rel {rel:.3e} > tol {tol})")


def main() -> int:
    golden_path = Path(__file__).resolve().parent / "golden_gc.json"
    cases = json.loads(golden_path.read_text())

    for case in cases:
        cid = case["id"]
        column = GCColumn(length=case["L"], diameter=case["d"],
                          film_thickness=case["df"], gas=case["gas"])
        conditions = GCConditions(temperature_k=case["T"] + 273.15,
                                  inlet_pressure=case["pin"],
                                  outlet_pressure=case["pout"])
        check(f"case {cid} tM", holdup_time(column, conditions),
              case["tM"], TOL_TM)

        by_name = {s.name: s for s in solutes_for_phase(case["phase"])}
        for peak in case["peaks"]:
            solute = by_name[peak["name"]]
            got = simulate_solute(solute, column, conditions)
            check(f"case {cid} {peak['name']} tR",
                  got.retention_time, peak["tR"], TOL_TR)
            check(f"case {cid} {peak['name']} tauR",
                  got.peak_width, peak["tauR"], TOL_TAU)

    print(f"compared {values} values across {len(cases)} oracle cases")
    if failures:
        for f in failures:
            print(f"FAIL {f}")
        print(f"{len(failures)} failures")
        return 1
    print("all values within tolerance")
    return 0


if __name__ == "__main__":
    sys.exit(main())

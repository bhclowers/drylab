"""Validate temperature-programmed GC against GasChromatographySimulator.jl.

Compares ``drylab.gc_program`` against ``golden_gc_program.json``: 64
cases x 8 solutes x (tR, tauR) = 1,024 values, half of them vacuum-outlet
(pout = 0), which is the regime where the isothermal closed forms' benign
singularity does not cancel.

On the tolerances
-----------------
Unlike compare_gc.py, BOTH sides here are numerical: the Python port
marches an ODE and so does the oracle. The achievable agreement is
therefore floored by the oracle's own discretisation error, measured at
~8.0e-10 by validation/oracle_convergence_gc.py. Asserting anything
tighter would be asserting agreement with the reference's noise.

The thresholds below are set from measurement with margin, NOT from the
1e-8/1e-12 used by the isothermal suite, which do not transfer to a
marched path.

Also checked, and arguably the stronger test: with a FLAT program the
marched path must reproduce ``gc.simulate_solute``'s closed forms, which
are validated against the same oracle independently. That check needs no
golden file and agrees to machine precision.

Usage:  python compare_gc_program.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drylab.gc import (  # noqa: E402
    GCColumn,
    GCConditions,
    simulate_solute,
    solutes_for_phase,
)
from drylab.gc_program import (  # noqa: E402
    GCProgram,
    simulate_solute_program,
)

# Oracle floor is ~8.0e-10; these carry roughly an order of magnitude of
# margin over the measured worst case at the shipped default tolerances.
TOL = {"tR": 1.0e-9, "tauR": 1.0e-8}
# The flat-program identity is exact arithmetic, so it is held to
# floating-point noise rather than to a solver tolerance.
TOL_CLOSED_FORM = 1.0e-13


def check_flat_program_identity() -> tuple[float, float]:
    """A flat program must reproduce the isothermal closed forms."""
    col = GCColumn(30.0, 0.25e-3, 0.25e-6, "He")
    worst_t = worst_w = 0.0
    for t_c in (80.0, 120.0, 160.0):
        for pin, pout in ((250e3, 101300.0), (150e3, 101300.0), (200e3, 0.0)):
            cond = GCConditions(temperature_k=t_c + 273.15,
                                inlet_pressure=pin, outlet_pressure=pout)
            prog = GCProgram.from_celsius([0.0, 1.0e6], [t_c, t_c])
            for s in solutes_for_phase("SLB5ms"):
                cf = simulate_solute(s, col, cond)
                mp = simulate_solute_program(s, col, prog, pin, pout)
                worst_t = max(worst_t, abs(mp.retention_time - cf.retention_time)
                              / cf.retention_time)
                worst_w = max(worst_w, abs(mp.peak_width - cf.peak_width)
                              / cf.peak_width)
    return worst_t, worst_w


def main() -> int:
    golden = Path(__file__).resolve().parent / "golden_gc_program.json"
    if not golden.exists():
        raise SystemExit(
            f"missing {golden.name}; regenerate with\n"
            f"  julia dump_golden_gc.jl <path-to-upstream-clone>")
    cases = json.loads(golden.read_text())

    ft, fw = check_flat_program_identity()
    print(f"Flat-program identity vs the isothermal closed forms: "
          f"tR {ft:.3e}, tauR {fw:.3e}")
    if max(ft, fw) > TOL_CLOSED_FORM:
        print(f"FAIL: a flat program must reproduce the closed forms to "
              f"{TOL_CLOSED_FORM:.0e}; the marched path and the validated "
              f"isothermal path have diverged.")
        return 1

    worst = {q: (0.0, "") for q in TOL}
    n = 0
    for c in cases:
        col = GCColumn(c["L"], c["d"], c["df"], c["gas"])
        prog = GCProgram.from_celsius(c["time_steps"], c["temp_steps"])
        by_name = {s.name: s for s in solutes_for_phase(c["phase"])}
        for pk in c["peaks"]:
            solute = by_name.get(pk["name"])
            if solute is None:
                print(f"FAIL: case {c['id']} references solute {pk['name']!r}, "
                      f"absent from the vendored table for {c['phase']}")
                return 1
            got = simulate_solute_program(solute, col, prog,
                                          c["pin"], c["pout"])
            for q, mine, ref in (("tR", got.retention_time, pk["tR"]),
                                 ("tauR", got.peak_width, pk["tauR"])):
                rel = abs(mine - ref) / max(abs(ref), 1e-30)
                n += 1
                if rel > worst[q][0]:
                    worst[q] = (rel, f"case {c['id']} ({c['program']}, "
                                     f"{c['gas']}, pout={c['pout']:.0f}) "
                                     f"{pk['name']}")

    print(f"\nCompared {n} values across {len(cases)} programmed oracle cases "
          f"({sum(1 for c in cases if c['pout'] == 0.0)} vacuum-outlet).")
    failed = False
    for q in ("tR", "tauR"):
        mark = "" if worst[q][0] <= TOL[q] else "   <-- EXCEEDS TOLERANCE"
        print(f"  {q:>5}  worst {worst[q][0]:.3e}  (tol {TOL[q]:.0e}){mark}")
        print(f"         at {worst[q][1]}")
        failed |= worst[q][0] > TOL[q]

    if failed:
        print("\nFAIL: programmed GC disagrees with the Julia oracle beyond "
              "the measured tolerances.")
        return 1
    print("\nPASS: programmed GC agrees with the Julia oracle within "
          "tolerances set by the oracle's own convergence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

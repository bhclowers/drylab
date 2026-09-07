"""Measure the GC oracle's OWN convergence for temperature-programmed cases.

Why this exists
---------------
For the isothermal cases the reference is effectively exact: the Julia
oracle integrates an ODE, but the Python port evaluates a closed form, so
agreement at ~1e-9 is an absolute statement about the port.

Under a temperature program that is no longer true. BOTH sides are
numerical. Whatever tolerance ``compare_gc_program.py`` asserts is
therefore floored by the oracle's own discretisation error, and asserting
a tolerance tighter than that floor would be asserting agreement with the
oracle's noise.

This script measures the floor, by re-dumping the same 64 cases at three
solver tolerances and comparing them against the tightest:

    loose  abstol 1e-10 / reltol 1e-8    golden_gc_program_loose.json
    mid    abstol 1e-12 / reltol 1e-10   golden_gc_program_mid.json
    tight  abstol 1e-14 / reltol 1e-12   golden_gc_program.json  <- SHIPPED

The tightest dump is the one that ships. That was not the original choice:
the first run shipped the loose dump, and this measurement showed it
carried ~1e-7 relative error where the tight dump costs no more to
generate and carries ~1e-9. The coarser dumps still ship as the EVIDENCE
for that claim — without them the shipped golden's error is an assertion
rather than a measurement.

Successive-refinement argument: if mid-vs-tight is far smaller than
loose-vs-tight, the sequence is converging and the shipped (tight) dump's
own error is bounded by roughly mid-vs-tight. If the two are comparable,
nothing is converged and no conclusion can be drawn — the script says so
rather than reporting a number that looks authoritative.

Usage:  python oracle_convergence_gc.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUANTITIES = ("tR", "tauR")


def load(path: Path) -> dict:
    with path.open() as fh:
        return {c["id"]: c for c in json.load(fh)}


def compare(a: dict, b: dict) -> dict[str, tuple[float, str]]:
    """Worst relative difference per quantity, with where it occurred."""
    worst = {q: (0.0, "") for q in QUANTITIES}
    for cid, ca in a.items():
        cb = b[cid]
        for pa, pb in zip(ca["peaks"], cb["peaks"]):
            if pa["name"] != pb["name"]:
                raise SystemExit(f"case {cid}: peak order differs between dumps")
            for q in QUANTITIES:
                denom = max(abs(pb[q]), 1e-30)
                rel = abs(pa[q] - pb[q]) / denom
                if rel > worst[q][0]:
                    worst[q] = (rel, f"case {cid} ({cb['program']}, {cb['gas']}, "
                                     f"pout={cb['pout']:.0f}) {pa['name']}")
    return worst


def main() -> int:
    mid_path = HERE / "golden_gc_program_mid.json"
    ref_path = HERE / "golden_gc_program.json"      # tightest == shipped
    shipped = HERE / "golden_gc_program_loose.json"
    for p in (mid_path, ref_path, shipped):
        if not p.exists():
            raise SystemExit(
                f"missing {p.name}; regenerate with\n"
                f"  julia dump_golden_gc.jl <clone> --prog-only "
                f"<abstol> <reltol> <outfile>")

    ref, mid, dflt = load(ref_path), load(mid_path), load(shipped)
    # The study runs on a SUBSET of the shipped grid: the coarse dumps are
    # expensive and the floor is a property of the solver, not of how many
    # cases it is asked to do. Compare on the shared ids rather than
    # demanding identical key sets, so extending the grid does not silently
    # break the study (it did once, on the 432 -> 720 extension).
    common = sorted(set(ref) & set(mid) & set(dflt))
    if not common:
        raise SystemExit(
            "the three dumps share no case ids; regenerate the coarse ones "
            "over a range of the current grid, e.g.\n"
            "  julia dump_golden_gc.jl <clone> --prog-only 1e-10 1e-8 "
            "golden_gc_program_loose.json --prog-range 1 64")
    ref = {i: ref[i] for i in common}
    mid = {i: mid[i] for i in common}
    dflt = {i: dflt[i] for i in common}

    d_vs_r = compare(dflt, ref)
    m_vs_r = compare(mid, ref)

    print(f"Oracle self-convergence over {len(ref)} programmed cases "
          f"(a subset of the shipped grid), "
          f"{sum(len(c['peaks']) for c in ref.values())} peaks.\n")
    print(f"{'quantity':>8}  {'loose vs tight':>15}  {'mid vs tight':>12}  ratio")
    verdict_ok = True
    for q in QUANTITIES:
        dr, mr = d_vs_r[q][0], m_vs_r[q][0]
        ratio = dr / mr if mr > 0 else float("inf")
        print(f"{q:>8}  {dr:15.3e}  {mr:12.3e}  {ratio:7.1f}x")
        # The reference is only usable as truth if tightening from mid to ref
        # changed things far less than the default already differs.
        if not (mr * 10.0 < dr or dr == 0.0):
            verdict_ok = False

    print()
    for q in QUANTITIES:
        print(f"  worst {q} (loose vs tight): {d_vs_r[q][0]:.3e} at {d_vs_r[q][1]}")

    print()
    if not verdict_ok:
        print("INCONCLUSIVE: mid-vs-tight is not clearly smaller than "
              "loose-vs-tight, so the sequence is not converged. Do NOT set "
              "compare tolerances from these numbers; re-dump tighter first.")
        return 1

    floor = max(m_vs_r[q][0] for q in QUANTITIES)
    print(f"CONVERGED: the shipped (tight) dump's own relative error is "
          f"bounded by about {floor:.1e}.")
    print(f"compare_gc_program.py must not assert agreement tighter than "
          f"this; the port cannot be shown to beat its own reference.")
    print(f"For scale, the loose dump originally shipped carried "
          f"{max(d_vs_r[q][0] for q in QUANTITIES):.1e}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Validate drylab's CZE core against SPYCE.

Reproduces SPYCE's own shipped CZE case — pyridine and aniline as analytes
in an acetic acid / Tris background, 30 mm capillary, 2 uA, 75 s — in
drylab.ce and compares the resulting field against the oracle dump.

On the tolerances
-----------------
Both sides are numerical, as with the programmed-GC suite, so the
achievable agreement is floored by the solvers' own error. SPYCE's RKF45
tolerance defaults to 1e-3, and the two implementations use different
adaptive step sequences and different endpoint handling, so this suite
compares PHYSICAL OBSERVABLES with tolerances set by measurement, NOT the
raw field point by point:

  - hold: peak position of each analyte at the final time
  - hold: integrated mass of each analyte (conservation)
  - hold: pH of the background electrolyte

A point-by-point field comparison at 1e-8, as used by the closed-form
suites, would be meaningless here and would fail for reasons that have
nothing to do with correctness.

Requires the oracle dump. Regenerate with:
    python SPYCE.py sampleInput/CZE_SPYCE.txt      (in a SPYCE checkout)
and copy the .npz to validation/golden_ce.npz.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drylab.ce import (  # noqa: E402
    CEConditions,
    CESpecies,
    grid_positions,
    simulate_cze,
)

# SPYCE's shipped CZE case, transcribed from sampleInput/CZE_SPYCE.txt.
# Concentrations there are mol/L and are scaled by 1000 to mol/m^3.
SPECIES = [
    CESpecies("Pyridine", (1,), (30.0e-9,), (5.16,)),
    CESpecies("Acetic-Acid", (-1,), (-42.4e-9,), (4.756,)),
    CESpecies("Aniline", (1,), (32.5e-9,), (4.80,)),
    CESpecies("Tris", (1,), (29.5e-9,), (8.076,)),
]
CONC_MOL_PER_L = [0.001, 0.02, 0.001, 0.012]
ANALYTE = [True, False, True, False]

# Position tolerance in mm, and mass-conservation tolerance (relative).
TOL_POSITION_MM = 1.0
TOL_MASS = 0.05
TOL_PH = 0.15


def build_initial(x: np.ndarray, length: float) -> np.ndarray:
    """SPYCE's initial condition: Gaussian plugs at 0.2 L on a flat BGE."""
    plug = np.exp(-((x - 0.2 * length) ** 2) / (0.025 * length) ** 2)
    c = np.zeros((len(SPECIES), x.size))
    for i, (conc, is_analyte) in enumerate(zip(CONC_MOL_PER_L, ANALYTE)):
        c[i] = conc * 1000.0 * (plug if is_analyte else np.ones_like(x))
    c[c < 1.0e-9] = 0.0
    return c


def peak_position_mm(profile: np.ndarray, position_mm: np.ndarray) -> float:
    """Centroid, not argmax: robust to a flat top or a coarse grid."""
    w = np.maximum(profile, 0.0)
    if w.sum() <= 0:
        return float("nan")
    return float((w * position_mm).sum() / w.sum())


def check_boundary_elution() -> tuple[bool, str]:
    """A zone reaching the end of the capillary must LEAVE, not blow up.

    Regression guard for a defect that produced a peak reappearing at the
    opposite end with the integrated mass up 16-fold. It needed BOTH
    Trefethen's endpoint derivative formulae and the Hou-Li spectral
    filter; fixing only the first left the blow-up in place, so a test
    that exercises the boundary is the only way to keep both.
    """
    species = [
        CESpecies("chloride", (-1,), (-79.1e-9,), (-2.0,)),
        CESpecies("Tris", (1,), (29.5e-9,), (8.076,)),
        CESpecies("HEPES", (-1,), (-21.8e-9,), (7.5,)),
        CESpecies("fast analyte", (-1,), (-40.0e-9,), (3.5,)),
    ]
    cond = CEConditions(n_points=129, t_final_s=90.0, voltage_v=None,
                        current_a=13.0e-6, save_every=10)
    x = grid_positions(cond)
    c = np.zeros((4, cond.n_points))
    c[0], c[1], c[2] = 50.0, 100.0, 50.0
    c[3] = 2.0 * np.exp(-((x - 0.026) / 0.0008) ** 2)
    run = simulate_cze(species, c, cond)
    mass = np.array([abs(np.trapezoid(run.concentrations[3, :, k],
                                      run.position_mm))
                     for k in range(run.times_s.size)])
    peak = mass.max()
    # Mass must never EXCEED its initial value (nothing is created), and
    # must end far below it (the zone has eluted).
    grew = peak > mass[0] * 1.05
    eluted = mass[-1] < mass[0] * 0.1
    if grew:
        return False, (f"mass grew to {peak:.3f} from {mass[0]:.3f} — the "
                       f"boundary blow-up has returned")
    if not eluted:
        return False, (f"zone did not elute: mass ended at {mass[-1]:.3f} "
                       f"of {mass[0]:.3f}")
    return True, (f"mass {mass[0]:.3f} -> {mass[-1]:.4f}, no growth "
                  f"(peak {peak:.3f})")


def check_eof_is_a_galilean_shift() -> tuple[bool, str]:
    """Switching EOF on must translate a zone by exactly v_eof * t.

    EOF is beyond the oracle: SPYCE models transport explicitly without
    bulk flow, so it cannot check this. The invariant does instead. EOF is
    PLUG flow, identical for every species, so its only effect is a uniform
    translation of the whole pattern — if it changed peak SHAPE or relative
    spacing, it would be entering the equations in the wrong place.
    """
    species = [
        CESpecies("acetate", (-1,), (-42.4e-9,), (4.756,)),
        CESpecies("Tris", (1,), (29.5e-9,), (8.076,)),
        CESpecies("marker", (1,), (40.1e-9,), (14.0,)),
    ]
    eof = 30.0e-9
    t_final = 10.0
    out = {}
    for tag, mu_eof in (("off", 0.0), ("on", eof)):
        cond = CEConditions(length_m=30.0e-3, voltage_v=500.0, n_points=129,
                            t_final_s=t_final, eof_mobility=mu_eof,
                            save_every=5)
        x = grid_positions(cond)
        c = np.zeros((3, cond.n_points))
        c[0], c[1] = 20.0, 12.0
        c[2] = 1.0 * np.exp(-((x - 0.010) / 0.0008) ** 2)
        run = simulate_cze(species, c, cond)
        out[tag] = (peak_position_mm(run.concentrations[2, :, -1],
                                     run.position_mm),
                    cond.field_v_per_m)
    shift = out["on"][0] - out["off"][0]
    predicted = eof * out["off"][1] * t_final * 1000.0
    rel = abs(shift - predicted) / predicted
    # 1% allows for the small variation of E along the capillary; a wrong
    # placement of the EOF term would be off by far more than that.
    ok = rel < 0.01
    return ok, (f"shift {shift:.4f} mm vs predicted {predicted:.4f} mm "
                f"({rel:.2e} relative)")


def check_apparent_mobility() -> tuple[bool, str]:
    """With EOF, migration time must follow mu_ep + mu_eof for BOTH signs.

    This is the defining CZE result: cations, neutrals and anions all reach
    the same detector, ordered by apparent mobility. A neutral marker
    reports mu_eof directly.
    """
    eof = 55.0e-9
    species = [
        CESpecies("acetate", (-1,), (-42.4e-9,), (4.756,)),
        CESpecies("Tris", (1,), (29.5e-9,), (8.076,)),
        CESpecies("cation", (1,), (76.2e-9,), (14.0,)),
        CESpecies("neutral", (1,), (0.0,), (14.0,)),
        CESpecies("anion", (-1,), (-25.0e-9,), (-2.0,)),
    ]
    cond = CEConditions(length_m=30.0e-3, voltage_v=500.0, n_points=129,
                        t_final_s=32.0, eof_mobility=eof, save_every=4)
    x = grid_positions(cond)
    c = np.zeros((5, cond.n_points))
    c[0], c[1] = 20.0, 12.0
    for i in (2, 3, 4):
        c[i] = 1.0 * np.exp(-((x - 0.006) / 0.0008) ** 2)
    run = simulate_cze(species, c, cond)
    _, traces = run.detector_trace(20.0)
    detector_m = 20.0e-3 - 0.006
    worst = 0.0
    order = []
    for i, mu_ep in ((2, 76.2e-9), (3, 0.0), (4, -25.0e-9)):
        if traces[i].max() <= 1e-6:
            return False, f"{species[i].name} never reached the detector"
        t_obs = float(run.times_s[int(np.argmax(traces[i]))])
        t_pred = detector_m / ((mu_ep + eof) * cond.field_v_per_m)
        worst = max(worst, abs(t_obs - t_pred) / t_pred)
        order.append((t_obs, species[i].name))
    ordered = [n for _, n in sorted(order)]
    if ordered != ["cation", "neutral", "anion"]:
        return False, f"migration order wrong: {ordered}"
    # 10%: peak MAXIMUM on a coarse saved-time grid, against an estimate
    # that ignores dispersion and the field's slight non-uniformity.
    ok = worst < 0.10
    return ok, (f"cation < neutral < anion, worst timing error {worst:.1%}")


def main() -> int:
    golden = Path(__file__).resolve().parent / "golden_ce.npz"
    if not golden.exists():
        raise SystemExit(
            f"missing {golden.name}. Generate it from a SPYCE checkout:\n"
            f"  python SPYCE.py sampleInput/CZE_SPYCE.txt\n"
            f"then copy output/*.npz here as golden_ce.npz")
    d = np.load(golden)
    t_ref = np.asarray(d["arr_0"])
    x_ref = np.asarray(d["arr_1"])[0, :, -1]
    c_ref = np.asarray(d["arr_2"])
    h_ref = np.asarray(d["arr_3"])[0, :, -1]

    # SPYCE's case is CONSTANT CURRENT (2 uA), so voltage_v must be None:
    # the mode guard in CEConditions rejects passing both, which is what
    # caught this script the first time it ran after voltage mode landed.
    cond = CEConditions(length_m=30.0e-3, voltage_v=None, current_a=2.0e-6,
                        diameter_m=50.0e-6, n_points=c_ref.shape[1],
                        t_final_s=float(t_ref[-1]), save_every=25)
    x = grid_positions(cond)
    run = simulate_cze(SPECIES, build_initial(x, cond.length_m), cond)

    print(f"SPYCE CZE case: {len(SPECIES)} species, {cond.n_points} nodes, "
          f"{cond.t_final_s:g} s")
    print(f"  oracle: {t_ref.size} saved times")
    print(f"  drylab: {run.n_steps} steps, {run.times_s.size} saved times\n")

    failed = False

    for _fn, _label in ((check_eof_is_a_galilean_shift, "EOF Galilean shift"),
                        (check_apparent_mobility, "Apparent mobility")):
        _ok, _msg = _fn()
        print(f"{_label}: {_msg}")
        if not _ok:
            print("  <-- FAILED")
        failed |= not _ok
    print()

    ok, msg = check_boundary_elution()
    print(f"Boundary elution: {msg}")
    if not ok:
        print("  <-- FAILED")
    failed |= not ok
    print()

    print("Analyte peak position at the final time (mm):")
    for i, sp in enumerate(SPECIES):
        if not ANALYTE[i]:
            continue
        p_ref = peak_position_mm(c_ref[i, :, -1], x_ref * 1000.0)
        p_got = peak_position_mm(run.concentrations[i, :, -1],
                                 run.position_mm)
        delta = abs(p_got - p_ref)
        mark = "" if delta <= TOL_POSITION_MM else "   <-- EXCEEDS"
        print(f"  {sp.name:12s} oracle {p_ref:6.2f}   drylab {p_got:6.2f}   "
              f"diff {delta:5.2f}{mark}")
        failed |= delta > TOL_POSITION_MM

    print("\nMass conservation (relative drift over the run):")
    for i, sp in enumerate(SPECIES):
        m0 = float(np.trapezoid(run.concentrations[i, :, 0], run.position_mm))
        m1 = float(np.trapezoid(run.concentrations[i, :, -1], run.position_mm))
        drift = abs(m1 - m0) / max(abs(m0), 1e-30)
        mark = "" if drift <= TOL_MASS else "   <-- EXCEEDS"
        print(f"  {sp.name:12s} {drift:.3e}{mark}")
        failed |= drift > TOL_MASS

    # SPYCE's saved hydronium array is ALREADY mol/L, whereas drylab's
    # CERun carries mol/m^3 like the rest of its transport quantities.
    # Dividing both by 1000 gave a clean 3.000 pH discrepancy, which is
    # log10(1000) and therefore a units bug in this probe, not physics:
    # Henderson-Hasselbalch for 20 mM acetic acid neutralised by 12 mM
    # Tris gives 4.756 + log10(12/8) = 4.932, which is what drylab
    # returned. Cross-check the chemistry before blaming the model.
    ph_ref = float(-np.log10(np.median(h_ref)))
    ph_got = float(-np.log10(np.median(run.hydronium[:, -1]) / 1000.0))
    d_ph = abs(ph_got - ph_ref)
    mark = "" if d_ph <= TOL_PH else "   <-- EXCEEDS"
    print(f"\nBackground pH: oracle {ph_ref:.3f}   drylab {ph_got:.3f}   "
          f"diff {d_ph:.3f}{mark}")
    failed |= d_ph > TOL_PH

    if failed:
        print("\nFAIL: drylab's CZE core disagrees with SPYCE.")
        return 1
    print("\nPASS: drylab's CZE core agrees with SPYCE on peak position, "
          "mass conservation and background pH.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

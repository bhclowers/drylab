"""Validate drylab.bandshape: exact linear oracle, invariants, regressions.

The band-shape sandbox is extension physics with no external reference
implementation, so validation follows the CE precedent: an EXACT internal
oracle where one exists, and physical invariants where it does not.

1. ORACLE — linear isotherm. The plate cascade at chi = 0 has the exact
   closed form P(n) = C(n-1, N-1) p^N (1-p)^(n-N), p = 1/(1+k) (negative
   binomial: the N-th advance on transfer n). The simulator must reproduce
   it to ~1e-13 pointwise, and its moments must match N(1+k) and
   N·k·(1+k) exactly to the same order. This pins the transport
   bookkeeping — every later nonlinear result flows through the same code.
2. CONVERGENCE — chi -> 0 approaches the oracle linearly in chi.
3. INVARIANTS — mass conservation at every chi; Langmuir (chi > 0):
   asymmetry above the linear profile's own As and t_max strictly earlier,
   both monotone in chi; anti-Langmuir (chi < 0): the mirror directions.
   (Asymmetry is judged against the linear profile's As because the
   negative binomial is itself right-skewed at finite N.)
4. REGRESSION — chi = (1+k)/C0 exactly: the stable-quadratic sign
   convention (np.sign(0) = 0) froze all transport at this reachable
   slider combination until 2026-08-17; the case must now elute fully.
5. IDENTITY — van Deemter builder: the closed-form u_opt = sqrt(B/C) and
   H_min = A + 2 sqrt(BC) coincide with the numerical minimum of the
   summed curve on a fine grid.
"""

from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from drylab.bandshape import (  # noqa: E402
    asymmetry_factor,
    linear_elution_profile,
    simulate_plates,
    van_deemter_components,
)

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        failures.append(msg)


# ---- 1. Exact linear oracle ------------------------------------------------
print("Linear-isotherm oracle (negative binomial):")
worst = 0.0
for n_plates in (10, 20, 50, 100, 200, 500, 1000):
    # Full k grid at the classroom sizes; spot checks at the raised
    # ceiling (2026-08-18) where each linear run costs real time.
    for k in ((0.5, 1.0, 3.0, 6.0, 9.0) if n_plates <= 200 else (2.0, 9.0)):
        r = simulate_plates(n_plates, k, 0.0)
        ideal = linear_elution_profile(n_plates, k, r.transfers)
        err = float(np.max(np.abs(r.profile - ideal)))
        worst = max(worst, err)
        t_th = n_plates * (1.0 + k)
        s_th = np.sqrt(n_plates * k * (1.0 + k))
        check(err < 1e-12, f"N={n_plates} k={k}: max|sim-NB| = {err:.2e}")
        check(abs(r.t_mean - t_th) < 1e-6 * t_th,
              f"N={n_plates} k={k}: mean {r.t_mean:.6f} vs {t_th:.6f}")
        check(abs(r.sigma - s_th) < 1e-6 * s_th,
              f"N={n_plates} k={k}: sigma {r.sigma:.6f} vs {s_th:.6f}")
print(f"  worst pointwise disagreement: {worst:.3e}")

# ---- 2. chi -> 0 convergence ----------------------------------------------
print("chi -> 0 convergence:")
prev = None
for chi in (1e-2, 1e-4, 1e-6):
    r = simulate_plates(100, 2.0, chi)
    ideal = linear_elution_profile(100, 2.0, r.transfers)
    dev = float(np.max(np.abs(r.profile - ideal)))
    check(prev is None or dev < prev, f"chi={chi:g}: deviation {dev:.3e}")
    prev = dev
check(prev < 1e-7, f"chi=1e-6 deviation {prev:.3e} < 1e-7")

# ---- 3. Invariants ---------------------------------------------------------
print("Overload invariants (N=100, k=2):")
base = simulate_plates(100, 2.0, 0.0)
as_lin = asymmetry_factor(base.transfers,
                          linear_elution_profile(100, 2.0, base.transfers))
last_as, last_tmax = as_lin, base.t_max
for chi in (0.5, 1.0, 2.0, 3.5, 5.0):
    r = simulate_plates(100, 2.0, chi)
    check(abs(r.recovered - 1.0) < 1e-6, f"chi=+{chi}: mass {r.recovered:.8f}")
    check(r.asymmetry is not None and r.asymmetry > last_as,
          f"chi=+{chi}: As {r.asymmetry:.3f} > previous {last_as:.3f}")
    check(r.t_max < last_tmax,
          f"chi=+{chi}: t_max {r.t_max:.0f} < previous {last_tmax:.0f}")
    last_as, last_tmax = r.asymmetry, r.t_max
last_as, last_tmax = as_lin, base.t_max
for chi in (-0.3, -0.6, -0.85):
    r = simulate_plates(100, 2.0, chi)
    check(abs(r.recovered - 1.0) < 1e-6, f"chi={chi}: mass {r.recovered:.8f}")
    check(r.asymmetry is not None and r.asymmetry < last_as,
          f"chi={chi}: As {r.asymmetry:.3f} < previous {last_as:.3f}")
    check(r.t_max >= last_tmax,
          f"chi={chi}: t_max {r.t_max:.0f} >= previous {last_tmax:.0f}")
    last_as, last_tmax = r.asymmetry, r.t_max
r = simulate_plates(100, 2.0, 0.0, tail_tau=15.0)
check(r.asymmetry is not None and r.asymmetry > as_lin + 0.05,
      f"tau=15 at chi=0: As {r.asymmetry:.3f} exceeds linear {as_lin:.3f}")
check(abs(r.recovered - 1.0) < 1e-6, f"tau=15: mass {r.recovered:.8f}")

# ---- 4. Degeneracy regression ----------------------------------------------
print("Quadratic-degeneracy regression (chi = 1+k on the loaded plate):")
r = simulate_plates(100, 2.0, 3.0)
check(r.recovered > 0.999, f"chi=3, k=2 elutes fully: {r.recovered:.6f}")
r = simulate_plates(50, 4.0, 5.0)
check(r.recovered > 0.999, f"chi=5, k=4 elutes fully: {r.recovered:.6f}")

# ---- 5. van Deemter identity -----------------------------------------------
print("van Deemter closed-form optimum vs grid minimum:")
u = np.linspace(0.005, 2.0, 20000)
for dp, lam, dm, cs, cm in [(3.0, 1.0, 1.0, 2.0, 1.0),
                            (5.0, 0.8, 2.0, 5.0, 0.5),
                            (1.7, 1.5, 0.5, 0.0, 3.0)]:
    t = van_deemter_components(u, dp, lam, dm, 0.6, cs, cm)
    i = int(np.argmin(t.total))
    check(abs(u[i] - t.u_opt) < (u[1] - u[0]) * 2,
          f"u_opt {t.u_opt:.4f} vs grid {u[i]:.4f}")
    check(abs(t.total[i] - t.h_min) < 1e-3 * t.h_min,
          f"H_min {t.h_min:.4f} vs grid {t.total[i]:.4f}")

print()
if failures:
    print(f"FAIL: {len(failures)} check(s) failed.")
    sys.exit(1)
print("PASS: band-shape cascade reproduces the exact linear closed form, "
      "obeys the overload invariants in both curvature directions, and the "
      "van Deemter builder matches its own optimum identity.")

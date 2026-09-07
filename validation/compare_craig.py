"""Validate drylab.craig against Appendix 16 of *Analytical Chemistry 2.0*.

The source supplies its own oracle: Table A16.1 (symbolic fractions for the
first four steps) and three worked examples with printed numeric answers.
This script checks all of them, plus the internal consistency of the two
independent code paths (closed-form A16.2 vs step-by-step simulation).

Exit status 0 if everything agrees, 1 otherwise with each failure named.

Usage:  python compare_craig.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drylab.craig import (
    Analyte,
    confidence_interval,
    distribution,
    fraction_lower,
    fraction_upper,
    moments,
    normal_approximation_valid,
    pooled_recovery,
    separation_factor,
    simulate,
    step_by_step,
    tube_fraction,
)

failures: list[str] = []
checks = 0


def check(label: str, got: float, expected: float, tol: float) -> None:
    global checks
    checks += 1
    if not math.isfinite(got):
        failures.append(f"{label}: non-finite value {got!r}")
        return
    if abs(got - expected) > tol:
        failures.append(f"{label}: got {got!r}, expected {expected!r} (tol {tol})")


# --- Table A16.1: symbolic fractions for steps 0-3 ---------------------------
# n=0: 1 | n=1: q, p | n=2: q^2, 2pq, p^2 | n=3: q^3, 3pq^2, 3p^2q, p^3
for D in (0.25, 0.5, 1.0, 5.0, 9.0):
    p = fraction_upper(D)
    q = 1.0 - p
    expected_rows = [
        [1.0],
        [q, p],
        [q**2, 2 * p * q, p**2],
        [q**3, 3 * p * q**2, 3 * p**2 * q, p**3],
    ]
    for n, row in enumerate(expected_rows):
        for r, want in enumerate(row):
            check(f"TableA16.1 D={D} n={n} r={r}", tube_fraction(r, n, p), want, 1e-15)

# --- A16.1 / p+q = 1 ---------------------------------------------------------
for D in (0.0, 0.5, 5.0, 9.0, 100.0):
    q = fraction_lower(D)
    check(f"A16.1 q(D={D})", q, 1.0 / (D + 1.0), 1e-15)
    check(f"p+q=1 (D={D})", fraction_upper(D) + q, 1.0, 1e-15)
# Unequal volumes: q = V_lower / (D*V_upper + V_lower)
check("A16.1 unequal volumes", fraction_lower(5.0, 2.0, 1.0), 1.0 / 11.0, 1e-15)

# --- Closed form vs step-by-step simulation ---------------------------------
for D in (0.5, 5.0, 9.0):
    p = fraction_upper(D)
    for n in (0, 1, 3, 10, 30, 60):
        a = distribution(n, p, n + 1)
        b = step_by_step(n, p, n + 1)
        check(f"A16.2 vs simulation D={D} n={n}", float(abs(a - b).max()), 0.0, 1e-12)

# --- Example A16.1: D_A=5.0, D_B=0.5, 30 steps ------------------------------
# Printed: A -> ~2e-15, ~1e-9, ~2e-5, 0.013, 0.192, 0.004 at tubes 5..30
#          B -> 0.023, 0.153, 0.025, 0, 0, 0
pA, pB = fraction_upper(5.0), fraction_upper(0.5)
check("A16.1 example p_A", pA, 0.833, 5e-4)
check("A16.1 example p_B", pB, 0.333, 5e-4)
check("A16.1 example q_A", fraction_lower(5.0), 0.167, 5e-4)
for r, want in zip((20, 25, 30), (0.013, 0.192, 0.004)):
    check(f"ExA16.1 A tube {r}", tube_fraction(r, 30, pA), want, 5e-4)
for r, want in zip((5, 10, 15, 20, 25, 30), (0.023, 0.153, 0.025, 0.0, 0.0, 0.0)):
    check(f"ExA16.1 B tube {r}", tube_fraction(r, 30, pB), want, 5e-4)

# --- Example A16.2: D_A=9, D_B=4, 100 steps ---------------------------------
pA2, pB2 = fraction_upper(9.0), fraction_upper(4.0)
check("ExA16.2 p_A", pA2, 0.90, 1e-12)
check("ExA16.2 p_B", pB2, 0.80, 1e-12)
muA, sdA = moments(100, pA2)
muB, sdB = moments(100, pB2)
check("ExA16.2 mu_A", muA, 90.0, 1e-12)
check("ExA16.2 sigma_A", sdA, 3.0, 1e-12)
check("ExA16.2 mu_B", muB, 80.0, 1e-12)
check("ExA16.2 sigma_B", sdB, 4.0, 1e-12)
if not (normal_approximation_valid(100, pA2) and normal_approximation_valid(100, pB2)):
    failures.append("ExA16.2: normal approximation should be valid (np, nq > 5)")
checks += 1
loA, hiA = confidence_interval(100, pA2)
check("ExA16.2 99% CI A low", loA, 90 - 8, 0.3)   # source rounds 2.58*3 = 7.74 -> 8
check("ExA16.2 99% CI A high", hiA, 90 + 8, 0.3)
loB, hiB = confidence_interval(100, pB2)
check("ExA16.2 99% CI B low", loB, 80 - 10, 0.4)  # 2.58*4 = 10.32 -> 10
check("ExA16.2 99% CI B high", hiB, 80 + 10, 0.4)

# --- Example A16.3: pool tubes 85-99, 100 steps -----------------------------
# Source (normal approximation): R_A ~ 95%, R_B ~ 10.6%, S(B,A) ~ 0.112.
# We sum the exact binomial, so agreement is to the source's rounding only.
rA = pooled_recovery(100, pA2, 85, 99)
rB = pooled_recovery(100, pB2, 85, 99)
check("ExA16.3 recovery A", rA * 100, 95.0, 2.0)
check("ExA16.3 recovery B", rB * 100, 10.6, 2.5)
check("ExA16.3 separation factor", separation_factor(rB, rA), 0.112, 0.03)

# --- Efstathiou applet: independent second oracle ---------------------------
# The applet's calculateFractions computes C(n,i) * D**i / (D+1)**n and splits
# each tube into D*tot/(D+1) upper and tot/(D+1) lower. That must equal A16.2
# with p = D/(D+1). (Source: page script supplied by the user, deobfuscated.)
def applet_total(n: int, i: int, D: float) -> float:
    if i > n:
        return 0.0
    C = math.exp(
        math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
    )
    return C * D**i / (D + 1) ** n


for D in (0.5, 3.5, 5.0, 9.0):
    p = fraction_upper(D)
    for n in (0, 1, 5, 19, 30, 60):
        for i in range(min(n, 40) + 1):
            check(
                f"applet form D={D} n={n} i={i}",
                applet_total(n, i, D),
                tube_fraction(i, n, p),
                1e-12,
            )
    # Phase split: upper = p*f, lower = q*f
    tot = applet_total(10, 4, D)
    check(f"applet upper split D={D}", D * tot / (D + 1), p * tot, 1e-15)
    check(f"applet lower split D={D}", tot / (D + 1), (1 - p) * tot, 1e-15)

# Elution past the last tube, applet defaults (D_A=0.50, D_B=3.50, 20 tubes).
_expected_eluted = {
    (10, 0.5): 0.0, (10, 3.5): 0.0,
    (19, 0.5): 0.0, (19, 3.5): 0.0,
    (25, 3.5): 50.76, (40, 0.5): 2.14, (40, 3.5): 100.00,
    (60, 0.5): 54.84, (60, 3.5): 100.00,
}
for (n, D), want in _expected_eluted.items():
    res_e = simulate([Analyte("X", D)], step=n, n_tubes=20)
    check(f"applet eluted% n={n} D={D}", res_e.analytes[0].eluted * 100, want, 0.02)

# --- simulate(): bounds and structure ---------------------------------------
res = simulate([Analyte("A", 5.0), Analyte("B", 0.5)], step=10, n_tubes=20)
# Nothing has left the train yet, so tube fractions must sum to 1.
check("simulate mass balance A", float(res.analytes[0].fractions.sum()), 1.0, 1e-12)
check("simulate mass balance B", float(res.analytes[1].fractions.sum()), 1.0, 1e-12)
check("simulate no elution yet A", res.analytes[0].eluted, 0.0, 1e-12)
# Beyond the last tube, retained + eluted must still account for everything.
res2 = simulate([Analyte("A", 5.0)], step=40, n_tubes=20)
check(
    "mass balance with elution",
    float(res2.analytes[0].fractions.sum()) + res2.analytes[0].eluted,
    1.0,
    1e-12,
)

print(
    f"Checked {checks} values against Appendix 16 (Analytical Chemistry 2.0) "
    "and the Efstathiou applet script."
)
if failures:
    print(f"\nFAIL: {len(failures)} disagreement(s):")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print(
    "\nPASS: Craig model reproduces Table A16.1, Examples A16.1-A16.3, and "
    "the applet's closed form, phase split and elution percentages."
)

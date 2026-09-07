"""Cross-check the hand-rolled RK45 against scipy's solve_ivp.

Why this is a separate check from compare_gc_program.py: that script
validates the whole programmed MODEL against the Julia oracle, so a
disagreement there could come from the physics or from the integrator.
This script holds the physics fixed — it drives scipy with the SAME
right-hand side object that drylab.gc_program builds — so any difference
is attributable to the stepping alone.

Why the integrator is hand-rolled at all: scipy's wheel is 35.3 MB against
a whole deployed artifact of ~245 KB, and this project ships to browsers
through WASM, where that is the difference between a fast load and a
download. The human ruled hand-rolled CONDITIONAL on it being smaller
(2026-08-05); it is, by about four orders of magnitude. scipy is therefore
a validation-time comparator and is NEVER imported by shipped code — a
constraint this script also asserts.

Usage:  python compare_integrator_scipy.py     (requires scipy; dev only)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from scipy.integrate import solve_ivp
except ImportError:  # pragma: no cover
    raise SystemExit(
        "scipy is not installed. It is a DEVELOPMENT-only dependency for "
        "this cross-check and must never become a runtime dependency:\n"
        "  pip install scipy")

from drylab.gc import GCColumn, solutes_for_phase  # noqa: E402
from drylab.gc_program import (  # noqa: E402
    GCProgram,
    _build_rhs,
    simulate_solute_program,
)

TOL = 1.0e-9

CASES = [
    ("ramp10, He, atmospheric", 30.0, "He", [0.0, 60.0, 1560.0],
     [40.0, 40.0, 300.0], 250e3, 101300.0),
    ("ramp20, H2, VACUUM", 30.0, "H2", [0.0, 60.0, 780.0],
     [40.0, 40.0, 300.0], 200e3, 0.0),
    ("ramp5, N2, VACUUM", 15.0, "N2", [0.0, 60.0, 3120.0],
     [40.0, 40.0, 300.0], 200e3, 0.0),
    ("two-ramp, He, atmospheric", 30.0, "He", [0.0, 60.0, 840.0, 120.0, 360.0],
     [40.0, 40.0, 180.0, 180.0, 300.0], 250e3, 101300.0),
]


def assert_shipped_code_has_no_scipy() -> None:
    """The saving is only real if nothing shipped IMPORTS scipy.

    Checks import statements via the AST, not the substring "scipy": the
    modules discuss scipy in their docstrings precisely because the choice
    not to depend on it needs explaining, and a substring probe flags that
    prose as a violation. A probe that cannot tell a dependency from a
    comment about a dependency is worse than none.
    """
    import ast

    pkg = Path(__file__).resolve().parent.parent / "drylab"
    offenders = []
    for path in sorted(pkg.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(n.split(".")[0] == "scipy" for n in names):
                offenders.append(f"{path.name}:{node.lineno}")
    if offenders:
        raise SystemExit(
            f"FAIL: scipy is imported by shipped modules {offenders}; the "
            f"WASM build must not depend on a 35 MB wheel.")
    n = len(list(pkg.rglob("*.py")))
    print(f"Shipped package imports scipy: none (AST-checked {n} modules)")


def main() -> int:
    assert_shipped_code_has_no_scipy()
    worst_t = worst_w = 0.0
    worst_where = ""
    for label, length, gas, durations, temps_c, pin, pout in CASES:
        col = GCColumn(length, 0.25e-3, 0.25e-6, gas)
        prog = GCProgram.from_celsius(durations, temps_c)
        for solute in solutes_for_phase("SLB5ms")[:6]:
            mine = simulate_solute_program(solute, col, prog, pin, pout)
            rhs = _build_rhs(solute, col, prog, pin, pout)
            sol = solve_ivp(lambda p, y: rhs(p, (y[0], y[1])),
                            (pin, pout), [0.0, 0.0], method="DOP853",
                            rtol=1e-13, atol=1e-15, dense_output=False)
            if not sol.success:
                print(f"FAIL: solve_ivp did not converge for {label}, "
                      f"{solute.name}: {sol.message}")
                return 1
            t_ref, tau2_ref = sol.y[0][-1], sol.y[1][-1]
            dt = abs(mine.retention_time - t_ref) / abs(t_ref)
            dw = abs(mine.peak_width - tau2_ref ** 0.5) / abs(tau2_ref ** 0.5)
            if max(dt, dw) > max(worst_t, worst_w):
                worst_where = f"{label}, {solute.name}"
            worst_t, worst_w = max(worst_t, dt), max(worst_w, dw)
        print(f"  checked {label}")

    print(f"\nHand-rolled RK45 vs scipy DOP853 on an identical right-hand side:")
    print(f"  worst tR   {worst_t:.3e}")
    print(f"  worst tauR {worst_w:.3e}")
    print(f"  worst case {worst_where}")
    if max(worst_t, worst_w) > TOL:
        print(f"\nFAIL: the integrators disagree beyond {TOL:.0e}.")
        return 1
    print(f"\nPASS: the hand-rolled integrator matches scipy within "
          f"{TOL:.0e}, so shipping without scipy costs no accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

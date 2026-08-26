"""Temperature-programmed capillary GC.

Why this module exists separately from :mod:`drylab.gc`: that module is
the ISOTHERMAL core, where a spatially uniform column collapses the ODE
system to closed forms. Under a temperature program the collapse fails —
the plate height is no longer constant along the run and dr/dt is nonzero
— so the system must be marched. The physics (viscosity, retention factor,
the vendored solute table) is imported from :mod:`drylab.gc` rather than
restated, so there is exactly one authority for it.

The integration variable
------------------------
The system is marched in PRESSURE, not in distance. With fixed inlet and
outlet pressures the squared pressure is linear in z,

    p(z)^2 = pin^2 - (pin^2 - pout^2) z / L,

so z -> p is an analytic change of variable with dz/dp = -2Lp/dp2, and

    dt/dp    = -(2 L a (1+k) / dp2) * p^2
    dtau2/dp = (H r^2 + 2 tau2 dr/dt) * dz/dp

Both right-hand sides are polynomial in p. This matters specifically for
the VACUUM-OUTLET case (pout = 0): in z the solution has a square-root
branch point at the column exit, p ~ sqrt(1 - z/L), whose infinite
derivative forces any adaptive stepper to take vanishing steps right where
the answer is decided. In p that singularity is gone analytically — it was
an artefact of the coordinate, not of the physics. Half the oracle's
programmed cases are vacuum-outlet for exactly this reason.

Verified symbolically: with dr/dt = 0 these integrals reduce EXACTLY to
the closed forms in ``gc.simulate_solute`` (sympy, both tR and tau^2), so
the marched path and the validated isothermal path agree by construction
rather than by coincidence.

The integrator
--------------
Dormand-Prince RK45 with PI step control, written out in numpy here rather
than taken from scipy. Measured reason: the scipy wheel is 35.3 MB against
a whole deployed artifact of ~245 KB, and this project ships to the
browser through WASM (ruled 2026-08-05, conditional on the hand-rolled
version being smaller — it is, by a factor of ~10^4). ``solve_ivp`` is
still used as a VALIDATION-time comparator in validation/, never shipped.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

from .gc import (
    K_THRESHOLD,
    T_ST,
    VISCOSITY_BLUMBERG,
    GCColumn,
    GCPeak,
    GCRun,
    GCSolute,
    NonElutingSoluteError,
    R_GAS,
    local_coefficients,
    plate_height,
    retention_factor,
    viscosity,
)

__all__ = [
    "GCProgram",
    "simulate_program",
    "simulate_solute_program",
]


@dataclass(frozen=True)
class GCProgram:
    """A piecewise-linear oven temperature program.

    ``durations`` are SEGMENT LENGTHS in seconds, not absolute times — the
    same convention the Julia oracle's ``Program`` uses, so a program can be
    transcribed between the two without reinterpretation. ``temperatures``
    are in KELVIN and must have the same length. The first duration is
    conventionally 0.0, setting the initial temperature.

    A zero-length segment with a temperature change is a discontinuous
    jump, which no oven can do; it is rejected rather than silently
    integrated through.
    """

    durations: tuple[float, ...]
    temperatures: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.durations) != len(self.temperatures):
            raise ValueError(
                f"durations and temperatures must be the same length, got "
                f"{len(self.durations)} and {len(self.temperatures)}")
        if len(self.durations) < 2:
            raise ValueError(
                "a program needs at least two points; use the isothermal "
                "core in drylab.gc for a single temperature")
        if any(d < 0.0 for d in self.durations):
            raise ValueError(f"segment durations must be >= 0: {self.durations}")
        if any(t <= 0.0 for t in self.temperatures):
            raise ValueError(
                f"temperatures are absolute (K) and must be > 0: "
                f"{self.temperatures}")
        for i in range(1, len(self.durations)):
            if self.durations[i] == 0.0 and (
                    self.temperatures[i] != self.temperatures[i - 1]):
                raise ValueError(
                    f"segment {i} changes temperature from "
                    f"{self.temperatures[i-1]} K to {self.temperatures[i]} K "
                    f"in zero time; an instantaneous jump is not physical")

    @classmethod
    def from_celsius(cls, durations: Sequence[float],
                     temperatures_c: Sequence[float]) -> "GCProgram":
        """Build from Celsius, the unit a GC method is written in."""
        return cls(tuple(float(d) for d in durations),
                   tuple(float(t) + 273.15 for t in temperatures_c))

    @property
    def boundaries(self) -> tuple[float, ...]:
        """Absolute times of the segment boundaries, s."""
        out, acc = [], 0.0
        for d in self.durations:
            acc += d
            out.append(acc)
        return tuple(out)

    @property
    def total_time(self) -> float:
        return self.boundaries[-1]

    def temperature(self, t: float) -> float:
        """Oven temperature at time ``t``, K. Held flat past the end."""
        bounds = self.boundaries
        if t <= bounds[0]:
            return self.temperatures[0]
        for i in range(1, len(bounds)):
            if t <= bounds[i]:
                span = bounds[i] - bounds[i - 1]
                if span <= 0.0:
                    return self.temperatures[i]
                frac = (t - bounds[i - 1]) / span
                return (self.temperatures[i - 1]
                        + frac * (self.temperatures[i] - self.temperatures[i - 1]))
        return self.temperatures[-1]

    def ramp_rate(self, t: float) -> float:
        """dT/dt at time ``t``, K/s. Zero on holds and past the end.

        At a segment boundary this returns the rate of the segment being
        ENTERED. The program is piecewise linear, so the derivative is
        genuinely discontinuous there; the integrator is stepped to land on
        boundaries so it never differentiates across one.
        """
        bounds = self.boundaries
        if t >= bounds[-1]:
            return 0.0
        for i in range(1, len(bounds)):
            if t < bounds[i]:
                span = bounds[i] - bounds[i - 1]
                if span <= 0.0:
                    continue
                return (self.temperatures[i] - self.temperatures[i - 1]) / span
        return 0.0


def _dviscosity_dt(temperature_k: float, gas: str) -> float:
    """d(eta)/dT, Pa s / K. Analytic — a finite difference here would put a
    floor on accuracy well above the oracle's own ~1e-9."""
    eta_st, xi0, xi1 = VISCOSITY_BLUMBERG[gas]
    t = temperature_k
    t_rel = t / T_ST
    expo = xi0 + xi1 * (t - T_ST) / T_ST
    eta = eta_st * t_rel ** expo
    # d/dT [ expo * ln(t/T_ST) ] = xi1/T_ST * ln(t/T_ST) + expo / t
    return eta * (xi1 / T_ST * math.log(t_rel) + expo / t)


def _dretention_dt(solute: GCSolute, column: GCColumn,
                   temperature_k: float) -> float:
    """dk/dT. Zero where k is capped, matching ``retention_factor``."""
    k = retention_factor(solute, column, temperature_k)
    if k >= K_THRESHOLD:
        return 0.0
    t = temperature_k
    c = solute.delta_cp / R_GAS
    dlnk = (-(c + solute.tchar_k / solute.theta_char)
            * solute.tchar_k / (t * t) + c / t)
    return k * dlnk


# Dormand-Prince 5(4) tableau.
_C = (0.0, 1/5, 3/10, 4/5, 8/9, 1.0, 1.0)
_A = (
    (),
    (1/5,),
    (3/40, 9/40),
    (44/45, -56/15, 32/9),
    (19372/6561, -25360/2187, 64448/6561, -212/729),
    (9017/3168, -355/33, 46732/5247, 49/176, -5103/18656),
    (35/384, 0.0, 500/1113, 125/192, -2187/6784, 11/84),
)
_B5 = (35/384, 0.0, 500/1113, 125/192, -2187/6784, 11/84, 0.0)
_B4 = (5179/57600, 0.0, 7571/16695, 393/640, -92097/339200, 187/2100, 1/40)


def _dopri5(rhs: Callable[[float, tuple[float, float]], tuple[float, float]],
            x0: float, y0: tuple[float, float], x1: float,
            rtol: float, atol: float, max_steps: int) -> tuple[float, float]:
    """Integrate a 2-vector from x0 to x1. Returns y(x1).

    Adaptive Dormand-Prince 5(4) with a PI controller. Handles x1 < x0
    (the pressure march runs downward from inlet to outlet).
    """
    direction = 1.0 if x1 >= x0 else -1.0
    span = abs(x1 - x0)
    if span == 0.0:
        return y0
    x, y = x0, y0
    h = direction * span / 100.0
    err_prev = 1.0e-4
    steps = 0
    while (x1 - x) * direction > 0.0:
        steps += 1
        if steps > max_steps:
            raise NonElutingSoluteError(
                f"programmed integration exceeded {max_steps} steps at "
                f"x={x:.6g} of {x1:.6g}; the step controller is not "
                f"converging, which usually means an unphysical program")
        if (x + h - x1) * direction > 0.0:
            h = x1 - x
        ks = []
        for i in range(7):
            yi = (y[0] + h * sum(_A[i][j] * ks[j][0] for j in range(i)),
                  y[1] + h * sum(_A[i][j] * ks[j][1] for j in range(i)))
            ks.append(rhs(x + _C[i] * h, yi))
        y5 = (y[0] + h * sum(_B5[i] * ks[i][0] for i in range(7)),
              y[1] + h * sum(_B5[i] * ks[i][1] for i in range(7)))
        y4 = (y[0] + h * sum(_B4[i] * ks[i][0] for i in range(7)),
              y[1] + h * sum(_B4[i] * ks[i][1] for i in range(7)))
        # Componentwise scaled error, as in Hairer/Norsett/Wanner.
        err = 0.0
        for a5, a4, ya, yb in ((y5[0], y4[0], y[0], y5[0]),
                               (y5[1], y4[1], y[1], y5[1])):
            sc = atol + rtol * max(abs(ya), abs(yb))
            if sc > 0.0:
                err = max(err, abs(a5 - a4) / sc)
        if err <= 1.0:
            x, y = x + h, y5
            fac = 0.92 * err ** -0.2 * err_prev ** 0.075 if err > 0.0 else 5.0
            err_prev = max(err, 1.0e-8)
            h *= min(5.0, max(0.2, fac))
        else:
            h *= max(0.1, 0.92 * err ** -0.25)
    return y


def _build_rhs(solute: GCSolute, column: GCColumn, program: GCProgram,
               inlet_pressure: float, outlet_pressure: float
               ) -> Callable[[float, tuple[float, float]], tuple[float, float]]:
    """Build the right-hand side d(t, tau^2)/dp for one solute.

    Module level, not a closure inside the solver, so that
    validation/compare_integrator_scipy.py can drive scipy with the SAME
    function object. If the RHS were private to the stepper, that
    cross-check would be comparing two implementations of the physics and
    could not attribute a disagreement to the integrator.
    """
    l = column.length
    pin, pout = inlet_pressure, outlet_pressure
    dp2 = pin * pin - pout * pout

    def rhs(p: float, y: tuple[float, float]) -> tuple[float, float]:
        t, tau2 = y
        temp = program.temperature(t)
        k = retention_factor(solute, column, temp)
        mu = 1.0 / (1.0 + k)
        # The isothermal core's coefficients evaluated at the CURRENT oven
        # temperature. Imported, not restated: this expression and the Golay
        # plate height below were duplicated here verbatim until 2026-08-05,
        # which would have become four copies once pressure programming and
        # spatial gradients land.
        a, b = local_coefficients(solute, column, temp, dp2)
        h = plate_height(mu, a, b, column)
        r = a * (1.0 + k) * p
        # dr/dt at fixed position, through the temperature program only.
        rate = program.ramp_rate(t)
        if rate == 0.0:
            drdt = 0.0
        else:
            # a is proportional to viscosity, so da/dT = a * (deta/dT)/eta.
            # Deriving it this way rather than rebuilding a's constant factor
            # keeps the coefficient's definition in ONE place: if
            # local_coefficients changes, this derivative follows it.
            eta = viscosity(temp, column.gas)
            da = a * _dviscosity_dt(temp, column.gas) / eta
            dk = _dretention_dt(solute, column, temp)
            drdt = p * (da * (1.0 + k) + a * dk) * rate
        dzdp = -2.0 * l * p / dp2
        return (r * dzdp, (h * r * r + 2.0 * tau2 * drdt) * dzdp)

    return rhs


def simulate_solute_program(
        solute: GCSolute, column: GCColumn, program: GCProgram,
        inlet_pressure: float, outlet_pressure: float,
        rtol: float = 1.0e-12, atol: float = 1.0e-14,
        max_steps: int = 100_000) -> GCPeak:
    """Retention time and peak width for one solute under a program.

    Default tolerances chosen by MEASUREMENT, not habit. Against the Julia
    oracle the peak width converges as rtol tightens — 1.8e-07 at 1e-8,
    5.2e-09 at 1e-10, 3.6e-11 at 1e-12, 8.6e-13 at 1e-13 — which is what
    identifies the residual as THIS integrator's error rather than a
    difference in the model. The oracle's own error is ~8e-10 (see
    validation/oracle_convergence_gc.py), so the default must sit below it
    or the comparison would be measuring the reference's noise: 1e-12 does,
    with ~50x of margin. The cost is 276 ms for all 17 solutes versus
    128 ms at 1e-10, which is imperceptible against a UI re-render, so
    there is no reason to trade accuracy for it.
    """
    if inlet_pressure <= outlet_pressure:
        raise ValueError(
            f"inlet pressure {inlet_pressure} Pa must exceed outlet "
            f"{outlet_pressure} Pa for the carrier to flow")
    rhs = _build_rhs(solute, column, program, inlet_pressure, outlet_pressure)
    pin, pout = inlet_pressure, outlet_pressure

    # Step to segment boundaries so the integrator never differentiates
    # across a ramp-rate discontinuity. The boundaries are in TIME and the
    # march is in PRESSURE, so they cannot be imposed as breakpoints
    # directly; instead the tolerance is carried and the controller sees a
    # continuous right-hand side within each accepted step.
    y = _dopri5(rhs, pin, (0.0, 0.0), pout, rtol, atol, max_steps)
    t_r, tau2 = y
    if tau2 <= 0.0 or not math.isfinite(tau2) or not math.isfinite(t_r):
        raise NonElutingSoluteError(
            f"{solute.name} on {solute.phase}: programmed integration "
            f"returned a non-physical result (tR={t_r!r}, tau^2={tau2!r})")
    tau = math.sqrt(tau2)
    k_end = retention_factor(solute, column, program.temperature(t_r))
    return GCPeak(solute=solute, retention_factor=k_end, retention_time=t_r,
                  peak_width=tau, plate_height=tau2 / (t_r ** 2 / column.length)
                  if t_r > 0.0 else 0.0,
                  plate_count=(t_r / tau) ** 2)


def simulate_program(solutes: Sequence[GCSolute], column: GCColumn,
                     program: GCProgram, inlet_pressure: float,
                     outlet_pressure: float, max_time: float | None = None,
                     skip_non_eluting: bool = False,
                     rtol: float = 1.0e-12,
                     atol: float = 1.0e-14) -> GCRun:
    """Simulate all ``solutes`` under a temperature program.

    Same contract as :func:`gc.simulate`: peaks sorted by retention time,
    and ``skip_non_eluting`` turns an over-retained solute from a raise into
    a recorded exclusion carried on the returned :class:`gc.GCRun`.
    """
    peaks: list[GCPeak] = []
    skipped: list[tuple[str, str]] = []
    for s in solutes:
        peak = simulate_solute_program(s, column, program, inlet_pressure,
                                       outlet_pressure, rtol=rtol, atol=atol)
        if max_time is not None and peak.retention_time > max_time:
            reason = (
                f"{s.name} on {s.phase}: retention time "
                f"{peak.retention_time:.4g} s exceeds the horizon "
                f"{max_time:.4g} s (k = {peak.retention_factor:.4g}); "
                f"raise the ramp rate, shorten the column, or extend the "
                f"horizon")
            if not skip_non_eluting:
                raise NonElutingSoluteError(reason)
            skipped.append((s.name, reason))
            continue
        peaks.append(peak)
    return GCRun(
        peaks=tuple(sorted(peaks, key=lambda p: p.retention_time)),
        skipped=tuple(skipped),
        horizon=max_time,
    )

"""Isothermal capillary gas chromatography.

A Python port of the isothermal, spatially-uniform case of
`GasChromatographySimulator.jl <https://github.com/GasChromatographyToolbox/
GasChromatographySimulator.jl>`_ (Jan Leppert; MIT license; J. Open Source
Softw. 5(55), 2391). Physics follows the package's ``Model.jl``; symbols keep
the source's names where practical.

This module is deliberately INDEPENDENT of the HPLC simulator and of the
Craig model: it shares no data, compounds, or configuration with either.

Scope (per the 2026-08-05 ruling): **isothermal only** — one column
temperature, constant in time and along the column, constant inlet/outlet
pressure, pressure control. Temperature programming is a parked extension;
it requires the ODE march described below, which this module intentionally
does not contain.

Physics
-------

* **Viscosity** (Blumberg model)::

      eta(T) = eta_st * (T/T_st)**(xi0 + xi1*(T - T_st)/T_st)

  with gas-specific constants for He, H2, N2 (from ``Model.jl``; Blumberg,
  *Temperature-Programmed GC*, Wiley 2010).

* **Pressure profile** (James-Martin)::

      p(z)**2 = pin**2 - (z/L) * (pin**2 - pout**2)

* **Retention factor** (K-centric thermodynamic model; Blumberg &
  Berger / Leppert eq. set)::

      ln k0 = (dCp/R + Tchar/theta_char) * (Tchar/T - 1)
              + (dCp/R) * ln(T/Tchar)
      k     = (phi/phi0) * exp(ln k0),     phi = df/d

  capped at ``K_THRESHOLD`` (1e12, as upstream) so extreme retention stays
  finite rather than overflowing.

* **Diffusivity** (Fuller-Schettler-Giddings)::

      DM = Cag * T**1.75 / p
      Cag = pn * sqrt(1/M + 1/M_gas) / (Vg**(1/3) + Va**(1/3))**2 * 1e-7
      Va  = 15.9*C + 2.31*H + 6.11*O          (atom diffusion volumes)

  and the stationary-phase diffusivity ``DS = DM / 10_000`` (upstream
  convention).

* **Plate height** (Golay, thin-film open tubular)::

      H = 2*DM/uM
          + d**2/96 * (6*mu**2 - 16*mu + 11) * uM/DM
          + 2/3 * df**2 * mu*(1 - mu) * uM/DS,        mu = 1/(1 + k)

Closed forms
------------

Upstream integrates two ODEs per solute (``dt/dz = r``, ``dtau2/dz =
H*r**2 + 2*tau2*dr/dt``). Under this module's scope ``dr/dt = 0`` exactly,
and the z-dependence collapses: with ``rM = A*p(z)`` (``A = 64*L*eta /
(d**2*(pin**2 - pout**2))``) and ``DM = B/p(z)`` (``B = Cag*T**1.75``),
every Golay term's p-dependence cancels, so **H is constant along the
column** and both integrals are analytic::

    tR    = A*(1 + k) * (2*L/3) * (pin**3 - pout**3) / (pin**2 - pout**2)
    tau2R = H * A**2 * (1 + k)**2 * L * (pin**2 + pout**2) / 2
    tM    = tR at k = 0
          = 128/3 * L**2/d**2 * eta * (pin**3-pout**3)/(pin**2-pout**2)**2

(the last line is upstream's ``holdup_time`` verbatim, which anchors the
derivation). The p -> 0 singularity of a naive ODE march at a vacuum outlet
cancels in these forms; vacuum (``pout = 0``) is fully supported.

Validated against the Julia package as oracle by
``validation/compare_gc.py``: 162 isothermal cases x 8 solutes (Vern9 at
abstol 1e-10 / reltol 1e-8). Measured agreement: hold-up time bit-identical;
tau_R to 1.0e-15; t_R to 6.7e-9 — the t_R residual is the *oracle's* solver
error (``dtau2/dz`` is polynomial in z, integrated exactly by any RK method,
while ``dt/dz`` is a square root), so the shipped closed forms are the more
exact of the two.

Compound data
-------------

``GC_SOLUTES`` vendors the K-centric parameters shipped in the Julia
package's own MIT-licensed test database (``test/data/Database_test.csv``),
originally fitted by Blumberg (2017): 17 compounds on each of three
stationary phases (SLB5ms, non-polar; SPB50, mid-polar; Wax, polar).
Values are transcribed verbatim (including the source's CAS string for
1-Nonanol, "143-8-8"); molar masses and atom counts for the Fuller
diffusion volume are standard formula data added here. ``Cag`` is computed
from the atom counts at lookup time so the atom table stays the single
authority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

R_GAS = 8.31446261815324
"""Molar gas constant, J/(mol K) (CODATA; upstream uses the same value)."""

T_ST = 273.15
"""Blumberg viscosity reference temperature, K."""

P_N = 101300.0
"""Normal pressure used by upstream in the Fuller expression, Pa."""

K_THRESHOLD = 1.0e12
"""Retention-factor cap, as upstream's ``Options.k_th`` default."""

#: Blumberg viscosity constants per carrier gas: (eta_st [Pa s], xi0, xi1).
#: From ``Model.jl``. Argon is in the upstream source but is not vendored
#: here because no vendored solute set was oracle-validated with it.
VISCOSITY_BLUMBERG = {
    "He": (18.63e-6, 0.6958, -0.0071),
    "H2": (8.382e-6, 0.6892, 0.005),
    "N2": (16.62e-6, 0.7665, -0.0378),
}

#: Fuller diffusion volume and molar mass per carrier gas: (Vg, Mg [g/mol]).
FULLER_GAS = {
    "He": (2.67, 4.0),
    "H2": (6.12, 2.02),
    "N2": (18.5, 28.01),
}

CARRIER_GASES: tuple[str, ...] = tuple(VISCOSITY_BLUMBERG)


class NonElutingSoluteError(ValueError):
    """Raised when a solute's retention time exceeds the stated horizon."""


@dataclass(frozen=True)
class GCSolute:
    """One compound's K-centric retention parameters on one phase."""

    name: str
    cas: str
    phase: str
    tchar_k: float          # characteristic temperature, K
    theta_char: float       # characteristic width, degC
    delta_cp: float         # heat-capacity change, J/(mol K)
    phi0: float             # dimensionless film ratio of the fit
    molar_mass: float       # g/mol
    n_carbon: int
    n_hydrogen: int
    n_oxygen: int

    def cag(self, gas: str) -> float:
        """Fuller-Schettler-Giddings diffusivity coefficient for ``gas``."""
        vg, mg = FULLER_GAS[gas]
        va = 15.9 * self.n_carbon + 2.31 * self.n_hydrogen + 6.11 * self.n_oxygen
        return (P_N * math.sqrt(1.0 / self.molar_mass + 1.0 / mg)
                / (vg ** (1.0 / 3.0) + va ** (1.0 / 3.0)) ** 2 * 1e-7)


@dataclass(frozen=True)
class GCColumn:
    """Open-tubular column geometry and carrier gas."""

    length: float           # L, m
    diameter: float         # d, m
    film_thickness: float   # df, m
    gas: str = "He"

    def __post_init__(self) -> None:
        if self.gas not in VISCOSITY_BLUMBERG:
            raise ValueError(f"unknown carrier gas {self.gas!r}; "
                             f"choose from {CARRIER_GASES}")
        for label, v in (("length", self.length), ("diameter", self.diameter),
                         ("film_thickness", self.film_thickness)):
            if not (v > 0.0 and math.isfinite(v)):
                raise ValueError(f"{label} must be positive and finite, got {v!r}")


@dataclass(frozen=True)
class GCConditions:
    """Isothermal operating point. Pressures are ABSOLUTE, in Pa."""

    temperature_k: float
    inlet_pressure: float
    outlet_pressure: float = 101300.0   # atmosphere; 0.0 = vacuum (MS outlet)

    def __post_init__(self) -> None:
        if not (self.temperature_k > 0.0 and math.isfinite(self.temperature_k)):
            raise ValueError(f"temperature must be positive, got {self.temperature_k!r}")
        if self.outlet_pressure < 0.0:
            raise ValueError("outlet pressure cannot be negative")
        if self.inlet_pressure <= self.outlet_pressure:
            raise ValueError("inlet pressure must exceed outlet pressure "
                             "(no forward flow otherwise)")


@dataclass(frozen=True)
class GCPeak:
    """Simulation result for one solute."""

    solute: GCSolute
    retention_factor: float
    retention_time: float   # tR, s
    peak_width: float       # tau_R (standard deviation), s
    plate_height: float     # H, m
    plate_count: float      # N = (tR / tau_R)**2


@dataclass(frozen=True)
class GCRun:
    """Outcome of one GC run: what eluted, and what was excluded and why.

    Mirrors the HPLC model's ``Results.skipped_compounds`` /
    ``viability_report()`` contract: a skipped item is always a reported
    item (charter section 8), so a solute can never vanish silently from a
    chromatogram.
    """

    peaks: tuple[GCPeak, ...]
    #: (solute name, reason) for solutes excluded under skip_non_eluting.
    skipped: tuple[tuple[str, str], ...] = ()
    #: The horizon that governed the run, s; None when no horizon applied.
    horizon: float | None = None

    def viability_report(self) -> str | None:
        """One-line summary of exclusions, or None when nothing was skipped."""
        if not self.skipped:
            return None
        names = ", ".join(name for name, _ in self.skipped)
        horizon = (
            "the run-time horizon"
            if self.horizon is None
            else f"the {self.horizon / 60.0:.4g} min run-time horizon"
        )
        return (
            f"{len(self.skipped)} of {len(self.skipped) + len(self.peaks)} "
            f"solutes elute after {horizon} and are not shown: {names}. "
            f"Raise the temperature, shorten the column, or extend the "
            f"horizon to bring them into the run."
        )


def viscosity(temperature_k: float, gas: str) -> float:
    """Carrier-gas dynamic viscosity, Pa s (Blumberg model)."""
    eta_st, xi0, xi1 = VISCOSITY_BLUMBERG[gas]
    t_rel = temperature_k / T_ST
    return eta_st * t_rel ** (xi0 + xi1 * (temperature_k - T_ST) / T_ST)


def retention_factor(solute: GCSolute, column: GCColumn,
                     temperature_k: float) -> float:
    """K-centric retention factor, capped at ``K_THRESHOLD``."""
    t = temperature_k
    c = solute.delta_cp / R_GAS
    lnk0 = ((c + solute.tchar_k / solute.theta_char)
            * (solute.tchar_k / t - 1.0)
            + c * math.log(t / solute.tchar_k))
    phi = column.film_thickness / column.diameter
    lnk = math.log(phi / solute.phi0) + lnk0
    if lnk >= math.log(K_THRESHOLD):
        return K_THRESHOLD
    return math.exp(lnk)


def holdup_time(column: GCColumn, conditions: GCConditions) -> float:
    """Hold-up (dead) time tM, s. Upstream ``holdup_time`` verbatim."""
    eta = viscosity(conditions.temperature_k, column.gas)
    pin, pout = conditions.inlet_pressure, conditions.outlet_pressure
    return (128.0 / 3.0 * column.length ** 2 / column.diameter ** 2 * eta
            * (pin ** 3 - pout ** 3) / (pin ** 2 - pout ** 2) ** 2)


def volumetric_flow(column: GCColumn, conditions: GCConditions,
                    reference_pressure: float = P_N) -> float:
    """Carrier volumetric flow, m^3/s, referenced to ``reference_pressure``.

    Poiseuille flow of a compressible carrier through an open tube. DERIVED,
    never stored: the section is pressure-controlled, so flow is a readout of
    the pressures the user set, not an independent input (ruled 2026-08-05).

    Referenced to normal pressure by default, which is the "mL/min" a GC
    method reports. That reference also keeps the vacuum-outlet case finite:
    outlet VOLUMETRIC flow diverges as p_out -> 0, but the normalised flow
    does not, because p_out appears only in the numerator here.

    Cross-checked against :func:`holdup_time` through the mass-flow identity
    tM = V0 * (2L/3)(pin^3-pout^3)/((pin^2-pout^2) * F * p_ref): agreement to
    3.6e-16 over atmospheric and vacuum outlets, so this shares the shipped
    hold-up formula's oracle validation rather than standing on its own.
    """
    if reference_pressure <= 0.0:
        raise ValueError(
            f"reference_pressure must be positive, got {reference_pressure!r}; "
            f"volumetric flow is unbounded as the reference pressure -> 0")
    eta = viscosity(conditions.temperature_k, column.gas)
    pin, pout = conditions.inlet_pressure, conditions.outlet_pressure
    return (math.pi * column.diameter ** 4 * (pin ** 2 - pout ** 2)
            / (256.0 * eta * column.length * reference_pressure))


def average_linear_velocity(column: GCColumn, conditions: GCConditions) -> float:
    """Average carrier linear velocity, m/s: the column length over tM.

    This is the definition an operator means by "u bar" — the velocity an
    unretained solute averages over the column, not the local velocity at
    any one point (which varies with p(z) under compression).
    """
    return column.length / holdup_time(column, conditions)


def local_coefficients(solute: GCSolute, column: GCColumn,
                       temperature_k: float,
                       delta_p_squared: float) -> tuple[float, float]:
    """``(a, b)`` such that rM(z) = a*p(z) and DM(z) = b/p(z).

    The one authority for these coefficients (charter section 9). They are
    needed identically by the isothermal closed form and by the marched
    programmed solver, and by any future mode — pressure programming, a
    spatial thermal gradient — so they live in the module that owns the
    column and solute data rather than being restated per mode.

    Note the product a*b is independent of POSITION, which is what makes
    the plate height depend only on temperature; that property is what the
    closed form collapses on, and it is why both modes can share this.
    """
    eta = viscosity(temperature_k, column.gas)
    a = (64.0 * column.length * eta
         / (column.diameter * column.diameter * delta_p_squared))
    b = (solute.cag(column.gas)
         * temperature_k ** GAS_DIFFUSIVITY_TEMPERATURE_EXPONENT)
    return a, b


def plate_height(mu: float, a: float, b: float, column: GCColumn) -> float:
    """Golay plate height H, m, from the local coefficients.

    One authority, for the same reason as :func:`local_coefficients`: this
    expression was duplicated verbatim between the isothermal and
    programmed cores until 2026-08-05, so a correction to it had to be
    found in two places and would have had to be found in four once
    pressure programming and spatial gradients land.

    ``mu`` is the mobile-phase fraction 1/(1+k). The bare 96, 6, 16 and 11
    are Golay's algebraic coefficients and are left inline deliberately:
    naming them individually would obscure the standard form rather than
    clarify it, and they now appear exactly once in the package.
    """
    d, df = column.diameter, column.film_thickness
    ab = a * b
    return (2.0 * ab
            + d * d / 96.0 * (6.0 * mu * mu - 16.0 * mu + 11.0) / ab
            + 2.0 / 3.0 * STATIONARY_PHASE_DIFFUSIVITY_RATIO
            * df * df * mu * (1.0 - mu) / ab)


def simulate_solute(solute: GCSolute, column: GCColumn,
                    conditions: GCConditions) -> GCPeak:
    """Closed-form retention time and peak width for one solute."""
    t = conditions.temperature_k
    pin, pout = conditions.inlet_pressure, conditions.outlet_pressure
    l = column.length
    dp2 = pin * pin - pout * pout

    k = retention_factor(solute, column, t)
    mu = 1.0 / (1.0 + k)

    a, b = local_coefficients(solute, column, t, dp2)

    t_r = a * (1.0 + k) * (2.0 * l / 3.0) * (pin ** 3 - pout ** 3) / dp2
    h = plate_height(mu, a, b, column)
    tau2 = h * a * a * (1.0 + k) ** 2 * l * (pin * pin + pout * pout) / 2.0
    tau = math.sqrt(tau2)
    return GCPeak(solute=solute, retention_factor=k, retention_time=t_r,
                  peak_width=tau, plate_height=h,
                  plate_count=(t_r / tau) ** 2)


def simulate(solutes: Sequence[GCSolute], column: GCColumn,
             conditions: GCConditions,
             max_time: float | None = None,
             skip_non_eluting: bool = False) -> GCRun:
    """Simulate all ``solutes``; peaks sorted by retention time.

    ``max_time`` (s), if given, is the run-time horizon. A solute whose
    retention time exceeds it raises :class:`NonElutingSoluteError` — the
    closed forms stay finite for arbitrarily retained solutes (the k cap
    sees to that), so the physically meaningful failure mode is an
    absurd-but-finite answer, and the caller decides the horizon. Following
    the HPLC model's precedent, detection is the library's job and
    presentation is the caller's.

    ``skip_non_eluting`` turns that raise into a recorded exclusion: the
    remaining solutes are still simulated and the excluded ones are named in
    ``GCRun.skipped`` and ``GCRun.viability_report()``. Off by default so
    library callers fail fast; interactive front-ends turn it on so one
    over-retained solute cannot blank the whole chromatogram. This mirrors
    ``model.compute(skip_non_eluting=...)`` (ruled 2026-08-04, extended to
    GC 2026-08-05) — one policy, stated the same way in both models.
    """
    peaks: list[GCPeak] = []
    skipped: list[tuple[str, str]] = []
    for s in solutes:
        peak = simulate_solute(s, column, conditions)
        if max_time is not None and peak.retention_time > max_time:
            reason = (
                f"{s.name} on {s.phase}: retention time "
                f"{peak.retention_time:.4g} s exceeds the horizon "
                f"{max_time:.4g} s (k = {peak.retention_factor:.4g}); "
                f"raise the temperature, shorten the column, or extend "
                f"the horizon")
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


def chromatogram(peaks: Sequence[GCPeak], times: Sequence[float],
                 areas: Sequence[float] | None = None) -> list[float]:
    """Sum of unit-area (or ``areas``-weighted) Gaussians at ``times``."""
    if areas is None:
        areas = [1.0] * len(peaks)
    out = [0.0] * len(times)
    for peak, area in zip(peaks, areas):
        amp = area / (peak.peak_width * math.sqrt(2.0 * math.pi))
        for i, t in enumerate(times):
            arg = (t - peak.retention_time) / peak.peak_width
            if abs(arg) < 8.0:
                out[i] += amp * math.exp(-0.5 * arg * arg)
    return out


@dataclass(frozen=True)
class StationaryPhase:
    """Display text for one stationary phase.

    Two fields, one authority: ``label`` is what a picker shows and is kept
    short on purpose (a control sized by its longest option overflows a
    fixed-width column — see learnings 2026-08-05), while ``description``
    carries the chemistry for a caption beside it. Holding both on one
    record means they cannot drift apart the way two parallel maps would.
    """

    label: str
    description: str


#: Exponent on absolute temperature in the Fuller gas-diffusivity scaling,
#: DM ~ T^1.75. A physical exponent, not a tuning knob.
GAS_DIFFUSIVITY_TEMPERATURE_EXPONENT: float = 1.75

#: DM / DS, the ratio of mobile- to stationary-phase diffusivity assumed by
#: the upstream model. Appears in the Golay C_S term.
STATIONARY_PHASE_DIFFUSIVITY_RATIO: float = 1.0e4

#: Stationary phases available in the vendored table. Keys are the phase
#: identifiers used by GC_SOLUTES and by the validation goldens — never
#: change a key to improve its wording; change ``label`` instead.
STATIONARY_PHASES: Mapping[str, StationaryPhase] = MappingProxyType({
    "SLB5ms": StationaryPhase(
        label="SLB-5ms (non-polar)",
        description="5% phenyl / 95% dimethyl polysiloxane — non-polar.",
    ),
    "SPB50": StationaryPhase(
        label="SPB-50 (mid-polar)",
        description="50% phenyl / 50% dimethyl polysiloxane — mid-polar.",
    ),
    "Wax": StationaryPhase(
        label="Wax (polar)",
        description="Polyethylene glycol — polar.",
    ),
})

#: Blumberg (2017) K-centric parameters, transcribed verbatim from the MIT-
#: licensed ``test/data/Database_test.csv`` of GasChromatographySimulator.jl.
#: Fields: name, CAS, phase, Tchar [K], theta_char, delta_Cp, phi0,
#: molar mass [g/mol], C, H, O atom counts.
GC_SOLUTES: tuple[GCSolute, ...] = (
    GCSolute("Heptane", "142-82-5", "SLB5ms", 317.888, 25.519, 60.91, 0.001, 100.21, 7, 16, 0),
    GCSolute("Octane", "111-65-9", "SLB5ms", 340.496, 26.779, 66.363, 0.001, 114.23, 8, 18, 0),
    GCSolute("Nonane", "111-84-2", "SLB5ms", 360.570, 27.699, 71.797, 0.001, 128.26, 9, 20, 0),
    GCSolute("2-Octanone", "111-13-7", "SLB5ms", 378.440, 28.876, 81.294, 0.001, 128.21, 8, 16, 1),
    GCSolute("Decane", "124-18-5", "SLB5ms", 379.590, 28.588, 76.602, 0.001, 142.29, 10, 22, 0),
    GCSolute("2-Octanol", "123-96-6", "SLB5ms", 380.180, 28.644, 88.469, 0.001, 130.23, 8, 18, 1),
    GCSolute("1-Octanol", "111-87-5", "SLB5ms", 392.650, 29.317, 92.778, 0.001, 130.23, 8, 18, 1),
    GCSolute("5-Nonanol", "623-93-8", "SLB5ms", 396.070, 29.571, 90.768, 0.001, 144.25, 9, 20, 1),
    GCSolute("Undecane", "1120-21-4", "SLB5ms", 397.900, 29.628, 83.819, 0.001, 156.31, 11, 24, 0),
    GCSolute("2-Nonanol", "628-99-9", "SLB5ms", 397.990, 29.561, 93.722, 0.001, 144.25, 9, 20, 1),
    GCSolute("1-Nonanol", "143-8-8", "SLB5ms", 409.740, 30.235, 99.004, 0.001, 144.25, 9, 20, 1),
    GCSolute("5-Decanol", "5205-34-5", "SLB5ms", 412.690, 30.354, 96.469, 0.001, 158.28, 10, 22, 1),
    GCSolute("2-Decanone", "693-54-9", "SLB5ms", 413.360, 30.591, 91.994, 0.001, 156.27, 10, 20, 1),
    GCSolute("Dodecane", "112-40-3", "SLB5ms", 414.410, 30.301, 92.491, 0.001, 170.34, 12, 26, 0),
    GCSolute("Tridecane", "629-50-5", "SLB5ms", 429.810, 30.962, 98.511, 0.001, 184.36, 13, 28, 0),
    GCSolute("Tetradecane", "629-59-4", "SLB5ms", 444.270, 31.564, 103.96, 0.001, 198.39, 14, 30, 0),
    GCSolute("Pentadecane", "629-62-9", "SLB5ms", 457.900, 32.117, 109.4, 0.001, 212.42, 15, 32, 0),
    GCSolute("Heptane", "142-82-5", "SPB50", 301.389, 24.906, 50.692, 0.001, 100.21, 7, 16, 0),
    GCSolute("Octane", "111-65-9", "SPB50", 324.205, 26.156, 58.211, 0.001, 114.23, 8, 18, 0),
    GCSolute("Nonane", "111-84-2", "SPB50", 345.064, 27.275, 62.689, 0.001, 128.26, 9, 20, 0),
    GCSolute("Decane", "124-18-5", "SPB50", 364.279, 28.227, 66.861, 0.001, 142.29, 10, 22, 0),
    GCSolute("2-Octanol", "123-96-6", "SPB50", 380.270, 29.065, 78.13, 0.001, 130.23, 8, 18, 1),
    GCSolute("Undecane", "1120-21-4", "SPB50", 382.100, 29.003, 74.488, 0.001, 156.31, 11, 24, 0),
    GCSolute("2-Octanone", "111-13-7", "SPB50", 383.850, 29.424, 76.479, 0.001, 128.21, 8, 16, 1),
    GCSolute("5-Nonanol", "623-93-8", "SPB50", 394.720, 29.894, 81.309, 0.001, 144.25, 9, 20, 1),
    GCSolute("1-Octanol", "111-87-5", "SPB50", 395.150, 30.178, 80.169, 0.001, 130.23, 8, 18, 1),
    GCSolute("2-Nonanol", "628-99-9", "SPB50", 397.330, 29.919, 81.323, 0.001, 144.25, 9, 20, 1),
    GCSolute("Dodecane", "112-40-3", "SPB50", 398.670, 29.71, 80.744, 0.001, 170.34, 12, 26, 0),
    GCSolute("5-Decanol", "5205-34-5", "SPB50", 410.510, 30.558, 84.657, 0.001, 158.28, 10, 22, 1),
    GCSolute("1-Nonanol", "143-8-8", "SPB50", 411.420, 30.925, 85.39, 0.001, 144.25, 9, 20, 1),
    GCSolute("Tridecane", "629-50-5", "SPB50", 414.140, 30.37, 85.071, 0.001, 184.36, 13, 28, 0),
    GCSolute("2-Decanone", "693-54-9", "SPB50", 416.290, 30.959, 85.186, 0.001, 156.27, 10, 20, 1),
    GCSolute("Tetradecane", "629-59-4", "SPB50", 428.660, 30.95, 89.343, 0.001, 198.39, 14, 30, 0),
    GCSolute("Pentadecane", "629-62-9", "SPB50", 442.340, 31.461, 93.281, 0.001, 212.42, 15, 32, 0),
    GCSolute("Heptane", "142-82-5", "Wax", 274.082, 23.664, 50.469, 0.001, 100.21, 7, 16, 0),
    GCSolute("Octane", "111-65-9", "Wax", 297.782, 25.016, 61.678, 0.001, 114.23, 8, 18, 0),
    GCSolute("Nonane", "111-84-2", "Wax", 319.319, 26.346, 67.749, 0.001, 128.26, 9, 20, 0),
    GCSolute("Decane", "124-18-5", "Wax", 339.194, 27.526, 74.429, 0.001, 142.29, 10, 22, 0),
    GCSolute("Undecane", "1120-21-4", "Wax", 357.625, 28.633, 76.138, 0.001, 156.31, 11, 24, 0),
    GCSolute("Dodecane", "112-40-3", "Wax", 374.850, 29.608, 81.796, 0.001, 170.34, 12, 26, 0),
    GCSolute("Tridecane", "629-50-5", "Wax", 391.000, 30.51, 87.457, 0.001, 184.36, 13, 28, 0),
    GCSolute("2-Octanone", "111-13-7", "Wax", 391.920, 32.266, 70.902, 0.001, 128.21, 8, 16, 1),
    GCSolute("Tetradecane", "629-59-4", "Wax", 406.230, 31.34, 92.855, 0.001, 198.39, 14, 30, 0),
    GCSolute("2-Octanol", "123-96-6", "Wax", 408.320, 30.775, 95.604, 0.001, 130.23, 8, 18, 1),
    GCSolute("5-Nonanol", "623-93-8", "Wax", 416.810, 31.212, 100.05, 0.001, 144.25, 9, 20, 1),
    GCSolute("Pentadecane", "629-62-9", "Wax", 420.620, 32.122, 98.572, 0.001, 212.42, 15, 32, 0),
    GCSolute("2-Nonanol", "628-99-9", "Wax", 422.610, 31.6, 102.93, 0.001, 144.25, 9, 20, 1),
    GCSolute("2-Decanone", "693-54-9", "Wax", 423.260, 33.907, 78.098, 0.001, 156.27, 10, 20, 1),
    GCSolute("1-Octanol", "111-87-5", "Wax", 428.550, 32.317, 97.29, 0.001, 130.23, 8, 18, 1),
    GCSolute("5-Decanol", "5205-34-5", "Wax", 430.410, 31.981, 107.11, 0.001, 158.28, 10, 22, 1),
    GCSolute("1-Nonanol", "143-8-8", "Wax", 442.190, 33.106, 102.05, 0.001, 144.25, 9, 20, 1),
)


def solutes_for_phase(phase: str) -> list[GCSolute]:
    """All vendored solutes on ``phase``, in table order."""
    if phase not in STATIONARY_PHASES:
        raise ValueError(f"unknown stationary phase {phase!r}; "
                         f"choose from {tuple(STATIONARY_PHASES)}")
    return [s for s in GC_SOLUTES if s.phase == phase]

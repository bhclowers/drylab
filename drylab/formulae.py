"""Pure chromatographic formulae.

Line-for-line port of ``hplc_formulae.js`` from mlibby/hplc_simulator (itself
derived from the Boswell/Carr/Stoll HPLC simulator). Every function is pure;
units are documented per function and follow the reference exactly, including
its unit-conversion constants.

Literature anchors carried over from the reference:

* Backpressure: Darcy/Kozeny-Carman form; Thompson & Carr, Anal. Chem. 2002,
  74, 4150-4159.
* Diffusion coefficient: Wilke & Chang, AIChE J. 1955, 1, 264-270.
* Eluent viscosity: Chen & Horvath 1993 (MeCN/water); JCA 1210 (2008) 30-44
  fit (MeOH/water).
"""

from __future__ import annotations

import math
from typing import Sequence

from .data import ViscosityParameters

__all__ = [
    "GradientNotImplementedError",
    "area",
    "association_parameter",
    "average_molar_volume",
    "backpressure",
    "chromatographic_flow_velocity",
    "diffusion_coefficient",
    "dwell_time",
    "dwell_volume",
    "eluent_viscosity",
    "hetp",
    "interstitial_flow_velocity",
    "k_prime",
    "kelvin",
    "open_tube_flow_velocity",
    "post_tubing_volume",
    "reduced_flow_velocity",
    "reduced_plate_height",
    "MILS_PER_MM",
    "mm_to_mils",
    "mils_to_mm",
    "sigma",
    "sigma_gradient",
    "tubing_time_broadening",
    "solvent_molecular_weight",
    "theoretical_plates",
    "total_porosity",
    "t_r",
    "void_time",
    "void_volume",
    "column_volume",
    "injected_amount",
]


class GradientNotImplementedError(NotImplementedError):
    """Raised where the JS reference silently returned NaN for gradient mode.

    The reference UI offered gradient elution but ``f.kPrime`` returned NaN;
    this port refuses loudly instead (charter §8: no silent NaN propagation).
    """


def kelvin(celsius: float) -> float:
    """Celsius -> Kelvin."""
    return celsius + 273.15


def area(diameter_mm: float) -> float:
    """Column cross-sectional area, mm^2, from diameter in mm."""
    return math.pi * (diameter_mm / 2.0) ** 2


def column_volume(area_mm2: float, length_mm: float) -> float:
    """Empty-tube column volume, mm^3."""
    return area_mm2 * length_mm


def total_porosity(interparticle: float, intraparticle: float) -> float:
    """Total porosity from inter- and intraparticle porosities (dimensionless)."""
    return interparticle + intraparticle * (1.0 - interparticle)


def void_volume(volume_mm3: float, total_porosity_: float) -> float:
    """Void (mobile-phase) volume, mL."""
    return volume_mm3 * total_porosity_ / 1000.0


def void_time(void_volume_ml: float, flow_rate_ml_min: float) -> float:
    """Column dead time t0, seconds."""
    return void_volume_ml / flow_rate_ml_min * 60.0


def open_tube_flow_velocity(flow_rate_ml_min: float, area_mm2: float) -> float:
    """Superficial (open-tube) linear velocity, cm/s."""
    return (flow_rate_ml_min / 60.0) / area_mm2 * 100.0


def chromatographic_flow_velocity(open_tube_v: float, total_porosity_: float) -> float:
    """Chromatographic linear velocity, cm/s."""
    return open_tube_v / total_porosity_


def interstitial_flow_velocity(open_tube_v: float, interparticle_porosity: float) -> float:
    """Interstitial linear velocity, cm/s."""
    return open_tube_v / interparticle_porosity


def association_parameter(solvent_fraction: float) -> float:
    """Wilke-Chang association parameter, linearly interpolated 2.6 (water) -> 1.9."""
    return (1.0 - solvent_fraction) * 0.7 + 1.9


def solvent_molecular_weight(solvent_fraction: float, solvent_mw: float) -> float:
    """Mixture molecular weight, g/mol, linear between water (18) and modifier."""
    return solvent_fraction * (solvent_mw - 18.0) + 18.0


def average_molar_volume(molar_volumes: Sequence[float]) -> float:
    """Arithmetic mean molar volume of the sample compounds, cm^3/mol.

    Raises ValueError on an empty sequence rather than dividing by zero.
    """
    if len(molar_volumes) == 0:
        raise ValueError("average_molar_volume: no compounds supplied")
    return sum(molar_volumes) / len(molar_volumes)


def eluent_viscosity(
    solvent_fraction: float, params: ViscosityParameters, temperature_c: float
) -> float:
    """Mobile-phase viscosity, cP, from the binary-mixture exponential fit."""
    k = kelvin(temperature_c)
    phi = solvent_fraction
    return math.exp(
        phi * (params.a + params.b / k)
        + (1.0 - phi) * (params.c + params.d / k)
        + phi * (1.0 - phi) * (params.e + params.f / k)
    )


def diffusion_coefficient(
    solvent_fraction: float,
    solvent_mw: float,
    temperature_c: float,
    eluent_viscosity_cp: float,
    molar_volumes: Sequence[float],
) -> float:
    """Average analyte diffusion coefficient, cm^2/s (Wilke-Chang).

    Note carried from the reference: the hard-coded constants may assume the
    primary solvent is water.
    """
    x = association_parameter(solvent_fraction)
    m = solvent_molecular_weight(solvent_fraction, solvent_mw)
    t = kelvin(temperature_c)
    v = average_molar_volume(molar_volumes)
    return 7.4e-8 * (math.sqrt(x * m) * t) / (eluent_viscosity_cp * v**0.6)


def reduced_flow_velocity(
    particle_size_um: float, interstitial_v: float, diffusion_coeff: float
) -> float:
    """Reduced (dimensionless) flow velocity nu."""
    return ((particle_size_um / 10000.0) * interstitial_v) / diffusion_coeff


def reduced_plate_height(a: float, b: float, c: float, reduced_v: float) -> float:
    """Reduced plate height h from the van Deemter/Knox form a + b/nu + c*nu."""
    return a + (b / reduced_v) + (c * reduced_v)


def hetp(particle_size_um: float, reduced_plate_height_: float) -> float:
    """Height equivalent to a theoretical plate, cm."""
    return particle_size_um / 10000.0 * reduced_plate_height_


def theoretical_plates(length_mm: float, hetp_cm: float) -> float:
    """Plate count N (dimensionless); column length converted mm -> cm."""
    return length_mm / 10.0 / hetp_cm


def backpressure(
    open_tube_v: float,
    length_mm: float,
    interparticle_porosity: float,
    particle_size_um: float,
    eluent_viscosity_cp: float,
) -> float:
    """Column backpressure, Pa (Darcy / Kozeny-Carman, coefficient 180)."""
    velocity = open_tube_v / 100.0  # cm/s -> m/s
    length = length_mm / 1000.0  # mm -> m
    viscosity = eluent_viscosity_cp / 1000.0  # cP -> Pa*s
    eps = interparticle_porosity
    dp = particle_size_um / 1_000_000.0  # um -> m
    numerator = velocity * length * viscosity * 180.0 * (1.0 - eps) ** 2
    return numerator / (eps**3 * dp**2)


def dwell_volume(mixing_volume_ul: float, non_mixing_volume_ul: float) -> float:
    """System dwell volume, uL."""
    return mixing_volume_ul + non_mixing_volume_ul


def dwell_time(dwell_volume_ul: float, flow_rate_ml_min: float) -> float:
    """System dwell time, minutes."""
    return (dwell_volume_ul / 1000.0) / flow_rate_ml_min


def post_tubing_volume(length_cm: float, diameter: float) -> float:
    """Post-column tubing volume, uL.

    Conversion constants (2.54e-5, 1e9) reproduced verbatim from the
    reference; its own comment questions the diameter unit ("mm ?"). Computed
    but not yet used in peak broadening — see issues.md (tubing broadening is
    commented out in the reference sigma).
    """
    length = length_cm / 100.0
    radius = (diameter * 2.54e-5) / 2.0
    return length * (math.pi * radius**2 * 1e9)


#: Tubing i.d. is stored in mils (0.001 inch) for reference fidelity -- the
#: Java applet's conversion constant identifies that unit. UIs should present
#: millimetres and convert with these named helpers rather than inlining 25.4.
MILS_PER_MM = 1000.0 / 25.4


def mm_to_mils(diameter_mm: float) -> float:
    """Tubing i.d. in mm -> mils (the reference's internal unit)."""
    return diameter_mm * MILS_PER_MM


def mils_to_mm(diameter_mils: float) -> float:
    """Tubing i.d. in mils -> mm (for display)."""
    return diameter_mils / MILS_PER_MM


def tubing_time_broadening(
    tubing_length_cm: float,
    tubing_diameter_mils: float,
    flow_rate_ml_min: float,
    diffusion_coeff: float,
) -> float:
    """Extra-column tubing contribution to peak variance, s^2 (Taylor-Aris).

    Ported from HPLCSimulatorApplet.java, which adds this term to sigma in
    BOTH elution modes. The JS port had it commented out — a port
    divergence; this project follows the Java ancestor (ruled 2026-08-04).
    Tubing diameter is in mils (0.001 inch), identified from the reference's
    0.00254 cm-per-mil conversion.

    Returns 0.0 for zero-length tubing (the default), so results with no
    tubing are unaffected.
    """
    if tubing_length_cm == 0.0:
        return 0.0
    if tubing_length_cm < 0:
        raise ValueError(
            f"tubing_time_broadening: length must be non-negative, got {tubing_length_cm}"
        )
    if tubing_diameter_mils <= 0:
        raise ValueError(
            "tubing_time_broadening: diameter must be positive, got "
            f"{tubing_diameter_mils}"
        )
    radius_cm = (tubing_diameter_mils * 0.00254) / 2.0
    open_tube_velocity = (flow_rate_ml_min / 60.0) / (math.pi * radius_cm**2)
    # Axial dispersion, cm^2
    z_broadening = (
        2.0 * diffusion_coeff * tubing_length_cm / open_tube_velocity
    ) + (
        (radius_cm**2 * tubing_length_cm * open_tube_velocity)
        / (24.0 * diffusion_coeff)
    )
    # -> mL^2 -> s^2
    volume_broadening = (math.sqrt(z_broadening) * math.pi * radius_cm**2) ** 2
    return ((math.sqrt(volume_broadening) / flow_rate_ml_min) * 60.0) ** 2


def k_prime(
    temperature_c: float,
    solvent_fraction: float,
    km: float,
    kb: float,
    sm: float,
    sb: float,
) -> float:
    """Isocratic retention factor k'.

    log10(k'_w) = km*T + kb ; S = -(sm*T + sb) ; k' = 10^(log10(k'_w) - S*phi).
    Gradient mode is not implemented (the JS reference returned NaN); callers
    selecting gradient elution must raise GradientNotImplementedError before
    reaching this function.
    """
    log_kprime_w = km * temperature_c + kb
    s1 = -1.0 * (sm * temperature_c + sb)
    return 10.0 ** (log_kprime_w - s1 * solvent_fraction)


def t_r(void_time_s: float, k_prime_: float) -> float:
    """Retention time, seconds."""
    return void_time_s * (1.0 + k_prime_)


def sigma(
    t_r_s: float,
    plates: float,
    time_constant_s: float,
    injection_volume_ul: float,
    flow_rate_ml_min: float,
    tubing_broadening_s2: float = 0.0,
) -> float:
    """Isocratic temporal peak standard deviation, seconds.

    Quadrature sum of column dispersion, detector time constant,
    injection-plug variance, and extra-column tubing (Java ancestor
    behavior; zero when no tubing is configured).
    """
    term1 = (t_r_s / math.sqrt(plates)) ** 2
    term2 = time_constant_s**2
    term3 = ((injection_volume_ul / 1000.0) / (flow_rate_ml_min / 60.0)) ** 2
    return math.sqrt(term1 + term2 + (1.0 / 12.0) * term3 + tubing_broadening_s2)


def sigma_gradient(
    void_time_s: float,
    k_prime_final: float,
    plates: float,
    time_constant_s: float,
    tubing_broadening_s2: float = 0.0,
    injection_volume_ul: float | None = None,
    flow_rate_ml_min: float | None = None,
) -> float:
    """Gradient-mode peak standard deviation, seconds.

    Uses k' at elution rather than the full retention time, per the
    reference. **Known gap reproduced deliberately:** the Java omits the
    injection-volume term here (its own source comment flags this), while
    its isocratic path includes it. Passing ``injection_volume_ul`` and
    ``flow_rate_ml_min`` adds that term back — off by default so validation
    matches the ancestor (ruled 2026-08-04: reproduce now, fix later behind
    a named switch).
    """
    term1 = ((void_time_s * (1.0 + k_prime_final)) / math.sqrt(plates)) ** 2
    term2 = time_constant_s**2
    total = term1 + term2 + tubing_broadening_s2
    if injection_volume_ul is not None:
        if flow_rate_ml_min is None:
            raise ValueError(
                "sigma_gradient: flow_rate_ml_min is required when "
                "injection_volume_ul is supplied"
            )
        total += (1.0 / 12.0) * (
            (injection_volume_ul / 1000.0) / (flow_rate_ml_min / 60.0)
        ) ** 2
    return math.sqrt(total)


def injected_amount(injection_volume_ul: float, concentration_um: float) -> float:
    """Injected amount w, in micromoles.

    ``injection_volume_ul`` / 1e6 converts uL to L; multiplying by a
    concentration in umol/L gives umol.
    """
    return (injection_volume_ul / 1_000_000.0) * concentration_um

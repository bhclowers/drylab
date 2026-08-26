"""Band-shape sandbox: broadening mechanisms and overload asymmetry.

This module is a PEDAGOGICAL EXTENSION, not a port (added 2026-08-17 on
Brian's ruling to build a band-broadening / tailing-fronting section for
the Wenzel unit). It deliberately does not touch the validated HPLC/GC
cores; it is a standalone single-solute sandbox with two parts:

1. :func:`van_deemter_components` — the textbook H(u) = A + B/u + C·u
   decomposition with each term built from its physical parameters
   (eddy/packing, longitudinal diffusion, mass transfer), so the notebook
   can draw the limbs separately. Pure definition; the "validation" is the
   closed-form optimum identity, asserted in validation/compare_bandshape.py.

2. :func:`simulate_plates` — a discrete plate (Craig-transfer) cascade with
   a NONLINEAR isotherm, producing tailing and fronting from first
   principles. Each transfer moves every plate's mobile phase forward one
   plate and re-equilibrates each plate against

       q(C) = a·C / (1 + b·C)

   where b > 0 is Langmuir curvature (convex isotherm: high concentrations
   migrate faster, so the band develops a self-sharpening FRONT and a
   diffuse REAR — tailing, with the peak maximum moving EARLIER as load
   rises) and b < 0 is anti-Langmuir (the mirror image: fronting, peak
   moving LATER with load). b = 0 is the linear isotherm, and there the
   cascade has an EXACT closed form: the elution profile at the column
   exit is the negative-binomial distribution

       P(n) = C(n-1, N-1) · p^N · (1-p)^(n-N),   p = 1/(1+k)

   (the probability that the N-th "advance" happens on transfer n), with
   mean N(1+k) and variance N·k·(1+k). That closed form is the module's
   oracle: the simulator run at b = 0 must reproduce it to floating-point
   accuracy, which pins the transport bookkeeping exactly; the nonlinear
   behaviour is then validated by invariants (mass conservation, asymmetry
   direction and retention shift versus curvature sign, and convergence to
   the linear limit as b -> 0), following the CE precedent of
   invariant-based validation where no external oracle exists.

Units are deliberately reduced: the time axis is the TRANSFER NUMBER
(one transfer = one plate volume of mobile phase), concentrations are in
units of the injected concentration, and the isotherm curvature enters
only through the dimensionless product chi = b·C0. Reduced units keep the
sandbox honest about what it is — a mechanism explorer, not an instrument
simulator — and make every displayed effect scale-free.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = [
    "VanDeemterTerms",
    "PlateSimResult",
    "van_deemter_components",
    "linear_elution_profile",
    "simulate_plates",
    "asymmetry_factor",
]


# --------------------------------------------------------------------------
# Part 1: van Deemter term builder
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class VanDeemterTerms:
    """H(u) decomposition on a shared velocity grid (all lengths in um).

    ``a_term`` is constant in u; ``b_term`` and the two C terms are arrays
    on ``u`` (cm/s). ``u_opt``/``h_min`` are the closed-form optimum of the
    SUMMED curve, u_opt = sqrt(B / (Cs + Cm)) and H_min = A + 2·sqrt(B·C),
    stated here so the figure can mark them and the validation can assert
    they coincide with the numerical minimum.
    """

    u: np.ndarray            # cm/s
    a_term: float            # um
    b_term: np.ndarray       # um
    cs_term: np.ndarray      # um
    cm_term: np.ndarray      # um
    total: np.ndarray        # um
    u_opt: float             # cm/s
    h_min: float             # um


def van_deemter_components(
    u: np.ndarray,
    particle_size_um: float,
    packing_lambda: float,
    diffusion_dm: float,
    obstruction_gamma: float,
    c_s_ms: float,
    c_m_ms: float,
) -> VanDeemterTerms:
    """Build the classic packed-column decomposition term by term.

    A = 2·lambda·dp                    (eddy diffusion / packing quality)
    B = 2·gamma·Dm                     (longitudinal diffusion)
    C = Cs + Cm                        (stationary + mobile mass transfer)

    ``diffusion_dm`` is in 1e-5 cm^2/s (so 1.0 is a typical small molecule
    in water/MeCN); ``c_s_ms``/``c_m_ms`` are the C coefficients in
    milliseconds, entered DIRECTLY rather than derived from d_f^2/D_s etc.
    — the Wenzel problems reason about the C terms as wholes ("what does a
    thicker film do to Cs?"), and a slider per whole keeps the mapping from
    lesson to control one-to-one. H is returned in um and u is cm/s, the
    units GC/LC method texts quote optima in.
    """
    u = np.asarray(u, dtype=float)
    if np.any(u <= 0.0):
        raise ValueError("velocities must be positive")
    a_um = 2.0 * packing_lambda * particle_size_um
    b_cm2_s = 2.0 * obstruction_gamma * diffusion_dm * 1e-5     # cm^2/s
    b_um = (b_cm2_s / u) * 1e4                                   # um
    c_s_um = (c_s_ms * 1e-3) * u * 1e4                           # um
    c_m_um = (c_m_ms * 1e-3) * u * 1e4
    total = a_um + b_um + c_s_um + c_m_um
    c_sum_s = (c_s_ms + c_m_ms) * 1e-3
    if c_sum_s > 0.0:
        u_opt = math.sqrt(b_cm2_s / c_sum_s)                     # cm/s
        h_min = a_um + 2.0 * math.sqrt(b_cm2_s * c_sum_s) * 1e4  # um
    else:
        u_opt = float("inf")
        h_min = a_um
    return VanDeemterTerms(
        u=u, a_term=a_um, b_term=b_um, cs_term=c_s_um, cm_term=c_m_um,
        total=total, u_opt=u_opt, h_min=h_min,
    )


# --------------------------------------------------------------------------
# Part 2: nonlinear plate cascade
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class PlateSimResult:
    """Elution profile at the column exit plus its summary measures.

    ``profile[n]`` is the amount (fraction of the injected mass) eluting on
    transfer ``transfers[n]``. Moments are computed from the profile itself
    — so under overload the APPARENT plate count ``n_apparent`` falls below
    the built-in N, which is a lesson, not a bug. ``recovered`` is the
    total mass on the profile; the simulator runs until less than 1e-9 of
    the injection remains on-column (or ``max_transfers``), and the
    shortfall from 1.0 is reported rather than hidden.
    """

    transfers: np.ndarray      # transfer index n
    profile: np.ndarray        # mass fraction eluting at n
    n_plates: int
    k_linear: float
    chi: float                 # b * C0 (signed, dimensionless curvature)
    t_max: float               # transfer of the profile maximum
    t_mean: float              # first moment
    sigma: float               # sqrt of second central moment
    n_apparent: float          # t_mean^2 / sigma^2
    asymmetry: float | None    # As = b/a at 10 % height; None if undefined
    recovered: float           # total mass on the profile (target 1.0)


def linear_elution_profile(n_plates: int, k: float,
                           transfers: np.ndarray) -> np.ndarray:
    """Exact linear-isotherm elution profile: negative binomial PMF.

    P(n) = C(n-1, N-1) p^N (1-p)^(n-N) with p = 1/(1+k), evaluated in log
    space (gammaln) so N = 200 stays finite. This is the module's oracle
    and the notebook's dashed "ideal" overlay — one function serving both,
    so the overlay IS the validated reference, not a lookalike.
    """
    if n_plates < 1:
        raise ValueError("need at least one plate")
    if k < 0.0:
        raise ValueError("retention factor cannot be negative")
    n = np.asarray(transfers, dtype=float)
    p = 1.0 / (1.0 + k)
    out = np.zeros_like(n)
    ok = n >= n_plates
    if k == 0.0:
        out[n == n_plates] = 1.0
        return out
    nn = n[ok]
    log_pmf = (
        _gammaln(nn) - _gammaln(nn - n_plates + 1.0) - _gammaln(float(n_plates))
        + n_plates * math.log(p) + (nn - n_plates) * math.log(1.0 - p)
    )
    out[ok] = np.exp(log_pmf)
    return out


def _gammaln(x):
    """log Gamma via math.lgamma, vectorized (no scipy — WASM ships without it)."""
    return np.vectorize(math.lgamma, otypes=[float])(x)


def _equilibrate(total: np.ndarray, k: float, chi: float) -> np.ndarray:
    """Mobile-phase concentration of each plate holding ``total`` mass.

    Per plate (unit mobile volume; stationary capacity folded into a = k):
    total = C + k·C/(1 + chi·C). chi = 0 gives C = total/(1+k) exactly —
    that branch is taken explicitly so the linear path is the closed form
    itself, not a quadratic that merely approaches it. Otherwise the
    positive root of  chi·C^2 + (1 + k - chi·total)·C - total = 0, via the
    numerically stable form (q-formula) so subtractive cancellation cannot
    corrupt small concentrations at large chi.
    """
    if chi == 0.0:
        return total / (1.0 + k)
    bq = 1.0 + k - chi * total
    disc = bq * bq + 4.0 * chi * total
    # disc = (1+k-chi*T)^2 + 4*chi*T >= 0 for all chi > -1/C_max regimes we
    # admit; the caller clamps chi so anti-Langmuir stays physical.
    sq = np.sqrt(np.maximum(disc, 0.0))
    # sign(bq) with the 0 -> +1 convention: np.sign(0) = 0 collapses the
    # q-formula to qf = 0 exactly where 1 + k = chi*total (a reachable
    # slider combination — caught 2026-08-17 when chi = 3 at k = 2 froze
    # the first plate and eluted nothing), so the tie must pick a branch.
    sgn = np.where(bq >= 0.0, 1.0, -1.0)
    qf = -0.5 * (bq + sgn * sq)
    with np.errstate(divide="ignore", invalid="ignore"):
        r1 = np.where(qf != 0.0, -total / np.where(qf == 0.0, 1.0, qf), 0.0)
        r2 = np.where(chi != 0.0, qf / chi, 0.0)
    c = np.where((r1 >= 0.0) & (r1 <= total + 1e-15), r1, r2)
    return np.maximum(c, 0.0)


def simulate_plates(
    n_plates: int,
    k: float,
    chi: float,
    injection_plates: int = 1,
    tail_tau: float = 0.0,
    max_transfers: int | None = None,
) -> PlateSimResult:
    """Run the cascade and return the exit profile with summary measures.

    ``chi`` = b·C0, the signed dimensionless curvature at the injected
    concentration; anti-Langmuir values are clamped to > -0.9 because the
    isotherm q = aC/(1+bC) loses meaning where 1 + b·C <= 0 (the caller is
    told via the clamp being visible in the result's ``chi``).
    ``injection_plates`` spreads the unit injection over the first plates
    (a wide injection is itself a broadening mechanism worth showing).
    ``tail_tau`` (in transfers) convolves the exit profile with a
    normalized exponential decay — the classic slow-desorption/extra-column
    tailing mechanism, kept SEPARATE from overload so the two kinds of
    tailing can be taught apart.
    """
    if n_plates < 1:
        raise ValueError("need at least one plate")
    if k < 0.0:
        raise ValueError("retention factor cannot be negative")
    if injection_plates < 1 or injection_plates > n_plates:
        raise ValueError("injection must cover 1..n_plates plates")
    chi = max(float(chi), -0.9)

    mean_n = n_plates * (1.0 + k)
    spread = math.sqrt(max(n_plates * k * (1.0 + k), 1.0))
    horizon = int(mean_n + 12.0 * spread + 10 * injection_plates + 50)
    if max_transfers is not None:
        horizon = min(horizon, int(max_transfers))

    # State: total mass per plate. The injected concentration defines the
    # concentration unit, so an injection spread over m plates puts 1/m in
    # each and chi refers to the concentration in ONE fully-loaded plate.
    total = np.zeros(n_plates, dtype=float)
    total[:injection_plates] = 1.0 / injection_plates

    exit_mass: list[float] = []
    remaining = 1.0
    for _ in range(horizon):
        c = _equilibrate(total, k, chi)
        # advance: every plate's mobile phase moves one plate forward; the
        # last plate's mobile phase is the detector signal this transfer.
        exit_mass.append(float(c[-1]))
        total = total - c
        total[1:] += c[:-1]
        remaining -= c[-1]
        if remaining < 1e-9:
            break

    profile = np.asarray(exit_mass)
    transfers = np.arange(1, profile.size + 1, dtype=float)

    if tail_tau > 0.0:
        # Normalized discrete exponential kernel; 'full' convolution keeps
        # every delayed contribution, then truncate where mass is spent.
        klen = int(10.0 * tail_tau) + 1
        kern = np.exp(-np.arange(klen) / tail_tau)
        kern /= kern.sum()
        profile = np.convolve(profile, kern)
        transfers = np.arange(1, profile.size + 1, dtype=float)

    recovered = float(profile.sum())
    if recovered > 0.0:
        w = profile / recovered
        t_mean = float((transfers * w).sum())
        sigma = float(math.sqrt(max(((transfers - t_mean) ** 2 * w).sum(), 0.0)))
    else:
        t_mean, sigma = float("nan"), float("nan")
    t_max = float(transfers[int(np.argmax(profile))]) if profile.size else float("nan")
    n_app = (t_mean / sigma) ** 2 if sigma and sigma > 0.0 else float("nan")

    return PlateSimResult(
        transfers=transfers, profile=profile, n_plates=n_plates,
        k_linear=k, chi=chi, t_max=t_max, t_mean=t_mean, sigma=sigma,
        n_apparent=n_app, asymmetry=asymmetry_factor(transfers, profile),
        recovered=recovered,
    )


def asymmetry_factor(x: np.ndarray, y: np.ndarray,
                     height_fraction: float = 0.1) -> float | None:
    """As = b/a at ``height_fraction`` of the maximum (USP-style, at 10 %).

    Crossings are located by linear interpolation on the OUTERMOST
    crossings each side of the maximum. None when either side never falls
    below the threshold inside the window (profile truncated), rather than
    a silently wrong number.
    """
    if y.size < 3:
        return None
    i_max = int(np.argmax(y))
    thr = float(y[i_max]) * height_fraction
    if thr <= 0.0:
        return None
    left = None
    for i in range(i_max, 0, -1):
        if y[i - 1] < thr <= y[i]:
            f = (thr - y[i - 1]) / (y[i] - y[i - 1])
            left = x[i - 1] + f * (x[i] - x[i - 1])
            break
    right = None
    for i in range(i_max, y.size - 1):
        if y[i] >= thr > y[i + 1]:
            f = (y[i] - thr) / (y[i] - y[i + 1])
            right = x[i] + f * (x[i + 1] - x[i])
            break
    if left is None or right is None:
        return None
    a = x[i_max] - left
    b = right - x[i_max]
    if a <= 0.0:
        return None
    return float(b / a)

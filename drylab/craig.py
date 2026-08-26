"""Craig countercurrent liquid-liquid extraction.

Implements Appendix 16 ("Countercurrent Separations") of *Analytical
Chemistry 2.0* by David Harvey, which in turn follows Craig, L. C.,
*J. Biol. Chem.* **1944**, 155, 519-534.

This module is deliberately INDEPENDENT of the HPLC simulator: it shares no
data, compounds or configuration with ``drylab.model``. It exists as a
standalone teaching model of the discrete separation that chromatographic
plate theory generalises.

Equations, numbered as in the source:

* **A16.1** - fraction remaining in the lower (stationary) phase::

      q = V_aq / (D * V_org + V_aq)

  With equal phase volumes this reduces to ``q = 1 / (D + 1)``. The fraction
  carried by the upper (mobile) phase is ``p = 1 - q``.

* **A16.2** - fraction of analyte in tube ``r`` after step ``n``::

      f(r, n) = n! / ((n - r)! r!) * p**r * q**(n - r)

  i.e. the binomial distribution. Within a tube, the upper phase holds
  ``p * f(r, n)`` and the lower phase ``q * f(r, n)``.

* **Elution past the last tube.** A real apparatus has a finite number of
  tubes, so once ``n`` exceeds the last tube index the binomial's tail has
  left the train. The fraction eluted is therefore::

      eluted = 1 - sum(f(r, n) for r in range(n_tubes))

  (This is how the original Efstathiou applet reports "Eluted A / Eluted B";
  its ``calculateFractions`` computes ``C(n,i) * D**i / (D+1)**n``, which is
  algebraically identical to A16.2 with ``p = D/(D+1)``, and splits each
  tube's total into ``p`` upper and ``q`` lower exactly as the appendix
  states.)

* Distribution moments::

      mean  mu    = n * p
      stdev sigma = sqrt(n * p * q)

  When both ``n*p`` and ``n*q`` exceed 5 the binomial is closely approximated
  by a normal distribution, licensing confidence intervals ``r = mu +/- z*sigma``
  and normal-approximation recoveries.

A note on the source text: in Example A16.1 the printed value ``q_B = 1/(4+1)
= 0.200`` is inconsistent with the stated ``D_B = 0.5`` and with the same
example's ``p_B = 0.333``. This module follows equation A16.1 and the p value
(``q_B = 1/(0.5+1) = 0.667``), which reproduces every tabulated fraction in
that example.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

__all__ = [
    "Analyte",
    "CraigResult",
    "fraction_lower",
    "fraction_upper",
    "tube_fraction",
    "distribution",
    "step_by_step",
    "moments",
    "normal_approximation_valid",
    "confidence_interval",
    "pooled_recovery",
    "separation_factor",
    "simulate",
]

#: Normal approximation requires n*p and n*q to exceed this (source: App. 16).
NORMAL_APPROX_MIN = 5.0


def fraction_lower(
    distribution_ratio: float,
    volume_upper: float = 1.0,
    volume_lower: float = 1.0,
) -> float:
    """q, the fraction remaining in the lower (stationary) phase [A16.1].

    ``q = V_aq / (D * V_org + V_aq)`` with the lower phase aqueous. Equal
    volumes give ``q = 1 / (D + 1)``.
    """
    if distribution_ratio < 0:
        raise ValueError(
            f"Distribution ratio must be non-negative, got {distribution_ratio}"
        )
    if volume_upper <= 0 or volume_lower <= 0:
        raise ValueError(
            "Phase volumes must be positive, got "
            f"upper={volume_upper}, lower={volume_lower}"
        )
    return volume_lower / (distribution_ratio * volume_upper + volume_lower)


def fraction_upper(
    distribution_ratio: float,
    volume_upper: float = 1.0,
    volume_lower: float = 1.0,
) -> float:
    """p, the fraction carried by the upper (mobile) phase; ``p = 1 - q``."""
    return 1.0 - fraction_lower(distribution_ratio, volume_upper, volume_lower)


def tube_fraction(r: int, n: int, p: float) -> float:
    """f(r, n), the fraction of analyte in tube r after step n [A16.2]."""
    if r < 0 or n < 0:
        raise ValueError(f"Tube and step indices must be non-negative, got r={r}, n={n}")
    if r > n:
        return 0.0  # analyte cannot outrun the mobile phase
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"p must lie in [0, 1], got {p}")
    return math.comb(n, r) * p**r * (1.0 - p) ** (n - r)


def distribution(n: int, p: float, n_tubes: int) -> np.ndarray:
    """Fractions in tubes 0..n_tubes-1 after step n, from the closed form."""
    if n_tubes < 1:
        raise ValueError(f"Need at least one tube, got {n_tubes}")
    return np.array([tube_fraction(r, n, p) for r in range(n_tubes)], dtype=float)


def step_by_step(n: int, p: float, n_tubes: int) -> np.ndarray:
    """Same distribution, built by simulating each extract/transfer cycle.

    Reproduces the process of Figure A16.1 rather than evaluating A16.2:
    extract (split each tube p/q between phases), then transfer every upper
    phase one tube along. Kept as an independent path so it can be checked
    against the closed form -- they must agree exactly.
    """
    if n_tubes < 1:
        raise ValueError(f"Need at least one tube, got {n_tubes}")
    tubes = np.zeros(n_tubes, dtype=float)
    tubes[0] = 1.0
    for _ in range(n):
        upper = tubes * p
        lower = tubes - upper
        moved = np.zeros_like(tubes)
        moved[1:] = upper[:-1]
        # upper[-1] leaves the apparatus; simulate() reports that as `eluted`.
        tubes = lower + moved
    return tubes


def moments(n: int, p: float) -> tuple[float, float]:
    """(mean, standard deviation) of the distribution: mu = np, sigma = sqrt(npq)."""
    q = 1.0 - p
    return n * p, math.sqrt(n * p * q)


def normal_approximation_valid(n: int, p: float) -> bool:
    """True when both n*p and n*q exceed 5, licensing the normal approximation."""
    return n * p > NORMAL_APPROX_MIN and n * (1.0 - p) > NORMAL_APPROX_MIN


def confidence_interval(n: int, p: float, z: float = 2.58) -> tuple[float, float]:
    """``r = mu +/- z*sigma``. Default z = 2.58 gives the 99% interval."""
    mu, sigma = moments(n, p)
    return mu - z * sigma, mu + z * sigma


def pooled_recovery(n: int, p: float, first_tube: int, last_tube: int) -> float:
    """Fraction of analyte in tubes ``first_tube..last_tube`` inclusive.

    Summed from the exact binomial rather than the normal approximation, so
    it stays correct when np or nq is small; the source's Example A16.3 uses
    the normal approximation and agrees to within its rounding.
    """
    if first_tube > last_tube:
        raise ValueError(
            f"first_tube must not exceed last_tube, got {first_tube} > {last_tube}"
        )
    lo = max(0, first_tube)
    hi = min(n, last_tube)
    if lo > hi:
        return 0.0
    return float(sum(tube_fraction(r, n, p) for r in range(lo, hi + 1)))


def separation_factor(recovery_b: float, recovery_a: float) -> float:
    """S(B,A) = R_B / R_A, as in Example A16.3."""
    if recovery_a == 0:
        raise ValueError("separation_factor: recovery of A is zero; ratio undefined")
    return recovery_b / recovery_a


@dataclass(frozen=True)
class Analyte:
    """One analyte in the extraction, identified by its distribution ratio D."""

    name: str
    distribution_ratio: float

    def q(self, volume_upper: float = 1.0, volume_lower: float = 1.0) -> float:
        return fraction_lower(self.distribution_ratio, volume_upper, volume_lower)

    def p(self, volume_upper: float = 1.0, volume_lower: float = 1.0) -> float:
        return fraction_upper(self.distribution_ratio, volume_upper, volume_lower)


@dataclass(frozen=True)
class AnalyteResult:
    """Per-analyte outcome of a countercurrent extraction."""

    name: str
    distribution_ratio: float
    p: float
    q: float
    fractions: np.ndarray  # per tube, index = tube number
    mean: float
    sigma: float
    normal_valid: bool
    #: Fraction carried past the last tube (0 while the band is still inside).
    eluted: float = 0.0

    @property
    def peak_tube(self) -> int:
        return int(np.argmax(self.fractions))


@dataclass(frozen=True)
class CraigResult:
    """Complete state of the apparatus after ``step`` transfers."""

    step: int
    n_tubes: int
    volume_upper: float
    volume_lower: float
    analytes: tuple[AnalyteResult, ...]

    def tube_numbers(self) -> np.ndarray:
        return np.arange(self.n_tubes)

    def resolution(self) -> float | None:
        """Rs = |mu2 - mu1| / (2*(sigma1 + sigma2)) for exactly two analytes.

        The chromatographic resolution expression applied to the tube axis;
        returns None unless there are exactly two analytes with non-zero width.
        """
        if len(self.analytes) != 2:
            return None
        a, b = self.analytes
        denom = 2.0 * (a.sigma + b.sigma)
        if denom == 0:
            return None
        return abs(b.mean - a.mean) / denom

    def operating_point(self) -> str:
        parts = ", ".join(
            f"{a.name}: D={a.distribution_ratio:g}" for a in self.analytes
        )
        return (
            f"{self.n_tubes} tubes | step {self.step} | {parts} | "
            f"V(upper):V(lower) = {self.volume_upper:g}:{self.volume_lower:g}"
        )


def simulate(
    analytes: Sequence[Analyte],
    step: int,
    n_tubes: int,
    volume_upper: float = 1.0,
    volume_lower: float = 1.0,
    use_step_by_step: bool = False,
) -> CraigResult:
    """Run the extraction to ``step`` and report every tube.

    Steps beyond ``n_tubes - 1`` are allowed: the binomial simply extends
    past the last tube, and that tail has left the apparatus. Each analyte's
    ``eluted`` field reports it, so the loss is visible rather than silent.
    """
    if not analytes:
        raise ValueError("simulate: at least one analyte is required")
    if n_tubes < 2:
        raise ValueError(f"simulate: need at least 2 tubes, got {n_tubes}")
    if step < 0:
        raise ValueError(f"simulate: step must be non-negative, got {step}")

    results = []
    for a in analytes:
        p = a.p(volume_upper, volume_lower)
        q = 1.0 - p
        fractions = (
            step_by_step(step, p, n_tubes)
            if use_step_by_step
            else distribution(step, p, n_tubes)
        )
        mu, sigma = moments(step, p)
        eluted = max(0.0, 1.0 - float(fractions.sum()))
        results.append(
            AnalyteResult(
                name=a.name,
                distribution_ratio=a.distribution_ratio,
                p=p,
                q=q,
                fractions=fractions,
                mean=mu,
                sigma=sigma,
                normal_valid=normal_approximation_valid(step, p),
                eluted=eluted,
            )
        )
    return CraigResult(
        step=step,
        n_tubes=n_tubes,
        volume_upper=volume_upper,
        volume_lower=volume_lower,
        analytes=tuple(results),
    )

"""Gradient elution: solvent-program mixing and band marching.

Port of ``calculateGradient()`` and the gradient branch of the retention
loop in ``HPLCSimulatorApplet.java`` (HPLC Simulator v1.1.3,
Boswell/Carr/Stoll), validated against a standalone harness built from that
source (``validation/HplcHarness.java``). Java is a validation-time oracle
only; nothing here depends on it at runtime.

Model, in brief:

1. The pump delivers the programmed composition. The **non-mixing volume**
   delays it as plug flow; the **mixing volume** acts as a well-stirred tank
   that smooths the step. ``mixer_profile`` simulates this over 1000 points
   and returns phi(t) at the column head.
2. Each analyte's band marches down the column in time steps. At each step
   the composition the band *currently sees* is looked up at the lagged time
   ``(total_time - integral) / 60``; k' follows from the LSS relation, and
   the band advances a fraction ``(dt/k')/t0`` of the column length.
   Elution is where fractional position reaches 1, located by linear
   interpolation.

Deviation from the reference (ruled 2026-08-04): the Java loop is
``while (!eluted)`` with no bound and hangs when a compound never elutes.
Here the march is bounded and raises :class:`NonElutingCompoundError`
naming the compound and conditions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

__all__ = [
    "GradientProgram",
    "GradientStop",
    "NonElutingCompoundError",
    "estimate_march_steps",
    "mixer_profile",
    "interpolate_profile",
    "march_band",
    "MarchResult",
]

#: Points in the simulated composition profile (reference: 1000).
PROFILE_POINTS = 1000
#: Band-march time steps per run span (reference: span / 1000).
MARCH_STEPS_PER_SPAN = 1000
#: Absolute backstop on march iterations, independent of any user budget.
#: The reference loop is unbounded; this bounds it even when budgeting is
#: disabled for validation.
MARCH_ITERATION_LIMIT = 2_000_000

#: Default per-compound step budget for interactive use. Measured context:
#: ordinary methods finish in under ~2,500 steps, and a legitimately slow
#: but usable method (weak final %B, strongly retained analyte) took ~28,000.
#: 100,000 leaves ~4x headroom over that while refusing runaway methods in
#: well under a second. Set SimulationInputs.march_step_budget to None to
#: disable (validation does this to reproduce the reference exactly).
DEFAULT_MARCH_STEP_BUDGET = 100_000

#: A cheap pre-check estimates steps as k'(strongest solvent) * t0 / dt.
#: Measured against real marches, that estimate runs from 0.24x to 1.0x of
#: the true count on pathological methods (and wildly UNDER-estimates benign
#: ones, which is why it may only be used to refuse, never to accept).
#: Refusing at 4x the budget means the true count is very likely over it.
PRECHECK_BUDGET_MULTIPLE = 4.0


class NonElutingCompoundError(RuntimeError):
    """A compound will not elute usefully under the requested conditions.

    Raised either by the cheap pre-check (before any marching) or by the
    step budget during the march. Names the compound and the numbers that
    made the method unviable, so the report says what did not line up
    instead of leaving an empty chromatogram unexplained.
    """

    def __init__(
        self,
        compound: str,
        k_prime: float,
        phi: float,
        iterations: int,
        *,
        predicted: bool = False,
    ):
        self.compound = compound
        self.k_prime = k_prime
        self.phi = phi
        self.iterations = iterations
        self.predicted = predicted
        if predicted:
            detail = (
                f"even at the strongest solvent in the program "
                f"({phi * 100:.1f}% B) its retention factor is k' = "
                f"{k_prime:,.0f}, so the band would need roughly "
                f"{iterations:,} simulation steps to cross the column"
            )
        else:
            detail = (
                f"the band stalled after {iterations:,} simulation steps "
                f"(k' = {k_prime:,.0f} at {phi * 100:.1f}% B)"
            )
        super().__init__(
            f"{compound!r} does not elute under these conditions: {detail}. "
            "Raise the final %B, extend the gradient time, lower the flow "
            "rate, or remove this analyte."
        )


@dataclass(frozen=True)
class GradientStop:
    """One row of the solvent program: ``time_min`` at ``percent_b``."""

    time_min: float
    percent_b: float


@dataclass(frozen=True)
class GradientProgram:
    """The programmed solvent composition, plus system dwell volumes.

    ``mixing_volume`` (uL) is the stirred-tank volume; ``non_mixing_volume``
    (uL) is pure plug delay. Both come from the reference's Gradient Options.
    """

    stops: tuple[GradientStop, ...] = (
        GradientStop(0.0, 5.0),
        GradientStop(10.0, 95.0),
    )
    mixing_volume: float = 200.0
    non_mixing_volume: float = 200.0

    def __post_init__(self) -> None:
        if len(self.stops) < 2:
            raise ValueError(
                f"GradientProgram needs at least 2 stops, got {len(self.stops)}"
            )
        times = [s.time_min for s in self.stops]
        if any(b <= a for a, b in zip(times, times[1:])):
            raise ValueError(
                f"GradientProgram stop times must strictly increase, got {times}"
            )
        for s in self.stops:
            if not 0.0 <= s.percent_b <= 100.0:
                raise ValueError(
                    f"GradientProgram %B must be within 0-100, got {s.percent_b}"
                )
        if self.mixing_volume < 0 or self.non_mixing_volume < 0:
            raise ValueError(
                "GradientProgram dwell volumes must be non-negative, got "
                f"mixing={self.mixing_volume}, non_mixing={self.non_mixing_volume}"
            )

    @classmethod
    def from_rows(
        cls,
        rows: Sequence[tuple[float, float]],
        mixing_volume: float = 200.0,
        non_mixing_volume: float = 200.0,
        sort_by_time: bool = False,
    ) -> "GradientProgram":
        """Build a program from (time_min, percent_b) rows.

        ``sort_by_time`` orders the rows by time before validating. Interactive
        editors let a user type a row out of order (a 7 min row added after a
        10 min row), which is a legitimate edit of a set of stops rather than
        an error -- a solvent program is inherently time-ordered, so sorting
        is the only sensible reading. Off by default so library callers still
        get a loud complaint about genuinely malformed input.
        """
        pairs = [(float(t), float(p)) for t, p in rows]
        if sort_by_time:
            pairs.sort(key=lambda tp: tp[0])
        return cls(
            stops=tuple(GradientStop(t, p) for t, p in pairs),
            mixing_volume=mixing_volume,
            non_mixing_volume=non_mixing_volume,
        )

    @staticmethod
    def duplicate_times(rows: Sequence[tuple[float, float]]) -> tuple[float, ...]:
        """Times appearing more than once - the one case sorting cannot fix."""
        seen: dict[float, int] = {}
        for t, _ in rows:
            seen[float(t)] = seen.get(float(t), 0) + 1
        return tuple(sorted(t for t, n in seen.items() if n > 1))

    @property
    def duration_min(self) -> float:
        return self.stops[-1].time_min

    def programmed_percent(self, time_min: float) -> float:
        """Programmed %B at the pump (no dwell effects), linearly interpolated.

        Held flat before the first and after the last stop, matching the
        reference's row-selection logic.
        """
        stops = self.stops
        if time_min <= stops[0].time_min:
            return stops[0].percent_b
        row_before = 0
        for j, s in enumerate(stops):
            if s.time_min <= time_min:
                row_before = j
            else:
                break
        if row_before >= len(stops) - 1:
            return stops[-1].percent_b
        a, b = stops[row_before], stops[row_before + 1]
        pos = (time_min - a.time_min) / (b.time_min - a.time_min)
        return pos * (b.percent_b - a.percent_b) + a.percent_b


def auto_end_time(program: GradientProgram, flow_rate: float) -> float:
    """Auto run length, seconds: program duration plus dwell flush.

    Reference: last stop time + (3*mixing + non-mixing) volume at flow.
    """
    if flow_rate <= 0:
        raise ValueError(f"auto_end_time: flow rate must be positive, got {flow_rate}")
    end = program.duration_min * 60.0
    end += (
        ((program.mixing_volume * 3 + program.non_mixing_volume) / 1000.0) / flow_rate
    ) * 60.0
    return end


def mixer_profile(
    program: GradientProgram, flow_rate: float, end_time_s: float
) -> np.ndarray:
    """Composition at the column head over the run.

    Returns an array of shape (PROFILE_POINTS, 2): column 0 is time in
    minutes, column 1 is %B. Simulates the non-mixing volume as plug delay
    and the mixing volume as a well-stirred tank, exactly as the reference.

    The stirred-tank recursion is inherently sequential (each step's mixer
    composition depends on the previous), so this loop is not vectorized.
    At 1000 points it costs well under a millisecond.
    """
    if flow_rate <= 0:
        raise ValueError(f"mixer_profile: flow rate must be positive, got {flow_rate}")
    n = PROFILE_POINTS
    out = np.empty((n, 2), dtype=float)
    mixer_composition = program.stops[0].percent_b
    final_time_min = end_time_s / 60.0
    time_step = final_time_min / (n - 1)
    flow_ul_per_min = flow_rate * 1000.0
    plug_delay_min = (program.non_mixing_volume / 1000.0) / flow_rate
    step_volume = flow_ul_per_min * time_step

    for i in range(n):
        time_min = i * time_step
        out[i, 0] = time_min
        out[i, 1] = mixer_composition

        solvent_b_in_mixer = mixer_composition * program.mixing_volume
        solvent_b_in_mixer -= step_volume * mixer_composition

        if time_min < plug_delay_min:
            incoming = program.stops[0].percent_b
        else:
            incoming = program.programmed_percent(time_min - plug_delay_min)

        solvent_b_in_mixer += step_volume * incoming

        # When a step displaces more than the mixer holds, the mixer is fully
        # swept and takes the incoming composition (reference behavior).
        if step_volume < program.mixing_volume:
            mixer_composition = solvent_b_in_mixer / program.mixing_volume
        else:
            mixer_composition = incoming

    return out


def interpolate_profile(profile: np.ndarray, time_min: float) -> float:
    """%B at ``time_min`` from a mixer profile, with linear extrapolation.

    Reproduces LinearInterpolationFunction: interpolate within range,
    extrapolate along the end segment's slope outside it.
    """
    t = profile[:, 0]
    y = profile[:, 1]
    if time_min < t[0]:
        slope = (y[1] - y[0]) / (t[1] - t[0])
        return slope * time_min + (y[0] - slope * t[0])
    if time_min > t[-1]:
        slope = (y[-1] - y[-2]) / (t[-1] - t[-2])
        return slope * time_min + (y[-1] - slope * t[-1])
    return float(np.interp(time_min, t, y))


@dataclass(frozen=True)
class MarchResult:
    """Outcome of marching one band down the column."""

    t_r: float  # s
    k_prime_final: float  # k' at elution
    #: (time_s, k') samples over the march — the reference's "retention
    #: factor vs time" plot.
    k_prime_track: np.ndarray
    #: (time_s, fractional position) samples — "band position vs time".
    position_track: np.ndarray


def estimate_march_steps(
    log_kw: float, s_value: float, void_time_s: float, profile: np.ndarray,
    end_time_s: float,
) -> tuple[float, float, float]:
    """Estimate march steps at the most favourable composition in the program.

    Returns ``(estimated_steps, k_prime_min, phi_max)``. Because it assumes
    the band always sees the strongest solvent the program ever reaches, it
    is optimistic for real runs — so it may be used to REFUSE a method
    (a method too slow even under this assumption is certainly too slow) but
    never to certify one as fast.
    """
    phi_max = float(profile[:, 1].max()) / 100.0
    k_min = 10.0 ** (log_kw - s_value * phi_max)
    dt = end_time_s / MARCH_STEPS_PER_SPAN
    return (k_min * void_time_s / dt), k_min, phi_max


def march_band(
    compound_name: str,
    log_kw: float,
    s_value: float,
    void_time_s: float,
    profile: np.ndarray,
    end_time_s: float,
    track: bool = False,
    step_budget: int | None = DEFAULT_MARCH_STEP_BUDGET,
) -> MarchResult:
    """March one analyte band to elution and return its retention time.

    ``log_kw`` is log10(k'_w) at the run temperature; ``s_value`` is S.
    Both are computed by the caller from the compound's LSST coefficients.

    Two guards, both raising NonElutingCompoundError rather than looping
    (ruled deviation from the reference):

    * a cheap pre-check that refuses obviously unviable methods before any
      marching, so a bad method fails instantly instead of slowly;
    * ``step_budget``, a per-compound cap during the march. Pass None to
      disable both and reproduce the reference exactly (validation does).

    MARCH_ITERATION_LIMIT remains an absolute backstop either way.
    """
    if void_time_s <= 0:
        raise ValueError(f"march_band: void time must be positive, got {void_time_s}")
    dt = (end_time_s - 0.0) / MARCH_STEPS_PER_SPAN
    if dt <= 0:
        raise ValueError(f"march_band: run span must be positive, got {end_time_s}")

    if step_budget is not None:
        estimated, k_min, phi_max = estimate_march_steps(
            log_kw, s_value, void_time_s, profile, end_time_s
        )
        if estimated > step_budget * PRECHECK_BUDGET_MULTIPLE:
            raise NonElutingCompoundError(
                compound_name, k_min, phi_max, int(estimated), predicted=True
            )

    hard_limit = (
        MARCH_ITERATION_LIMIT
        if step_budget is None
        else min(step_budget, MARCH_ITERATION_LIMIT)
    )

    integral = 0.0
    t_r_final = 0.0
    d_d = 0.0
    total_time = 0.0
    total_dead_time = 0.0
    x_position = 0.0
    last_x = [0.0, 0.0]
    last_ko = [0.0, 0.0]
    k_prime = 1.0
    phi = 0.0
    eluted = False
    iterations = 0

    k_track: list[tuple[float, float]] = []
    p_track: list[tuple[float, float]] = []

    while not eluted:
        iterations += 1
        if iterations > hard_limit:
            raise NonElutingCompoundError(
                compound_name, k_prime, phi, iterations - 1
            )

        phi = interpolate_profile(profile, (total_time - integral) / 60.0) / 100.0
        k_prime = 10.0 ** (log_kw - (s_value * phi))
        cur_val = dt / k_prime
        x_movement = cur_val / void_time_s

        if track:
            k_track.append((total_time, k_prime))
            p_track.append((total_time, x_position))

        if x_position >= 1.0:
            d_d = ((1.0 - last_x[0]) / (x_position - last_x[0])) * (
                total_dead_time - last_x[1]
            ) + last_x[1]
        else:
            last_x[0] = x_position
            last_x[1] = total_dead_time

        total_dead_time += x_movement * void_time_s

        if x_position >= 1.0:
            t_r_final = ((d_d - last_ko[0]) / (integral - last_ko[0])) * (
                total_time - last_ko[1]
            ) + last_ko[1]
        else:
            last_ko[0] = integral
            last_ko[1] = total_time

        total_time += dt + cur_val
        integral += cur_val

        if x_position > 1.0:
            eluted = True
            break

        x_position += x_movement

    return MarchResult(
        t_r=t_r_final,
        k_prime_final=k_prime,
        k_prime_track=np.array(k_track, dtype=float).reshape(-1, 2),
        position_track=np.array(p_track, dtype=float).reshape(-1, 2),
    )

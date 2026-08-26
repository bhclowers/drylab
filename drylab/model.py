"""Simulation model: inputs, derived state, and the explicit compute step.

The JS reference (``hplc_simulator.js``) wired every input through
getter/setter properties that re-ran ``update()`` on any assignment. In
marimo, cell reactivity provides that dependency propagation, so this port
replaces the observer graph with one explicit, pure pipeline::

    inputs = SimulationInputs(...)
    results = compute(inputs)

``Results`` carries both the numbers and the operating point that produced
them (charter: a certified number carries its operating point).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Mapping

import numpy as np

from . import formulae as f
from .gradient import (
    DEFAULT_MARCH_STEP_BUDGET,
    GradientProgram,
    NonElutingCompoundError,
    MarchResult,
    auto_end_time,
    interpolate_profile,
    march_band,
    mixer_profile,
)
from .data import (
    COLUMN_PRESETS,
    COMPOUNDS,
    DEFAULT_SAMPLE_MIX,
    SECONDARY_SOLVENTS,
    ColumnPreset,
    Solvent,
)


class ElutionMode(str, Enum):
    ISOCRATIC = "Isocratic"
    GRADIENT = "Gradient"


@dataclass(frozen=True)
class Column:
    """Column geometry/packing plus its derived quantities.

    Base fields mirror ColumnPreset (length/diameter mm, particle_size um);
    derived fields are computed by ``from_preset``/``derive`` — one source of
    truth, derived values never set directly.
    """

    name: str
    length: float
    diameter: float
    particle_size: float
    interparticle_porosity: float
    intraparticle_porosity: float
    van_deemter_a: float
    van_deemter_b: float
    van_deemter_c: float
    # Derived (mm^2, mm^3, -, mL):
    area: float = field(init=False, default=0.0)
    volume: float = field(init=False, default=0.0)
    total_porosity: float = field(init=False, default=0.0)
    void_volume: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        area = f.area(self.diameter)
        volume = f.column_volume(area, self.length)
        total_porosity = f.total_porosity(
            self.interparticle_porosity, self.intraparticle_porosity
        )
        void_volume = f.void_volume(volume, total_porosity)
        object.__setattr__(self, "area", area)
        object.__setattr__(self, "volume", volume)
        object.__setattr__(self, "total_porosity", total_porosity)
        object.__setattr__(self, "void_volume", void_volume)

    @classmethod
    def from_preset(cls, preset_name: str) -> "Column":
        try:
            p: ColumnPreset = COLUMN_PRESETS[preset_name]
        except KeyError as e:
            raise KeyError(
                f"Unknown column preset {preset_name!r}; "
                f"known presets: {sorted(COLUMN_PRESETS)}"
            ) from e
        return cls(
            name=p.name,
            length=p.length,
            diameter=p.diameter,
            particle_size=p.particle_size,
            interparticle_porosity=p.interparticle_porosity,
            intraparticle_porosity=p.intraparticle_porosity,
            van_deemter_a=p.van_deemter_a,
            van_deemter_b=p.van_deemter_b,
            van_deemter_c=p.van_deemter_c,
        )

    def with_overrides(self, **kwargs: float) -> "Column":
        """A copy with geometry overrides; derived fields recompute in __post_init__."""
        return replace(self, **kwargs)


@dataclass(frozen=True)
class SampleCompound:
    """An analyte in the injected mix, resolved against a modifier solvent.

    ``concentration`` is in micromolar (umol/L), matching the reference.
    """

    name: str
    concentration: float
    molar_volume: float
    km: float
    kb: float
    sm: float
    sb: float

    @classmethod
    def from_table(
        cls, name: str, solvent_name: str, concentration: float
    ) -> "SampleCompound":
        try:
            record = COMPOUNDS[name]
        except KeyError as e:
            raise KeyError(
                f"Unknown compound {name!r}; known compounds: {sorted(COMPOUNDS)}"
            ) from e
        try:
            rc = record.retention[solvent_name]
        except KeyError as e:
            raise KeyError(
                f"Compound {name!r} has no retention coefficients for solvent "
                f"{solvent_name!r}; available: {sorted(record.retention)}"
            ) from e
        return cls(
            name=name,
            concentration=concentration,
            molar_volume=record.molar_volume,
            km=rc.km,
            kb=rc.kb,
            sm=rc.sm,
            sb=rc.sb,
        )


@dataclass(frozen=True)
class SimulationInputs:
    """All user-settable inputs, defaults matching the JS reference."""

    elution_mode: ElutionMode = ElutionMode.ISOCRATIC
    flow_rate: float = 2.0  # mL/min
    initial_time: float = 0.0  # s
    final_time: float | None = None  # s; None -> auto (1.1 * max tR)
    injection_volume: float = 5.0  # uL
    mixing_volume: float = 200.0  # uL
    non_mixing_volume: float = 200.0  # uL
    noise: float = 2.0  # signal units, uniform half-amplitude (reference behavior: unused in model)
    plot_points: int = 3000
    post_tubing_diameter: float = 5.0  # reference marks unit uncertain ("mm ?")
    post_tubing_length: float = 0.0  # cm
    secondary_solvent: str = "Acetonitrile"
    signal_offset: float = 0.0
    solvent_percent: float = 50.0  # %B, 0-100
    temperature: float = 25.0  # Celsius
    time_constant: float = 0.1  # s
    # Gradient program; used only when elution_mode is GRADIENT.
    gradient_program: GradientProgram = field(default_factory=GradientProgram)
    # Add the injection-volume term to gradient sigma. Default False
    # reproduces the Java reference's known omission (ruled 2026-08-04).
    gradient_sigma_includes_injection: bool = False
    # Per-compound cap on gradient band-march steps, so an unviable method
    # fails fast and loudly instead of grinding. None disables the guard and
    # reproduces the reference exactly (used by validation).
    march_step_budget: int | None = DEFAULT_MARCH_STEP_BUDGET
    column_preset: str = "Agilent Zorbax SB-C18"
    # Geometry/packing overrides applied on top of the preset, e.g.
    # (("length", 150.0), ("particle_size", 5.0)). Empty -> preset as-is.
    column_overrides: tuple[tuple[str, float], ...] = ()
    sample_mix: tuple[tuple[str, float], ...] = DEFAULT_SAMPLE_MIX

    @property
    def solvent_fraction(self) -> float:
        return self.solvent_percent / 100.0


@dataclass(frozen=True)
class CompoundResult:
    """Per-compound outputs (seconds where temporal).

    In gradient mode ``k_prime`` is the retention factor at elution, and the
    optional tracks carry the band history recorded during the march.
    """

    name: str
    concentration: float
    k_prime: float
    t_r: float
    sigma: float
    w: float
    k_prime_track: np.ndarray | None = None
    position_track: np.ndarray | None = None
    #: False when the band elutes after the end of the simulated run — the
    #: number is still the reference's, but the condition is not viable.
    eluted_within_run: bool = True


@dataclass(frozen=True)
class PairMetrics:
    """Separation metrics for one adjacent pair of eluting compounds.

    ``resolution`` and ``alpha`` are None where undefined (zero combined
    width; non-positive earlier retention factor) rather than NaN, so a
    renderer must decide how to display the absence instead of silently
    formatting one.
    """

    earlier: str
    later: str
    resolution: float | None
    alpha: float | None


@dataclass(frozen=True)
class Results:
    """All derived outputs plus the operating point (`inputs`, `column`) that produced them."""

    inputs: SimulationInputs
    column: Column
    solvent: Solvent
    post_tubing_volume: float  # uL
    void_time: float  # s
    open_tube_flow_velocity: float  # cm/s
    chromatographic_flow_velocity: float  # cm/s
    interstitial_flow_velocity: float  # cm/s
    eluent_viscosity: float  # cP
    diffusion_coefficient: float  # cm^2/s
    reduced_flow_velocity: float
    reduced_plate_height: float
    backpressure: float  # Pa
    hetp: float  # cm
    theoretical_plates: float
    dwell_volume: float  # uL
    dwell_time: float  # min
    tubing_time_broadening: float  # s^2
    final_time: float  # s (resolved: auto or user-set)
    compounds: tuple[CompoundResult, ...]
    #: (time_min, %B) at the column head; gradient mode only, else None.
    gradient_profile: np.ndarray | None = None
    #: (compound, reason) for analytes excluded because they cannot elute
    #: under these conditions. Populated only when compute(...,
    #: skip_non_eluting=True); a skipped item is always a reported item.
    skipped_compounds: tuple[tuple[str, str], ...] = ()

    @property
    def non_viable_compounds(self) -> tuple[CompoundResult, ...]:
        """Compounds whose retention time falls outside the simulated run.

        The reference returns a retention time regardless (a band always
        reaches the outlet eventually), so the value is kept for fidelity;
        this surfaces the fact loudly instead of letting an off-scale peak
        vanish from the chromatogram (ruled 2026-08-04: report, do not hang).
        """
        return tuple(c for c in self.compounds if not c.eluted_within_run)

    def viability_report(self) -> str | None:
        """Report on analytes that were skipped or elute outside the run.

        Returns None when every analyte elutes within the simulated run.
        """
        lines: list[str] = []
        if self.skipped_compounds:
            names = ", ".join(name for name, _ in self.skipped_compounds)
            lines.append(
                f"{len(self.skipped_compounds)} analyte(s) excluded - they "
                f"cannot elute under these conditions: {names}."
            )
            # One full reason is enough detail; they usually share a cause.
            lines.append(self.skipped_compounds[0][1])
        bad = self.non_viable_compounds
        if bad:
            parts = ", ".join(
                f"{c.name} (tR = {c.t_r / 60.0:,.1f} min)" for c in bad
            )
            lines.append(
                f"{len(bad)} analyte(s) elute after the end of the "
                f"{self.final_time / 60.0:,.1f} min run: {parts}. "
                "Raise the final %B, extend the gradient, or remove them."
            )
        return " ".join(lines) if lines else None

    @property
    def backpressure_bar(self) -> float:
        return self.backpressure / 100000.0

    def operating_point_items(self) -> tuple[tuple[str, str], ...]:
        """Operating point as (parameter, value) pairs for table rendering."""
        i = self.inputs
        c = self.column
        return (
            ("Column", c.name),
            ("Geometry", f"{c.length:g} x {c.diameter:g} mm, {c.particle_size:g} um"),
            ("Flow rate", f"{i.flow_rate:g} mL/min"),
            ("Mobile phase", f"{i.solvent_percent:g}% {i.secondary_solvent} in water"),
            ("Temperature", f"{i.temperature:g} °C"),
            ("Injection volume", f"{i.injection_volume:g} uL"),
            ("Detector time constant", f"{i.time_constant:g} s"),
            (
                "Post-column tubing",
                f"{i.post_tubing_length:g} cm x "
                f"{f.mils_to_mm(i.post_tubing_diameter):.3g} mm i.d."
                if i.post_tubing_length
                else "none",
            ),
            ("Detector noise", f"{i.noise:g}" if i.noise else "off"),
            ("Elution mode", i.elution_mode.value),
        )

    def operating_point(self) -> str:
        """One-line operating point for stamping onto outputs (charter §4)."""
        i = self.inputs
        return (
            f"{self.column.name} {self.column.length:g}x{self.column.diameter:g} mm, "
            f"{self.column.particle_size:g} um | {i.flow_rate:g} mL/min | "
            f"{i.solvent_percent:g}% {i.secondary_solvent} | {i.temperature:g} °C | "
            f"inj {i.injection_volume:g} uL | tau {i.time_constant:g} s"
        )

    def pair_metrics(self) -> tuple["PairMetrics", ...]:
        """Adjacent-pair separation metrics, in elution order.

        One entry per compound after the first, pairing it with the compound
        that elutes immediately before it: resolution
        ``Rs = (t2 - t1) / (2 (sigma1 + sigma2))`` (the 4-sigma form, using
        the sigmas the model actually reports, extra-column terms included)
        and selectivity ``alpha = k2' / k1'`` (None when the earlier k' is
        not positive, e.g. an unretained marker — alpha is undefined there,
        and reporting a number would be an invention).

        This is presentation-supporting arithmetic, not new physics: every
        input is an already-validated field of ``CompoundResult``. It lives
        here rather than in the notebook so the on-screen table and the CSV
        export cannot disagree (added 2026-08-17 for the classroom
        resolution-triage exercise).
        """
        ordered = sorted(self.compounds, key=lambda c: c.t_r)
        out: list[PairMetrics] = []
        for earlier, later in zip(ordered, ordered[1:]):
            denom = 2.0 * (earlier.sigma + later.sigma)
            rs = (later.t_r - earlier.t_r) / denom if denom > 0.0 else None
            alpha = (
                later.k_prime / earlier.k_prime
                if earlier.k_prime > 0.0
                else None
            )
            out.append(
                PairMetrics(
                    earlier=earlier.name,
                    later=later.name,
                    resolution=rs,
                    alpha=alpha,
                )
            )
        return tuple(out)


def compute(
    inputs: SimulationInputs,
    track_bands: bool = False,
    skip_non_eluting: bool = False,
) -> Results:
    """Run the full derived-quantity pipeline for one set of inputs.

    Mirrors ``Simulator.update`` + ``updateCompounds`` in the reference,
    in the same order, as one pure function. In gradient mode the retention
    branch follows the Java ancestor's band-marching algorithm.

    ``track_bands`` records per-step k' and band-position histories
    (gradient mode only); off by default since it allocates per compound.

    ``skip_non_eluting`` (gradient only) turns a non-eluting analyte from a
    raised error into a recorded exclusion: the remaining analytes are still
    simulated and the skipped ones are named in ``Results.skipped_compounds``
    and ``viability_report()``. Off by default so library callers fail fast;
    interactive front-ends turn it on so one bad analyte does not blank the
    whole chromatogram.
    """
    try:
        solvent = SECONDARY_SOLVENTS[inputs.secondary_solvent]
    except KeyError as e:
        raise KeyError(
            f"Unknown secondary solvent {inputs.secondary_solvent!r}; "
            f"known: {sorted(SECONDARY_SOLVENTS)}"
        ) from e

    column = Column.from_preset(inputs.column_preset)
    if inputs.column_overrides:
        column = column.with_overrides(**dict(inputs.column_overrides))
    compounds = tuple(
        SampleCompound.from_table(name, solvent.name, conc)
        for name, conc in inputs.sample_mix
    )
    if not compounds:
        raise ValueError("compute: sample_mix is empty; at least one compound required")

    post_tubing_volume = f.post_tubing_volume(
        inputs.post_tubing_length, inputs.post_tubing_diameter
    )
    void_time = f.void_time(column.void_volume, inputs.flow_rate)
    open_v = f.open_tube_flow_velocity(inputs.flow_rate, column.area)
    chrom_v = f.chromatographic_flow_velocity(open_v, column.total_porosity)
    inter_v = f.interstitial_flow_velocity(open_v, column.interparticle_porosity)
    viscosity = f.eluent_viscosity(
        inputs.solvent_fraction, solvent.viscosity, inputs.temperature
    )
    molar_volumes = [c.molar_volume for c in compounds]
    diff = f.diffusion_coefficient(
        inputs.solvent_fraction,
        solvent.molecular_weight,
        inputs.temperature,
        viscosity,
        molar_volumes,
    )
    reduced_v = f.reduced_flow_velocity(column.particle_size, inter_v, diff)
    reduced_h = f.reduced_plate_height(
        column.van_deemter_a, column.van_deemter_b, column.van_deemter_c, reduced_v
    )
    bp = f.backpressure(
        open_v,
        column.length,
        column.interparticle_porosity,
        column.particle_size,
        viscosity,
    )
    hetp = f.hetp(column.particle_size, reduced_h)
    plates = f.theoretical_plates(column.length, hetp)
    is_gradient = inputs.elution_mode is ElutionMode.GRADIENT
    if is_gradient:
        dwell_vol = f.dwell_volume(
            inputs.gradient_program.mixing_volume,
            inputs.gradient_program.non_mixing_volume,
        )
    else:
        dwell_vol = f.dwell_volume(inputs.mixing_volume, inputs.non_mixing_volume)
    dwell_t = f.dwell_time(dwell_vol, inputs.flow_rate)

    tubing_broadening = f.tubing_time_broadening(
        inputs.post_tubing_length,
        inputs.post_tubing_diameter,
        inputs.flow_rate,
        diff,
    )

    compound_results = []
    gradient_profile = None
    skipped: list[tuple[str, str]] = []

    if is_gradient:
        program = inputs.gradient_program
        end_time = (
            auto_end_time(program, inputs.flow_rate)
            if inputs.final_time is None
            else inputs.final_time
        )
        gradient_profile = mixer_profile(program, inputs.flow_rate, end_time)
        for c in compounds:
            log_kw = c.km * inputs.temperature + c.kb
            s_value = -1.0 * (c.sm * inputs.temperature + c.sb)
            try:
                march = march_band(
                    c.name,
                    log_kw,
                    s_value,
                    void_time,
                    gradient_profile,
                    end_time,
                    track=track_bands,
                    step_budget=inputs.march_step_budget,
                )
            except NonElutingCompoundError as e:
                if not skip_non_eluting:
                    raise
                skipped.append((c.name, str(e)))
                continue
            sig = f.sigma_gradient(
                void_time,
                march.k_prime_final,
                plates,
                inputs.time_constant,
                tubing_broadening_s2=tubing_broadening,
                injection_volume_ul=(
                    inputs.injection_volume
                    if inputs.gradient_sigma_includes_injection
                    else None
                ),
                flow_rate_ml_min=(
                    inputs.flow_rate
                    if inputs.gradient_sigma_includes_injection
                    else None
                ),
            )
            compound_results.append(
                CompoundResult(
                    name=c.name,
                    concentration=c.concentration,
                    k_prime=march.k_prime_final,
                    t_r=march.t_r,
                    sigma=sig,
                    w=f.injected_amount(inputs.injection_volume, c.concentration),
                    k_prime_track=march.k_prime_track if track_bands else None,
                    position_track=march.position_track if track_bands else None,
                )
            )
        final_time = end_time
        compound_results = [
            replace(cr, eluted_within_run=cr.t_r <= final_time)
            for cr in compound_results
        ]
        if not compound_results:
            reasons = " ".join(reason for _, reason in skipped[:1])
            raise ValueError(
                "No analyte in this sample elutes under these conditions. "
                + reasons
            )
    else:
        for c in compounds:
            kp = f.k_prime(
                inputs.temperature, inputs.solvent_fraction, c.km, c.kb, c.sm, c.sb
            )
            tr = f.t_r(void_time, kp)
            sig = f.sigma(
                tr,
                plates,
                inputs.time_constant,
                inputs.injection_volume,
                inputs.flow_rate,
                tubing_broadening_s2=tubing_broadening,
            )
            compound_results.append(
                CompoundResult(
                    name=c.name,
                    concentration=c.concentration,
                    k_prime=kp,
                    t_r=tr,
                    sigma=sig,
                    w=f.injected_amount(inputs.injection_volume, c.concentration),
                )
            )
        if inputs.final_time is None:
            final_time = max(cr.t_r for cr in compound_results) * 1.1
        else:
            final_time = inputs.final_time

    return Results(
        inputs=inputs,
        column=column,
        solvent=solvent,
        post_tubing_volume=post_tubing_volume,
        void_time=void_time,
        open_tube_flow_velocity=open_v,
        chromatographic_flow_velocity=chrom_v,
        interstitial_flow_velocity=inter_v,
        eluent_viscosity=viscosity,
        diffusion_coefficient=diff,
        reduced_flow_velocity=reduced_v,
        reduced_plate_height=reduced_h,
        backpressure=bp,
        hetp=hetp,
        theoretical_plates=plates,
        dwell_volume=dwell_vol,
        dwell_time=dwell_t,
        tubing_time_broadening=tubing_broadening,
        final_time=final_time,
        compounds=compound_results,
        gradient_profile=gradient_profile,
        skipped_compounds=tuple(skipped),
    )


def compound_signal(
    results: Results, compound: CompoundResult, time_s: np.ndarray | float
) -> np.ndarray | float:
    """Detector signal for one compound at time(s) `time_s` (seconds).

    Vectorized port of ``Simulator.getCompoundSignal``. Returns the analyte
    concentration in the detector cell, in umol/L (= uM), given sample
    concentrations in umol/L. Includes the global signal offset, as the
    reference does.
    """
    flow = results.inputs.flow_rate / 60000.0  # mL/min -> L/s
    gauss = np.exp(-((np.asarray(time_s, dtype=float) - compound.t_r) ** 2)
                   / (2.0 * compound.sigma**2))
    return (compound.w / (np.sqrt(2.0 * np.pi) * compound.sigma * flow)) * gauss \
        + results.inputs.signal_offset


def time_grid(results: Results, n_points: int | None = None) -> np.ndarray:
    """Plotting time grid, seconds. Defaults to inputs.plot_points samples."""
    n = n_points if n_points is not None else results.inputs.plot_points
    if n < 2:
        raise ValueError(f"time_grid: need at least 2 points, got {n}")
    return np.linspace(results.inputs.initial_time, results.final_time, n)


def chromatogram(
    results: Results,
    n_points: int | None = None,
    rng: np.random.Generator | None = None,
) -> tuple[np.ndarray, Mapping[str, np.ndarray], np.ndarray]:
    """(time, per-compound signals, summed signal), optionally with noise.

    Noise (uniform in [-noise/2, +noise/2], applied to the summed trace only)
    requires an explicit rng so results stay reproducible; with rng=None the
    trace is noise-free.
    """
    t = time_grid(results, n_points)
    per_compound = {c.name: compound_signal(results, c, t) for c in results.compounds}
    total = np.sum(list(per_compound.values()), axis=0)
    if rng is not None and results.inputs.noise > 0:
        total = total + rng.uniform(
            -results.inputs.noise / 2.0, results.inputs.noise / 2.0, size=t.shape
        )
    return t, per_compound, total

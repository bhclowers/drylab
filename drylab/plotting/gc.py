"""Chromatogram plot for the isothermal GC model.

Deliberately independent of the HPLC chromatogram plot: the GC model has its
own result type and its own time base, and the two must be free to diverge.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Sequence

import numpy as np
import plotly.graph_objects as go

from ..gc import (
    CARRIER_GASES,
    GCColumn,
    GCConditions,
    GCPeak,
    GCSolute,
    average_linear_velocity,
    chromatogram,
    simulate_solute,
)
from .base import BasePlot
from .config import PlotConfig


class GCChromatogramPlot(BasePlot):
    """Summed Gaussian trace plus per-solute traces for GC peaks."""

    x_key = "time_min"
    y_key = "signal"

    def __init__(
        self,
        peaks: Sequence[GCPeak],
        column: GCColumn,
        conditions: GCConditions,
        holdup: float,
        config: PlotConfig | None = None,
        title: str | None = None,
        show_components: bool = True,
        show_sum: bool = True,
        program=None,
    ):
        super().__init__(config=config, title=title)
        self.peaks = list(peaks)
        self.column = column
        self.conditions = conditions
        self.holdup = holdup
        self.show_components = show_components
        self.show_sum = show_sum
        #: Optional GCProgram. When given, the oven temperature is drawn on a
        #: secondary axis, matching how the HPLC gradient plot overlays %B —
        #: the elution program is the thing that explains the peak spacing,
        #: so it belongs on the same time axis as the peaks.
        self.program = program

    def _operating_point(self) -> str:
        c, cond = self.column, self.conditions
        pout = (
            "vacuum"
            if cond.outlet_pressure == 0.0
            else f"{cond.outlet_pressure / 1e3:.1f} kPa"
        )
        # The thermal clause tells the truth about the mode: with a program
        # attached, stamping the oven-slider temperature as "isothermal"
        # would certify conditions the peaks were not produced under
        # (charter §4; caught 2026-08-17 when the programmed export began
        # carrying this stamp).
        if self.program is not None:
            temps_c = [t - 273.15 for t in self.program.temperatures]
            thermal = (
                f"programmed {temps_c[0]:g} -> {max(temps_c):g} degC"
            )
        else:
            thermal = f"{cond.temperature_k - 273.15:g} degC isothermal"
        return (
            f"{c.length:g} m x {c.diameter * 1e3:g} mm, "
            f"df {c.film_thickness * 1e6:g} um, {c.gas} | "
            f"{thermal} | "
            f"inlet {cond.inlet_pressure / 1e3:.1f} kPa -> outlet {pout} | "
            f"tM {self.holdup:.2f} s"
        )

    def time_axis(self) -> np.ndarray:
        """The time base (s) the figure is drawn on.

        Public (renamed from ``_time_axis``, 2026-08-17) so a trace CSV
        export can sample the identical axis the plot used — one authority
        for the grid, so the file and the figure cannot disagree.
        """
        if not self.peaks:
            return np.linspace(0.0, max(self.holdup * 2.0, 60.0), 500)
        last = max(p.retention_time + 6.0 * p.peak_width for p in self.peaks)
        first = min(
            self.holdup * 0.5,
            min(p.retention_time - 6.0 * p.peak_width for p in self.peaks),
        )
        n = max(500, min(4000, int((last - first) * 20)))
        return np.linspace(max(first, 0.0), last * 1.02, n)

    def _build(self, fig: go.Figure) -> None:
        cfg = self.config
        t = self.time_axis()
        t_min = t / 60.0

        total = np.asarray(chromatogram(self.peaks, t))
        if self.show_components:
            for p in self.peaks:
                fig.add_trace(
                    go.Scatter(
                        x=t_min,
                        y=chromatogram([p], t),
                        name=f"{p.solute.name} (k = {p.retention_factor:.2f})",
                        mode="lines",
                        line=dict(width=cfg.compound_trace_width),
                        # Filled to zero exactly as ChromatogramPlot draws the
                        # HPLC components, so the two chromatograms read the
                        # same way (ruled 2026-08-05).
                        fill="tozeroy",
                        opacity=cfg.compound_fill_opacity,
                        hovertemplate=(
                            f"{p.solute.name}: tR = {p.retention_time:.1f} s"
                            "<extra></extra>"
                        ),
                    )
                )
        if self.program is not None:
            self._add_program_axis(fig, t, t_min)
        if self.show_sum:
            fig.add_trace(
                go.Scatter(
                    x=t_min,
                    y=total,
                    name="Sum",
                    mode="lines",
                    line=dict(width=cfg.gc_sum_trace_width,
                              color=cfg.sum_trace_color),
                    hovertemplate=(
                        f"sum: %{{y:.{cfg.hover_decimals}f}} at %{{x:.2f}} min"
                        "<extra></extra>"
                    ),
                )
            )
        fig.add_vline(
            x=self.holdup / 60.0,
            line_dash="dot",
            line_width=1,
            annotation_text="tM",
            annotation_position="top",
        )


    def _add_program_axis(self, fig: go.Figure, t, t_min) -> None:
        """Draw the oven temperature on a secondary right-hand axis.

        Sampled on the SAME time base as the chromatogram so the ramp lines
        up with the peaks it produced; a separate grid would let the two
        drift apart visually and defeat the point of the overlay.
        """
        temps_c = [self.program.temperature(float(x)) - 273.15 for x in t]
        fig.add_trace(
            go.Scatter(
                x=t_min,
                y=temps_c,
                name="Oven temperature",
                mode="lines",
                line=dict(dash="dash", color="#888888"),
                yaxis="y2",
                hovertemplate="Oven: %{y:.1f} degC at %{x:.2f} min<extra></extra>",
            )
        )
        fig.update_layout(
            yaxis2=dict(
                title="Temperature (degC)",
                overlaying="y",
                side="right",
                showgrid=False,
            )
        )


class GCOverlayPlot(BasePlot):
    """Two or more GC runs on one time axis, for isothermal vs programmed.

    Takes already-simulated peak lists rather than conditions, so the caller
    decides what is being compared and this plot never re-runs the model.
    The comparison is only meaningful if the arms share a column and
    pneumatics — that is the caller's contract, the same precondition the
    HPLC compare view carries, and the notebook satisfies it by building
    both arms from one set of controls.
    """

    x_key = "time_min"
    y_key = "signal"

    def __init__(
        self,
        labeled_runs: Sequence[tuple[str, Sequence[GCPeak]]],
        column: GCColumn,
        config: PlotConfig | None = None,
        title: str | None = None,
        subtitle: str | None = None,
        n_points: int = 4000,
    ):
        if not labeled_runs:
            raise ValueError(
                "GCOverlayPlot: at least one (label, peaks) pair is required")
        if all(not peaks for _, peaks in labeled_runs):
            raise ValueError(
                "GCOverlayPlot: every arm is empty, so there is nothing to "
                "compare; check the run-time horizon")
        super().__init__(config=config, title=title)
        self.labeled_runs = list(labeled_runs)
        self.column = column
        self.subtitle = subtitle
        self.n_points = n_points

    def _operating_point(self) -> str:
        c = self.column
        base = (f"{c.length:g} m x {c.diameter * 1e3:g} mm, "
                f"df {c.film_thickness * 1e6:g} um, {c.gas}")
        return f"{base} | {self.subtitle}" if self.subtitle else base

    def _build(self, fig: go.Figure) -> None:
        cfg = self.config
        # One shared time axis so the arms are visually comparable: a
        # per-arm axis would rescale each run and hide the very difference
        # the plot exists to show.
        t_max = max((max(p.retention_time + 4.0 * p.peak_width for p in peaks)
                     for _, peaks in self.labeled_runs if peaks), default=1.0)
        t = np.linspace(0.0, t_max, self.n_points)
        t_min = t / 60.0
        for label, peaks in self.labeled_runs:
            y = (np.asarray(chromatogram(list(peaks), t)) if peaks
                 else np.zeros_like(t))
            fig.add_trace(
                go.Scatter(
                    x=t_min,
                    y=y,
                    name=label if peaks else f"{label} (no peaks)",
                    mode="lines",
                    line=dict(width=cfg.gc_sum_trace_width),
                    hovertemplate=(
                        f"{label}: %{{y:.{cfg.hover_decimals}f}} at "
                        f"%{{x:.2f}} min<extra></extra>"),
                )
            )


class GCGolayPlot(BasePlot):
    """Golay curve for one solute: plate height H vs average carrier
    velocity, one trace per carrier gas.

    The sweep variable is INLET PRESSURE — the quantity the section's
    controls actually set — and each point is placed at the average linear
    velocity that pressure produces for that gas, which is the x-axis a
    Golay plot is read on. Sweeping pressure rather than velocity keeps
    every point reachable from the real controls: a velocity grid would
    include operating points no inlet setting can produce.

    Each trace's minimum is marked, because the minimum (H_min at u_opt) is
    the whole point of the comparison: N2's sharp low optimum against H2's
    flat fast curve is the textbook argument for carrier choice, and this
    view exists to let that argument be read off directly (added 2026-08-17
    for the carrier-gas classroom exercise).

    All physics goes through :func:`drylab.gc.simulate_solute` — the same
    closed forms the chromatogram uses — so this plot can never disagree
    with the peaks (one authority, charter §9).
    """

    x_key = "carrier_velocity_cm_s"
    y_key = "gc_plate_height_mm"

    def __init__(
        self,
        solute: GCSolute,
        column: GCColumn,
        temperature_k: float,
        outlet_pressure: float,
        inlet_pressures: Sequence[float],
        gases: Sequence[str] | None = None,
        config: PlotConfig | None = None,
        title: str | None = None,
    ):
        pressures = [float(p) for p in inlet_pressures]
        if len(pressures) < 2:
            raise ValueError(
                f"Golay sweep needs at least 2 inlet pressures, got "
                f"{len(pressures)}")
        bad = [p for p in pressures if p <= outlet_pressure]
        if bad:
            raise ValueError(
                f"Inlet pressures must exceed the outlet pressure "
                f"({outlet_pressure:g} Pa); offending: {bad!r}")
        gases = list(gases) if gases is not None else list(CARRIER_GASES)
        unknown = [g for g in gases if g not in CARRIER_GASES]
        if unknown:
            raise KeyError(
                f"Unknown carrier gas(es) {unknown!r}; known: "
                f"{list(CARRIER_GASES)}")
        super().__init__(config=config, title=title)
        self.solute = solute
        self.column = column
        self.temperature_k = float(temperature_k)
        self.outlet_pressure = float(outlet_pressure)
        self.inlet_pressures = pressures
        self.gases = gases
        # One row per (gas, inlet pressure): computed once, read by both the
        # figure and data_columns so they cannot diverge.
        self._rows: list[dict] = []
        for gas in gases:
            col = replace(column, gas=gas)
            for pin in pressures:
                cond = GCConditions(
                    temperature_k=self.temperature_k,
                    inlet_pressure=pin,
                    outlet_pressure=self.outlet_pressure,
                )
                peak = simulate_solute(solute, col, cond)
                self._rows.append({
                    "gas": gas,
                    "inlet_pressure_kpa": pin / 1e3,
                    "u_cm_s": average_linear_velocity(col, cond) * 100.0,
                    "h_mm": peak.plate_height * 1e3,
                })

    def _operating_point(self) -> str:
        c = self.column
        pout = ("vacuum" if self.outlet_pressure == 0.0
                else f"{self.outlet_pressure / 1e3:.1f} kPa")
        return (
            f"{self.solute.name} on {self.solute.phase} | "
            f"{c.length:g} m x {c.diameter * 1e3:g} mm, "
            f"df {c.film_thickness * 1e6:g} um | "
            f"{self.temperature_k - 273.15:g} degC | "
            f"inlet {self.inlet_pressures[0] / 1e3:g}-"
            f"{self.inlet_pressures[-1] / 1e3:g} kPa -> outlet {pout}"
        )

    def _build(self, fig: go.Figure) -> None:
        for gas in self.gases:
            rows = [r for r in self._rows if r["gas"] == gas]
            rows.sort(key=lambda r: r["u_cm_s"])
            x = [r["u_cm_s"] for r in rows]
            y = [r["h_mm"] for r in rows]
            fig.add_trace(
                go.Scatter(
                    x=x, y=y, mode="lines+markers", name=gas,
                    hovertemplate=(
                        f"{gas}: H = %{{y:.4f}} mm at "
                        "%{x:.1f} cm/s<extra></extra>"),
                )
            )
            i_min = min(range(len(y)), key=y.__getitem__)
            fig.add_trace(
                go.Scatter(
                    x=[x[i_min]], y=[y[i_min]], mode="markers",
                    name=f"{gas} minimum", showlegend=False,
                    marker=dict(symbol="diamond", size=10),
                    hovertemplate=(
                        f"{gas} optimum: H_min = %{{y:.4f}} mm at "
                        "u_opt = %{x:.1f} cm/s<extra></extra>"),
                )
            )

    def data_columns(self) -> list[dict]:
        """The sweep in long form: one row per (gas, inlet pressure), with
        the velocity and plate height that figure point was drawn at. Long
        form because the x grid differs per gas (the same inlet pressure
        yields a different velocity for each carrier), so a wide table
        would misalign the rows.
        """
        return [dict(r) for r in self._rows]

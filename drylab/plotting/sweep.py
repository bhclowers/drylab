"""Parameter sweeps and condition overlays — the generalizable views.

``SweepPlot`` varies one ``SimulationInputs`` field across a range and plots
one or more named outputs against it (van Deemter curves, backpressure vs
flow, k' vs %B, ...). ``OverlayPlot`` draws several computed conditions'
summed chromatograms on one axis for comparison.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Callable, Mapping, Sequence

import numpy as np
import plotly.graph_objects as go

from ..model import Results, SimulationInputs, chromatogram, compute
from .base import BasePlot
from .config import PlotConfig

# Registry of sweepable outputs: name -> (axis-label key, extractor).
# Per-compound outputs expand to one trace per compound.
OUTPUTS: Mapping[str, tuple[str, Callable[[Results], float]]] = {
    "backpressure_bar": ("backpressure_bar", lambda r: r.backpressure_bar),
    "eluent_viscosity": ("eluent_viscosity", lambda r: r.eluent_viscosity),
    "hetp": ("hetp", lambda r: r.hetp),
    "theoretical_plates": ("theoretical_plates", lambda r: r.theoretical_plates),
    "reduced_plate_height": ("reduced_plate_height", lambda r: r.reduced_plate_height),
    "reduced_flow_velocity": ("reduced_flow_velocity", lambda r: r.reduced_flow_velocity),
    "void_time": ("time_s", lambda r: r.void_time),
}
PER_COMPOUND_OUTPUTS: Mapping[str, tuple[str, Callable[[Results, int], float]]] = {
    "k_prime": ("k_prime", lambda r, i: r.compounds[i].k_prime),
    "t_r": ("t_r_s", lambda r, i: r.compounds[i].t_r),
    "sigma": ("time_s", lambda r, i: r.compounds[i].sigma),
}
# Sweepable inputs: field name -> axis-label key.
SWEEPABLE_INPUTS: Mapping[str, str] = {
    "flow_rate": "flow_rate",
    "solvent_percent": "solvent_percent",
    "temperature": "temperature",
    "injection_volume": "injection_volume",
    "time_constant": "time_constant",
}


class SweepPlot(BasePlot):
    """Vary one input over ``values``; plot each requested output vs it."""

    def __init__(
        self,
        base_inputs: SimulationInputs,
        parameter: str,
        values: Sequence[float],
        outputs: Sequence[str],
        config: PlotConfig | None = None,
        title: str | None = None,
    ):
        if parameter not in SWEEPABLE_INPUTS:
            raise KeyError(
                f"Unknown sweep parameter {parameter!r}; "
                f"known: {sorted(SWEEPABLE_INPUTS)}"
            )
        if len(values) < 2:
            raise ValueError(f"Sweep needs at least 2 values, got {len(values)}")
        unknown = [
            o for o in outputs if o not in OUTPUTS and o not in PER_COMPOUND_OUTPUTS
        ]
        if unknown:
            raise KeyError(
                f"Unknown output(s) {unknown!r}; known: "
                f"{sorted(OUTPUTS) + sorted(PER_COMPOUND_OUTPUTS)}"
            )
        if not outputs:
            raise ValueError("SweepPlot: at least one output required")
        super().__init__(
            config=config,
            title=title or f"Sweep: {parameter}",
        )
        self.base_inputs = base_inputs
        self.parameter = parameter
        self.values = list(values)
        self.outputs = list(outputs)
        self.x_key = SWEEPABLE_INPUTS[parameter]
        # y label: single-output sweeps get the output's unit; multi-output
        # sweeps get a neutral label with units carried per trace name.
        if len(outputs) == 1 and outputs[0] in OUTPUTS:
            self.y_key = OUTPUTS[outputs[0]][0]
        elif len(outputs) == 1:
            self.y_key = PER_COMPOUND_OUTPUTS[outputs[0]][0]
        else:
            self.y_key = self.x_key  # replaced in _build for multi-output
        self._results = [
            compute(replace(base_inputs, **{parameter: v})) for v in self.values
        ]

    def _operating_point(self) -> str:
        # Operating point of the base condition, with the swept axis named.
        return (
            f"sweep of {self.parameter}; other conditions: "
            + self._results[0].operating_point()
        )

    def _build(self, fig: go.Figure) -> None:
        x = self.values
        multi = len(self.outputs) > 1
        for out in self.outputs:
            if out in OUTPUTS:
                label_key, getter = OUTPUTS[out]
                y = [getter(r) for r in self._results]
                name = self.config.axis_label(label_key) if multi else out
                fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=name))
            else:
                label_key, getter_pc = PER_COMPOUND_OUTPUTS[out]
                for i, cr in enumerate(self._results[0].compounds):
                    y = [getter_pc(r, i) for r in self._results]
                    fig.add_trace(
                        go.Scatter(
                            x=x, y=y, mode="lines+markers",
                            name=f"{out} - {cr.name}",
                        )
                    )
        if multi:
            fig.update_yaxes(title_text="Value (per-trace units)")

    def figure(self) -> go.Figure:
        fig = super().figure()
        if len(self.outputs) > 1:
            fig.update_yaxes(title_text="Value (per-trace units)")
        return fig

    def data_columns(self) -> dict[str, list]:
        """The sweep as columns: the swept parameter first, one column per
        plotted trace after it (per-compound outputs expand exactly as the
        figure does).

        This reads the same ``_results`` the figure was drawn from, so an
        export built on it cannot disagree with the plot (added 2026-08-17
        for the van Deemter fitting exercise; the caller serialises —
        keeping pandas out of the plotting package).
        """
        cols: dict[str, list] = {self.parameter: list(self.values)}
        for out in self.outputs:
            if out in OUTPUTS:
                _, getter = OUTPUTS[out]
                cols[out] = [getter(r) for r in self._results]
            else:
                _, getter_pc = PER_COMPOUND_OUTPUTS[out]
                for i, cr in enumerate(self._results[0].compounds):
                    cols[f"{out}_{cr.name}"] = [
                        getter_pc(r, i) for r in self._results
                    ]
        return cols


class OverlayPlot(BasePlot):
    """Summed chromatograms of several computed conditions on one axis."""

    x_key = "time_s"
    y_key = "signal"

    def __init__(
        self,
        labeled_results: Sequence[tuple[str, Results]],
        config: PlotConfig | None = None,
        title: str | None = "Condition overlay",
        n_points: int | None = None,
    ):
        if not labeled_results:
            raise ValueError("OverlayPlot: at least one (label, Results) required")
        super().__init__(config=config, title=title)
        self.labeled_results = list(labeled_results)
        self.n_points = n_points

    def _operating_point(self) -> str:
        return " | ".join(
            f"{label}: {r.operating_point()}" for label, r in self.labeled_results[:2]
        ) + (" | ..." if len(self.labeled_results) > 2 else "")

    def _build(self, fig: go.Figure) -> None:
        for label, r in self.labeled_results:
            t, _, total = chromatogram(r, n_points=self.n_points)
            fig.add_trace(go.Scatter(x=t, y=total, mode="lines", name=label))

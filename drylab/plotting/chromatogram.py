"""Chromatogram figure: per-compound Gaussians, summed trace, second-axis plot."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from ..model import Results, chromatogram
from .base import BasePlot
from .config import PlotConfig

# Quantities the reference offered as its "second plot", constant in
# isocratic mode (drawn as a flat reference line on a right-hand axis).
SECOND_PLOT_QUANTITIES = {
    "Solvent B Fraction": ("solvent_fraction", lambda r: r.inputs.solvent_fraction),
    "Backpressure": ("backpressure_bar", lambda r: r.backpressure_bar),
    "Mobile Phase Viscosity": ("eluent_viscosity", lambda r: r.eluent_viscosity),
}


class ChromatogramPlot(BasePlot):
    """The main detector-signal figure.

    Parameters
    ----------
    results:
        Output of :func:`drylab.compute`.
    second_plot:
        None, or one of ``SECOND_PLOT_QUANTITIES`` — adds a right-hand axis
        with that quantity (constant under isocratic elution, as in the
        reference UI).
    annotate_peaks:
        Label each apex with the compound name and tR.
    seed:
        If not None, adds the reference-style uniform noise to the summed
        trace with a seeded generator (reproducible).
    """

    x_key = "time_s"
    y_key = "signal"

    def __init__(
        self,
        results: Results,
        config: PlotConfig | None = None,
        title: str | None = "Chromatogram",
        second_plot: str | None = None,
        annotate_peaks: bool = True,
        n_points: int | None = None,
        seed: int | None = None,
    ):
        super().__init__(config=config, title=title)
        if second_plot is not None and second_plot not in SECOND_PLOT_QUANTITIES:
            raise KeyError(
                f"Unknown second_plot {second_plot!r}; "
                f"known: {sorted(SECOND_PLOT_QUANTITIES)}"
            )
        self.results = results
        self.second_plot = second_plot
        self.annotate_peaks = annotate_peaks
        self.n_points = n_points
        self.seed = seed

    def _operating_point(self) -> str:
        return self.results.operating_point()

    def _build(self, fig: go.Figure) -> None:
        cfg = self.config
        rng = np.random.default_rng(self.seed) if self.seed is not None else None
        t, per_compound, total = chromatogram(
            self.results, n_points=self.n_points, rng=rng
        )
        hover = f"%{{y:.{cfg.hover_decimals}f}}"

        for cr in self.results.compounds:
            fig.add_trace(
                go.Scatter(
                    x=t,
                    y=per_compound[cr.name],
                    name=cr.name,
                    mode="lines",
                    line=dict(width=cfg.compound_trace_width),
                    fill="tozeroy",
                    opacity=cfg.compound_fill_opacity,
                    hovertemplate=f"{cr.name}: {hover}<extra></extra>",
                )
            )
        fig.add_trace(
            go.Scatter(
                x=t,
                y=total,
                name="Sum",
                mode="lines",
                line=dict(width=cfg.sum_trace_width, color=cfg.sum_trace_color),
                hovertemplate=f"Sum: {hover}<extra></extra>",
            )
        )

        if self.annotate_peaks:
            for cr in self.results.compounds:
                apex = float(
                    np.interp(cr.t_r, t, per_compound[cr.name])
                )
                fig.add_annotation(
                    x=cr.t_r,
                    y=apex,
                    text=f"{cr.name}<br>tR={cr.t_r:.1f}s",
                    showarrow=True,
                    arrowhead=0,
                    ax=0,
                    ay=-30,
                    font=dict(size=cfg.operating_point_font_size),
                )

        if self.second_plot is not None:
            label_key, getter = SECOND_PLOT_QUANTITIES[self.second_plot]
            # In gradient mode the delivered solvent composition genuinely
            # varies with time, so draw the real profile rather than a
            # constant line.
            if (
                self.second_plot == "Solvent B Fraction"
                and self.results.gradient_profile is not None
            ):
                profile = self.results.gradient_profile
                fig.add_trace(
                    go.Scatter(
                        x=profile[:, 0] * 60.0,
                        y=profile[:, 1] / 100.0,
                        name="Solvent B Fraction",
                        mode="lines",
                        line=dict(dash="dash", color="#888888"),
                        yaxis="y2",
                        hovertemplate=f"Solvent B: {hover}<extra></extra>",
                    )
                )
                fig.update_layout(
                    yaxis2=dict(
                        title=cfg.axis_label(label_key),
                        overlaying="y",
                        side="right",
                        showgrid=False,
                    )
                )
                return
            value = getter(self.results)
            fig.add_trace(
                go.Scatter(
                    x=[t[0], t[-1]],
                    y=[value, value],
                    name=self.second_plot,
                    mode="lines",
                    line=dict(dash="dash", color="#888888"),
                    yaxis="y2",
                    hovertemplate=f"{self.second_plot}: {hover}<extra></extra>",
                )
            )
            fig.update_layout(
                yaxis2=dict(
                    title=cfg.axis_label(label_key),
                    overlaying="y",
                    side="right",
                    showgrid=False,
                )
            )

"""Gradient-specific views: solvent profile and per-band histories."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from ..model import Results
from .base import BasePlot
from .config import PlotConfig


class GradientProfilePlot(BasePlot):
    """Programmed vs delivered solvent composition over the run.

    The programmed trace is what the pump is told to do; the delivered trace
    is what reaches the column head after the non-mixing (plug) delay and
    mixing-volume (stirred-tank) smoothing. The gap between them is the
    system dwell — the thing that makes gradient methods transfer badly
    between instruments.
    """

    x_key = "time_min"
    y_key = "solvent_percent"

    def __init__(
        self,
        results: Results,
        config: PlotConfig | None = None,
        title: str | None = "Solvent program",
        show_programmed: bool = True,
    ):
        if results.gradient_profile is None:
            raise ValueError(
                "GradientProfilePlot requires a gradient-mode Results "
                "(gradient_profile is None; this run was isocratic)"
            )
        super().__init__(config=config, title=title)
        self.results = results
        self.show_programmed = show_programmed

    def _operating_point(self) -> str:
        return self.results.operating_point()

    def _build(self, fig: go.Figure) -> None:
        profile = self.results.gradient_profile
        t_min = profile[:, 0]
        fig.add_trace(
            go.Scatter(
                x=t_min,
                y=profile[:, 1],
                name="Delivered (column head)",
                mode="lines",
                line=dict(width=self.config.sum_trace_width),
                hovertemplate="%{y:.2f}% B at %{x:.2f} min<extra></extra>",
            )
        )
        if self.show_programmed:
            program = self.results.inputs.gradient_program
            programmed = [program.programmed_percent(t) for t in t_min]
            fig.add_trace(
                go.Scatter(
                    x=t_min,
                    y=programmed,
                    name="Programmed (pump)",
                    mode="lines",
                    line=dict(dash="dash", color="#888888"),
                    hovertemplate="%{y:.2f}% B at %{x:.2f} min<extra></extra>",
                )
            )
        # Mark each analyte's elution point on the profile.
        for cr in self.results.compounds:
            if not cr.eluted_within_run:
                continue
            t_elute_min = cr.t_r / 60.0
            fig.add_trace(
                go.Scatter(
                    x=[t_elute_min],
                    y=[float(np.interp(t_elute_min, t_min, profile[:, 1]))],
                    name=cr.name,
                    mode="markers",
                    marker=dict(size=8, symbol="circle"),
                    hovertemplate=(
                        f"{cr.name} elutes at %{{x:.2f}} min, "
                        "%{y:.1f}% B<extra></extra>"
                    ),
                )
            )


class BandTrackPlot(BasePlot):
    """Per-analyte band history during a gradient run.

    ``quantity='k_prime'`` shows the retention factor collapsing as the
    stronger solvent arrives; ``quantity='position'`` shows the band's
    fractional progress down the column. Both come from the marching loop
    and require ``compute(..., track_bands=True)``.
    """

    QUANTITIES = {
        "k_prime": ("k_prime", "k_prime_track", "Retention factor k'"),
        "position": ("position_fraction", "position_track", "Fractional column position"),
    }

    x_key = "time_s"

    def __init__(
        self,
        results: Results,
        quantity: str = "k_prime",
        config: PlotConfig | None = None,
        title: str | None = None,
        log_y: bool = False,
    ):
        if quantity not in self.QUANTITIES:
            raise KeyError(
                f"Unknown quantity {quantity!r}; known: {sorted(self.QUANTITIES)}"
            )
        tracked = [c for c in results.compounds if getattr(c, self.QUANTITIES[quantity][1]) is not None]
        if not tracked:
            raise ValueError(
                "BandTrackPlot requires band tracks; call "
                "compute(inputs, track_bands=True) for a gradient run"
            )
        label_key, attr, nice = self.QUANTITIES[quantity]
        super().__init__(config=config, title=title or nice)
        self.results = results
        self.quantity = quantity
        self._attr = attr
        self.y_key = label_key
        self.log_y = log_y

    def _operating_point(self) -> str:
        return self.results.operating_point()

    def _build(self, fig: go.Figure) -> None:
        for cr in self.results.compounds:
            track = getattr(cr, self._attr)
            if track is None or len(track) == 0:
                continue
            fig.add_trace(
                go.Scatter(
                    x=track[:, 0],
                    y=track[:, 1],
                    name=cr.name,
                    mode="lines",
                    line=dict(width=self.config.compound_trace_width),
                    hovertemplate=f"{cr.name}: %{{y:.4g}} at %{{x:.1f}} s<extra></extra>",
                )
            )
        if self.quantity == "position":
            fig.add_hline(
                y=1.0,
                line=dict(dash="dot", color="#888888"),
                annotation_text="column outlet",
                annotation_position="bottom right",
            )
        if self.log_y:
            fig.update_layout(yaxis=dict(type="log"))

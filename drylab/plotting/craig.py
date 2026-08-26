"""Stepped tube-distribution plot for the Craig countercurrent extraction."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from ..craig import CraigResult
from .base import BasePlot
from .config import PlotConfig


class CraigPlot(BasePlot):
    """Fraction of each analyte per tube, drawn as a stepped profile.

    A step (``hvh``) shape is used rather than a smooth line because the tube
    axis is genuinely discrete -- each tube holds one value, and a connecting
    curve would imply intermediate tubes that do not exist.
    """

    x_key = "tube_number"
    y_key = "analyte_fraction"

    def __init__(
        self,
        result: CraigResult,
        config: PlotConfig | None = None,
        title: str | None = None,
        show_normal: bool = False,
        fill: bool = True,
    ):
        super().__init__(config=config, title=title)
        self.result = result
        self.show_normal = show_normal
        self.fill = fill

    def _operating_point(self) -> str:
        return self.result.operating_point()

    def _build(self, fig: go.Figure) -> None:
        cfg = self.config
        tubes = self.result.tube_numbers()
        for a in self.result.analytes:
            fig.add_trace(
                go.Scatter(
                    x=tubes,
                    y=a.fractions,
                    name=f"{a.name} (D = {a.distribution_ratio:g})",
                    mode="lines",
                    line=dict(width=cfg.sum_trace_width, shape="hvh"),
                    fill="tozeroy" if self.fill else None,
                    opacity=1.0 if not self.fill else 0.85,
                    hovertemplate=(
                        f"{a.name}: %{{y:.{cfg.hover_decimals}f}} in tube %{{x}}"
                        "<extra></extra>"
                    ),
                )
            )
            # Normal approximation, shown only where the source licenses it
            # (n*p and n*q both > 5).
            if self.show_normal and a.normal_valid and a.sigma > 0:
                x = np.linspace(0, self.result.n_tubes - 1, 400)
                y = np.exp(-((x - a.mean) ** 2) / (2 * a.sigma**2)) / (
                    a.sigma * np.sqrt(2 * np.pi)
                )
                fig.add_trace(
                    go.Scatter(
                        x=x,
                        y=y,
                        name=f"{a.name}: normal approx.",
                        mode="lines",
                        line=dict(dash="dot", width=1.2),
                        hoverinfo="skip",
                        showlegend=True,
                    )
                )
        fig.update_layout(
            xaxis=dict(dtick=max(1, self.result.n_tubes // 20), rangemode="tozero"),
            yaxis=dict(rangemode="tozero"),
        )

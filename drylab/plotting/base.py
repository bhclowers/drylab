"""Base plot class: subclasses supply traces and axis keys, base owns layout."""

from __future__ import annotations

from abc import ABC, abstractmethod

import plotly.graph_objects as go

from .config import PlotConfig


class BasePlot(ABC):
    """Common Plotly figure scaffolding.

    Subclasses implement ``_build(fig)`` to add traces and any axis overrides;
    the base applies theme, titles, canonical axis labels, and (when the data
    carries one) the operating-point stamp — so every figure states the
    conditions that produced it.
    """

    #: canonical axis-label keys (see config.AXIS_LABELS); subclasses override
    x_key: str = "time_s"
    y_key: str = "signal"

    def __init__(self, config: PlotConfig | None = None, title: str | None = None):
        self.config = config or PlotConfig()
        self.title = title

    @abstractmethod
    def _build(self, fig: go.Figure) -> None:
        """Add traces (and any subclass-specific layout) to ``fig``."""

    def _operating_point(self) -> str | None:
        """Override to return the operating-point line to stamp, or None."""
        return None

    def operating_point(self) -> str | None:
        """The operating-point line this figure is stamped with, or None.

        Public so a CSV export built from the same plot object carries the
        identical stamp (charter §4: a certified number carries its
        operating point) — the figure and the file cannot drift apart.
        """
        return self._operating_point()

    def figure(self) -> go.Figure:
        cfg = self.config
        fig = go.Figure()
        self._build(fig)
        fig.update_layout(
            template=cfg.template,
            colorway=list(cfg.colorway),
            height=cfg.height,
            font=dict(size=cfg.font_size),
            margin=dict(cfg.margin),
            title=self.title,
            showlegend=cfg.show_legend,
            dragmode=cfg.dragmode,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        )
        # Title ONLY the primary axes. update_xaxes/update_yaxes without a
        # selector patch every axis, which clobbers a subclass's secondary
        # axis title (learnings.md 2026-08-04).
        fig.update_layout(
            xaxis=dict(title_text=cfg.axis_label(self.x_key)),
            yaxis=dict(title_text=cfg.axis_label(self.y_key)),
        )
        op = self._operating_point()
        if cfg.show_operating_point and op:
            # Reserve room so the stamp doesn't collide with the x title.
            fig.update_layout(
                margin=dict(
                    b=max(int(cfg.margin.get("b", 50)),
                          cfg.operating_point_margin_b)
                )
            )
            fig.add_annotation(
                text=op,
                xref="paper",
                yref="paper",
                x=0,
                y=cfg.operating_point_y,
                showarrow=False,
                font=dict(size=cfg.operating_point_font_size, color="#666666"),
                xanchor="left",
            )
        return fig

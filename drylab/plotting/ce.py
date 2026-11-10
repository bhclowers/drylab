"""Capillary-electrophoresis plots.

Two views, because an electromigration simulation is a space-AND-time
field and the two slices answer different questions:

- :class:`CEProfilePlot` — concentrations against POSITION at one instant.
  This is what shows zones forming, stacking, and the pH gradient. It has
  no chromatographic analogue.
- :class:`CEProfileAnimationPlot` — the same view over the whole run, with
  plotly animation frames and the plot's own time slider, so scrubbing is
  browser-side and cannot re-run notebook cells.
- :class:`CEElectropherogramPlot` — concentration against TIME at a fixed
  detector position. This is the familiar trace, and is deliberately built
  to read like ``ChromatogramPlot``: same filled component traces, same
  legend and operating-point treatment.

Both accept already-computed arrays rather than conditions, so neither can
trigger a simulation. That is what makes the notebook's time scrubbing free:
the expensive march happens once behind a run button, and the animation
frames are cut from the arrays it returned.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import plotly.graph_objects as go

from .base import BasePlot
from .config import PlotConfig


def ph_from_hydronium(c_h: np.ndarray) -> np.ndarray:
    """pH from hydronium concentration in mol/m^3.

    The solver works in mol/m^3 (SI) while pH is defined on mol/L, hence
    the factor of 1000. Getting this wrong shifts every pH by exactly 3
    units, which is the kind of error that looks like chemistry rather
    than arithmetic, so it is done in one named place.
    """
    c_h = np.asarray(c_h, dtype=float)
    if np.any(c_h <= 0.0):
        raise ValueError(
            "hydronium concentration must be positive to take a logarithm; "
            "got a minimum of %r mol/m^3" % float(np.min(c_h)))
    return -np.log10(c_h / 1000.0)


class _CEBase(BasePlot):
    """Shared operating-point stamp and secondary-axis overlay for CE."""

    def __init__(
        self,
        species_names: Sequence[str],
        config: PlotConfig | None = None,
        title: str | None = None,
        current_density: float | None = None,
        capillary_length_mm: float | None = None,
        overlay: str = "none",
    ):
        if overlay not in ("none", "ph", "conductivity"):
            raise ValueError(
                f"overlay must be 'none', 'ph' or 'conductivity', got "
                f"{overlay!r}")
        super().__init__(config=config, title=title)
        self.species_names = list(species_names)
        self.current_density = current_density
        self.capillary_length_mm = capillary_length_mm
        self.overlay = overlay

    def _operating_point(self) -> str | None:
        bits = []
        if self.capillary_length_mm is not None:
            bits.append(f"{self.capillary_length_mm:g} mm capillary")
        if self.current_density is not None:
            bits.append(f"j = {self.current_density:.1f} A/m2")
        return " | ".join(bits) if bits else None

    def _add_overlay(self, fig: go.Figure, x, values) -> None:
        """Draw pH or conductivity on a secondary right-hand axis.

        Same pattern as the GC oven-ramp overlay: sampled on the SAME axis
        as the primary traces so the two cannot drift apart visually.
        """
        if self.overlay == "none":
            return
        label = "pH" if self.overlay == "ph" else "Conductivity (S/m)"
        fig.add_trace(
            go.Scatter(
                x=x,
                y=np.asarray(values, dtype=float),
                name=label,
                mode="lines",
                line=dict(dash="dash", color="#888888"),
                yaxis="y2",
                hovertemplate=f"{label}: %{{y:.3f}}<extra></extra>",
            )
        )
        fig.update_layout(
            yaxis2=dict(title=label, overlaying="y", side="right",
                        showgrid=False)
        )


class CEProfilePlot(_CEBase):
    """Concentrations against position at one instant, optionally with pH."""

    x_key = "position_mm"
    y_key = "concentration_mM"

    def __init__(self, position_mm, concentrations, species_names,
                 overlay_values=None, hidden=(), **kwargs):
        super().__init__(species_names, **kwargs)
        #: Names drawn but starting hidden in the legend. The background
        #: electrolyte runs at 50-100 mM against analytes at ~2 mM, so
        #: showing everything on one axis crushes the analyte peaks into
        #: the baseline -- they are a 2% feature. Hiding the BGE by default
        #: rescales the axis to the analytes, which is what an
        #: electropherogram actually shows; the traces stay one legend
        #: click away rather than being discarded.
        self.hidden = set(hidden)
        self.position_mm = np.asarray(position_mm, dtype=float)
        self.concentrations = np.asarray(concentrations, dtype=float)
        if self.concentrations.shape[0] != len(self.species_names):
            raise ValueError(
                f"got {self.concentrations.shape[0]} concentration rows for "
                f"{len(self.species_names)} species names; the caller has "
                f"sliced the field inconsistently")
        if self.concentrations.shape[1] != self.position_mm.size:
            raise ValueError(
                f"concentration grid is {self.concentrations.shape[1]} wide "
                f"but the position axis has {self.position_mm.size} points")
        self.overlay_values = overlay_values

    def _build(self, fig: go.Figure) -> None:
        cfg = self.config
        for name, row in zip(self.species_names, self.concentrations):
            fig.add_trace(
                go.Scatter(
                    x=self.position_mm,
                    y=row,
                    name=name,
                    mode="lines",
                    visible=("legendonly" if name in self.hidden else True),
                    line=dict(width=cfg.compound_trace_width),
                    fill="tozeroy",
                    opacity=cfg.compound_fill_opacity,
                    hovertemplate=(
                        f"{name}: %{{y:.4g}} mM at %{{x:.2f}} mm"
                        "<extra></extra>"),
                )
            )
        if self.overlay_values is not None:
            self._add_overlay(fig, self.position_mm, self.overlay_values)


class CEProfileAnimationPlot(CEProfilePlot):
    """:class:`CEProfilePlot` over the WHOLE run, scrubbed inside the plot.

    Takes the full saved field (species x position x time) and emits plotly
    animation frames with the plot's own time slider and play button.
    Scrubbing is pure browser-side JavaScript: no Python re-executes, so the
    surrounding notebook UI cannot rebuild (and reset) mid-drag, which is
    exactly what happened when the slice index was a marimo slider upstream
    of this figure (issues.md 2026-11-10).

    The saved slices are thinned to at most ``max_frames`` evenly spaced
    frames, first and last always kept: a 60 s run saves ~1500 slices, and a
    figure carrying all of them is slow to build and to animate for no
    visible gain. Frame arrays are cast to float32, halving the serialized
    payload; the whole app's output must stay under marimo's
    output_max_bytes (8 MB default), and the other tabs already use most
    of it (issues.md 2026-11-10). Both y axes get FIXED ranges computed over every frame
    (visible species only, on the left), because per-frame autoranging makes
    the axes breathe while the movie plays and reads as data motion.
    Showing a hidden BGE trace via the legend can therefore clip it;
    double-clicking the y axis re-autoscales, and the panel text says so.
    """

    def __init__(self, position_mm, concentrations_xt, species_names,
                 times_s, overlay_values_xt=None, max_frames=80, **kwargs):
        conc = np.asarray(concentrations_xt, dtype=float)
        times = np.asarray(times_s, dtype=float)
        if conc.ndim != 3:
            raise ValueError(
                f"concentrations_xt must be (species, position, time), got "
                f"shape {conc.shape}")
        if conc.shape[2] != times.size:
            raise ValueError(
                f"concentrations_xt has {conc.shape[2]} time slices but "
                f"times_s has {times.size}")
        if max_frames < 2:
            raise ValueError(f"max_frames must be >= 2, got {max_frames}")
        ov = None if overlay_values_xt is None else np.asarray(
            overlay_values_xt, dtype=float)
        if ov is not None and ov.shape != conc.shape[1:]:
            raise ValueError(
                f"overlay_values_xt must be (position, time) = "
                f"{conc.shape[1:]}, got {ov.shape}")
        idx = np.unique(np.round(np.linspace(
            0, times.size - 1, min(int(max_frames), times.size))).astype(int))
        self.frame_indices = idx
        self.frame_times_s = times[idx]
        self.conc_xt = conc
        self.overlay_xt = ov
        super().__init__(
            position_mm, conc[:, :, idx[0]], species_names,
            overlay_values=(None if ov is None else ov[:, idx[0]]),
            **kwargs)

    def _build(self, fig: go.Figure) -> None:
        super()._build(fig)  # traces for the first frame, overlay last
        shown = [i for i, n in enumerate(self.species_names)
                 if n not in self.hidden]
        sub = self.conc_xt[shown][:, :, self.frame_indices]
        y_max = float(sub.max()) if shown else float(
            self.conc_xt[:, :, self.frame_indices].max())
        fig.update_layout(yaxis=dict(range=[0.0, 1.06 * max(y_max, 1e-12)]))
        if self.overlay_xt is not None:
            ov = self.overlay_xt[:, self.frame_indices]
            lo, hi = float(ov.min()), float(ov.max())
            pad = 0.05 * max(hi - lo, 1e-9)
            fig.update_layout(
                yaxis2=dict(range=[lo - pad, hi + pad]))
        frames = []
        conc32 = self.conc_xt.astype(np.float32)
        ov32 = (None if self.overlay_xt is None
                else self.overlay_xt.astype(np.float32))
        for k, t in zip(self.frame_indices, self.frame_times_s):
            data = [go.Scatter(y=conc32[i, :, k])
                    for i in range(len(self.species_names))]
            if ov32 is not None:
                data.append(go.Scatter(y=ov32[:, k]))
            frames.append(go.Frame(name=f"{t:.2f}", data=data))
        fig.frames = frames
        steps = [dict(method="animate", label=f.name,
                      args=[[f.name],
                            dict(mode="immediate",
                                 frame=dict(duration=0, redraw=False),
                                 transition=dict(duration=0))])
                 for f in frames]
        fig.update_layout(
            sliders=[dict(
                active=0, steps=steps, x=0.0, len=1.0, pad=dict(t=28),
                currentvalue=dict(prefix="t = ", suffix=" s",
                                  font=dict(size=13)),
                font=dict(size=9),
            )],
            updatemenus=[dict(
                type="buttons", direction="left", x=0.0, y=-0.62,
                xanchor="left", yanchor="top", pad=dict(t=0),
                buttons=[
                    dict(label="Play", method="animate",
                         args=[None, dict(mode="immediate", fromcurrent=True,
                                          frame=dict(duration=60,
                                                     redraw=False),
                                          transition=dict(duration=0))]),
                    dict(label="Pause", method="animate",
                         args=[[None], dict(mode="immediate",
                                            frame=dict(duration=0,
                                                       redraw=False),
                                            transition=dict(duration=0))]),
                ])],
        )


class CEElectropherogramPlot(_CEBase):
    """Concentration against time at a fixed detector position."""

    x_key = "time_s"
    y_key = "concentration_mM"

    def __init__(self, times_s, traces, species_names,
                 detector_position_mm=None, hidden=(), **kwargs):
        super().__init__(species_names, **kwargs)
        self.hidden = set(hidden)
        self.times_s = np.asarray(times_s, dtype=float)
        self.traces = np.asarray(traces, dtype=float)
        if self.traces.shape[0] != len(self.species_names):
            raise ValueError(
                f"got {self.traces.shape[0]} traces for "
                f"{len(self.species_names)} species names")
        if self.traces.shape[1] != self.times_s.size:
            raise ValueError(
                f"traces have {self.traces.shape[1]} samples but the time "
                f"axis has {self.times_s.size}")
        self.detector_position_mm = detector_position_mm

    def _operating_point(self) -> str | None:
        base = super()._operating_point()
        if self.detector_position_mm is None:
            return base
        det = f"detector at {self.detector_position_mm:.1f} mm"
        return f"{base} | {det}" if base else det

    def _build(self, fig: go.Figure) -> None:
        cfg = self.config
        for name, row in zip(self.species_names, self.traces):
            fig.add_trace(
                go.Scatter(
                    x=self.times_s,
                    y=row,
                    name=name,
                    mode="lines",
                    visible=("legendonly" if name in self.hidden else True),
                    line=dict(width=cfg.compound_trace_width),
                    fill="tozeroy",
                    opacity=cfg.compound_fill_opacity,
                    hovertemplate=(
                        f"{name}: %{{y:.4g}} mM at %{{x:.2f}} s"
                        "<extra></extra>"),
                )
            )

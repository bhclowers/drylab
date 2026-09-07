"""Figures for the band-shape sandbox (mechanism builder + overload shapes).

Deliberately independent of the HPLC/GC plots, like every section's
plotting module: the sandbox has its own reduced units and must be free to
diverge. Both classes expose ``data_columns()`` and inherit the public
``operating_point()``, so their CSV exports are built from the same
instance as the figure (the 2026-08-17 export rule).
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from ..bandshape import (
    PlateSimResult,
    VanDeemterTerms,
    asymmetry_factor,
    linear_elution_profile,
    van_deemter_components,
)
from .base import BasePlot
from .config import PlotConfig


class VanDeemterBuilderPlot(BasePlot):
    """H(u) with each broadening mechanism drawn as its own limb.

    The whole point is the DECOMPOSITION: eddy (A, flat), longitudinal
    diffusion (B/u, falling), and the two mass-transfer terms (C·u,
    rising) are separate traces under the bold total, so Wenzel's
    one-mechanism-at-a-time thought experiments become one figure. The
    closed-form optimum is marked on the total.
    """

    x_key = "linear_velocity_cm_s"
    y_key = "plate_height_um"

    def __init__(
        self,
        particle_size_um: float,
        packing_lambda: float,
        diffusion_dm: float,
        obstruction_gamma: float,
        c_s_ms: float,
        c_m_ms: float,
        u_range: tuple[float, float] = (0.02, 1.0),
        n_points: int = 300,
        log_x: bool = False,
        config: PlotConfig | None = None,
        title: str | None = None,
    ):
        super().__init__(config=config, title=title)
        self.params = dict(
            particle_size_um=float(particle_size_um),
            packing_lambda=float(packing_lambda),
            diffusion_dm=float(diffusion_dm),
            obstruction_gamma=float(obstruction_gamma),
            c_s_ms=float(c_s_ms),
            c_m_ms=float(c_m_ms),
        )
        u = np.linspace(u_range[0], u_range[1], n_points)
        # A log axis is only meaningful over strictly positive velocities.
        # van_deemter_components already rejects u <= 0, but guard here too
        # so a future caller with a widened range degrades to linear instead
        # of producing a broken log axis (Brian's ruling, 2026-08-27: the
        # student must never be able to put 0 or a negative on the log
        # scale).
        self.log_x = bool(log_x) and u[0] > 0.0
        self.terms: VanDeemterTerms = van_deemter_components(u, **self.params)

    def _operating_point(self) -> str:
        p = self.params
        t = self.terms
        opt = (f"u_opt {t.u_opt:.3f} cm/s, H_min {t.h_min:.2f} um"
               if np.isfinite(t.u_opt) else "no optimum (C = 0)")
        return (
            f"dp {p['particle_size_um']:g} um, lambda {p['packing_lambda']:g}, "
            f"Dm {p['diffusion_dm']:g}e-5 cm2/s, gamma "
            f"{p['obstruction_gamma']:g}, Cs {p['c_s_ms']:g} ms, "
            f"Cm {p['c_m_ms']:g} ms | {opt}"
        )

    def _build(self, fig: go.Figure) -> None:
        t = self.terms
        u = t.u
        if self.log_x:
            fig.update_xaxes(type="log")
        fig.add_trace(go.Scatter(
            x=u, y=np.full_like(u, t.a_term), mode="lines", name="A (eddy)",
            line=dict(dash="dot")))
        fig.add_trace(go.Scatter(
            x=u, y=t.b_term, mode="lines", name="B/u (longitudinal)",
            line=dict(dash="dash")))
        fig.add_trace(go.Scatter(
            x=u, y=t.cs_term, mode="lines", name="Cs·u (stationary MT)",
            line=dict(dash="dashdot")))
        fig.add_trace(go.Scatter(
            x=u, y=t.cm_term, mode="lines", name="Cm·u (mobile MT)",
            line=dict(dash="longdash")))
        fig.add_trace(go.Scatter(
            x=u, y=t.total, mode="lines", name="H total",
            line=dict(width=3)))
        if np.isfinite(t.u_opt) and u[0] <= t.u_opt <= u[-1]:
            fig.add_trace(go.Scatter(
                x=[t.u_opt], y=[t.h_min], mode="markers", showlegend=False,
                marker=dict(symbol="diamond", size=10),
                hovertemplate=("optimum: H_min = %{y:.2f} um at "
                               "u_opt = %{x:.3f} cm/s<extra></extra>")))

    def data_columns(self) -> dict[str, list]:
        t = self.terms
        return {
            "u_cm_s": list(t.u),
            "a_um": [t.a_term] * len(t.u),
            "b_um": list(t.b_term),
            "cs_um": list(t.cs_term),
            "cm_um": list(t.cm_term),
            "h_total_um": list(t.total),
        }


class PlateShapePlot(BasePlot):
    """Simulated exit profile against the exact linear-isotherm ideal.

    The dashed ideal is :func:`linear_elution_profile` — the SAME closed
    form the validation suite uses as the oracle — evaluated at the run's
    own N and k. It is always drawn, because the negative binomial is
    itself right-skewed at finite N: asymmetry only means something
    relative to that honest baseline, so the baseline is never optional.
    """

    x_key = "transfer_n"
    y_key = "mass_fraction"

    def __init__(
        self,
        result: PlateSimResult,
        config: PlotConfig | None = None,
        title: str | None = None,
    ):
        super().__init__(config=config, title=title)
        self.result = result
        self.ideal = linear_elution_profile(
            result.n_plates, result.k_linear, result.transfers)
        self.ideal_asymmetry = asymmetry_factor(result.transfers, self.ideal)

    def _operating_point(self) -> str:
        r = self.result
        asym = "n/a" if r.asymmetry is None else f"{r.asymmetry:.2f}"
        lin = ("n/a" if self.ideal_asymmetry is None
               else f"{self.ideal_asymmetry:.2f}")
        return (
            f"N {r.n_plates}, k {r.k_linear:g}, chi {r.chi:+.2f} | "
            f"t_max {r.t_max:.0f} (ideal {r.n_plates * (1 + r.k_linear):.0f}), "
            f"As {asym} (ideal {lin}), N_app {r.n_apparent:.0f}, "
            f"recovered {r.recovered:.4f}"
        )

    def _build(self, fig: go.Figure) -> None:
        r = self.result
        fig.add_trace(go.Scatter(
            x=r.transfers, y=self.ideal, mode="lines",
            name="Ideal (linear isotherm)", line=dict(dash="dash"),
            hovertemplate="ideal: %{y:.4f} at n = %{x:.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(
            x=r.transfers, y=r.profile, mode="lines", name="Simulated",
            line=dict(width=3), fill="tozeroy", opacity=0.85,
            hovertemplate="sim: %{y:.4f} at n = %{x:.0f}<extra></extra>"))
        fig.add_vline(
            x=r.n_plates * (1.0 + r.k_linear), line_dash="dot", line_width=1,
            annotation_text="ideal tR", annotation_position="top")

    def data_columns(self) -> dict[str, list]:
        r = self.result
        return {
            "transfer_n": list(r.transfers),
            "simulated": list(r.profile),
            "ideal_linear": list(self.ideal),
        }

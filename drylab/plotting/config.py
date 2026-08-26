"""Shared plot configuration. All figure styling flows from here."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

# ColorBrewer "Paired" — the palette the D3 reference used for compound traces.
#
# ONE DELIBERATE DIVERGENCE from ColorBrewer: slot 11 is #9e9d24 (olive)
# where ColorBrewer has #ffff99 (pale yellow). Measured reason, not taste:
# traces are drawn at compound_fill_opacity, and composited over a white
# canvas #ffff99 reaches a contrast ratio of 1.015 — against 1.108 for the
# faintest colour anyone has been able to read, and 1.015 is visually
# indistinguishable from the background. #9e9d24 measures 1.265 there,
# above the palette median, and keeps the yellow-family identity of the
# slot. Reported by the human 2026-08-05 ("hard to see on white"); the
# other three pale members of the Paired pairs measured 1.108-1.190 and
# were left alone. Appearance only — no computed value depends on colour.
PAIRED_12: tuple[str, ...] = (
    "#a6cee3", "#1f78b4", "#b2df8a", "#33a02c", "#fb9a99", "#e31a1c",
    "#fdbf6f", "#ff7f00", "#cab2d6", "#6a3d9a", "#9e9d24", "#b15928",
)

# Canonical axis labels with units, one authority for every figure.
AXIS_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "time_s": "Time (s)",
        "time_min": "Time (min)",
        # Displayed in arbitrary units (ruled 2026-08-05). The underlying
        # quantity is unchanged: it is the analyte concentration in the
        # detector cell, in umol/L, given sample concentrations in uM. "a.u."
        # is a DISPLAY convention here, NOT absorbance units -- converting to
        # absorbance would need per-analyte extinction coefficients and a path
        # length, which the reference does not carry. See data.py for the
        # unit derivation.
        "signal": "Signal (a.u.)",
        "solvent_fraction": "Solvent B fraction",
        "solvent_percent": "Solvent B (%)",
        "position_fraction": "Fractional column position",
        # Capillary electrophoresis. Concentrations are real mM here, not
        # arbitrary units: an electromigration model carries absolute
        # concentrations because the equilibria and the conductivity depend
        # on them, unlike the chromatographic models whose detector signal
        # is scale-free.
        "position_mm": "Position (mm)",
        "concentration_mM": "Concentration (mM)",
        "ph": "pH",
        "conductivity": "Conductivity (S/m)",
        "backpressure_bar": "Backpressure (bar)",
        "eluent_viscosity": "Viscosity (cP)",
        "concentration_um": "Concentration (µmol/L)",
        "tube_number": "Tube number",
        "analyte_fraction": "Fraction of analyte",
        "flow_rate": "Flow rate (mL/min)",
        "temperature": "Temperature (°C)",
        "hetp": "HETP (cm)",
        "theoretical_plates": "Plates N",
        "reduced_flow_velocity": "Reduced velocity nu",
        "reduced_plate_height": "Reduced plate height h",
        "k_prime": "Retention factor k'",
        "t_r_s": "Retention time (s)",
        "t_r_min": "Retention time (min)",
        "injection_volume": "Injection volume (uL)",
        "time_constant": "Time constant (s)",
        # Gas chromatography Golay view. Velocity in cm/s and H in mm are
        # the units GC method literature quotes optima in (u_opt tens of
        # cm/s, H_min fractions of a mm), so the plot reads against any
        # textbook figure without conversion.
        "carrier_velocity_cm_s": "Average carrier velocity ū (cm/s)",
        "gc_plate_height_mm": "Plate height H (mm)",
        # Band-shape sandbox: reduced units by design (one transfer = one
        # plate volume; mass as fraction of the injection), so the axes say
        # so instead of implying instrument units.
        "linear_velocity_cm_s": "Linear velocity u (cm/s)",
        "plate_height_um": "Plate height H (µm)",
        "transfer_n": "Transfer number n",
        "mass_fraction": "Mass fraction eluting per transfer",
    }
)


@dataclass(frozen=True)
class Theme:
    """A named look: Plotly figure theme plus notebook font/accent hints.

    Two tiers of reliability, deliberately kept distinct:

    * ``plotly_template``/``colorway``/``paper`` drive the figures, which this
      package renders itself -- fully under our control and stable.
    * ``heading_font``/``text_font``/``mono_font``/``accent`` feed notebook
      CSS. marimo documents only three stable CSS variables
      (``--marimo-heading-font``, ``--marimo-text-font``,
      ``--marimo-monospace-font``); anything beyond them is explicitly not
      guaranteed across marimo versions, so ``notebook_css`` sticks to those
      plus generic selectors and degrades to a no-op rather than breaking.

    Palettes are original work evoking the named HTML5 UP templates (CC BY
    3.0, https://html5up.net) -- no stylesheet from those templates is
    copied or redistributed here.
    """

    name: str
    plotly_template: str
    colorway: tuple[str, ...]
    accent: str
    paper: str  # figure background; "" = inherit from the template
    heading_font: str
    text_font: str
    mono_font: str
    credit: str = ""

    def notebook_css(self) -> str:
        """CSS for this theme: fonts and accent only.

        Themes are light-only by design (ruled 2026-08-05). An earlier dark
        mode was removed because it fought marimo's own theming -- this CSS
        deliberately sets no background or text colour, so marimo's light/dark
        setting stays authoritative for the notebook chrome and nothing
        clashes. Only marimo's three documented variables are used.
        """
        return f""":root {{
  --marimo-heading-font: {self.heading_font};
  --marimo-text-font: {self.text_font};
  --marimo-monospace-font: {self.mono_font};
  --hplc-accent: {self.accent};
}}
a {{ color: var(--hplc-accent); }}
h1, h2, h3 {{ letter-spacing: -0.01em; }}
"""


#: Named themes. "Studio" is the built-in neutral default.
THEMES: Mapping[str, Theme] = MappingProxyType(
    {
        "Studio (default)": Theme(
            name="Studio (default)",
            plotly_template="plotly_white",
            colorway=PAIRED_12,
            accent="#1f78b4",
            paper="",
            heading_font="system-ui, -apple-system, 'Segoe UI', sans-serif",
            text_font="system-ui, -apple-system, 'Segoe UI', sans-serif",
            mono_font="ui-monospace, 'SF Mono', Menlo, monospace",
        ),
        "Future Imperfect": Theme(
            name="Future Imperfect",
            plotly_template="plotly_white",
            # Deepened relative to the template's own dark-background palette
            # so the hues stay legible on a light canvas.
            colorway=(
                "#c8384f", "#2e8f94", "#d99400", "#6b5b9a", "#4a9a5e",
                "#c25c26", "#a3508f", "#2f6fa8", "#9a8f1f", "#5d8471",
            ),
            accent="#e4677e",
            paper="#1f2226",
            heading_font="'Source Sans Pro', 'Segoe UI', sans-serif",
            text_font="'Source Sans Pro', 'Segoe UI', sans-serif",
            mono_font="'Roboto Mono', ui-monospace, monospace",
            credit="Evokes Future Imperfect by HTML5 UP (html5up.net)",
        ),
        "Strongly Typed": Theme(
            name="Strongly Typed",
            plotly_template="simple_white",
            colorway=(
                "#2c3e50", "#3b7dd8", "#5aa469", "#c0603f", "#8e6bab",
                "#4c9aa8", "#b08a3e", "#a04f6d", "#607d8b", "#7a8b3c",
            ),
            accent="#3b7dd8",
            paper="#ffffff",
            heading_font="Georgia, 'Times New Roman', serif",
            text_font="Georgia, 'Times New Roman', serif",
            mono_font="'Courier New', ui-monospace, monospace",
            credit="Evokes Strongly Typed by HTML5 UP (html5up.net)",
        ),
        "Dopetrope": Theme(
            name="Dopetrope",
            plotly_template="plotly_white",
            colorway=(
                "#e2725b", "#3d9aa1", "#f0a830", "#5b6c8f", "#8ab661",
                "#c05f8c", "#6b8fbc", "#d4a24c", "#7f9b7a", "#a56a9e",
            ),
            accent="#e2725b",
            paper="#fdfaf6",
            heading_font="'Yanone Kaffeesatz', 'Segoe UI', sans-serif",
            text_font="'Open Sans', 'Segoe UI', sans-serif",
            mono_font="ui-monospace, Menlo, monospace",
            credit="Evokes Dopetrope by HTML5 UP (html5up.net)",
        ),
    }
)

@dataclass(frozen=True)
class PlotConfig:
    """Theme and sizing shared by every plot class."""

    template: str = "plotly_white"
    colorway: tuple[str, ...] = PAIRED_12
    height: int = 480
    sum_trace_color: str = "#333333"
    sum_trace_width: float = 2.0
    #: Sum-trace width for the GC figure, kept separate from the HPLC value.
    #: The GC chromatogram carries up to 17 filled component traces beneath
    #: the sum, where a 2.0 line reads as heavy; ruled thinner 2026-08-05.
    #: Named here rather than passed at the call site so the value is
    #: discoverable and changeable in one place (charter section 4).
    gc_sum_trace_width: float = 1.4
    compound_trace_width: float = 1.2
    compound_fill_opacity: float = 0.25
    hover_decimals: int = 3
    font_size: int = 13
    #: Legend visibility. A run with many traces (22 HPLC analytes, 17 GC
    #: solutes plus the sum) spends more vertical space on the legend than
    #: on the chromatogram, so it is OFF by default (ruled 2026-08-05) and
    #: front-ends expose a per-section switch. Trace identity survives
    #: legend-off: every section carries a results table, and hover labels
    #: are unaffected.
    show_legend: bool = False
    show_operating_point: bool = True
    operating_point_font_size: int = 10
    #: Operating-point stamp placement, in paper coordinates, plus the
    #: bottom margin reserved for it. The stamp previously sat at -0.18
    #: with 90px reserved, which put it on top of the x-axis title
    #: (reported 2026-08-05); these two move together and must stay
    #: consistent, so they live side by side.
    operating_point_y: float = -0.30
    operating_point_margin_b: int = 120
    #: Mouse drag behaviour. Plotly's own default inside marimo is box
    #: SELECT, which draws a rectangle and produces a selection — but no
    #: cell in this project reads a figure's .value, so the selection goes
    #: nowhere in all eight plots. Zoom is the useful gesture on a
    #: chromatogram (ruled 2026-08-05); double-click still resets the view.
    dragmode: str = "zoom"
    margin: Mapping[str, int] = field(
        default_factory=lambda: MappingProxyType(
            {"l": 60, "r": 60, "t": 60, "b": 50}
        )
    )

    @classmethod
    def from_theme(cls, theme_name: str, **overrides) -> "PlotConfig":
        """Build a PlotConfig from a named theme (light-only by design)."""
        try:
            theme = THEMES[theme_name]
        except KeyError as e:
            raise KeyError(
                f"Unknown theme {theme_name!r}; known: {sorted(THEMES)}"
            ) from e
        return cls(
            template=theme.plotly_template,
            colorway=theme.colorway,
            **overrides,
        )

    def axis_label(self, key: str) -> str:
        """Resolve a canonical axis label; refuses unknown keys by name."""
        try:
            return AXIS_LABELS[key]
        except KeyError as e:
            raise KeyError(
                f"Unknown axis-label key {key!r}; known keys: {sorted(AXIS_LABELS)}"
            ) from e

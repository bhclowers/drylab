# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo>=0.20",
#     "numpy>=1.26",
#     "pandas>=2.0",
#     "plotly>=5.20",
# ]
# ///
"""drylab (marimo).

Reversed-phase HPLC (isocratic and gradient), a standalone Craig
countercurrent-extraction model, and a standalone isothermal capillary GC
model (ported from GasChromatographySimulator.jl, MIT).

Port of the HPLC Simulator by Paul Boswell, Peter Carr, and Dwight Stoll
(hplcsimulator.org), via mlibby/hplc_simulator (JS). CC BY-NC-SA 3.0 US.

Layout: instrument/sample controls are SHARED across both elution modes, so
an isocratic-vs-gradient comparison differs only in the elution program
(decision 2026-08-04). Each mode tab owns its own program and views.

Runs with ``marimo run drylab_nb.py`` (imports the ``drylab``
package). For the browser/WASM build, ``python tools/build_wasm_notebook.py``
produces a self-contained variant.
"""

import marimo

__generated_with = "0.23.16"
# width="full": the content column stretches to the window. This is
# the marimo-level stretch policy (App width, not per-widget CSS);
# "medium" pinned the app to a ~1100 px column regardless of screen
# (Brian, 2026-08-26).
app = marimo.App(width="full", app_title="drylab")


@app.cell
def _():
    # [[INLINE:drylab:BEGIN]]
    from drylab import (
        Analyte,
        CARRIER_GASES,
        COLUMN_PRESETS,
        COMPOUNDS,
        DEFAULT_SAMPLE_MIX,
        SECONDARY_SOLVENTS,
        STATIONARY_PHASES,
        DiagnosticsLog,
        ElutionMode,
        GCColumn,
        GCProgram,
        GCConditions,
        GradientProgram,
        NonElutingCompoundError,
        NonElutingSoluteError,
        SimulationInputs,
        chromatogram,
        compute,
        craig_simulate,
        gc_average_linear_velocity,
        gc_chromatogram,
        gc_holdup_time,
        gc_simulate,
        gc_simulate_program,
        gc_volumetric_flow,
        solutes_for_phase,
    )
    from drylab.formulae import mm_to_mils
    from drylab.bandshape import simulate_plates as bandshape_simulate
    from drylab.plotting import (
        SECOND_PLOT_QUANTITIES,
        SWEEPABLE_INPUTS,
        THEMES,
        BandTrackPlot,
        ChromatogramPlot,
        CraigPlot,
        GCChromatogramPlot,
        GCGolayPlot,
        GCOverlayPlot,
        CEElectropherogramPlot,
        CEProfilePlot,
        ph_from_hydronium,
        GradientProfilePlot,
        OverlayPlot,
        PlateShapePlot,
        PlotConfig,
        SweepPlot,
        VanDeemterBuilderPlot,
    )
    import drylab

    DRYLAB_VERSION = drylab.__version__
    # [[INLINE:drylab:END]]
    return (
        Analyte,
        PlateShapePlot,
        VanDeemterBuilderPlot,
        bandshape_simulate,
        CARRIER_GASES,
        COLUMN_PRESETS,
        COMPOUNDS,
        DEFAULT_SAMPLE_MIX,
        DiagnosticsLog,
        DRYLAB_VERSION,
        SECOND_PLOT_QUANTITIES,
        SECONDARY_SOLVENTS,
        STATIONARY_PHASES,
        SWEEPABLE_INPUTS,
        THEMES,
        BandTrackPlot,
        ChromatogramPlot,
        CraigPlot,
        ElutionMode,
        GCChromatogramPlot,
        GCGolayPlot,
        GCOverlayPlot,
        CEElectropherogramPlot,
        CEProfilePlot,
        ph_from_hydronium,
        GCColumn,
        GCProgram,
        GCConditions,
        GradientProfilePlot,
        GradientProgram,
        NonElutingCompoundError,
        NonElutingSoluteError,
        OverlayPlot,
        PlotConfig,
        SimulationInputs,
        SweepPlot,
        chromatogram,
        compute,
        craig_simulate,
        gc_average_linear_velocity,
        gc_chromatogram,
        gc_holdup_time,
        gc_simulate,
        gc_simulate_program,
        gc_volumetric_flow,
        mm_to_mils,
        solutes_for_phase,
    )


@app.cell
def _():
    import io
    from dataclasses import replace

    import marimo as mo
    import numpy as np
    import pandas as pd

    return io, mo, np, pd, replace


@app.cell
def _(DiagnosticsLog):
    # No dependencies -> marimo runs this once, so the log survives the
    # re-runs triggered by moving a slider. Repeats are deduplicated.
    diagnostics = DiagnosticsLog(max_records=50, mirror_to_stderr=True)
    return (diagnostics,)


@app.cell
def _(DRYLAB_VERSION, mo):
    mo.vstack(
        [
            mo.md("# drylab"),
            mo.accordion(
                {
                    "About this simulator": mo.md(
                        f"""
                        Three independent models, core `drylab`
                        v{DRYLAB_VERSION}:

                        **HPLC simulator** - reversed-phase separations,
                        isocratic and gradient, validated against the original
                        Java applet (Boswell/Carr/Stoll) and the JavaScript
                        port. Instrument and sample settings are shared by both
                        elution modes.

                        **Craig apparatus** - countercurrent liquid-liquid
                        extraction, the discrete separation that plate theory
                        generalises. Validated against Appendix 16 of Harvey's
                        *Analytical Chemistry 2.0* and the Efstathiou applet.

                        **GC** - isothermal capillary gas chromatography,
                        ported from GasChromatographySimulator.jl (Leppert,
                        MIT) and validated against it over 162 cases.
                        Retention data: Blumberg (2017), 17 compounds on
                        three stationary phases.
                        """
                    )
                }
            ),
        ]
    )
    return


@app.cell
def _(mo):
    # ---- Classroom presets (added 2026-08-17 for the POGIL exercises) ----
    # A preset is a set of CONSTRUCTION DEFAULTS for the section's controls:
    # selecting one rebuilds the seeded controls at the preset's values, and
    # the student adjusts freely from there. This is the marimo-idiomatic
    # mechanism (UI elements cannot be assigned to after construction), it
    # needs no persistence machinery, and it works unchanged in the WASM
    # deployment. Every scenario below was VERIFIED against the model on
    # 2026-08-17 (validation notes in .context/memory/decisions.md):
    # the triage pair shows Rs = 0.65 at its preset, and the co-elution
    # pair's ln k lines cross near 102 °C on Wax.
    #
    # None = the section's ordinary defaults; "ALL" = every available name.
    HPLC_PRESETS = {
        "Default": None,
        "Ex 3 — Resolution triage": dict(
            compounds=("acetophenone", "p-chlorophenol"),
            solvent_percent=50.0,
            secondary_solvent="Acetonitrile",
        ),
        "Ex 4 — General elution": dict(
            compounds="ALL",
            solvent_percent=30.0,
            secondary_solvent="Acetonitrile",
        ),
    }
    GC_PRESETS = {
        "Default": None,
        "Ex 4 — General elution": dict(
            phase="SLB5ms",
            solutes=("Heptane", "Octane", "Nonane", "Decane", "Undecane",
                     "Dodecane", "Tridecane", "Tetradecane", "Pentadecane"),
            temperature=120.0,
        ),
        "Ex 5 — Alkane ladder": dict(
            phase="SLB5ms",
            solutes=("Octane", "Decane", "Dodecane"),
            temperature=120.0,
        ),
        "Ex 5 — Polarity trio": dict(
            phase="SLB5ms",
            solutes=("Decane", "1-Octanol", "2-Octanone"),
            temperature=120.0,
        ),
        "Ex 5 — Co-elution hunt": dict(
            phase="Wax",
            solutes=("Tridecane", "2-Octanone"),
            temperature=120.0,
        ),
    }
    # URL-distributable start states: ?hplc=<key>&gc=<key> selects presets,
    # so an instructor can hand each group a link instead of instructions.
    # Unknown or absent keys fall back to Default — a stale link can only
    # ever be as wrong as the ordinary start state.
    _HPLC_KEYS = {"ex3": "Ex 3 — Resolution triage",
                  "ex4": "Ex 4 — General elution"}
    _GC_KEYS = {"ex4": "Ex 4 — General elution",
                "ex5a": "Ex 5 — Alkane ladder",
                "ex5b": "Ex 5 — Polarity trio",
                "ex5c": "Ex 5 — Co-elution hunt"}

    def _initial(param, keys, table):
        try:
            raw = mo.query_params().get(param)
        except Exception:
            raw = None
        label = keys.get(str(raw).lower()) if raw is not None else None
        return label if label in table else "Default"

    hplc_preset = mo.ui.dropdown(
        options=list(HPLC_PRESETS),
        value=_initial("hplc", _HPLC_KEYS, HPLC_PRESETS),
        label="Classroom preset",
    )
    gc_preset = mo.ui.dropdown(
        options=list(GC_PRESETS),
        value=_initial("gc", _GC_KEYS, GC_PRESETS),
        label="Classroom preset",
    )
    return GC_PRESETS, HPLC_PRESETS, gc_preset, hplc_preset


@app.cell
def _(
    COLUMN_PRESETS,
    COMPOUNDS,
    DEFAULT_SAMPLE_MIX,
    HPLC_PRESETS,
    SECONDARY_SOLVENTS,
    hplc_preset,
    mo,
):
    # ---- SHARED controls: instrument + sample, common to both modes ----
    # The preset seeds CONSTRUCTION defaults for the sample and mobile-phase
    # chemistry only (analytes, solvent identity — %B is seeded in its own
    # cell); instrument geometry and pneumatics stay at their ordinary
    # defaults so a preset states the separation PROBLEM, never a solution.
    _p = HPLC_PRESETS[str(hplc_preset.value)]
    _analytes = (
        [name for name, _ in DEFAULT_SAMPLE_MIX]
        if _p is None
        else (sorted(COMPOUNDS) if _p["compounds"] == "ALL"
              else [n for n in _p["compounds"] if n in COMPOUNDS])
    )
    _solvent_b = "Acetonitrile" if _p is None else _p["secondary_solvent"]
    flow_rate = mo.ui.slider(
        0.1, 5.0, value=2.0, step=0.1, label="Flow rate (mL/min)"
    )
    secondary_solvent = mo.ui.dropdown(
        options=sorted(SECONDARY_SOLVENTS), value=_solvent_b,
        label="Solvent B",
    )
    temperature = mo.ui.slider(
        10, 80, value=25, step=1, label="Temperature (°C)",
    )
    column_preset = mo.ui.dropdown(
        options=sorted(COLUMN_PRESETS),
        value="Agilent Zorbax SB-C18",
        label="Column preset"
    )
    column_length = mo.ui.slider(
        30, 300, value=100, step=5, label="Column length (mm)",
    )
    particle_size = mo.ui.slider(
        1.5, 10.0, value=3.0, step=0.5, label="Particle size (µm)"
    )
    compound_picker = mo.ui.multiselect(
        options=sorted(COMPOUNDS),
        value=list(_analytes),
        label="Analytes"
    )
    injection_volume = mo.ui.slider(
        0.1, 500.0, value=5.0, step=0.1, label="Injection volume (µL)"
    )
    time_constant = mo.ui.slider(
        0.0, 5.0, value=0.1, step=0.05, label="Detector time constant (s)"
    )
    tubing_length = mo.ui.slider(
        0.0, 200.0, value=0.0, step=1.0, label="Post-column tubing (cm)"
    )
    # Presented in mm; converted to the reference's mils at the boundary.
    tubing_diameter_mm = mo.ui.slider(
        0.05, 1.0, value=0.13, step=0.01, label="Tubing i.d. (mm)"
    )
    noise_on = mo.ui.switch(value=False, label="Detector noise")
    noise_amplitude = mo.ui.slider(
        0.0, 20.0, value=2.0, step=0.1, label="Noise amplitude (signal units)"
    )
    noise_seed = mo.ui.number(0, 9999, value=42, label="Noise seed")
    return (
        column_length,
        column_preset,
        compound_picker,
        flow_rate,
        injection_volume,
        noise_amplitude,
        noise_on,
        noise_seed,
        particle_size,
        secondary_solvent,
        temperature,
        time_constant,
        tubing_diameter_mm,
        tubing_length,
    )


@app.cell
def _(mo):
    # Craig apparatus: deliberately standalone - no shared settings, no link
    # to the chromatography model.
    # Ceiling 100 -> 250 (Brian, 2026-08-26). Cost is nil — the tube
    # distribution is a closed-form array — and 250 tubes keeps high-D
    # bands on-axis at the transfer slider's 200-step maximum.
    craig_tubes = mo.ui.slider(
        4, 250, value=20, step=1, label="Number of tubes"
    )
    # Transfers are NOT capped by the tube count: past the last tube the
    # binomial tail leaves the apparatus, reported as eluted fraction.
    craig_step = mo.ui.slider(0, 200, value=5, step=1, label="Transfers (n)")
    craig_d_a = mo.ui.number(
        0.0, 100.0, value=0.5, step=0.01, label="D for analyte A"
    )
    craig_d_b = mo.ui.number(
        0.0, 100.0, value=3.5, step=0.01, label="D for analyte B"
    )
    craig_vol_upper = mo.ui.number(
        0.1, 10.0, value=1.0, step=0.1, label="Upper (mobile) phase volume"
    )
    craig_vol_lower = mo.ui.number(
        0.1, 10.0, value=1.0, step=0.1, label="Lower (stationary) phase volume"
    )
    craig_show_normal = mo.ui.switch(
        value=False, label="Overlay normal approximation"
    )
    return (
        craig_d_a,
        craig_d_b,
        craig_show_normal,
        craig_step,
        craig_tubes,
        craig_vol_lower,
        craig_vol_upper,
    )


@app.cell
def _(
    Analyte,
    craig_d_a,
    craig_d_b,
    craig_simulate,
    craig_step,
    craig_tubes,
    craig_vol_lower,
    craig_vol_upper,
    diagnostics,
    mo,
):
    _step = int(craig_step.value)
    _res = None
    with diagnostics.capture("Craig apparatus") as _craig_failed:
        _res = craig_simulate(
            [
                Analyte("A", float(craig_d_a.value)),
                Analyte("B", float(craig_d_b.value)),
            ],
            step=_step,
            n_tubes=int(craig_tubes.value),
            volume_upper=float(craig_vol_upper.value),
            volume_lower=float(craig_vol_lower.value),
        )
    # NO mo.stop. mo.stop halts this cell AND every descendant, and the
    # top-level layout cell descends from all producers — so stopping any one
    # of them blanked the ENTIRE app, sidebars included, removing the very
    # control needed to fix the input (reported 2026-08-05 against the
    # gradient editor's duplicate-time error). Errors are carried forward and
    # rendered by the panel that owns them.
    craig_error = (
        None if _res is not None else
        f"Craig extraction failed: "
        f"{_craig_failed[0] if _craig_failed else 'unknown'}"
    )
    craig_result = _res
    return craig_error, craig_result


@app.cell
def _(THEMES, mo):
    # ---- Appearance controls (Config tab) ----
    theme_picker = mo.ui.dropdown(
        options=sorted(THEMES), value="Studio (default)", label="Theme"
    )
    apply_notebook_css = mo.ui.switch(
        value=True, label="Apply theme fonts/accent to the notebook"
    )
    return apply_notebook_css, theme_picker


@app.cell
def _(PlotConfig, THEMES, apply_notebook_css, mo, theme_picker):
    theme = THEMES[theme_picker.value]
    # Figure styling: fully under this package's control, always reliable.
    plot_config = PlotConfig.from_theme(theme_picker.value)
    # Notebook styling: marimo guarantees only three CSS variables, so this is
    # a best-effort layer that is safe to switch off.
    theme_style = (
        mo.Html(f"<style>{theme.notebook_css()}</style>")
        if apply_notebook_css.value
        else mo.Html("")
    )
    return plot_config, theme, theme_style


@app.cell
def _(mo):
    # Legend visibility, one switch per top-level section (ruled 2026-08-05).
    # Defined together because they are all plot presentation; RENDERED in
    # each section above its plots, so the control sits where its effect is.
    # A switch's .value cannot be read in its defining cell, hence the split
    # from the derivation cell below.
    # OFF by default (ruled 2026-08-05): with 17-22 traces the legend takes
    # more height than the chromatogram. PlotConfig.show_legend defaults to
    # False too, so a library caller gets the same behaviour as the app.
    hplc_legend = mo.ui.switch(value=False, label="Legend")
    craig_legend = mo.ui.switch(value=False, label="Legend")
    gc_legend = mo.ui.switch(value=False, label="Legend")
    # GC only: the summed trace overlays the filled component traces, so
    # being able to drop it is what makes the components readable.
    gc_show_sum = mo.ui.switch(value=True, label="Sum trace")
    # Oven-ramp overlay on the Programmed tab's secondary y axis.
    gc_show_program = mo.ui.switch(value=True, label="Oven ramp")
    return (
        craig_legend,
        gc_legend,
        gc_show_program,
        gc_show_sum,
        hplc_legend,
    )


@app.cell
def _(craig_legend, gc_legend, hplc_legend, plot_config, replace):
    # One derived config per section. Plot cells consume these rather than
    # plot_config directly, so legend policy has a single authority per
    # section instead of a flag threaded through every figure call.
    hplc_plot_config = replace(plot_config, show_legend=hplc_legend.value)
    craig_plot_config = replace(plot_config, show_legend=craig_legend.value)
    gc_plot_config = replace(plot_config, show_legend=gc_legend.value)
    return craig_plot_config, gc_plot_config, hplc_plot_config


@app.cell
def _(HPLC_PRESETS, SECOND_PLOT_QUANTITIES, hplc_preset, mo, pd):
    # ---- Mode-specific controls: the elution program and its views ----
    # %B is seeded by the classroom preset. A preset change therefore also
    # rebuilds the gradient editor sharing this cell — acceptable, since a
    # preset defines a start state and the default program is that state.
    _p_pct = HPLC_PRESETS[str(hplc_preset.value)]
    solvent_percent = mo.ui.slider(
        5, 95,
        value=int(50 if _p_pct is None else _p_pct["solvent_percent"]),
        step=1, label="Solvent B (%)")
    iso_second_plot = mo.ui.dropdown(
        options=["No Plot"] + sorted(SECOND_PLOT_QUANTITIES),
        value="No Plot",
        label="Second plot",
    )
    gradient_editor = mo.ui.data_editor(
        pd.DataFrame({"time_min": [0.0, 10.0], "percent_b": [5.0, 95.0]}),
        label="Gradient program",
    )
    mixing_volume = mo.ui.slider(
        0.0, 2000.0, value=200.0, step=10.0, label="Mixing volume (uL)"
    )
    non_mixing_volume = mo.ui.slider(
        0.0, 2000.0, value=200.0, step=10.0, label="Non-mixing volume (uL)"
    )
    grad_second_plot = mo.ui.dropdown(
        options=["No Plot"] + sorted(SECOND_PLOT_QUANTITIES),
        value="Solvent B Fraction",
        label="Second plot",
    )
    grad_sigma_injection = mo.ui.switch(
        value=False, label="Include injection-volume term in gradient sigma"
    )
    band_quantity = mo.ui.dropdown(
        options=["k_prime", "position"], value="k_prime", label="Band track"
    )
    return (
        band_quantity,
        grad_second_plot,
        grad_sigma_injection,
        gradient_editor,
        iso_second_plot,
        mixing_volume,
        non_mixing_volume,
        solvent_percent,
    )


@app.cell
def _(
    column_length,
    column_preset,
    compound_picker,
    flow_rate,
    injection_volume,
    mo,
    noise_amplitude,
    noise_on,
    particle_size,
    secondary_solvent,
    temperature,
    mm_to_mils,
    time_constant,
    tubing_diameter_mm,
    tubing_length,
):
    # Shared input fields, built ONCE and reused by both modes. Building them
    # in one place is what guarantees the two modes differ only in the
    # elution program (decision 2026-08-04).
    _DEFAULT_CONCENTRATION = 10.0
    _REFERENCE_CONCENTRATIONS = {
        "phenol": 5.0,
        "3-phenyl propanol": 25.0,
        "acetophenone": 40.0,
        "p-chlorophenol": 15.0,
        "p-nitrotoluene": 10.0,
    }
    # Carried, not stopped: deselecting every analyte must not remove the
    # analyte picker from the screen.
    hplc_error = (
        "Select at least one analyte to simulate."
        if len(compound_picker.value) == 0 else None
    )
    shared_fields = dict(
        sample_mix=tuple(
            (name, _REFERENCE_CONCENTRATIONS.get(name, _DEFAULT_CONCENTRATION))
            for name in compound_picker.value
        ),
        flow_rate=flow_rate.value,
        temperature=temperature.value,
        secondary_solvent=secondary_solvent.value,
        injection_volume=injection_volume.value,
        time_constant=time_constant.value,
        post_tubing_length=tubing_length.value,
        post_tubing_diameter=mm_to_mils(tubing_diameter_mm.value),
        noise=float(noise_amplitude.value) if noise_on.value else 0.0,
        column_preset=column_preset.value,
        column_overrides=(
            ("length", float(column_length.value)),
            ("particle_size", float(particle_size.value)),
        ),
    )
    return (shared_fields,)


@app.cell
def _(SimulationInputs, compute, diagnostics, mo, shared_fields, solvent_percent):
    iso_inputs = SimulationInputs(solvent_percent=solvent_percent.value, **shared_fields)
    _iso = None
    with diagnostics.capture("Isocratic simulation") as _failed:
        _iso = compute(iso_inputs)
    iso_error = hplc_error or (
        None if _iso is not None else
        f"Isocratic simulation failed: {_failed[0] if _failed else 'unknown'}"
        " - see the Diagnostics tab."
    )
    iso_results = _iso
    return iso_error, iso_inputs, iso_results


@app.cell
def _(
    ElutionMode,
    GradientProgram,
    NonElutingCompoundError,
    SimulationInputs,
    compute,
    diagnostics,
    grad_sigma_injection,
    gradient_editor,
    mixing_volume,
    mo,
    non_mixing_volume,
    shared_fields,
):
    # The gradient rows come from an editable table, so validate loudly
    # rather than letting a malformed program produce a wrong chromatogram.
    # A row added in the editor starts empty (NaN). That is a half-finished
    # edit, not an error: drop such rows, tell the student, and simulate with
    # what is complete. Charter: a skipped item is a reported item.
    _all_rows = list(gradient_editor.value.itertuples(index=False))
    _rows = []
    _incomplete = 0
    for _r in _all_rows:
        _t, _p = _r.time_min, _r.percent_b
        if _t is None or _p is None or _t != _t or _p != _p:  # NaN-safe
            _incomplete += 1
            continue
        _rows.append((float(_t), float(_p)))

    _program = None
    _error = None
    _notice = None
    if _incomplete:
        _notice = (
            f"{_incomplete} gradient row(s) are still blank and were ignored. "
            "Fill in both Time and %B to include them."
        )
    if len(_rows) < 2:
        _error = (
            "A gradient needs at least two complete rows (time and %B). "
            "Finish filling in the table to see a chromatogram."
        )
    else:
        # Rows typed out of order are a normal edit, not an error: a solvent
        # program is time-ordered by nature, so sort. Duplicate times are the
        # one case sorting cannot resolve, so name them and ask.
        _dupes = GradientProgram.duplicate_times(_rows)
        _out_of_order = _rows != sorted(_rows, key=lambda tp: tp[0])
        if _dupes:
            _error = (
                "Two gradient rows share the same time ("
                + ", ".join(f"{t:g} min" for t in _dupes)
                + "). Give each row a distinct time."
            )
        elif _out_of_order:
            _notice = " ".join(
                filter(
                    None,
                    [
                        _notice,
                        "Gradient rows were out of order and have been sorted "
                        "by time.",
                    ],
                )
            )
    if _error is None:
        try:
            _program = GradientProgram.from_rows(
                _rows,
                mixing_volume=mixing_volume.value,
                non_mixing_volume=non_mixing_volume.value,
                sort_by_time=True,
            )
        except ValueError as e:
            _error = f"Gradient program is not valid: {e}"
            diagnostics.record("Gradient program", e)

    _results = None
    if _program is not None:
        try:
            # skip_non_eluting: a runaway analyte is reported and excluded
            # rather than blanking the whole gradient view.
            _results = compute(
                SimulationInputs(
                    elution_mode=ElutionMode.GRADIENT,
                    gradient_program=_program,
                    gradient_sigma_includes_injection=grad_sigma_injection.value,
                    **shared_fields,
                ),
                track_bands=True,
                skip_non_eluting=True,
            )
        except (NonElutingCompoundError, ValueError) as e:
            _error = str(e)
            diagnostics.record("Gradient simulation", e)

    grad_error = (
        None if _results is not None
        else (_error or "Gradient could not be computed.")
    )
    grad_results = _results
    grad_notice = _notice
    return grad_error, grad_notice, grad_results


@app.cell
def _(
    ChromatogramPlot,
    iso_error,
    iso_results,
    iso_second_plot,
    mo,
    noise_on,
    noise_seed,
    hplc_plot_config,
    replace,
):
    if iso_results is None:
        iso_chromatogram = mo.callout(mo.md(iso_error or
                                            "Isocratic run unavailable."),
                                      kind="warn")
    else:
        iso_chromatogram = mo.ui.plotly(
        ChromatogramPlot(
            iso_results,
            second_plot=(
                None if iso_second_plot.value == "No Plot" else iso_second_plot.value
            ),
            seed=int(noise_seed.value) if noise_on.value else None,
            title=None,
            config=replace(hplc_plot_config, show_operating_point=False),
        ).figure()
    )
    return (iso_chromatogram,)


@app.cell
def _(
    ChromatogramPlot,
    grad_error,
    grad_results,
    grad_second_plot,
    mo,
    noise_on,
    noise_seed,
    hplc_plot_config,
    replace,
):
    if grad_results is None:
        grad_chromatogram = mo.callout(mo.md(grad_error or
                                             "Gradient run unavailable."),
                                       kind="warn")
    else:
        grad_chromatogram = mo.ui.plotly(
        ChromatogramPlot(
            grad_results,
            second_plot=(
                None if grad_second_plot.value == "No Plot" else grad_second_plot.value
            ),
            seed=int(noise_seed.value) if noise_on.value else None,
            title=None,
            config=replace(hplc_plot_config, show_operating_point=False),
        ).figure()
    )
    return (grad_chromatogram,)


@app.cell
def _(
    BandTrackPlot,
    GradientProfilePlot,
    band_quantity,
    grad_error,
    grad_results,
    mo,
    hplc_plot_config,
    replace,
):
    if grad_results is None:
        _msg = mo.callout(mo.md(grad_error or "Gradient run unavailable."),
                          kind="warn")
        band_track_view = _msg
        gradient_profile_view = _msg
    else:
        _cfg = replace(hplc_plot_config, show_operating_point=False)
        gradient_profile_view = mo.ui.plotly(
            GradientProfilePlot(grad_results, config=_cfg, title=None).figure()
        )
        band_track_view = mo.ui.plotly(
            BandTrackPlot(
                grad_results,
                quantity=band_quantity.value,
                config=_cfg,
                title=None,
                log_y=band_quantity.value == "k_prime",
            ).figure()
        )
    return band_track_view, gradient_profile_view


@app.cell
def _(mo, pd):
    def results_panel(results, error=None):
        """Per-compound, operating-point, and system views for one Results.

        Accepts None so a failed run degrades this panel alone. Every caller
        sits upstream of the top-level layout cell, so raising here would
        blank the whole app — the defect this signature exists to prevent.
        """
        if results is None:
            return mo.callout(mo.md(error or "No results to show."),
                              kind="warn")
        # Elution order, with adjacent-pair metrics from the model's own
        # pair_metrics() (one authority with the CSV export). Rows were in
        # sample-mix order until 2026-08-17; elution order is what makes
        # "Rs vs prev" readable, since the previous ROW is now the previous
        # PEAK. The dash on the first row is deliberate: the first peak has
        # no predecessor, and alpha is dashed wherever the earlier k' is not
        # positive (an unretained marker), where selectivity is undefined.
        _ordered = sorted(results.compounds, key=lambda c: c.t_r)
        _pairs = {m.later: m for m in results.pair_metrics()}

        def _pair_cell(name, attr, digits):
            m = _pairs.get(name)
            v = getattr(m, attr) if m is not None else None
            return "—" if v is None else round(v, digits)

        compounds_df = pd.DataFrame(
            [
                {
                    "Compound": c.name,
                    "Conc. (µM)": c.concentration,
                    "k'": round(c.k_prime, 3),
                    "tR (s)": round(c.t_r, 2),
                    "tR (min)": round(c.t_r / 60.0, 3),
                    "sigma (s)": round(c.sigma, 3),
                    "Rs (vs prev)": _pair_cell(c.name, "resolution", 2),
                    "alpha (vs prev)": _pair_cell(c.name, "alpha", 3),
                    "Elutes in run": "yes" if c.eluted_within_run else "NO",
                }
                for c in _ordered
            ]
        )
        system_df = pd.DataFrame(
            {
                "Quantity": [
                    "Void time t0 (s)",
                    "Backpressure (bar)",
                    "Eluent viscosity (cP)",
                    "Diffusion coeff. (cm^2/s)",
                    "Plates N",
                    "HETP (cm)",
                    "Reduced velocity nu",
                    "Dwell time (min)",
                    "Tubing broadening (s^2)",
                    "Run end (min)",
                ],
                "Value": [
                    round(results.void_time, 3),
                    round(results.backpressure_bar, 2),
                    round(results.eluent_viscosity, 4),
                    f"{results.diffusion_coefficient:.3e}",
                    round(results.theoretical_plates, 0),
                    f"{results.hetp:.3e}",
                    round(results.reduced_flow_velocity, 3),
                    round(results.dwell_time, 3),
                    f"{results.tubing_time_broadening:.3e}",
                    round(results.final_time / 60.0, 3),
                ],
            }
        )
        _op_rows = "\n".join(
            f"| {k} | {v} |" for k, v in results.operating_point_items()
        )
        blocks = []
        _report = results.viability_report()
        if _report:
            blocks.append(mo.callout(_report, kind="warn"))
        blocks += [
            mo.md("**Per-compound results**"),
            mo.ui.table(compounds_df, selection=None, show_download=False),
            mo.md("**Operating point**"),
            mo.md("| Parameter | Value |\n|---|---|\n" + _op_rows),
            mo.md("**System**"),
            mo.ui.table(system_df, selection=None, show_download=False),
        ]
        return mo.vstack(blocks)

    return (results_panel,)


@app.cell
def _(SWEEPABLE_INPUTS, mo):
    sweep_parameter = mo.ui.dropdown(
        options=sorted(SWEEPABLE_INPUTS), value="flow_rate", label="Sweep parameter"
    )
    sweep_output = mo.ui.dropdown(
        options=[
            "hetp",
            "theoretical_plates",
            "backpressure_bar",
            "eluent_viscosity",
            "k_prime",
            "t_r",
        ],
        value="hetp",
        label="Output",
    )
    sweep_points = mo.ui.slider(5, 100, value=30, step=5, label="Points")
    return sweep_output, sweep_parameter, sweep_points


@app.cell
def _(
    SweepPlot,
    io,
    iso_inputs,
    mo,
    np,
    pd,
    hplc_plot_config,
    sweep_output,
    sweep_parameter,
    sweep_points,
):
    # Sweep ranges per parameter, named here rather than scattered.
    _SWEEP_RANGES = {
        "flow_rate": (0.2, 5.0),
        "solvent_percent": (10.0, 90.0),
        "temperature": (10.0, 80.0),
        "injection_volume": (0.5, 500.0),
        "time_constant": (0.0, 5.0),
    }
    _lo, _hi = _SWEEP_RANGES[sweep_parameter.value]
    _sweep_plot = SweepPlot(
        iso_inputs,
        sweep_parameter.value,
        np.linspace(_lo, _hi, int(sweep_points.value)),
        [sweep_output.value],
        title=None,
        config=hplc_plot_config,
    )
    sweep_view = mo.ui.plotly(_sweep_plot.figure())

    def _sweep_csv() -> bytes:
        # data_columns reads the same computed results the figure was drawn
        # from, and the file carries the figure's operating-point stamp —
        # export and plot cannot disagree (added 2026-08-17 so the van
        # Deemter A/B/C fit can be done offline on exactly what was seen).
        df = pd.DataFrame(_sweep_plot.data_columns())
        df["operating_point"] = _sweep_plot.operating_point()
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        return buf.getvalue().encode()

    sweep_download = mo.download(
        data=_sweep_csv,
        filename=f"sweep_{sweep_parameter.value}_{sweep_output.value}.csv",
        label="Sweep data (CSV)",
    )
    return sweep_download, sweep_view


@app.cell
def _(
    OverlayPlot,
    grad_error,
    grad_results,
    iso_error,
    iso_results,
    mo,
    hplc_plot_config,
    replace,
):
    if iso_results is None or grad_results is None:
        compare_view = mo.callout(
            mo.md(iso_error or grad_error or "Comparison unavailable."),
            kind="warn",
        )
    else:
        compare_view = mo.ui.plotly(
            OverlayPlot(
                [("Isocratic", iso_results), ("Gradient", grad_results)],
                config=replace(hplc_plot_config, show_operating_point=False),
                title=None,
            ).figure()
        )
    return (compare_view,)


@app.cell
def _(chromatogram, io, mo, pd):
    def export_panel(results, tag):
        def _trace_csv() -> bytes:
            t, per_compound, total = chromatogram(results)
            df = pd.DataFrame({"time_s": t, **per_compound, "sum": total})
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            return buf.getvalue().encode()

        def _results_csv() -> bytes:
            # Elution order with the same pair_metrics the on-screen table
            # shows (2026-08-17): the resolution-triage homework is done on
            # this file, so it must carry exactly what was seen. Undefined
            # metrics export as empty cells, not sentinels.
            _pairs = {m.later: m for m in results.pair_metrics()}
            df = pd.DataFrame(
                [
                    {
                        "compound": c.name,
                        "concentration": c.concentration,
                        "k_prime": c.k_prime,
                        "t_r_s": c.t_r,
                        "sigma_s": c.sigma,
                        "w": c.w,
                        "rs_vs_prev": (
                            _pairs[c.name].resolution
                            if c.name in _pairs else None
                        ),
                        "alpha_vs_prev": (
                            _pairs[c.name].alpha
                            if c.name in _pairs else None
                        ),
                        "eluted_within_run": c.eluted_within_run,
                    }
                    for c in sorted(results.compounds, key=lambda c: c.t_r)
                ]
            )
            df["operating_point"] = results.operating_point()
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            return buf.getvalue().encode()

        return mo.vstack(
            [
                mo.md(
                    "Exports are stamped with the operating point; the trace "
                    "CSV carries per-compound and summed signals."
                ),
                mo.download(
                    data=_trace_csv,
                    filename=f"chromatogram_trace_{tag}.csv",
                    label="Chromatogram trace (CSV)",
                ),
                mo.download(
                    data=_results_csv,
                    filename=f"compound_results_{tag}.csv",
                    label="Compound results (CSV)",
                ),
            ]
        )

    return (export_panel,)


@app.cell
def _(
    CraigPlot,
    craig_d_a,
    craig_d_b,
    craig_legend,
    craig_error,
    craig_result,
    craig_show_normal,
    craig_step,
    craig_tubes,
    craig_vol_lower,
    craig_vol_upper,
    mo,
    pd,
    craig_plot_config,
    replace,
):
    _plot = mo.ui.plotly(
        CraigPlot(
            craig_result,
            config=replace(craig_plot_config, show_operating_point=False),
            title=None,
            show_normal=craig_show_normal.value,
        ).figure()
    )

    if craig_result is None:
        craig_panel = mo.callout(mo.md(craig_error or
                                       "Craig run unavailable."), kind="warn")
    else:
        _a, _b = craig_result.analytes
        _table = pd.DataFrame(
            [
                {
                    "Analyte": x.name,
                    "D": x.distribution_ratio,
                    "q = 1/(D+1)": round(x.q, 4),
                    "p = 1 - q": round(x.p, 4),
                    "mean tube (np)": round(x.mean, 2),
                    "sigma (sqrt(npq))": round(x.sigma, 3),
                    "peak tube": x.peak_tube,
                    "eluted %": round(100 * x.eluted, 2),
                    "normal approx valid": "yes" if x.normal_valid else "no (np or nq < 5)",
                }
                for x in craig_result.analytes
            ]
        )
        _rs = craig_result.resolution()

        _maths = mo.md(
            r"""
    ### The equations

    **Partitioning in one tube (A16.1).** With an analyte distributed between an
    upper (mobile) and lower (stationary) phase, the fraction left in the lower
    phase is

    $$q = \frac{V_{aq}}{D\,V_{org} + V_{aq}} \qquad\text{(equal volumes: } q = \tfrac{1}{D+1}\text{)}$$

    and the fraction carried by the upper phase is \(p = 1 - q\).

    **Distribution after n steps (A16.2).** Each step is an extraction followed by
    transfer of every upper phase to the next tube. The fraction of analyte in
    tube \(r\) after step \(n\) follows the binomial distribution

    $$f(r,n) = \frac{n!}{(n-r)!\,r!}\,p^{r} q^{\,n-r}$$

    Within that tube, the upper phase holds \(p\,f(r,n)\) and the lower phase
    \(q\,f(r,n)\).

    **Where the analyte ends up.**

    $$\mu = np \qquad \sigma = \sqrt{npq}$$

    When both \(np > 5\) and \(nq > 5\), the binomial is closely approximated by a
    normal distribution, and the tubes holding an analyte can be bracketed by
    \(r = \mu \pm z\sigma\) (\(z = 2.58\) for 99%).

    *Source: Appendix 16, "Countercurrent Separations", in D. Harvey,
    *Analytical Chemistry 2.0*; after Craig, L. C., J. Biol. Chem. **1944**, 155,
    519-534.*
            """
        )

        _notices = []
        _any_eluted = any(x.eluted > 1e-9 for x in craig_result.analytes)
        if _any_eluted:
            _notices.append(
                mo.callout(
                    "Analyte has passed the last tube. "
                    + "; ".join(
                        f"eluted {x.name}: {100 * x.eluted:.2f}%"
                        for x in craig_result.analytes
                    )
                    + ". Add tubes to keep it in the apparatus.",
                    kind="warn",
                )
            )
        _summary_bits = [
            f"**{craig_result.step} transfers** in a "
            f"**{craig_result.n_tubes}-tube** apparatus."
        ]
        if _rs is not None:
            _summary_bits.append(
                f"Resolution on the tube axis "
                f"$R_s = |\\mu_B-\\mu_A| / [2(\\sigma_A+\\sigma_B)]$ = **{_rs:.2f}**."
            )

        craig_panel = mo.vstack(
            _notices
            + [
                mo.md(" ".join(_summary_bits)),
                craig_legend,
                _plot,
                mo.ui.table(_table, selection=None, show_download=False),
                _maths,
            ],
            gap=0.75,
        )

    # Controls are built OUTSIDE the guard: they are what the user needs in
    # order to fix a bad input, so they must never depend on the run
    # succeeding.
    craig_controls = mo.vstack(
        [
            mo.md("### Craig apparatus"),
            mo.md("*Countercurrent extraction - independent of the HPLC model.*"),
            craig_tubes,
            craig_step,
            mo.md("**Distribution ratios**"),
            craig_d_a,
            craig_d_b,
            mo.md("**Phase volumes**"),
            craig_vol_upper,
            craig_vol_lower,
            craig_show_normal,
        ],
        gap=0.5,
    )
    return craig_controls, craig_panel


@app.cell
def _(CARRIER_GASES, GC_PRESETS, STATIONARY_PHASES, gc_preset, mo, pd):
    # GC: deliberately standalone - no shared settings, no link to HPLC/Craig.
    # Short labels on purpose: a dropdown is sized by its longest option, and
    # the sidebar column is pinned at 340px, so a long option overflows into
    # the plot (reported 2026-08-05). The full chemistry goes in a caption
    # below, which wraps instead of widening. See gc.StationaryPhase.
    # The classroom preset seeds phase, oven temperature and (in the picker
    # cell) the solute selection — the chemistry that defines a scenario.
    # Column, carrier and pneumatics stay at ordinary defaults: a preset
    # states the problem, never the solution.
    _p = GC_PRESETS[str(gc_preset.value)]
    gc_phase = mo.ui.dropdown(
        options={phase.label: key for key, phase in STATIONARY_PHASES.items()},
        value=(STATIONARY_PHASES[_p["phase"]].label if _p is not None
               else next(iter(STATIONARY_PHASES.values())).label),
        label="Stationary phase",
    )
    gc_gas = mo.ui.dropdown(
        options=list(CARRIER_GASES), value="He", label="Carrier gas"
    )
    gc_temperature = mo.ui.slider(
        40, 250,
        value=int(120 if _p is None else _p["temperature"]),
        step=5, label="Oven temperature (°C)"
    )
    gc_length = mo.ui.slider(10, 60, value=30, step=5, label="Column length (m)")
    gc_diameter = mo.ui.dropdown(
        options={"0.10 mm": 0.10, "0.18 mm": 0.18, "0.25 mm": 0.25,
                 "0.32 mm": 0.32, "0.53 mm": 0.53},
        value="0.25 mm",
        label="Inner diameter",
    )
    gc_film = mo.ui.slider(
        0.1, 1.0, value=0.25, step=0.05, label="Film thickness (µm)"
    )
    gc_inlet_kpa = mo.ui.slider(
        110, 500, value=250, step=10, label="Inlet pressure (kPa, absolute)"
    )
    gc_outlet = mo.ui.dropdown(
        options={"Atmosphere (101.3 kPa)": 101300.0, "Vacuum (MS detector)": 0.0},
        value="Atmosphere (101.3 kPa)",
        label="Outlet",
    )
    gc_horizon_min = mo.ui.slider(
        5, 240, value=60, step=5, label="Run-time horizon (min)"
    )
    # Temperature program. Rows are (time_min, temperature_C) at the START of
    # each segment, i.e. ABSOLUTE times, which is how a GC method is written
    # on paper. GCProgram takes segment DURATIONS, so the conversion happens
    # in one place below rather than asking the student to think in deltas.
    gc_program_editor = mo.ui.data_editor(
        pd.DataFrame({"time_min": [0.0, 1.0, 27.0],
                      "temperature_C": [40.0, 40.0, 300.0]}),
        label="Temperature program",
    )
    return (
        gc_diameter,
        gc_film,
        gc_gas,
        gc_horizon_min,
        gc_inlet_kpa,
        gc_length,
        gc_outlet,
        gc_phase,
        gc_program_editor,
        gc_temperature,
    )


@app.cell
def _(GC_PRESETS, gc_phase, gc_preset, mo, solutes_for_phase):
    # Solute selection lives in its own cell BECAUSE its options depend on
    # the phase: changing the phase rebuilds the picker with that phase's
    # parameter set (the Blumberg fits are per-phase, so carrying a
    # selection across phases would be carrying names, not solutes) and
    # resets it to everything — the pre-2026-08-17 behaviour, so an
    # untouched picker changes nothing. A classroom preset instead seeds
    # its own solute list, intersected with the phase's names so a manual
    # phase change under an active preset can only narrow, never invent.
    _names = [s.name for s in solutes_for_phase(str(gc_phase.value))]
    _p = GC_PRESETS[str(gc_preset.value)]
    _seed = (
        list(_names) if _p is None or _p["solutes"] == "ALL"
        else [n for n in _p["solutes"] if n in _names]
    ) or list(_names)
    gc_solute_picker = mo.ui.multiselect(
        options=_names, value=_seed, label="Solutes"
    )
    # Golay-view solute: one curve per carrier for ONE solute, so this is a
    # single choice, not the multiselect. Decane is the default because it
    # sits mid-table (k neither trivial nor extreme at the default oven
    # temperature), which keeps the three curves in a readable band.
    gc_golay_solute = mo.ui.dropdown(
        options=_names,
        value="Decane" if "Decane" in _names else _names[0],
        label="Golay-view solute",
    )
    return gc_golay_solute, gc_solute_picker


@app.cell
def _(gc_phase, gc_solute_picker, solutes_for_phase):
    # Resolve picked names back to solute objects ONCE; both elution modes
    # consume this list, so the Compare tab's "same everything but the
    # program" contract extends to the sample.
    _picked = set(gc_solute_picker.value)
    gc_selected_solutes = [
        s for s in solutes_for_phase(str(gc_phase.value)) if s.name in _picked
    ]
    gc_selection_error = (
        "**No solutes selected.** Pick at least one solute in the controls "
        "to run a chromatogram."
        if not gc_selected_solutes
        else None
    )
    return gc_selected_solutes, gc_selection_error


@app.cell
def _(GCChromatogramPlot, gc_chromatogram, io, mo, pd):
    def gc_export_panel(peaks, column, conditions, holdup, tag,
                        program=None):
        """Download buttons for one GC run, mirroring the HPLC export_panel.

        The trace CSV samples the IDENTICAL time axis the chromatogram plot
        draws on (GCChromatogramPlot.time_axis — one authority for the
        grid), and both files carry the plot's operating-point stamp, so
        exported numbers can always be traced to the conditions that
        produced them (charter §4). Added 2026-08-17 for the classroom
        exercises: peak-capacity and ln k vs 1/T work needs these numbers
        off-screen.
        """
        _plot = GCChromatogramPlot(peaks, column, conditions, holdup,
                                   program=program)
        _op = _plot.operating_point()

        def _trace_csv() -> bytes:
            t = _plot.time_axis()
            df = pd.DataFrame({
                "time_s": t,
                **{p.solute.name: gc_chromatogram([p], t) for p in peaks},
                "sum": gc_chromatogram(list(peaks), t),
            })
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            return buf.getvalue().encode()

        def _results_csv() -> bytes:
            df = pd.DataFrame(
                [
                    {
                        "solute": p.solute.name,
                        "cas": p.solute.cas,
                        "phase": p.solute.phase,
                        "k": p.retention_factor,
                        "t_r_s": p.retention_time,
                        "tau_s": p.peak_width,
                        "plate_height_m": p.plate_height,
                        "plate_count": p.plate_count,
                    }
                    for p in peaks
                ]
            )
            df["operating_point"] = _op
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            return buf.getvalue().encode()

        return mo.vstack(
            [
                mo.md(
                    "Exports are stamped with the operating point; the trace "
                    "CSV carries per-solute and summed signals on the plot's "
                    "own time axis."
                ),
                mo.download(
                    data=_trace_csv,
                    filename=f"gc_trace_{tag}.csv",
                    label="Chromatogram trace (CSV)",
                ),
                mo.download(
                    data=_results_csv,
                    filename=f"gc_results_{tag}.csv",
                    label="Peak results (CSV)",
                ),
            ]
        )

    return (gc_export_panel,)


@app.cell
def _(
    GCColumn,
    GCConditions,
    diagnostics,
    gc_diameter,
    gc_film,
    gc_gas,
    gc_horizon_min,
    gc_inlet_kpa,
    gc_length,
    gc_outlet,
    gc_selected_solutes,
    gc_selection_error,
    gc_simulate,
    gc_temperature,
    mo,
):
    gc_column = GCColumn(
        length=float(gc_length.value),
        diameter=float(gc_diameter.value) * 1e-3,
        film_thickness=float(gc_film.value) * 1e-6,
        gas=str(gc_gas.value),
    )
    gc_conditions = GCConditions(
        temperature_k=float(gc_temperature.value) + 273.15,
        inlet_pressure=float(gc_inlet_kpa.value) * 1e3,
        outlet_pressure=float(gc_outlet.value),
    )
    _run = None
    _gc_failed = []
    # skip_non_eluting: an over-retained solute is excluded and named, not
    # raised (ruled 2026-08-05, following the gradient precedent) — one bad
    # solute must not blank the chromatogram. diagnostics.capture still
    # guards genuinely unexpected failures.
    if gc_selection_error is None:
        with diagnostics.capture("GC") as _gc_failed:
            _run = gc_simulate(
                gc_selected_solutes,
                gc_column,
                gc_conditions,
                max_time=float(gc_horizon_min.value) * 60.0,
                skip_non_eluting=True,
            )
    # Errors carried, not stopped (see the Craig cell): a bad GC input must
    # not take the HPLC and Craig sections down with it.
    gc_error = None
    if gc_selection_error is not None:
        gc_error = gc_selection_error
    elif _run is None:
        gc_error = (f"GC simulation stopped: "
                    f"{_gc_failed[0] if _gc_failed else 'unknown'}")
    elif not _run.peaks:
        gc_error = (
            f"**No solute elutes within the "
            f"{float(gc_horizon_min.value):g} min horizon.** "
            f"{_run.viability_report()}"
        )
    gc_run = _run
    gc_peaks = _run.peaks if _run is not None else ()
    return gc_column, gc_conditions, gc_error, gc_peaks, gc_run


@app.cell
def _(
    GCProgram,
    diagnostics,
    gc_column,
    gc_horizon_min,
    gc_inlet_kpa,
    gc_outlet,
    gc_program_editor,
    gc_selected_solutes,
    gc_selection_error,
    gc_simulate_program,
    mo,
):
    # Validate the program table before simulating. Same policy as the HPLC
    # gradient editor: a blank row is a half-finished edit, not an error, so
    # drop it and SAY SO; rows typed out of order are sorted; duplicate times
    # are the one case sorting cannot resolve, so they are named and refused.
    _rows = []
    _incomplete = 0
    for _r in gc_program_editor.value.itertuples(index=False):
        _t, _tc = _r.time_min, _r.temperature_C
        if _t is None or _tc is None or _t != _t or _tc != _tc:  # NaN-safe
            _incomplete += 1
            continue
        _rows.append((float(_t), float(_tc)))

    gc_prog_notice = None
    gc_prog_error = None
    if _incomplete:
        gc_prog_notice = (
            f"{_incomplete} program row(s) are still blank and were ignored. "
            f"Fill in both Time and Temperature to include them."
        )
    if len(_rows) < 2:
        gc_prog_error = (
            "A temperature program needs at least two complete rows. "
            "Finish filling in the table to see a chromatogram."
        )
    else:
        _times = [t for t, _ in _rows]
        _dupes = sorted({t for t in _times if _times.count(t) > 1})
        if _dupes:
            gc_prog_error = (
                "Two program rows share the same time ("
                + ", ".join(f"{t:g} min" for t in _dupes)
                + "). Give each row a distinct time."
            )
        elif _rows != sorted(_rows, key=lambda tt: tt[0]):
            _rows = sorted(_rows, key=lambda tt: tt[0])
            gc_prog_notice = " ".join(filter(None, [
                gc_prog_notice,
                "Program rows were out of time order and have been sorted.",
            ]))

    # An empty solute selection outranks program problems: with nothing to
    # inject, a perfect program still has nothing to show, and the fix the
    # user needs is in the picker, not the table.
    if gc_selection_error is not None:
        gc_prog_error = gc_selection_error

    gc_program = None
    gc_prog_run = None
    if gc_prog_error is None:
        # The editor holds ABSOLUTE times in minutes; GCProgram takes segment
        # DURATIONS in seconds. Converting here keeps the editor in the units
        # a method is written in and the model in SI.
        _t_s = [t * 60.0 for t, _ in _rows]
        _durations = [0.0] + [_t_s[i] - _t_s[i - 1] for i in range(1, len(_t_s))]
        try:
            gc_program = GCProgram.from_celsius(_durations, [c for _, c in _rows])
        except ValueError as _exc:
            gc_prog_error = f"Temperature program rejected: {_exc}"

    if gc_program is not None:
        with diagnostics.capture("GC program") as _prog_failed:
            gc_prog_run = gc_simulate_program(
                gc_selected_solutes,
                gc_column,
                gc_program,
                float(gc_inlet_kpa.value) * 1000.0,
                float(gc_outlet.value),
                max_time=float(gc_horizon_min.value) * 60.0,
                skip_non_eluting=True,
            )
        if gc_prog_run is None:
            gc_prog_error = (
                f"Programmed GC simulation stopped: "
                f"{_prog_failed[0] if _prog_failed else 'unknown'}"
            )
    return gc_prog_error, gc_prog_notice, gc_prog_run, gc_program


@app.cell
def _(
    GCChromatogramPlot,
    STATIONARY_PHASES,
    gc_column,
    gc_conditions,
    gc_diameter,
    gc_export_panel,
    gc_film,
    gc_gas,
    gc_average_linear_velocity,
    gc_golay_solute,
    gc_holdup_time,
    gc_horizon_min,
    gc_volumetric_flow,
    gc_inlet_kpa,
    gc_legend,
    gc_length,
    gc_outlet,
    gc_error,
    gc_peaks,
    gc_phase,
    gc_plot_config,
    gc_preset,
    gc_program_editor,
    gc_run,
    gc_show_sum,
    gc_solute_picker,
    gc_temperature,
    mo,
    pd,
    replace,
):
    # Full phase chemistry as a caption under the picker — built BEFORE the
    # error guard, because gc_controls below uses it unconditionally.
    # (Until 2026-08-17 it was built inside the else-branch, so any GC error
    # raised NameError here and blanked the section's controls — exactly
    # what the "controls outside the guard" rule exists to prevent.)
    # max-width keeps it inside the 340px controls column: the dropdown was
    # widened by its option text, and a caption that overflowed would
    # reintroduce exactly the overlap this replaced. overflow-wrap breaks
    # any long token rather than letting one push the column wider.
    _phase_caption = mo.md(
        f"*{STATIONARY_PHASES[str(gc_phase.value)].description}*"
    ).style({"max-width": "300px", "overflow-wrap": "anywhere",
             "font-size": "0.85em"})

    if gc_error is not None or not gc_peaks:
        gc_panel = mo.callout(mo.md(gc_error or
                                    "GC run unavailable."), kind="warn")
    else:
        _tm = gc_holdup_time(gc_column, gc_conditions)
        _plot = mo.ui.plotly(
            GCChromatogramPlot(
                gc_peaks,
                gc_column,
                gc_conditions,
                _tm,
                config=replace(gc_plot_config, show_operating_point=True),
                title=None,
                show_sum=gc_show_sum.value,
            ).figure()
        )

        _table = pd.DataFrame(
            [
                {
                    "Solute": p.solute.name,
                    "CAS": p.solute.cas,
                    "k": round(p.retention_factor, 3),
                    "tR (min)": round(p.retention_time / 60.0, 3),
                    "τR (s)": round(p.peak_width, 3),
                    "H (mm)": round(p.plate_height * 1e3, 4),
                    "N (plates)": int(round(p.plate_count)),
                }
                for p in gc_peaks
            ]
        )

        _maths = mo.md(
            r"""
    ### The equations

    **Retention** follows the K-centric thermodynamic model
    (parameters $T_{char}, \theta_{char}, \Delta C_p$ fitted per compound and
    phase by Blumberg, 2017):

    $$\ln k_0 = \left(\tfrac{\Delta C_p}{R} + \tfrac{T_{char}}{\theta_{char}}\right)
    \left(\tfrac{T_{char}}{T} - 1\right) + \tfrac{\Delta C_p}{R}\ln\tfrac{T}{T_{char}},
    \qquad k = \tfrac{\phi}{\phi_0}e^{\ln k_0},\quad \phi = d_f/d$$

    **Flow** through the column follows the James-Martin pressure profile
    $p(z)^2 = p_{in}^2 - \tfrac{z}{L}(p_{in}^2 - p_{out}^2)$ with the carrier
    viscosity from Blumberg's model. **Band broadening** follows the Golay
    equation with Fuller-Schettler-Giddings diffusivity.

    **Closed forms.** Isothermal and spatially uniform, the plate height is
    constant along the column and both migration integrals are analytic:

    $$t_R = A(1+k)\,\tfrac{2L}{3}\,\tfrac{p_{in}^3 - p_{out}^3}{p_{in}^2 - p_{out}^2},
    \qquad
    \tau_R^2 = H A^2 (1+k)^2 \tfrac{L\,(p_{in}^2 + p_{out}^2)}{2},
    \qquad A = \tfrac{64 L \eta}{d^2 (p_{in}^2 - p_{out}^2)}$$

    with $t_M$ = $t_R$ at $k=0$ (the familiar hold-up expression). Validated
    against GasChromatographySimulator.jl (Leppert, *J. Open Source Softw.*
    **5**(55), 2391, MIT) over 162 cases: `validation/compare_gc.py`.

    *Retention parameters: Blumberg (2017), as shipped in the reference
    package's test database (17 compounds × 3 phases).*
            """
        )

        # Derived readouts, not inputs: the section is pressure-controlled, so
        # these are a restatement of the pressures the user set (ruled
        # 2026-08-05). Recomputed here rather than cached, so they cannot
        # disagree with the conditions that produced the peaks.
        _flow_ml_min = gc_volumetric_flow(gc_column, gc_conditions) * 6.0e7
        _u_cm_s = gc_average_linear_velocity(gc_column, gc_conditions) * 100.0

        _first = gc_peaks[0]
        _last = gc_peaks[-1]
        _summary = mo.md(
            f"**{len(gc_peaks)} solutes** on "
            f"**{gc_peaks[0].solute.phase}**: first peak "
            f"{_first.solute.name} at **{_first.retention_time / 60.0:.2f} min**, "
            f"last {_last.solute.name} at "
            f"**{_last.retention_time / 60.0:.2f} min** "
            f"(hold-up {_tm:.1f} s). "
            f"Carrier {_flow_ml_min:.2f} mL/min at normal pressure, "
            f"average linear velocity {_u_cm_s:.1f} cm/s."
        )

        # A skipped solute is a reported solute: name every exclusion above the
        # chromatogram, where the missing peaks would have been.
        _gc_notices = []
        if gc_run.viability_report():
            _gc_notices.append(
                mo.callout(mo.md(gc_run.viability_report()), kind="warn")
            )

        gc_panel = mo.vstack(
            _gc_notices
            + [
                _summary,
                mo.hstack([gc_legend, gc_show_sum], justify="start", gap=1),
                _plot,
                mo.ui.table(_table, selection=None, show_download=False),
                gc_export_panel(gc_peaks, gc_column, gc_conditions, _tm,
                                "isothermal"),
                _maths,
            ],
            gap=0.75,
        )

    # Controls built OUTSIDE the guard: the user fixes a bad GC input
    # with these, so they must not depend on the run succeeding.
    gc_controls = mo.vstack(
        [
            mo.md("### Gas chromatography"),
            mo.md(
                "*Isothermal capillary GC - independent of the HPLC and "
                "Craig models.*"
            ),
            gc_preset,
            gc_phase,
            _phase_caption,
            gc_gas,
            gc_temperature,
            mo.md("**Sample**"),
            gc_solute_picker,
            # The Golay-view solute is grouped with the sample because it is
            # chosen from the same per-phase table; it drives only the Golay
            # tab and never filters the chromatograms.
            gc_golay_solute,
            mo.md("**Column**"),
            gc_length,
            gc_diameter,
            gc_film,
            mo.md("**Pneumatics**"),
            gc_inlet_kpa,
            gc_outlet,
            gc_horizon_min,
            # One controls region for all three GC tabs. Column, carrier and
            # pneumatics are therefore SHARED between the isothermal and
            # programmed arms, which is what makes the Compare tab honest:
            # the two runs provably differ only in the elution program.
            mo.md("**Temperature program** (Programmed and Compare tabs)"),
            mo.md("*Absolute times; the oven slider above drives the "
                  "isothermal arm.*").style({"font-size": "0.85em",
                                             "max-width": "300px"}),
            gc_program_editor,
        ],
        gap=0.5,
    )
    return gc_controls, gc_panel


@app.cell
def _(
    GCChromatogramPlot,
    GCOverlayPlot,
    GCProgram,
    gc_column,
    gc_conditions,
    gc_export_panel,
    gc_holdup_time,
    gc_legend,
    gc_peaks,
    gc_plot_config,
    gc_prog_error,
    gc_prog_notice,
    gc_prog_run,
    gc_program,
    gc_show_program,
    gc_show_sum,
    gc_temperature,
    mo,
    pd,
    replace,
):
    # Programmed panel. mo.stop is deliberately NOT used here: an invalid
    # program must not blank the isothermal view, which is independent of it.
    if gc_prog_error is not None:
        _prog_panel = mo.callout(mo.md(gc_prog_error), kind="warn")
        _compare_panel = mo.callout(
            mo.md("Fix the temperature program to see the comparison."),
            kind="warn",
        )
    else:
        _pk = gc_prog_run.peaks
        _notes = []
        if gc_prog_notice:
            _notes.append(mo.callout(mo.md(gc_prog_notice), kind="info"))
        if gc_prog_run.viability_report():
            _notes.append(
                mo.callout(mo.md(gc_prog_run.viability_report()), kind="warn")
            )
        if not _pk:
            _prog_panel = mo.vstack(
                _notes + [mo.callout(
                    mo.md("**No solute elutes within the run-time horizon "
                          "under this program.**"), kind="warn")],
                gap=0.5,
            )
            _compare_panel = _prog_panel
        else:
            _ramps = " -> ".join(
                f"{t / 60.0:g} min at {k - 273.15:g} degC"
                for t, k in zip(gc_program.boundaries, gc_program.temperatures)
            )
            _summary = mo.md(
                f"**{len(_pk)} solutes** programmed: first peak "
                f"**{_pk[0].solute.name}** at "
                f"**{_pk[0].retention_time / 60.0:.2f} min**, last "
                f"**{_pk[-1].solute.name}** at "
                f"**{_pk[-1].retention_time / 60.0:.2f} min**. "
                f"Program: {_ramps}."
            )
            _table = pd.DataFrame([
                {"Solute": p.solute.name,
                 "tR (min)": round(p.retention_time / 60.0, 4),
                 "k at elution": round(p.retention_factor, 4),
                 "tauR (s)": round(p.peak_width, 4),
                 "N": round(p.plate_count, 1)}
                for p in _pk
            ])
            _prog_plot = mo.ui.plotly(
                GCChromatogramPlot(
                    _pk, gc_column, gc_conditions,
                    gc_holdup_time(gc_column, gc_conditions),
                    config=replace(gc_plot_config, show_operating_point=False),
                    title=None,
                    show_sum=gc_show_sum.value,
                    # Oven ramp on the right-hand axis, mirroring how the
                    # HPLC gradient view overlays %B: the program is what
                    # explains the peak spacing, so it belongs on the same
                    # time axis. Toggleable, because with the legend off the
                    # dashed line is otherwise unlabelled.
                    program=gc_program if gc_show_program.value else None,
                ).figure()
            )
            _prog_panel = mo.vstack(
                _notes + [
                    _summary,
                    mo.hstack([gc_legend, gc_show_sum, gc_show_program],
                              justify="start", gap=1),
                    _prog_plot,
                    mo.ui.table(_table, selection=None, show_download=False),
                    # Same exporter as the isothermal tab; passing the
                    # program makes the operating-point stamp say
                    # "programmed", not the oven slider's isothermal value.
                    gc_export_panel(_pk, gc_column, gc_conditions,
                                    gc_holdup_time(gc_column, gc_conditions),
                                    "programmed", program=gc_program),
                ],
                gap=0.75,
            )

            # Comparison. Both arms are built from the SAME gc_column and the
            # same inlet/outlet controls, so they provably differ only in the
            # elution program - the precondition the HPLC compare view
            # carries, restated here because the plot cannot enforce it.
            _iso_label = (
                f"Isothermal {gc_conditions.temperature_k - 273.15:g} degC"
            )
            _iso_arm = list(gc_peaks)
            _compare_panel = mo.vstack([
                mo.md(
                    "Both traces use the **same column, carrier and "
                    "pneumatics**; only the elution program differs."
                ),
                mo.ui.plotly(
                    GCOverlayPlot(
                        ([(_iso_label, _iso_arm)] if _iso_arm else [])
                        + [("Programmed", _pk)],
                        gc_column,
                        config=replace(gc_plot_config, show_legend=True),
                        title=None,
                        subtitle=(
                            f"isothermal {gc_temperature.value:g} degC vs "
                            f"program to "
                            f"{gc_program.temperatures[-1] - 273.15:g} degC"
                        ),
                    ).figure()
                ),
            ], gap=0.5)

    gc_prog_panel = _prog_panel
    gc_compare_panel = _compare_panel
    return gc_compare_panel, gc_prog_panel


@app.cell
def _(
    GCGolayPlot,
    diagnostics,
    gc_column,
    gc_golay_solute,
    gc_outlet,
    gc_phase,
    gc_plot_config,
    gc_temperature,
    io,
    mo,
    np,
    pd,
    replace,
    solutes_for_phase,
):
    # Golay view: H vs average velocity for ONE solute, one trace per
    # carrier gas, at the section's column, oven and outlet settings. The
    # sweep spans the inlet-pressure slider's own range (110-500 kPa), so
    # every plotted point is reachable from the real control — and the
    # carrier-gas dropdown is deliberately ignored here, because all three
    # gases on one axis IS the view.
    _GOLAY_INLET_RANGE_KPA = (110.0, 500.0)
    _GOLAY_POINTS = 40

    _solute = next(
        s for s in solutes_for_phase(str(gc_phase.value))
        if s.name == str(gc_golay_solute.value)
    )
    _golay = None
    with diagnostics.capture("GC Golay") as _golay_failed:
        _golay = GCGolayPlot(
            _solute,
            gc_column,
            temperature_k=float(gc_temperature.value) + 273.15,
            outlet_pressure=float(gc_outlet.value),
            inlet_pressures=np.linspace(
                _GOLAY_INLET_RANGE_KPA[0] * 1e3,
                _GOLAY_INLET_RANGE_KPA[1] * 1e3,
                _GOLAY_POINTS,
            ),
            config=replace(gc_plot_config, show_operating_point=True,
                           show_legend=True),
            title=None,
        )

    if _golay is None:
        gc_golay_panel = mo.callout(
            mo.md(f"Golay view unavailable: "
                  f"{_golay_failed[0] if _golay_failed else 'unknown'}"),
            kind="warn",
        )
    else:
        def _golay_csv() -> bytes:
            df = pd.DataFrame(_golay.data_columns())
            df["operating_point"] = _golay.operating_point()
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            return buf.getvalue().encode()

        gc_golay_panel = mo.vstack(
            [
                mo.md(
                    "Golay plate height for **one solute** across the "
                    "inlet-pressure range, one curve per carrier gas — the "
                    "carrier dropdown does not apply here. Diamonds mark "
                    "each gas's optimum (H_min at u_opt). Column, oven and "
                    "outlet follow the shared controls."
                ),
                mo.ui.plotly(_golay.figure()),
                mo.download(
                    data=_golay_csv,
                    filename=(
                        f"gc_golay_{str(gc_golay_solute.value)}.csv"
                    ),
                    label="Golay sweep data (CSV)",
                ),
            ],
            gap=0.75,
        )
    return (gc_golay_panel,)


@app.cell
def _(diagnostics, diagnostics_refresh, mo, pd):
    diagnostics_refresh  # re-render when the student clicks Refresh
    _records = diagnostics.records
    if not _records:
        _body = mo.callout(
            "No errors recorded this session.", kind="success"
        )
    else:
        _table = pd.DataFrame(
            [
                {
                    "Time": r.last_seen.strftime("%H:%M:%S"),
                    "Where": r.context,
                    "Error": r.kind,
                    "Message": r.message,
                    "Times": r.count,
                }
                for r in _records
            ]
        )
        _details = mo.accordion(
            {
                f"{r.kind} in {r.context} ({r.last_seen.strftime('%H:%M:%S')})":
                    mo.md(
                        "**"
                        + r.message
                        + "**\n\n```\n"
                        + (r.traceback_text or "(no traceback: recorded note)")
                        + "\n```"
                    )
                for r in _records
            }
        )
        _body = mo.vstack(
            [
                mo.callout(
                    f"{len(_records)} distinct issue(s) recorded this session. "
                    "Most recent first.",
                    kind="warn",
                ),
                mo.ui.table(_table, selection=None, show_download=False),
                mo.md("**Full tracebacks**"),
                _details,
            ]
        )

    diagnostics_panel = mo.vstack(
        [
            mo.md("### Diagnostics"),
            mo.md(
                "Errors are recorded here *and* printed to the terminal "
                "(stderr) for anyone running the notebook locally. Repeats "
                "are counted rather than duplicated, and the log keeps the "
                "50 most recent distinct issues."
            ),
            mo.hstack([diagnostics_refresh], justify="start"),
            _body,
        ]
    )
    return (diagnostics_panel,)


@app.cell
def _(mo):
    diagnostics_refresh = mo.ui.refresh(
        options=["off", "2s", "5s"], default_interval="off",
        label="Auto-refresh diagnostics",
    )
    return (diagnostics_refresh,)


@app.cell
def _(apply_notebook_css, mo, theme, theme_picker):
    _credit = (
        mo.md(f"*{theme.credit}*") if theme.credit else mo.md("")
    )
    config_panel = mo.vstack(
        [
            mo.md("### Appearance"),
            theme_picker,
            apply_notebook_css,
            _credit,
            mo.md(
                f"""
                Currently rendering **{theme.name}**.

                Figure colours, templates and palettes are handled by this
                package, so they always follow the theme. Notebook fonts and
                accent colour are applied through marimo's documented CSS
                variables (`--marimo-heading-font`, `--marimo-text-font`,
                `--marimo-monospace-font`); marimo does not guarantee any
                other selector across versions, so that layer is intentionally
                light and can be switched off above. These themes set no
                background or text colour, so marimo's own light/dark setting
                (in its settings menu) stays authoritative for the notebook
                chrome and the two cannot clash.

                Theme palettes are original, written for this project to evoke
                the named [HTML5 UP](https://html5up.net) templates. No
                stylesheet from those templates is copied or redistributed.
                """
            ),
        ]
    )
    return (config_panel,)


@app.cell
def _(mo):
    # Each top-level section owns its own controls, so no panel shows
    # settings that do not apply to it. A flex child defaults to
    # min-width:auto and will not shrink below its content, which is what
    # made earlier two-column attempts overlap; pinning the sidebar and
    # setting min-width:0 on the content column is the fix.
    # Sidebar grows to whatever height its controls need: no max-height and
    # no overflow rule, so nothing is clipped or trapped behind a scrollbar.
    # Only the WIDTH is pinned, which is what stops it overlapping the plots.
    _SIDEBAR_STYLE = {
        "flex": "0 0 340px",
        "width": "340px",
        "max-width": "340px",
        "overflow": "visible",
    }
    # min-width:0 lets the content column shrink instead of pushing outwards;
    # overflow-x:auto applies to wide plots only, not to the controls.
    _CONTENT_STYLE = {"flex": "1 1 0%", "min-width": "0", "overflow-x": "auto"}

    def with_sidebar(controls, content):
        return mo.hstack(
            [
                mo.vstack([controls], gap=0.5).style(_SIDEBAR_STYLE),
                mo.vstack([content], gap=0.5).style(_CONTENT_STYLE),
            ],
            justify="start",
            align="start",
            gap=1.5,
        )

    return (with_sidebar,)


@app.cell
def _(
    band_quantity,
    band_track_view,
    column_length,
    column_preset,
    compare_view,
    compound_picker,
    export_panel,
    flow_rate,
    grad_chromatogram,
    grad_error,
    grad_notice,
    grad_results,
    grad_second_plot,
    grad_sigma_injection,
    gradient_editor,
    gradient_profile_view,
    hplc_legend,
    hplc_preset,
    injection_volume,
    iso_chromatogram,
    iso_error,
    iso_results,
    iso_second_plot,
    mixing_volume,
    mo,
    noise_amplitude,
    noise_on,
    noise_seed,
    non_mixing_volume,
    particle_size,
    results_panel,
    secondary_solvent,
    solvent_percent,
    sweep_download,
    sweep_output,
    sweep_parameter,
    sweep_points,
    sweep_view,
    temperature,
    time_constant,
    tubing_diameter_mm,
    tubing_length,
    with_sidebar,
):
    # One cell per top-level SECTION. Before 2026-08-05 a single cell built
    # all three plus the layout, consuming 49 names; because the layout cell
    # is a descendant of every producer, any failure anywhere took the whole
    # interface down (the mo.stop defect). Splitting by section bounds a
    # failure to its own section STRUCTURALLY, rather than relying on each
    # future producer remembering not to halt.
    _shared_controls = mo.vstack(
        [
            mo.md("### Settings"),
            hplc_preset,
            mo.md("**Mobile phase**"),
            flow_rate,
            secondary_solvent,
            temperature,
            mo.md("**Column**"),
            column_preset,
            column_length,
            particle_size,
            mo.md("**Sample**"),
            compound_picker,
            mo.md("**Injection / detection**"),
            injection_volume,
            time_constant,
            tubing_length,
            tubing_diameter_mm,
            mo.md("**Detector noise**"),
            noise_on,
            noise_amplitude,
            noise_seed,
        ],
        gap=0.5,
    )

    _iso_tabs = mo.ui.tabs(
        {
            "Chromatogram": mo.vstack(
                [
                    mo.hstack(
                        [solvent_percent, iso_second_plot], justify="start", gap=1
                    ),
                    iso_chromatogram,
                ]
            ),
            "Results": results_panel(iso_results, iso_error),
            "Sweeps": mo.vstack(
                [
                    mo.hstack([sweep_parameter, sweep_output, sweep_points], gap=1),
                    sweep_view,
                    sweep_download,
                ]
            ),
            "Export": export_panel(iso_results, "isocratic"),
        }
    )

    _grad_program = mo.vstack(
        [gradient_editor, mo.hstack([mixing_volume, non_mixing_volume], gap=1)]
    )
    _grad_tabs = mo.ui.tabs(
        {
            "Chromatogram": mo.vstack(
                [
                    _grad_program,
                    (
                        mo.callout(grad_notice, kind="warn")
                        if grad_notice
                        else mo.md("")
                    ),
                    grad_second_plot,
                    grad_chromatogram,
                ]
            ),
            "Solvent profile": mo.vstack([_grad_program, gradient_profile_view]),
            "Band tracks": mo.vstack([band_quantity, band_track_view]),
            "Results": mo.vstack([grad_sigma_injection,
                                  results_panel(grad_results, grad_error)]),
            "Export": export_panel(grad_results, "gradient"),
        }
    )

    # HPLC simulator: elution-mode tabs, driven by the shared settings.
    # The legend switch sits above the tabs because it governs every HPLC
    # figure; one switch per section, not per figure (ruled 2026-08-05).
    _hplc_tabs = mo.ui.tabs(
        {
            "Isocratic": _iso_tabs,
            "Gradient": _grad_tabs,
            "Compare": mo.vstack(
                [
                    mo.md(
                        "Both modes run on the same shared settings, so the "
                        "only difference between these traces is the elution "
                        "program."
                    ),
                    compare_view,
                ]
            ),
        }
    )

    hplc_section = with_sidebar(
        _shared_controls, mo.vstack([hplc_legend, _hplc_tabs], gap=0.5)
    )
    return (hplc_section,)


@app.cell
def _(craig_controls, craig_panel, with_sidebar):
    craig_section = with_sidebar(craig_controls, craig_panel)
    return (craig_section,)


@app.cell
def _(mo):
    # ---- Band-shape sandbox controls (added 2026-08-17, Brian's ruling:
    # a section capturing the band-broadening mechanisms and the
    # tailing/fronting parameters of an overloaded column, for the Wenzel
    # unit). Two independent control groups, one per tab.
    #
    # Mechanisms tab — each slider owns ONE van Deemter mechanism:
    bs_dp = mo.ui.slider(1.0, 10.0, value=3.0, step=0.5,
                         label="Particle size dp (µm)")
    bs_lambda = mo.ui.slider(0.5, 2.0, value=1.0, step=0.05,
                             label="Packing factor λ (eddy)")
    bs_dm = mo.ui.slider(0.2, 4.0, value=1.0, step=0.1,
                         label="Diffusion Dm (×10⁻⁵ cm²/s)")
    bs_cs = mo.ui.slider(0.0, 10.0, value=2.0, step=0.25,
                         label="Cs — stationary-phase MT (ms)")
    bs_cm = mo.ui.slider(0.0, 10.0, value=1.0, step=0.25,
                         label="Cm — mobile-phase MT (ms)")
    # Peak-shape tab — the overload machine:
    # Ceiling raised 200 -> 1000 (Brian, 2026-08-18). Cost at the max is
    # ~0.8 s natively (N=1000, k=9, ~12k transfers), so a few seconds in
    # WASM — a deliberate setting, not the default path.
    bs_plates = mo.ui.slider(10, 1000, value=100, step=10,
                             label="Plates N")
    bs_k = mo.ui.slider(0.0, 9.0, value=2.0, step=0.5,
                        label="Retention factor k (linear)")
    bs_curvature = mo.ui.slider(
        -0.85, 5.0, value=0.0, step=0.05,
        label="Isotherm curvature b·C₀ (− fronting / + tailing)")
    bs_load = mo.ui.slider(0.1, 10.0, value=1.0, step=0.1,
                           label="Sample load (× reference)")
    bs_injection = mo.ui.slider(1, 20, value=1, step=1,
                                label="Injection width (plates)")
    bs_tau = mo.ui.slider(0.0, 40.0, value=0.0, step=1.0,
                          label="Slow-site tailing τ (transfers)")
    return (
        bs_cm,
        bs_cs,
        bs_curvature,
        bs_dm,
        bs_dp,
        bs_injection,
        bs_k,
        bs_lambda,
        bs_load,
        bs_plates,
        bs_tau,
    )


@app.cell
def _(bandshape_simulate, bs_curvature, bs_injection, bs_k, bs_load,
      bs_plates, bs_tau, diagnostics, mo):
    # Effective curvature is chemistry × injection: chi = (b·C_ref) × load.
    # The model clamps anti-Langmuir chi at -0.9 because the isotherm
    # q = aC/(1+bC) loses meaning at b·C <= -1; when the clamp engages the
    # student is TOLD, not silently corrected.
    _chi_req = float(bs_curvature.value) * float(bs_load.value)
    bs_result = None
    with diagnostics.capture("Band shape") as _bs_failed:
        bs_result = bandshape_simulate(
            int(bs_plates.value),
            float(bs_k.value),
            _chi_req,
            injection_plates=int(bs_injection.value),
            tail_tau=float(bs_tau.value),
        )
    bs_error = None
    bs_notice = None
    if bs_result is None:
        bs_error = (f"Band-shape simulation stopped: "
                    f"{_bs_failed[0] if _bs_failed else 'unknown'}")
    elif bs_result.chi != _chi_req:
        bs_notice = (
            f"Requested curvature × load = {_chi_req:+.2f} exceeds isotherm "
            f"validity (b·C must stay above −1); shown at the clamp, "
            f"χ = {bs_result.chi:+.2f}."
        )
    return bs_error, bs_notice, bs_result


@app.cell
def _(
    PlateShapePlot,
    VanDeemterBuilderPlot,
    bs_cm,
    bs_cs,
    bs_curvature,
    bs_dm,
    bs_dp,
    bs_error,
    bs_injection,
    bs_k,
    bs_lambda,
    bs_load,
    bs_notice,
    bs_plates,
    bs_result,
    bs_tau,
    io,
    mo,
    pd,
    plot_config,
    replace,
):
    # ---- Mechanisms tab ----
    _vd = VanDeemterBuilderPlot(
        particle_size_um=float(bs_dp.value),
        packing_lambda=float(bs_lambda.value),
        diffusion_dm=float(bs_dm.value),
        obstruction_gamma=0.6,
        c_s_ms=float(bs_cs.value),
        c_m_ms=float(bs_cm.value),
        config=replace(plot_config, show_legend=True,
                       show_operating_point=True),
        title=None,
    )

    def _vd_csv() -> bytes:
        df = pd.DataFrame(_vd.data_columns())
        df["operating_point"] = _vd.operating_point()
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        return buf.getvalue().encode()

    _mech_tab = mo.vstack([
        mo.md(
            r"Each broadening mechanism drawn as its own limb under the "
            r"total: **A** (eddy diffusion — packing and particle size, "
            r"flat in \(u\)), **\(B/u\)** (longitudinal diffusion, dominant "
            r"when slow), and the two **\(C \cdot u\)** mass-transfer terms "
            r"(dominant when fast). \(\gamma\) is fixed at 0.6 (a typical "
            r"packed-bed obstruction factor). The diamond marks the "
            r"closed-form optimum "
            r"\(u_{\mathrm{opt}} = \sqrt{B/C}\), "
            r"\(H_{\mathrm{min}} = A + 2\sqrt{BC}\)."
        ),
        mo.hstack([bs_dp, bs_lambda], gap=1),
        mo.hstack([bs_dm, bs_cs, bs_cm], gap=1),
        mo.ui.plotly(_vd.figure()),
        mo.download(data=_vd_csv, filename="van_deemter_terms.csv",
                    label="Term curves (CSV)"),
    ], gap=0.75)

    # ---- Peak-shape tab ----
    if bs_error is not None or bs_result is None:
        _shape_tab = mo.callout(mo.md(bs_error or "Run unavailable."),
                                kind="warn")
    else:
        _plot = PlateShapePlot(
            bs_result,
            config=replace(plot_config, show_legend=True,
                           show_operating_point=True),
            title=None,
        )

        def _shape_csv() -> bytes:
            df = pd.DataFrame(_plot.data_columns())
            df["operating_point"] = _plot.operating_point()
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            return buf.getvalue().encode()

        _r = bs_result
        _ideal_as = _plot.ideal_asymmetry
        _readout = pd.DataFrame({
            "Quantity": [
                "Peak maximum t_max (transfers)",
                "Ideal t_R = N(1+k) (transfers)",
                "First moment (transfers)",
                "Sigma (transfers)",
                "Apparent plates N_app",
                "Built-in plates N",
                "Asymmetry As (10 %)",
                "Ideal-profile As (10 %)",
                "Mass recovered",
            ],
            "Value": [
                f"{_r.t_max:.0f}",
                f"{_r.n_plates * (1 + _r.k_linear):.0f}",
                f"{_r.t_mean:.1f}",
                f"{_r.sigma:.2f}",
                f"{_r.n_apparent:.0f}",
                f"{_r.n_plates}",
                "n/a" if _r.asymmetry is None else f"{_r.asymmetry:.2f}",
                "n/a" if _ideal_as is None else f"{_ideal_as:.2f}",
                f"{_r.recovered:.4f}",
            ],
        })
        _notes = ([mo.callout(mo.md(bs_notice), kind="info")]
                  if bs_notice else [])
        _shape_tab = mo.vstack(_notes + [
            mo.md(
                r"A plate cascade with a **nonlinear isotherm** "
                r"\(q = \dfrac{aC}{1 + bC}\), against the exact "
                r"linear-isotherm profile "
                "(dashed). Positive curvature (Langmuir): the loaded band's "
                "front self-sharpens and the rear diffuses — **tailing**, "
                "with the maximum arriving *earlier* as load rises. "
                "Negative curvature: the mirror — **fronting**, maximum "
                "*later*. Compare As against the ideal profile's own As: "
                "the ideal is itself slightly right-skewed at finite N, so "
                "asymmetry only means something against that baseline. The "
                "τ slider adds slow-desorption tailing — the *other* "
                "classic tailing mechanism, present at any load."
            ),
            mo.hstack([bs_plates, bs_k], gap=1),
            mo.hstack([bs_curvature, bs_load], gap=1),
            mo.hstack([bs_injection, bs_tau], gap=1),
            mo.ui.plotly(_plot.figure()),
            mo.ui.table(_readout, selection=None, show_download=False),
            mo.download(data=_shape_csv, filename="band_shape_profile.csv",
                        label="Profile (CSV)"),
        ], gap=0.75)

    bandshape_section = mo.vstack([
        mo.md(
            "*A single-solute sandbox in reduced units (time = transfers, "
            "one transfer = one plate volume) — a mechanism explorer, "
            "deliberately separate from the validated instrument models. "
            "Linear-isotherm runs reproduce the exact closed form "
            "(validation/compare_bandshape.py).*"
        ),
        mo.ui.tabs({
            "Mechanisms (van Deemter)": _mech_tab,
            "Peak shape (overload)": _shape_tab,
        }),
    ], gap=0.5)
    return (bandshape_section,)


@app.cell
def _():
    # CE engine import is GUARDED: drylab/ce.py is a SPYCE derivative and is
    # gitignored pending a licence grant, so it is absent from a clean clone
    # and from the WASM artifact. The section must degrade to an explanation
    # rather than break the app.
    try:
        from drylab.ce import (
            CE_ION_LIBRARY,
            CEConditions,
            CESpecies,
            grid_positions,
            joule_report,
            simulate_cze,
            validate_composition,
        )
        CE_AVAILABLE = True
    except ImportError:
        CEConditions = CESpecies = grid_positions = simulate_cze = None
        joule_report = None
        CE_ION_LIBRARY = {}

        def validate_composition(rows, working_ph=7.0):
            return [], []

        CE_AVAILABLE = False
    return (CE_ION_LIBRARY, CEConditions, CESpecies, CE_AVAILABLE,
            grid_positions, joule_report, simulate_cze, validate_composition)


@app.cell
def _(mo):
    ce_length_mm = mo.ui.slider(10, 60, value=30, step=5,
                                label="Capillary length (mm)")
    ce_voltage = mo.ui.slider(200, 1500, value=500, step=50,
                              label="Applied voltage (V)")
    ce_time_s = mo.ui.slider(6, 60, value=20, step=2,
                             label="Run time (s)")
    ce_points = mo.ui.dropdown({"65": 65, "129": 129, "257": 257},
                               value="129", label="Grid points")
    ce_detector_mm = mo.ui.slider(5.0, 28.0, value=15.0, step=1.0,
                                  label="Detector position (mm)")
    # Electroosmotic flow. Bare fused silica gives roughly 40-70e-9 above
    # pH 6, falling toward zero below pH 3 as the silanols protonate; a
    # coated capillary suppresses it deliberately. With EOF strong enough,
    # anions are swept to the same detector as cations, which is what makes
    # a single CZE run able to see both.
    ce_eof = mo.ui.slider(0.0, 80.0, value=0.0, step=5.0,
                          label="EOF mobility (1e-9 m2/Vs)")
    ce_overlay = mo.ui.dropdown({"pH": "ph", "Conductivity": "conductivity",
                                 "None": "none"}, value="None",
                                label="Overlay")
    # Composition editor. Columns mirror what a method actually specifies:
    # what the ion is, its charge and mobility, its pKa, how much, and
    # whether it fills the capillary (BGE) or is injected as a plug
    # (Sample). Mobility is in 1e-9 m2/Vs, the unit tables are published in.
    ce_composition = mo.ui.data_editor(
        pd.DataFrame({
            "name": ["acetate", "Tris", "potassium K+", "sodium Na+",
                     "lithium Li+"],
            "valence": [-1, 1, 1, 1, 1],
            "mobility_e9": [-42.4, 29.5, 76.2, 51.9, 40.1],
            "p_ka": [4.756, 8.076, 14.0, 14.0, 14.0],
            "concentration_mM": [20.0, 12.0, 1.0, 1.0, 1.0],
            "role": ["BGE", "BGE", "Sample", "Sample", "Sample"],
        }),
        label="Composition",
    )
    # The march is gated behind this: parameter sliders must NOT trigger a
    # multi-second solve on every drag (ruled 2026-08-05).
    ce_run = mo.ui.run_button(label="Run CE simulation")
    return (ce_composition, ce_detector_mm, ce_eof, ce_length_mm,
            ce_overlay, ce_points, ce_run, ce_time_s, ce_voltage)


@app.cell
def _(CEConditions, CESpecies, CE_AVAILABLE, ce_composition, ce_eof,
      ce_length_mm, ce_points, ce_run, ce_time_s, ce_voltage, diagnostics,
      grid_positions, np, simulate_cze, validate_composition):
    # Read and validate the composition table BEFORE marching. Same ruled
    # policy as the gradient and GC program editors: a blank row is a
    # half-finished edit and is dropped with a notice; contradictions are
    # named and refused; things that are legal but surprising are warnings
    # that do not block.
    _rows = []
    _incomplete = 0
    for _r in ce_composition.value.itertuples(index=False):
        _vals = (_r.name, _r.valence, _r.mobility_e9, _r.p_ka,
                 _r.concentration_mM, _r.role)
        if any(v is None or (isinstance(v, float) and v != v) or
               (isinstance(v, str) and not v.strip()) for v in _vals):
            _incomplete += 1
            continue
        _rows.append({
            "name": str(_r.name).strip(),
            "valence": int(_r.valence),
            "mobility": float(_r.mobility_e9) * 1e-9,
            "p_ka": float(_r.p_ka),
            "concentration_mM": float(_r.concentration_mM),
            "role": str(_r.role).strip(),
        })
    _bad_role = sorted({r["role"] for r in _rows
                        if r["role"] not in ("BGE", "Sample")})

    ce_error = None
    ce_notice = None
    ce_warnings = []
    ce_field = None

    if not CE_AVAILABLE:
        ce_error = (
            "**CE engine not installed.** `drylab/ce.py` is a restructured "
            "derivative of SPYCE, which currently ships with no licence "
            "grant, so it is excluded from the repository and from the "
            "deployed build."
        )
    elif _bad_role:
        ce_error = ("Role must be `BGE` or `Sample`; found "
                    + ", ".join(repr(b) for b in _bad_role) + ".")
    else:
        _errs, ce_warnings = validate_composition(_rows)
        if _incomplete:
            ce_notice = (f"{_incomplete} composition row(s) are incomplete "
                         f"and were ignored.")
        if _errs:
            ce_error = "  \n".join("- " + e for e in _errs)

    if ce_error is None and ce_run.value:
        with diagnostics.capture("CE") as _ce_failed:
            _cond = CEConditions(
                length_m=float(ce_length_mm.value) / 1000.0,
                voltage_v=float(ce_voltage.value),
                n_points=int(ce_points.value),
                t_final_s=float(ce_time_s.value),
                eof_mobility=float(ce_eof.value) * 1e-9,
                save_every=3,
            )
            _sp = [CESpecies(r["name"], (r["valence"],), (r["mobility"],),
                             (r["p_ka"],)) for r in _rows]
            _x = grid_positions(_cond)
            _c = np.zeros((len(_rows), _cond.n_points))
            for _i, _r in enumerate(_rows):
                if _r["role"] == "BGE":
                    _c[_i] = _r["concentration_mM"]
                else:
                    # Injected plug. Cations migrate toward increasing x and
                    # anions toward decreasing x, so the plug is placed
                    # upstream of the detector for whichever the sample is.
                    # Placement follows the APPARENT mobility (mu_ep +
                    # mu_eof), not the charge: with strong EOF an anion
                    # still travels toward the cathode, and placing it by
                    # sign alone would send it away from the detector.
                    _mu_app = [q["mobility"] + _cond.eof_mobility
                               for q in _rows if q["role"] == "Sample"]
                    _cathodic = sum(_mu_app) >= 0.0
                    _centre = (0.2 if _cathodic else 0.8) * _cond.length_m
                    _c[_i] = _r["concentration_mM"] * np.exp(
                        -((_x - _centre) / 0.0008) ** 2)
            ce_field = simulate_cze(_sp, _c, _cond)
        if ce_field is None:
            ce_error = (f"CE simulation failed: "
                        f"{_ce_failed[0] if _ce_failed else 'unknown'}")
    return ce_error, ce_field, ce_notice, ce_warnings


@app.cell
def _(ce_field, mo):
    # Scrubbing control. Free: it re-slices the stored field, never re-solves.
    _n = ce_field.times_s.size if ce_field is not None else 1
    ce_time_idx = mo.ui.slider(0, max(_n - 1, 1), value=_n - 1, step=1,
                               label="Time slice")
    return (ce_time_idx,)


@app.cell
def _(CEElectropherogramPlot, CEProfilePlot, ce_current_ua, ce_detector_mm,
      ce_composition, ce_error, ce_field, ce_notice, ce_overlay, ce_run,
      ce_time_idx, ce_warnings, joule_report, mo, np, pd,
      ph_from_hydronium, plot_config, replace):
    if ce_error is not None:
        ce_panel = mo.callout(mo.md(ce_error), kind="warn")
    elif ce_field is None or not ce_run.value:
        ce_panel = mo.callout(
            mo.md("Set the conditions, then press **Run CE simulation**. "
                  "Parameter changes deliberately do not trigger the solve; "
                  "the time slider afterwards is free."),
            kind="info")
    else:
        _r = ce_field
        _k = min(int(ce_time_idx.value), _r.times_s.size - 1)
        _cfg = replace(plot_config, show_legend=True)
        if ce_overlay.value == "ph":
            _ov = ph_from_hydronium(_r.hydronium[:, _k])
        elif ce_overlay.value == "conductivity":
            _ov = _r.conductivity[:, _k]
        else:
            _ov = None
        # BGE membership comes from the table's Role column, so renaming an
        # ion cannot silently change which traces are hidden.
        _roles = dict(zip(ce_composition.value["name"].astype(str).str.strip(),
                          ce_composition.value["role"].astype(str).str.strip()))
        _bge = {n for n in _r.species_names if _roles.get(n) == "BGE"}
        _profile = CEProfilePlot(
            _r.position_mm, _r.concentrations[:, :, _k], _r.species_names,
            overlay_values=_ov, overlay=ce_overlay.value, hidden=_bge,
            current_density=_r.current_density,
            capillary_length_mm=float(_r.position_mm.max()),
            config=_cfg, title=None,
        ).figure()
        _node, _traces = _r.detector_trace(float(ce_detector_mm.value))
        _epg = CEElectropherogramPlot(
            _r.times_s, _traces, _r.species_names, hidden=_bge,
            detector_position_mm=float(_r.position_mm[_node]),
            current_density=_r.current_density,
            config=_cfg, title=None,
        ).figure()
        # Migration time and peak width per analyte, from the detector
        # trace: the numbers a student would read off an electropherogram.
        _rows = []
        for _i, _nm in enumerate(_r.species_names):
            if _nm in _bge:
                continue
            _sig = _traces[_i]
            if float(_sig.max()) <= 1e-9:
                _rows.append({"Analyte": _nm, "Migration time (s)": "did not elute",
                              "Peak height (mM)": 0.0, "Mobility (1e-9 m2/Vs)": ""})
                continue
            _j = int(np.argmax(_sig))
            _half = _sig.max() / 2.0
            _above = np.where(_sig >= _half)[0]
            _w = (float(_r.times_s[_above[-1]] - _r.times_s[_above[0]])
                  if _above.size > 1 else 0.0)
            # Apparent mobility measured back out of the run: the quantity
            # an analyst actually reports, and the one that makes EOF
            # visible (a neutral marker returns mu_eof itself).
            _dist = (float(_r.position_mm[_node])
                     - float(_r.position_mm[np.argmax(
                         _r.concentrations[_i, :, 0])])) / 1000.0
            _t = float(_r.times_s[_j])
            _mu_app = (_dist / (_t * _r.conditions.field_v_per_m) * 1e9
                       if _t > 0 and _r.conditions.field_v_per_m else float("nan"))
            _rows.append({
                "Analyte": _nm,
                "Migration time (s)": round(_t, 2),
                "Apparent mobility (1e-9)": round(_mu_app, 1),
                "Peak width FWHM (s)": round(_w, 2),
                "Peak height (mM)": round(float(_sig.max()), 3),
            })
        _summary = pd.DataFrame(_rows)

        # Joule heating, from the conductivity the run actually produced
        # rather than a nominal value: it is the electrolyte that sets it.
        _power, _dt, _joule_warn = joule_report(
            float(np.median(_r.conductivity[:, _k])),
            _r.conditions.field_v_per_m,
            _r.conditions.diameter_m,
        )

        _notices = []
        for _jw in _joule_warn:
            _notices.append(mo.callout(mo.md(_jw), kind="warn"))
        if ce_notice:
            _notices.append(mo.callout(mo.md(ce_notice), kind="info"))
        for _w in ce_warnings:
            _notices.append(mo.callout(mo.md(_w), kind="warn"))

        ce_panel = mo.vstack(_notices + [
            mo.md(f"**t = {_r.times_s[_k]:.1f} s** of "
                  f"{_r.times_s[-1]:.0f} s | {_r.n_steps} adaptive steps | "
                  f"detector node at {_r.position_mm[_node]:.1f} mm"),
            ce_time_idx,
            mo.md("**Spatial profile** - concentrations along the capillary"),
            mo.ui.plotly(_profile),
            mo.md("**Electropherogram** - detector trace over the whole run"),
            mo.ui.plotly(_epg),
            mo.md(
                "**Sample:** "
                + ", ".join(
                    f"{n} ({c:g} mM)" for n, c in zip(
                        ce_composition.value["name"],
                        ce_composition.value["concentration_mM"])
                    if _roles.get(str(n).strip()) == "Sample")
                + " in "
                + ", ".join(
                    f"{n} ({c:g} mM)" for n, c in zip(
                        ce_composition.value["name"],
                        ce_composition.value["concentration_mM"])
                    if _roles.get(str(n).strip()) == "BGE")
                + f". Field **{_r.conditions.field_v_per_m:.0f} V/m**, "
                f"Joule heating **{_power:.2f} W/m** "
                f"(radial dT {_dt:.2f} K), "
                f"background pH "
                f"**{float(np.median(-np.log10(_r.hydronium[:, _k] / 1000.0))):.2f}**."
            ),
            mo.md("**Migration times and resolution**"),
            mo.ui.table(_summary, selection=None, show_download=False),
            mo.md(
                "*Background electrolyte traces are hidden by default: at "
                "50-100 mM they are 25x the analyte concentration and would "
                "flatten the peaks. Click them in the legend to show them.*"
            ),
        ], gap=0.5)
    return (ce_panel,)


@app.cell
def _(ce_composition, ce_detector_mm, ce_eof, ce_length_mm, ce_overlay,
      ce_panel, ce_points, ce_run, ce_time_s, ce_voltage, mo, with_sidebar):
    ce_controls = mo.vstack([
        mo.md("### Capillary electrophoresis"),
        mo.md("*CZE - independent of the HPLC, Craig and GC models.*"),
        mo.md("**Capillary**"),
        ce_length_mm,
        ce_points,
        mo.md("**Electrical**"),
        ce_voltage,
        ce_time_s,
        mo.md("**Detection**"),
        ce_detector_mm,
        ce_eof,
        ce_overlay,
        mo.md("**Composition**"),
        mo.md("*Mobility in 1e-9 m2/Vs. Role is BGE (fills the capillary) "
              "or Sample (injected plug). A permanently charged cation "
              "needs a HIGH pKa; an anion a LOW one.*")
        .style({"font-size": "0.8em", "max-width": "300px"}),
        ce_composition,
        ce_run,
    ], gap=0.5)
    ce_section = with_sidebar(ce_controls, ce_panel)
    return (ce_section,)


@app.cell
def _(gc_compare_panel, gc_controls, gc_golay_panel, gc_panel, gc_prog_panel,
      mo, with_sidebar):
    gc_section = with_sidebar(
        gc_controls,
        mo.ui.tabs({
            "Isothermal": gc_panel,
            "Programmed": gc_prog_panel,
            "Compare": gc_compare_panel,
            "Golay": gc_golay_panel,
        }),
    )
    return (gc_section,)


@app.cell
def _(
    bandshape_section,
    ce_section,
    config_panel,
    craig_section,
    diagnostics_panel,
    gc_section,
    hplc_section,
    mo,
    theme_style,
):
    # ?tab=<key> opens the app on a chosen section, so an instructor can
    # hand out a link that lands directly on, e.g., the Craig apparatus
    # (?tab=craig). Same contract as the preset params: unknown or absent
    # keys fall back to the default (HPLC), so a stale link can only ever
    # be as wrong as the ordinary start state. Composable with the preset
    # params (?tab=hplc&hplc=ex3).
    _TAB_KEYS = {
        "hplc": "HPLC",
        "gc": "GC",
        "ce": "CE",
        "band": "Band shape",
        "craig": "Craig apparatus",
        "config": "Config",
        "diagnostics": "Diagnostics",
    }
    try:
        _raw = mo.query_params().get("tab")
    except Exception:
        _raw = None
    _initial_tab = _TAB_KEYS.get(str(_raw).lower() if _raw else "", "HPLC")

    _top_tabs = mo.ui.tabs(
        {
            "HPLC": hplc_section,
            "GC": gc_section,
            "CE": ce_section,
            "Band shape": bandshape_section,
            "Craig apparatus": craig_section,
            "Config": config_panel,
            "Diagnostics": diagnostics_panel,
        },
        value=_initial_tab,
    )

    mo.vstack([theme_style, _top_tabs], gap=0.5)
    return




@app.cell
def _(mo):
    mo.accordion(
        {
            "References": mo.md(
                """
                **The simulator this port is based on**

                1. Boswell, P. G.; Stoll, D. R.; Carr, P. W.; Nagel, M. L.;
                   Vitha, M. F.; Mabbott, G. A. *An Advanced, Interactive,
                   High-Performance Liquid Chromatography Simulator and
                   Instructor Resources.* **J. Chem. Educ.** 2013, *90* (2),
                   198-202.
                   [doi:10.1021/ed300117b](https://doi.org/10.1021/ed300117b)
                   - free full text:
                   [PMC3610537](https://pmc.ncbi.nlm.nih.gov/articles/PMC3610537/)
                2. Abate-Pella, D.; Boswell, P. G.; Stoll, D. R.; Carr, P. W.
                   *An open-source simulator for exploring HPLC theory.*
                   **LC-GC North America** 2015, *33* (3), 200-207.
                   [Record](https://experts.umn.edu/en/publications/an-open-source-simulator-for-exploring-hplc-theory)
                   - covers gradient delay and extra-column tubing directly.

                **Physics used by the model**

                3. Wilke, C. R.; Chang, P. *Correlation of diffusion
                   coefficients in dilute solutions.* **AIChE J.** 1955, *1*
                   (2), 264-270.
                   [doi:10.1002/aic.690010222](https://doi.org/10.1002/aic.690010222)
                   - the analyte diffusion coefficient.
                4. Thompson, J. D.; Carr, P. W. *High-Speed Liquid
                   Chromatography by Simultaneous Optimization of Temperature
                   and Eluent Composition.* **Anal. Chem.** 2002, *74* (16),
                   4150-4159.
                   [doi:10.1021/ac0112622](https://doi.org/10.1021/ac0112622)
                   - the backpressure treatment.
                5. Billen, J.; Broeckhoven, K.; Liekens, A.; Choikhet, K.;
                   Rozing, G.; Desmet, G. *Influence of pressure and
                   temperature on the physico-chemical properties of mobile
                   phase mixtures commonly used in high-performance liquid
                   chromatography.* **J. Chromatogr. A** 2008, *1210* (1),
                   30-44.
                   [doi:10.1016/j.chroma.2008.09.056](https://doi.org/10.1016/j.chroma.2008.09.056)
                   - source of the methanol/water viscosity fit.

                Every entry above was checked against its publisher record.
                The acetonitrile/water viscosity fit is credited in the
                original source to Chen & Horvath, *Analytical Methods and
                Instrumentation* 1993, *1*, 213-222; that citation is
                reproduced as given because no stable public record could be
                confirmed for it.

                **Software lineage**

                - Current web simulator:
                  [multidlc.org/hplcsim](https://www.multidlc.org/hplcsim/)
                - JavaScript port:
                  [mlibby/hplc_simulator](https://github.com/mlibby/hplc_simulator)

                *Derived from the HPLC Simulator by Paul Boswell, Peter Carr,
                and Dwight Stoll. License: CC BY-NC-SA 3.0 US.*

                ---

                **The capillary-electrophoresis engine**

                The CE section is a restructured derivative of **SPYCE 2.0**
                by Prateek Gupta and Supreet Singh Bahga (IIT Delhi), used
                with the authors' written permission on the condition that
                it remains freely available to the community (recorded in
                full in the repository's `NOTICE.md`). Cite these when
                publishing work that uses the CE model — the numerical
                method is theirs:

                6. Gupta, P.; Bahga, S. S. **Electrophoresis** 2021, *42*,
                   890-898.
                   [doi:10.1002/elps.202000259](https://doi.org/10.1002/elps.202000259)
                7. Bahga, S. S.; Gupta, P. *Electrophoresis simulations
                   using Chebyshev pseudo-spectral method on a moving
                   mesh.* **Electrophoresis** 2021, *42*, 2321-2328.
                   [doi:10.1002/elps.202100279](https://doi.org/10.1002/elps.202100279)

                The electroosmotic-flow model, Joule-heating estimates, ion
                library and all interface code are drylab's own; SPYCE
                remains the validation oracle for the transport core.

                **The GC model**

                8. Ported from
                   [GasChromatographySimulator.jl](https://github.com/JanLeppert/GasChromatographySimulator.jl)
                   (Jan Leppert, MIT licence; *J. Open Source Softw.* 5(55),
                   2391), which also serves as the validation oracle.
                   Retention parameters: Blumberg's K-centric thermodynamic
                   model (2017), as distributed with that package.

                **The Craig apparatus**

                9. Harvey, D. *Analytical Chemistry 2.0*, Appendix 16
                   (Countercurrent Separations) — the closed forms and the
                   worked examples the model is validated against.
                """
            )
        }
    )
    return


if __name__ == "__main__":
    app.run()

# drylab — a chromatography simulator in marimo

Python port of [mlibby/hplc_simulator](https://github.com/mlibby/hplc_simulator)
(JavaScript), itself derived from the **HPLC Simulator** by Paul Boswell,
Peter Carr, and Dwight Stoll ([hplcsimulator.org](http://www.hplcsimulator.org)).
**Isocratic and gradient** reversed-phase HPLC with an interactive
chromatogram, solvent-profile and band-track views, parameter sweeps
(van Deemter, k′ vs %B, backpressure vs flow), and CSV export.

**License: CC BY-NC-SA 3.0 US** (inherited from the reference; see LICENSE).

## Licensing and provenance

drylab is CC BY-NC-SA 3.0 US (inherited from its upstream HPLC reference).
The CE module derives from SPYCE, used with the authors' written
permission on the condition that it **remains available to the community
for free** — see `NOTICE.md`, which records the grant in full. That
obligation binds derivatives: do not put the CE module behind a paywall.

## Repository conventions

- **`dist/` is generated.** Regenerate with `python tools/build_wasm_notebook.py`;
  never edit it. It is tracked because it is the deployable, and marked
  `-diff linguist-generated` so it does not show up as reviewable source.
  A clean checkout rebuilds it byte-for-byte, so a dirty working tree after
  a build means the notebook and the artifact are out of step.
- **GC goldens are tracked; the others are not.** `golden_gc*.json` need
  Julia to regenerate, and shipping them is what lets `compare_gc.py` and
  `compare_gc_program.py` run with no external runtime. `golden.json` (Node)
  and `golden_java.json` (JDK) are regenerated on demand and gitignored.
- **`validation/reference_java/` is vendored upstream source** and is kept
  byte-for-byte, CRLF included (`-text`), so it can still be compared
  against the original distribution.
- **Version lives in `drylab/__version__`.** `pyproject.toml` derives it;
  the notebook and the build stamp read it. Do not restate it anywhere.

## Layout

- `drylab/` — the core: `data.py` (solvents, compounds, column presets),
  `formulae.py` (pure chromatographic formulae, units documented),
  `model.py` (`SimulationInputs` → `compute()` → `Results`).
- `drylab/plotting/` — reusable, config-driven Plotly classes:
  `ChromatogramPlot`, `SweepPlot`, `OverlayPlot` over a shared `PlotConfig`
  and `BasePlot`. Every figure is stamped with its operating point.
- `drylab_nb.py` — the marimo notebook (thin UI over the package).
- `drylab/gradient.py` — solvent-program mixing (plug delay + stirred
  tank) and bounded band marching.
- `drylab/craig.py` — Craig countercurrent extraction (Appendix 16 of
  Harvey, *Analytical Chemistry 2.0*). Standalone: shares no data or config
  with the HPLC model.
- `drylab/gc.py` — isothermal capillary GC, ported from
  GasChromatographySimulator.jl (Leppert, MIT; JOSS 5(55), 2391).
  Closed-form (no ODE in the shipped regime); vendored Blumberg (2017)
  retention data, 17 compounds × 3 stationary phases. Standalone: shares
  nothing with the HPLC or Craig models. Temperature programming is a
  parked extension (see issues.md).
- validation: seven oracle suites (~52,000 reference values against Julia, Java,
  JavaScript, Analytical Chemistry 2.0, SPYCE and exact closed forms) are
  maintained in the private development tree and pass before every release;
  they are not part of this repository.
  - JS reference (isocratic): `node dump_golden.js > golden.json` then
    `python compare_golden.py` — 3373 values, worst rel. err ≈ 4.5e-16.
  - Craig apparatus: `python compare_craig.py` — 530 values against Table
    A16.1, worked Examples A16.1–A16.3, and the Efstathiou applet's closed
    form, phase split and elution percentages.
  - Java applet (both modes): `javac -d /tmp/harness HplcHarness.java`,
    `java -cp /tmp/harness HplcHarness > golden_java.json`, then
    `python compare_java.py` — 26,544 values across 74 isocratic and 23
    gradient cases; gradient retention times are bit-identical. The harness
    is gated by a trust check against the JS goldens. **Java is a
    validation-time oracle only — it is not a runtime dependency.**
  - GC (isothermal): `python compare_gc.py` — 13,770 values across 810
    cases against a pre-generated dump from GasChromatographySimulator.jl
    (`golden_gc.json`). Covers all three stationary phases, two film
    thicknesses and 0.10–0.53 mm bores. Regenerate with `julia
    dump_golden_gc.jl <upstream-clone>`; it supports `--iso-only`,
    `--iso-range`, `--iso-tol`, `--prog-only`, `--prog-range` and
    `--with-uncertainty`, because the full grid no longer fits one run.
    Oracle tolerance is 1e-12/1e-10: at the original 1e-10/1e-8 the
    reference itself was under-converged at 0.53 mm with a vacuum outlet.
  - GC (temperature-programmed): `python compare_gc_program.py` — 11,520
    values across 720 cases, half vacuum-outlet, against
    `golden_gc_program.json`. Also asserts that a flat program reproduces
    the isothermal closed forms (≈8e-16). Tolerances are set from the
    oracle's own convergence, not chosen: under a program BOTH sides are
    numerical.
  - Oracle convergence study: `python oracle_convergence_gc.py` — compares
    three solver tolerances over a slice of the programmed grid to bound
    the reference's own error (~7.9e-10). This is what licenses the
    tolerances above.
  - Integrator cross-check: `python compare_integrator_scipy.py` — the
    hand-rolled RK45 against scipy's DOP853 on an identical right-hand
    side, and an AST check that no shipped module imports scipy.
    **scipy is a development-only dependency; the 35 MB wheel must never
    enter the WASM build.**
    **Julia is a validation-time oracle only — it is not a runtime
    dependency.**
- `tools/build_wasm_notebook.py` — generates the self-contained notebook in
  `dist/` for browser/WASM deployment (build artifact: regenerate, don't edit).
- `.context/memory/` — working memory per MEMORY_DIRECTIVE.md.

## Run

```bash
pip install marimo numpy pandas plotly
marimo run drylab_nb.py     # app mode
marimo edit drylab_nb.py    # editable notebook
```

## Validate (requires node)

```bash
cd validation
node dump_golden.js > golden.json
python compare_golden.py golden.json
```

## Deploy to the web (Pyodide/WASM)

```bash
python tools/build_wasm_notebook.py
marimo export html-wasm dist/drylab_wasm_nb_v0_13_0.py -o site --mode run
python -m http.server -d site 8000
```

## Scope

Isocratic and gradient elution, both validated against the original Java
applet. Extra-column tubing broadening follows the Java ancestor (the JS
port had it commented out). Known gaps — the gradient σ injection-volume
term (reproduced from the Java, switchable), gradient sweeps, additional
column presets, and a per-compound concentration editor — are tracked in
`.context/memory/issues.md` with what unblocks each.

Non-viable conditions are reported, never hung: a band that does not reach
the outlet raises `NonElutingCompoundError`, and one that elutes past the
end of the run is flagged by `Results.viability_report()`.

GC runs isothermally or under a piecewise-linear temperature program
(`gc_program.GCProgram`), marched with a hand-rolled Dormand-Prince RK45 in
pressure rather than distance — which removes the vacuum-outlet singularity
analytically and keeps scipy (35 MB) out of the WASM build. The notebook's
GC section has Isothermal, Programmed and Compare tabs over one set of
controls, so the comparison differs only in the elution program.

The GC model follows the same policy in its own types: `gc.simulate()`
returns a `GCRun` and raises `NonElutingSoluteError` by default, while
`skip_non_eluting=True` excludes an over-retained solute and names it in
`GCRun.skipped` / `GCRun.viability_report()`. The notebook opts in, so one
over-retained solute cannot blank the chromatogram; library callers keep
fail-fast. Legend visibility is a per-section switch backed by
`PlotConfig.show_legend`.

Core library usage without the notebook:

```python
from drylab import SimulationInputs, compute, chromatogram
res = compute(SimulationInputs(flow_rate=1.0, solvent_percent=60))
t, per_compound, total = chromatogram(res)
print(res.operating_point(), res.backpressure_bar)

# Gradient
from drylab import ElutionMode, GradientProgram
grad = compute(
    SimulationInputs(
        elution_mode=ElutionMode.GRADIENT,
        gradient_program=GradientProgram.from_rows([(0, 5), (10, 95)]),
    ),
    track_bands=True,
)
print([(c.name, round(c.t_r, 1)) for c in grad.compounds])
print(grad.viability_report())  # None when every analyte elutes in the run
```

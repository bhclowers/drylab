# drylab — a separation-science simulator that runs in your browser

drylab is an interactive teaching simulator for chromatography and
electrophoresis. It runs entirely in the browser (no install, no server —
Python compiled to WebAssembly) or locally as a [marimo](https://marimo.io)
notebook, and it was built to accompany a graduate separation-science
course: every control exists so that a student can *predict what a knob
will do, turn it, and reconcile*.

## What you can do with it

**HPLC** — reversed-phase liquid chromatography, isocratic and gradient,
with a 22-compound library on a C18 column. Watch the chromatogram respond
live to solvent strength, solvent identity (acetonitrile ↔ methanol),
temperature, flow, column geometry and particle size. Includes parameter
sweeps (van Deemter, k′ vs %B, backpressure vs flow), a gradient designer
with dwell-volume realism, band-track views that show each analyte's k′
collapsing as the gradient front arrives, and a results table with
adjacent-pair resolution and selectivity.

**GC** — capillary gas chromatography: 17 solutes (alkanes, alcohols,
ketones) on three stationary phases from non-polar to Wax, with He/H₂/N₂
carriers, pressure control down to vacuum outlets, isothermal and
temperature-programmed elution, a Compare tab that overlays both modes on
identical pneumatics, and a Golay tab showing plate height vs carrier
velocity for all three gases at once.

**CE** — capillary zone electrophoresis with real acid–base equilibrium
chemistry: an editable background electrolyte and sample composition, an
electroosmotic-flow control (the "pH knob"), and Joule-heating estimates
that show where voltage stops buying plates.

**Band shape** — a mechanism sandbox: build the van Deemter curve one
broadening term at a time (eddy, longitudinal diffusion, mass transfer),
and overload a model column with a curved isotherm to produce genuine
tailing and fronting — with the exact linear-isotherm profile always drawn
as the honest baseline.

**Craig apparatus** — countercurrent extraction, the conceptual bridge
from the separatory funnel to the theoretical plate: watch band centers
separate linearly in transfer count while widths grow only as its square
root.

**Built for the classroom.** Sidebar preset menus (also selectable by URL,
e.g. `?hplc=ex3&gc=ex5b`) drop every student into an identical scenario,
and `?tab=` opens the app on a chosen section (`hplc`, `gc`, `ce`,
`band`, `craig` — e.g. `?tab=craig` lands directly on the Craig
apparatus; parameters combine: `?tab=hplc&hplc=ex3`);
every CSV export is stamped with the operating point that produced it, so
homework arrives traceable. A POGIL-style exercise set and instructor key
are developed alongside the simulator.

## Try it / run it

Deployed as a static site via GitHub Pages (see `DEPLOY.md`; ~28 MB first
load while Pyodide fetches the scientific wheels). Locally:

```bash
pip install marimo numpy pandas plotly
marimo run drylab_nb.py     # app mode
marimo edit drylab_nb.py    # editable notebook
```

Core library usage without the notebook:

```python
from drylab import SimulationInputs, compute, chromatogram
res = compute(SimulationInputs(flow_rate=1.0, solvent_percent=60))
t, per_compound, total = chromatogram(res)
print(res.operating_point(), res.backpressure_bar)
```

## Is it right? — validation

Every model is checked against an external reference or an exact closed
form, and the suites run before every release:

- **HPLC**: 26,544 values against the original Java applet (gradient
  retention times bit-identical) and 3,373 against the JavaScript
  reference (worst relative error ≈ 4.5e-16).
- **GC**: 13,770 isothermal and 11,520 temperature-programmed values
  against GasChromatographySimulator.jl, with tolerances set from the
  oracle's own measured convergence.
- **CE**: peak positions, mass conservation and background pH against
  stock SPYCE.
- **Craig**: 530 values against *Analytical Chemistry 2.0* Appendix 16 and
  the Efstathiou applet's closed forms.
- **Band shape**: the plate cascade reproduces its exact negative-binomial
  closed form to ~1e-14, plus physical invariants for the nonlinear
  regime.
- validation: seven oracle suites (~52,000 reference values against Julia, Java,
  JavaScript, Analytical Chemistry 2.0, SPYCE and exact closed forms) are
  maintained in the private development tree and pass before every release;
  they are not part of this repository.

## References

If you use drylab in teaching or publications, cite the models it stands
on (these are also in the app's References tab and in `NOTICE.md`):

- **HPLC**: Boswell, P. G.; Stoll, D. R.; Carr, P. W.; Nagel, M. L.;
  Vitha, M. F.; Mabbott, G. A. *J. Chem. Educ.* **2013**, *90*, 198–202.
  doi:10.1021/ed300117b — via the JavaScript port
  [mlibby/hplc_simulator](https://github.com/mlibby/hplc_simulator).
- **CE**: the transport core is a restructured derivative of **SPYCE 2.0**
  (Gupta & Bahga, IIT Delhi), used with the authors' written permission on
  the condition that it remains freely available to the community
  (`NOTICE.md` records the grant in full):
  - Gupta, P.; Bahga, S. S. *Electrophoresis* **2021**, *42*, 890–898.
    doi:10.1002/elps.202000259
  - Bahga, S. S.; Gupta, P. Electrophoresis simulations using Chebyshev
    pseudo-spectral method on a moving mesh. *Electrophoresis* **2021**,
    *42*, 2321–2328. doi:10.1002/elps.202100279
- **GC**: ported from and validated against
  [GasChromatographySimulator.jl](https://github.com/JanLeppert/GasChromatographySimulator.jl)
  (Jan Leppert, MIT; *J. Open Source Softw.* 5(55), 2391), carrying
  Blumberg's (2017) K-centric retention parameters as distributed with it.
- **Craig**: Harvey, D. *Analytical Chemistry 2.0*, Appendix 16.

## Licensing and provenance

drylab is **CC BY-NC-SA 3.0 US** (inherited from its upstream HPLC
reference; see `LICENSE`). The CE module derives from SPYCE, used with the
authors' written permission on the condition that it **remains available
to the community for free** — see `NOTICE.md`, which records the grant in
full. That obligation binds derivatives: do not put the CE module behind a
paywall.

## Layout

- `drylab/` — the core package: `data.py` (solvents, compounds, column
  presets), `formulae.py` (pure chromatographic formulae, units
  documented), `model.py` (`SimulationInputs` → `compute()` → `Results`,
  including adjacent-pair `pair_metrics()`), `gradient.py` (solvent
  programs and band marching), `gc.py` + `gc_program.py` (closed-form
  isothermal GC and the pressure-domain programmed march), `ce.py` (the
  SPYCE-derived CZE engine), `craig.py`, `bandshape.py` (van Deemter
  builder and the nonlinear-isotherm plate cascade).
- `drylab/plotting/` — config-driven Plotly classes over a shared
  `BasePlot`; every figure is stamped with its operating point, and every
  CSV export is built from the same object as its figure.
- `drylab_nb.py` — the marimo notebook (thin UI over the package).
- `tools/build_wasm_notebook.py` — generates the self-contained notebook
  in `dist/` for browser deployment (build artifact: regenerate, don't
  edit). `tools/build_publish_repo.py` — builds the publication
  repository.

## Repository conventions

- **`dist/` is generated.** Regenerate with
  `python tools/build_wasm_notebook.py`; never edit it. It is tracked
  because it is the deployable, and a clean checkout rebuilds it
  byte-for-byte — a dirty tree after a build means the notebook and the
  artifact are out of step (CI enforces this).
- **Version lives in `drylab/__init__.py`.** `pyproject.toml` derives it;
  the notebook and the build stamp read it. Do not restate it anywhere.
- **Non-viable conditions are reported, never hung**: bands that cannot
  elute raise typed errors or are excluded by name
  (`viability_report()`); the notebook opts into exclusion so one
  over-retained solute cannot blank a chromatogram.

## Deploy to the web (Pyodide/WASM)

```bash
python tools/build_wasm_notebook.py
pip install uv   # newer marimo requires it for html-wasm export
marimo export html-wasm dist/drylab_wasm_nb_v<latest>.py -o site --mode run
python -m http.server -d site 8000
```

See `DEPLOY.md` for GitHub Pages and `GITHUB_SETUP.md` for first-time
repository setup.

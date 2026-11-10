# decisions

## 2026-08-03 — Target platform is marimo [HUMAN]
Jupyter/ipywidgets considered and rejected; user briefly said "jupyter" then
confirmed marimo when the fork was raised. Core is factored so a Jupyter
front-end later is additive, not a rewrite.

## 2026-08-03 — Package + thin notebook, not single-file [HUMAN, adopting assistant recommendation]
`hplc_sim/` is the single source of truth; `hplc_simulator_nb.py` imports it.
WASM/Pyodide deployment gets a generated self-contained variant via
`tools/build_wasm_notebook.py` (embeds module sources between the
`[[INLINE:hplc_sim:...]]` sentinels). The generated file in `dist/` is a
build artifact — never edit, always regenerate.

## 2026-08-03 — v1 is isocratic-only [HUMAN]
Matches what the JS reference actually implements (its gradient mode is a
NaN stub). Gradient is parked in issues.md.

## 2026-08-03 — Validation kept permanently [HUMAN: "keep both for now"]
Both halves stay in-repo as a chartered validation run: `validation/
dump_golden.js` (node, runs the vendored reference) and `validation/
compare_golden.py` (recomputes with hplc_sim, fails loudly per quantity).
Status at adoption: PASS, 3373 values / 72 cases, worst rel. err ~4.5e-16.

## 2026-08-03 — Vendored the five reference JS model files [ASSISTANT]
Copied into `validation/reference_js/` so the golden dump is reproducible
without the upstream repo. CC BY-NC-SA 3.0 US permits this with attribution
(kept in README); whole project carries the same license.

## 2026-08-03 — Observer graph replaced by pure compute() [ASSISTANT]
The JS reference's getter/setter update graph is not ported; marimo cell
reactivity provides dependency propagation. `compute(SimulationInputs) ->
Results` is the one pipeline; `Results` carries its operating point.

## 2026-08-03 — Gradient mode raises, never NaN [ASSISTANT]
`GradientNotImplementedError` with a diagnostic replaces the reference's
silent `NaN` (charter §8).

## 2026-08-03 — Numba omitted for v1 [ASSISTANT, per "numba if necessary"]
Measured need absent: full compute + 3000-point chromatogram is microseconds
in vectorized numpy. Revisit if gradient elution (per-compound numerical
integration over the gradient program) lands.

## 2026-08-03 — Detector noise is opt-in, seeded, sum-trace only [ASSISTANT]
The reference declares a `noise` input but no use of it was found in its
model code (see issues.md). Port implements uniform ±noise/2 on the summed
trace, only when an explicit seeded RNG is supplied — reproducibility over
mimicry of unlocated behavior.

## 2026-08-04 — UI ranges and noise variable [HUMAN, ranges partly ASSISTANT-chosen]
Human ruled: wider injection range; detector time constant max 5 s; noise
magnitude a variable; operating-point metadata as a table (renders under the
chromatogram in an accordion and in the Results tab; exports keep the string
stamp). Assistant chose injection range 0.1-500 uL pending confirmation
("wider" was not quantified). Noise wiring: amplitude lives in
SimulationInputs.noise (0 = off), switch gates it, seed unchanged.

## 2026-08-04 — v0.2.0 [ASSISTANT]
Version bump for the yaxis2-clobber fix + notebook features; dist artifact
regenerated as hplc_simulator_wasm_nb_v0_2_0.py, v0.1.0 artifact removed.

## 2026-08-04 — Original Java applet source (v1.1.3) adopted as ground truth [HUMAN supplied source; ASSISTANT extraction]
User provided the HPLC Simulator Java source from hplcsimulator.org.
Adopted as the ancestor reference; Globals.java + HPLCSimulatorApplet.java
vendored under validation/reference_java/. Compound table (22 analytes,
LSST coefficients both solvents + molar volumes) extracted programmatically
with strict labeled-row parsing; the 5 compounds shared with the JS port
verified byte-identical before regeneration. Notebook gained an analyte
multiselect (classic five keep reference concentrations; newly enabled
analytes use a named default of 10.0). v0.3.0.

## 2026-08-04 — Operating point rendered as compact markdown table [HUMAN: "crowded", ASSISTANT fix]
mo.ui.table brought search/Columns/Explore chrome and dtype captions to a
9-row key/value display and collided with the controls column. Replaced
with a plain markdown table in both the chromatogram accordion and the
Results tab. v0.3.1.

## 2026-08-04 — Gradient elution implemented; seven rulings [HUMAN]
1. GO on gradient (reverses the 2026-08-03 isocratic-only ruling).
2. Layout B: nested mode tabs (Isocratic | Gradient | Compare), each mode
   owning its own views.
3. Inputs SHARED across modes (incl. flow rate); only the elution program is
   mode-specific. Built once in one cell so the two modes provably differ
   only in the program.
4. Gradient sigma reproduces the Java's omission of the injection-volume
   term; the term is available behind
   SimulationInputs.gradient_sigma_includes_injection (default False).
   "Fix later" is the standing intent.
5. Tubing broadening follows the JAVA ancestor: added to sigma in both
   modes. Zero-length tubing yields exactly 0.0, so JS goldens still pass.
6. Validation via a Java harness (validation/HplcHarness.java) that is an
   ORACLE ONLY; the shipped port is pure Python with no Java runtime
   dependency. Harness gated by a trust check against the JS goldens.
7. No hang on non-viable conditions: bounded march raising
   NonElutingCompoundError, PLUS viability reporting (see learnings) since
   the real-world failure is absurd-but-finite tR, not an infinite loop.
v0.4.0.

## 2026-08-04 — Fast-fail guard for unviable gradient methods [HUMAN: "students are unpredictable"]
Two layers, both named and configurable, neither altering physics:
- Cheap pre-check (estimate_march_steps): k' at the strongest composition in
  the program x t0/dt. Refuses at PRECHECK_BUDGET_MULTIPLE (4x) the budget,
  before any marching -> 0.7 ms refusal instead of 600-1200 ms grind.
- SimulationInputs.march_step_budget (default 100,000 steps/compound) as the
  in-march backstop. None disables both; validation sets None so the port
  still reproduces the reference on pathological cases.
Budget sized from measurement: ordinary methods < 2,500 steps, legitimately
slow-but-usable ~28,000, so 100,000 leaves ~4x headroom.
compute(..., skip_non_eluting=True) reports and excludes runaway analytes
instead of raising; the notebook uses it so one bad analyte cannot blank the
gradient view. Library default stays fail-fast. v0.4.1.

## 2026-08-04 — Theming, About card, verified references [HUMAN]
- Intro text moved into an "About this simulator" accordion card.
- Config tab: theme picker (Studio default, Future Imperfect, Strongly
  Typed, Dopetrope), light/dark radio (Follow theme / Light / Dark), and a
  switch for the notebook CSS layer.
- Two-tier theming by design: figure styling flows through PlotConfig
  (fully controlled, always reliable); notebook styling uses only marimo's
  three documented CSS variables and is switchable off, because marimo
  explicitly does not guarantee other selectors across versions.
- HTML5 UP palettes are ORIGINAL work evoking those templates, not copies of
  their CSS: the templates are CC BY 3.0 while this project is CC BY-NC-SA
  3.0 US, and redistributing their stylesheets would tangle the licenses.
  Attribution and links included in the Config tab.
- References section lists only entries verified against publisher records
  (5 with DOIs). Chen & Horvath 1993 is reproduced as cited in the source
  with an explicit note that it could not be independently confirmed.
v0.5.0.

## 2026-08-04 — Diagnostics tab + signal-unit clarification [HUMAN]
- hplc_sim/diagnostics.py: DiagnosticsLog, bounded (50) and deduplicating,
  mirrors every record to stderr so terminal users keep the normal stream
  while web/WASM students see the same errors in a Diagnostics tab (marimo
  ships show_tracebacks:false, so failures are otherwise invisible in-app).
  Log lives in a dependency-free cell so it survives cell re-runs.
- Units INVESTIGATED, not merely relabelled: the Java Concentration field is
  labelled uM (ChemicalDialog.java) and its y-axis is "Signal, moles/liter"
  with SI prefixing. w = (uL->L) x umol/L = umol; signal = w/(sqrt(2pi) sigma F)
  = umol/L. The existing value was therefore CORRECT; only the presentation
  was poor. Now: y-axis "Signal, analyte in detector (umol/L)", results
  column "Conc. (uM)", and the convention documented in data.py, formulae.py
  and model.py. No numbers changed - both oracles still pass.
v0.6.0.

## 2026-08-04 — Bug fixes and unit presentation [HUMAN, from screenshot + traceback]
- Blank gradient rows: a newly added editor row is NaN. Treated as a
  half-finished edit, not an error: incomplete rows are dropped with a
  visible notice; fewer than two complete rows gives friendly guidance
  instead of a ValueError. Reproduced the reported failure as a mutation
  test before and after.
- Layout overlap: all shared controls now full_width=True, hstack widths
  3:8 with gap=2 and align="start". The overlap was fixed-width widgets
  overflowing a narrow column.
- Dark mode: rewritten around the standard CSS `color-scheme` property plus
  surface/ink colours on generic containers, rather than marimo internals.
  Noted that marimo's own theme setting wins for widgets it styles directly.
- Tubing i.d. now presented in mm; mils retained as the stored unit for
  reference fidelity, converted at the UI boundary via named helpers
  (MILS_PER_MM / mm_to_mils / mils_to_mm). Exact: 5 mils = 0.127 mm.
- degC -> °C, uL -> µL, um -> µm throughout labels and operating point.
v0.6.1. Both oracles unaffected (26,544 values still PASS).

## OPEN QUESTION — column presets [ASSISTANT, awaiting ruling]
Confirmed by source: exactly ONE preset exists in both references
(ColumnProperties.java:313 and the JS presets object). Adding more requires
either real fitted van Deemter coefficients per column (data we do not have)
or clearly-labelled geometry-only variants reusing the Zorbax packing model.
Not invented unilaterally (charter §4: never silently pick a domain value).

## 2026-08-05 — Dark mode removed; a.u. label; sidebar layout; gradient row sorting [HUMAN]
- Dark mode REMOVED as an option. It clashed with marimo's own theming.
  Theme.dark, the light/dark radio, and all background/text CSS are gone;
  themes now set fonts and accent only, so marimo's own light/dark setting
  stays authoritative and the two cannot fight. Future Imperfect's palette
  was deepened to stay legible on a light canvas.
- Y axis is now "Signal (a.u.)" in both modes. DISPLAY convention only: the
  computed quantity is still detector-cell concentration in umol/L, and
  "a.u." here means arbitrary units, NOT absorbance (which would need
  extinction coefficients the reference does not carry). Documented at the
  label definition so a later reader cannot mistake it.
- Layout: shared controls moved into mo.sidebar(width="340px"); the tab area
  now owns the page width. An hstack column could not reliably contain
  full-width widgets.
- Gradient rows out of temporal order are SORTED (from_rows(sort_by_time=
  True)) with a notice, rather than raising. Duplicate times -- the one case
  sorting cannot fix -- are named with actionable guidance. Library callers
  still get the strict error by default.
v0.7.0. Both oracles unaffected.

## 2026-08-05 — Layout: wrapping control bar above the tabs [HUMAN reported controls missing]
mo.sidebar (v0.7.0) hid the shared controls in the user's app view. Reverted.
Final arrangement: controls in a single mo.hstack(wrap=True) row of five
groups at natural widths, placed ABOVE the tabs, with no accordion (mo.accordion
starts collapsed and has no open-by-default option, which would reproduce the
same complaint). full_width=True removed from every control - it sized widgets
to the notebook width, which is what overflowed the column originally.
Layout is now purely vertical stacking, so horizontal overlap is impossible.
v0.7.1.

## 2026-08-05 — Craig apparatus tab [HUMAN supplied source]
Source is Appendix 16 "Countercurrent Separations" of D. Harvey, *Analytical
Chemistry 2.0* (after Craig, J. Biol. Chem. 1944, 155, 519-534), supplied as
PDF. The linked applet page could NOT be retrieved (dead Java, returns only
"This will not work in this browser"), so nothing was inferred from it; the
uploaded text is the sole authority.
- hplc_sim/craig.py implements A16.1 (q = V_aq/(D V_org + V_aq)), A16.2
  (binomial f(r,n)), mu = np, sigma = sqrt(npq), the np/nq > 5 normal-approx
  criterion, confidence intervals, pooled recovery and separation factor.
- Two independent paths (closed-form A16.2 and step-by-step extract/transfer
  simulation) are cross-checked against each other.
- DELIBERATELY standalone: shares no data or config with the HPLC model, per
  the human's instruction not to link the simulations.
- Number of tubes is a variable (4-100). Steps are bounded at tubes-1 because
  analyte reaches tube n after n steps; exceeding that would push analyte off
  the apparatus, which the source does not model. The UI clamps and says so.
- Stepped (hvh) plot, since the tube axis is discrete.
- Equations are displayed alongside the plot with their source numbering.
SOURCE TYPO recorded: Example A16.1 prints q_B = 1/(4+1) = 0.200 for
D_B = 0.5, inconsistent with its own p_B = 0.333. The implementation follows
equation A16.1 and p_B, i.e. q_B = 0.667, which reproduces every tabulated
fraction in that example.
Validation: validation/compare_craig.py, 108 values vs Table A16.1 and
Examples A16.1-A16.3. PASS.

## 2026-08-05 — Layout root cause found and fixed [HUMAN wanted sidebar + plot]
Side-by-side restored. The real defect in all earlier attempts: a flex child
defaults to min-width:auto, so neither column could shrink below its content
and the wider one overflowed its neighbour. Fixed by pinning the settings
column (flex: 0 0 320px) and giving the content column min-width: 0. Adjusting
widths= ratios could never have fixed this. v0.8.0.

## 2026-08-05 — Applet script supplied; adopted as a second Craig oracle [HUMAN supplied source]
The user pasted the page's embedded (obfuscated) JavaScript. Deobfuscated by
hand; math recorded in validation/reference_applet/README.md (math only, no
code copied). Findings:
- calculateFractions computes C(n,i)*D^i/(D+1)^n and splits each tube into
  D*tot/(D+1) upper and tot/(D+1) lower. This is ALGEBRAICALLY IDENTICAL to
  A16.2 with p = D/(D+1). Applet and textbook are the same model; verified to
  1.2e-14 across 4 D values and n up to 60.
- calculateElution defines eluted = 1 - sum over tubes 0..Ntubes, and the
  applet lets transfers exceed the tube count.
CHANGED BEHAVIOUR: simulate() no longer refuses steps beyond n_tubes-1. It
now reports AnalyteResult.eluted, which is more instructive and matches both
the applet and the natural reading of A16.2. UI shows eluted % per analyte
and a notice once material leaves the train.
Validation now 530 values across both oracles. v0.8.1.

## 2026-08-05 — Two top-level sections [HUMAN]
The Craig controls were living in the shared HPLC sidebar, where they applied
to nothing. Restructured to top-level tabs: "HPLC simulator" (shared settings
sidebar + Isocratic/Gradient/Compare) and "Craig apparatus" (its own controls
sidebar + panel), with Config and Diagnostics as global sections. Each section
owns its own controls, so no panel shows settings that do not apply to it.
Sidebar/content styling factored into one _with_sidebar helper rather than
repeated per section. v0.9.0.

## 2026-08-05 — Sidebar no longer clipped; app renamed [HUMAN]
- The controls column carried a style() from an earlier layout AND was wrapped
  again by _with_sidebar, so the inner overflow-x:hidden clipped the column
  dropdown. Removed the inner style; only _with_sidebar styles the column now,
  pinning WIDTH only (flex 0 0 340px) with overflow:visible and no max-height,
  so the controls extend downwards instead of scrolling.
- App renamed "Chromatography Simulator"; the HPLC model is now one section
  ("HPLC") alongside "Craig apparatus". About card describes both models.
v0.9.1.

## 2026-08-05 — GC port: five branch-point rulings [HUMAN; provenance per item]
1. Uncertainty [HUMAN, terse: "measure the uncertainty against Julia"]:
   Measurements.jl propagation is NOT ported. Interpretation recorded by the
   assistant (to be confirmed by the measurements themselves): quantify
   against the Julia oracle both (a) what Measurements.jl propagation
   yields on a reference case, so the feature's value is known from data,
   and (b) the port-vs-oracle disagreement, so the port's own uncertainty
   is a measured number.
2. Compound data [ASSISTANT choice under HUMAN delegation "your choice"]:
   vendored curated table, one stationary phase, Cag precomputed via
   Fuller; check the upstream database license before copying, fall back
   to the compounds in the package's own test CSV if the license is
   awkward. No runtime lookup; ChemicalIdentifiers.jl not ported.
3. Layout [HUMAN: "top level selection"]: GC is a third top-level section
   beside HPLC and Craig, with its own controls region.
4. Scope v1 [HUMAN: "isothermal for now with extended options for later"]:
   ISOTHERMAL — constant oven temperature in time, no spatial gradient.
   Parallels the isocratic-first HPLC ruling of 2026-08-03. Assistant
   interpretation: the core keeps piecewise-linear T(t)/p(t) machinery
   (a constant is a degenerate program, identical code path) but v1 UI
   exposes a single temperature; temperature programming is parked in
   issues.md as the extension.
5. Validation methodology [ASSISTANT choice under HUMAN delegation]: run
   both sides at tight solver tolerances, set the pass tolerance from a
   measurement, implement analytic ∂r/∂t only if FD proves limiting.
   Note: under isothermal v1, ∂r/∂t = 0 exactly, so the τ² ODE reduces
   to dτ²/dz = H·r² and the FD-vs-ForwardDiff question largely vanishes.

## 2026-08-05 — GC v1 core is closed-form, not an ODE march [ASSISTANT, from measurement]
Under the isothermal ruling, the shipped core uses the exact analytic
tR/τ²/tM forms (see learnings entry of same date); scipy's solve_ivp is
NOT a runtime dependency of the GC model. The ODE system moves into the
parked temperature-programming extension, where it is genuinely needed.
Validation tolerances set from measurement: tR ≤ 1e-8 relative (limited by
the oracle's own solver tolerance), τR ≤ 1e-12, tM ≤ 1e-14.

## 2026-08-05 — v0.10.0: GC section ships; builder derives its import block [ASSISTANT]
Version bumped 0.9.1 → 0.10.0 (new model = minor bump, matching the Craig
precedent). dist/ keeps the old versioned artifact alongside the new one.
The WASM builder now derives the inline import block from the notebook's
[[INLINE]] cell instead of restating it (see issues.md RESOLVED entry).

## 2026-08-05 — Three GC/UI rulings from a screenshot report [HUMAN]
Reported: the GC stationary-phase dropdown overlapped the plot, the legend
consumed too much plot area, and a NonElutingSoluteError blanked the GC
section with no route back.
1. Non-eluting solutes: SKIP AND EXCLUDE [HUMAN, overriding the assistant's
   recommendation]. The assistant recommended report-never-drop (the HPLC
   ISOCRATIC precedent) on the grounds that GC closed forms are always
   finite and cheap, so nothing is gained by withholding a 76-minute peak.
   The human ruled for the GRADIENT precedent instead: excluded, named,
   never silently dropped. Implemented as gc.simulate(skip_non_eluting=...)
   returning a new GCRun (peaks, skipped, horizon) with viability_report(),
   mirroring Results.skipped_compounds. Library default stays fail-fast;
   the notebook opts in. compare_gc.py calls simulate_solute, not simulate,
   so the contract change did not touch validation (still PASS, 2,754).
2. Legend visibility: PER-SECTION SWITCH above each plot [HUMAN]. Not a
   global Config toggle and not per-figure. PlotConfig gained show_legend,
   honoured once in BasePlot.figure(); three switches feed three derived
   configs (hplc/craig/gc_plot_config) which the section's plot cells
   consume instead of plot_config. Chosen over threading a flag through
   all seven replace() call sites, which is the duplicated-authority
   pattern that has already broken this project four times.
3. Dropdown width: SHORTEN THE OPTION LABELS, full text as a caption
   [HUMAN], with the explicit added constraint that the caption must not
   interfere with the plot axes. STATIONARY_PHASES values are now
   StationaryPhase(label, description) records — one object carries both,
   so they cannot drift. Longest option 43 -> 19 chars. The caption is
   width-constrained (max-width 300px, overflow-wrap anywhere) so it wraps
   inside the 340px column rather than reintroducing the overlap. Phase
   KEYS are unchanged: they index GC_SOLUTES and the validation goldens.
Also fixed in the same change: gc_peaks[0]/[-1] were indexed unguarded, so
the all-skipped case would have raised IndexError; the notebook now stops
with the viability report instead. v0.10.1.

## 2026-08-05 — GC figure legibility: five rulings [HUMAN, from screenshot]
1. Legend OFF BY DEFAULT for ALL plots. Applied at both levels so the app
   and a library caller agree: PlotConfig.show_legend default flipped
   True -> False, and all three per-section switches start off.
2. GC sum trace thinner. Kept SEPARATE from the HPLC sum: new
   PlotConfig.gc_sum_trace_width = 1.4 (assistant-chosen named default;
   "a little thinner" was not quantified) while sum_trace_width stays 2.0,
   so the HPLC figures the human did not complain about are unchanged.
3. GC sum trace hideable: GCChromatogramPlot(show_sum=...) plus a
   "Sum trace" switch beside the GC legend switch. GC only, since the sum
   is what overlays the newly filled components there; the HPLC figures
   can get the same switch on request.
4. GC component traces now FILLED (fill="tozeroy", compound_fill_opacity)
   exactly as ChromatogramPlot draws the HPLC components, so the two
   chromatograms read the same way.
5. Operating-point stamp collided with the x-axis title. Root cause: the
   stamp sat at a hardcoded y=-0.18 with 90px reserved. Now named values,
   operating_point_y = -0.30 and operating_point_margin_b = 120, kept
   adjacent in PlotConfig because they must move together.
v0.10.2. All four oracle suites re-run: PASS.

## 2026-08-05 — Palette legibility and default drag mode [HUMAN]
- YELLOW REPLACED in the default colorway. PAIRED_12 slot 11 goes
  #ffff99 -> #9e9d24 (olive). This is a DELIBERATE divergence from
  ColorBrewer "Paired" and therefore from the D3 reference's appearance;
  recorded here because decisions of 2026-08-03 adopted that palette for
  fidelity. Numbers are untouched — no computed value depends on colour.
  Chosen by measurement, not taste: composited at compound_fill_opacity
  over white, #ffff99 gives contrast ratio 1.015 (indistinguishable from
  the canvas) versus 1.108 for the faintest otherwise-acceptable member;
  #9e9d24 gives 1.265. The other three pale Paired members measured
  1.108-1.190 and were LEFT ALONE — the human reported yellow, and the
  measurement agreed yellow was the lone outlier.
- DRAGMODE now "zoom" by default, as PlotConfig.dragmode. The human asked
  for the GC plot; the fix is at BasePlot because the same defect exists
  in ALL EIGHT mo.ui.plotly figures — no cell in the project reads a
  figure's .value, so marimo's box-select default produces a selection
  that nothing consumes, everywhere. Scoping it to GC would have left the
  identical dead gesture in the other seven (charter section 5).
v0.10.3. All four oracle suites re-run: PASS.

## 2026-08-05 — GC flow readout + temperature-programming plan: four rulings [HUMAN]
1. FLOW: read-only readout, PLUS average linear velocity. No flow-control
   input mode — the section stays pressure-controlled, so every shipped
   number remains on a path the Julia oracle validated. Both quantities are
   derived, never stored (charter section 9: one source of truth).
2. INTEGRATOR for temperature programming: prefer a hand-rolled RK in numpy
   IF it is smaller, and VALIDATE IT AGAINST scipy's solve_ivp. Note the
   human's condition is conditional — "if the hand-rolled version is
   smaller" — so the size comparison is a measurement to make and report,
   not a foregone conclusion. scipy stays a validation-time tool here; the
   motivation is the WASM payload.
3. PROGRAM SCOPE v1: temperature only. Pressure programming stays parked
   even though upstream supports it.
4. SEQUENCING: oracle-first. Extend dump_golden_gc.jl with programmed cases
   and regenerate golden_gc.json BEFORE writing the core, per the standing
   project rule that every model is validated against an external oracle.
   Human confirmed the ~25 min Julia install/precompile cost.

## 2026-08-05 — Programmed-temperature goldens: separate file, not a schema change [ASSISTANT]
golden_gc_program.json is a SEPARATE artifact from golden_gc.json rather
than new records inside it. Two reasons: (a) compare_gc.py reads a flat
list of isothermal records and a schema change would have broken a suite
that passes, and (b) keeping the 2,754 validated isothermal values in an
untouched file means adding programmed coverage cannot perturb them.
Grid: 64 cases (2 columns x 2 gases x 4 programs x 2 pressure pairs x 2
phases), 8 solutes each = 512 peaks = 1,024 comparable values. Programs are
ramp5 / ramp10 / ramp20 (40 C, 1 min hold, then linear to 300 C) and a
two-ramp 40 -> 180 (2 min hold) -> 300. HALF THE CASES ARE VACUUM OUTLET
(pout = 0) on purpose: that singularity cancels in the isothermal closed
forms but not under a program, so those cases are what will actually
exercise the future integrator.
Verified before being trusted: all 1,024 values finite and positive; and
elution is monotonic in ramp rate (last peak 505.5 s at 20 K/min, 787.8 s
at 10 K/min, 1269.3 s at 5 K/min) for a fixed column, gas, pressure and
phase — a physical check the oracle would fail if the programs had been
mis-encoded as absolute times rather than segment durations.

## 2026-08-05 — Programmed goldens: ship the TIGHTEST dump, keep coarser ones as evidence [ASSISTANT]
Measured the oracle against itself at three solver tolerances (Vern9):
loose 1e-10/1e-8, mid 1e-12/1e-10, tight 1e-14/1e-12. Successive
refinement converges cleanly (mid-vs-tight is 88x smaller than
loose-vs-tight for tR, 98x for tauR), so the tight dump is settled and its
own relative error is bounded at ~8.0e-10.
CORRECTION to the previous session decision: golden_gc_program.json now
holds the TIGHT dump, not the loose one first shipped. The loose dump
carried ~7.8e-08 relative error — 100x worse — and the tight dump costs
nothing extra to generate (129 s). golden_gc_program_loose.json and
golden_gc_program_mid.json ship alongside as the EVIDENCE; without them
the shipped golden's error would be an assertion rather than a
measurement, and validation/oracle_convergence_gc.py reproduces the whole
argument without Julia.
CONSEQUENCE for the not-yet-written compare_gc_program.py: it must not
assert agreement tighter than ~1e-9. Under a program both sides are
numerical, unlike the isothermal suite where the Python side is a closed
form and ~1e-9 was an absolute statement. Note the worst tR discrepancy
falls on a VACUUM-OUTLET case (ramp10, H2, pout=0), which is exactly the
regime flagged as the trap for the future integrator.

## 2026-08-05 — Temperature-programmed GC core: hand-rolled RK45, validated [HUMAN ruling discharged]
The human's ruling was CONDITIONAL ("hand-rolled if smaller, validate
against solve_ivp"). Measurement discharging the condition: the scipy
wheel is 35.3 MB against a whole deployed artifact of ~272 KB — about four
orders of magnitude — so hand-rolled wins decisively for a WASM target.
Dormand-Prince 5(4) with a PI controller, ~120 lines, in hplc_sim/
gc_program.py. scipy stays a validation-time comparator and is never
imported by shipped code, which compare_integrator_scipy.py now ASSERTS
via AST (mutation-verified: an injected `from scipy.special import erf`
is caught and located).
KEY DESIGN CHOICE — march in PRESSURE, not distance. p^2 is linear in z,
so z -> p is analytic, and both right-hand sides become polynomial in p.
This removes the vacuum-outlet singularity ANALYTICALLY: in z the solution
has a sqrt branch point at the column exit whose infinite derivative
starves any adaptive stepper exactly where the answer is decided. The
issue notes had flagged this as the trap for the programmed extension; it
turned out to be an artefact of the coordinate, not of the physics.
Verified symbolically (sympy) that with dr/dt = 0 the integrals reduce
EXACTLY to gc.simulate_solute's closed forms, so the marched and
closed-form paths agree by construction.
TOLERANCE DEFAULTS by measurement: peak width converges 1.8e-07 (rtol
1e-8) -> 5.2e-09 (1e-10) -> 3.6e-11 (1e-12) -> 8.6e-13 (1e-13), which is
what identified the residual as the integrator's error rather than a model
difference. Default is rtol 1e-12 / atol 1e-14, below the oracle's own
~8e-10 floor with ~50x margin, costing 276 ms for 17 solutes versus 128 ms
at 1e-10 — imperceptible against a UI re-render.
RESULTS: vs the Julia oracle, 1,024 values, worst tR 6.9e-13 and worst
tauR 8.7e-11 — both BELOW the oracle's own error, i.e. as close as the
reference permits. Flat-program identity vs the closed forms: 8.1e-16.
Hand-rolled vs scipy DOP853 on an IDENTICAL right-hand side object: worst
1.5e-13 / 8.8e-11. v0.12.0.
STILL MISSING: the notebook UI (programming tab and the isothermal-vs-
programmed comparison plot). The core and its validation are done; nothing
is wired into the app yet.

## 2026-08-05 — Oracle coverage audit and grid expansion [HUMAN: "fold into a single harness and run"]
Audit finding that prompted it: the GC UI exposed parameter space the
oracles had never touched. The Wax phase was SELECTABLE with 17 solutes in
the vendored table and ZERO oracle cases of any kind; film thickness was a
continuous 0.1-1.0 um slider validated at exactly one value; three of five
bore options were uncovered.
Isothermal grid 162 -> 810 cases (2,754 -> 13,770 values): added Wax,
df in {0.25, 1.0} um, and 0.10/0.53 mm bores. Programmed grid 64 -> 432
cases (1,024 -> 6,912 values): added N2, 0.32 mm, Wax, and the second film
thickness. Both PASS.
Method that preserved the integrity check: the grid was extended by ADDING
combinations with the existing ones enumerated first, so the original 162
remained a strict subset. At equal solver tolerance they reproduced at
0.000e+00, proving the expansion additive before anything else was
concluded from it.
ISOTHERMAL ORACLE TOLERANCE RAISED 1e-10/1e-8 -> 1e-12/1e-10. Case 809
(0.53 mm bore, N2, vacuum outlet, Wax, 160 C) failed at 1.12e-08 against a
1e-08 comparison tolerance. Probing showed the ORACLE was wrong, not the
port: as its tolerance tightened the oracle converged ONTO the Python
value (1.12e-08 -> 3.38e-11 -> 2.89e-13), and the Python side is a closed
form, i.e. exact. The old tolerance had been set against a grid of
comfortable cases and quietly stopped being defensible once the grid
reached hard ones. Re-dumping converged rather than loosening the
comparison tolerance was the correct fix — the alternative would have been
accommodating a reference now known to be wrong.
RESIDUAL GAP, stated plainly: the programmed grid covers 0.25/0.32 mm
only. It was matched to the ORIGINAL isothermal columns, not the extended
five, so 0.10 and 0.53 mm remain unvalidated under a program.
Harness now supports --iso-only, --iso-range, --iso-tol, --prog-only,
--prog-range and --with-uncertainty, all resumable in chunks.

## 2026-08-05 — Programmed grid extended to 0.10/0.53 mm; the residual gap is CLOSED [HUMAN]
Programmed grid 432 -> 720 cases (6,912 -> 11,520 values). Bore coverage
is now {0.10, 0.25, 0.32, 0.53} mm under a program, matching the
isothermal grid, so the gap recorded in the previous entry no longer
exists: every bore the UI dropdown offers has oracle cases in BOTH modes,
as do all three phases and both film thicknesses.
Method — only 288 cases were actually computed. The column loop is
outermost, so APPENDING the two new bores leaves ids 1..432 generated in
the same order. That was verified rather than assumed: re-running ids 1-24
under the edited harness reproduced the shipped values at 0.000e+00 with
no parameter mismatches, after which only 433..720 needed generating.
Roughly half the compute saved, and the check is stronger than the saving.
RESULT: worst tR 9.6e-13 and worst tauR 9.2e-11 across all 720 cases —
IDENTICAL to the 432-case figures, and both still located at old cases
(203, 291). The extreme bores, including 0.53 mm with vacuum outlet and a
1.0 um film, did not degrade agreement at all, which is evidence the
pressure-substitution formulation is well behaved across the whole
UI-reachable range rather than tuned to the middle of it.
Cost note for future sizing: under a program the worst case measured
17.6 s (0.53 mm, 1.0 um film, N2, vacuum, Wax) against ~0.7 s typical.

## 2026-08-05 — GC UI, and the housekeeping backlog cleared [HUMAN]
GC section now has Isothermal / Programmed / Compare sub-tabs under ONE
controls region. Sharing the column, carrier and pneumatics controls is
what makes Compare honest — the same precondition the HPLC compare view
carries — so the two arms provably differ only in the elution program.
The program editor takes ABSOLUTE times in minutes, the unit a GC method is
written in, and converts to GCProgram's segment durations in a single
place. Row validation reuses the gradient editor's ruled policy verbatim:
blank rows dropped and reported, out-of-order rows sorted and reported,
duplicate times refused by name. An invalid program does NOT blank the
isothermal tab (no mo.stop there) because the arms are independent.
New GCOverlayPlot takes already-simulated peak lists rather than
conditions, so it never re-runs the model, and uses ONE shared time axis:
a per-arm axis would rescale each run and hide the difference the plot
exists to show.
Housekeeping cleared in the same pass: pyproject version made dynamic from
hplc_sim.__version__ (verified by building hplc_sim-0.12.3.whl, so the
drift is now structurally impossible), dist/ pruned to the single current
artifact per the human's earlier ruling, three stale OPEN issue entries
re-labelled CLOSED with provenance rather than deleted.
NOT done, deliberately: the app name is still the placeholder
"Chromatography Simulator". Naming is the human's call and no measurement
settles it. The HPLC column presets issue also stands, still blocked on the
unresolved SB-C18 / SB-C8 provenance discrepancy.

## 2026-08-05 — Errors are carried, never mo.stop'd; oven ramp on a second axis [HUMAN]
Reported: entering two gradient rows with the same time showed the correct
error but "crashed the UI" — the whole interface disappeared, so the value
could not be corrected. Root cause: mo.stop halts the cell AND all
descendants, and the single top-level layout cell descends from every
producer. All SIX mo.stop sites (Craig, analyte selection, isocratic,
gradient, and two GC) now carry an error value that the owning panel
renders. Controls are constructed outside every guard so they always
survive. Verified by reproducing the reported state (two rows at 20 min):
the message appears, the gradient editor stays on screen, and the HPLC,
Craig and GC sections all keep rendering.
Second request: GCChromatogramPlot gained an optional `program=` overlay
drawing the oven temperature on a secondary right-hand axis, mirroring the
HPLC gradient view's %B overlay, sampled on the SAME time base as the
chromatogram so the ramp lines up with the peaks it produced. Exposed on
the Programmed tab as an "Oven ramp" switch beside Legend and Sum trace,
default on.

## 2026-08-05 — Doctrine items 1 and 2: shared GC physics, per-section layout [HUMAN]
1. ONE AUTHORITY FOR THE GC PHYSICS. gc.py gains local_coefficients() (the
   a, b with rM = a*p and DM = b/p) and plate_height() (Golay H). gc_program
   now imports both instead of restating them. Measured: the Golay literals
   (64, 96, 1.75, 6, 16, 11, 1e4) went 8 -> 0 in gc_program.py. Also named
   GAS_DIFFUSIVITY_TEMPERATURE_EXPONENT and
   STATIONARY_PHASE_DIFFUSIVITY_RATIO; Golay's 96/6/16/11 stay inline in the
   one function that owns them, since naming them individually would obscure
   the standard form. da/dT is now derived as a*(deta/dT)/eta rather than
   rebuilding a's constant factor, so the derivative follows the coefficient
   definition automatically.
   CORRECTION TO THE AUDIT that motivated this: I claimed a change to gc.py
   would diverge SILENTLY from the programmed copy. That was wrong, and
   measuring it showed so — pre-refactor, perturbing gc.py's plate height
   failed BOTH suites, because compare_gc_program.py's flat-program identity
   check already detected divergence between the pair. The real benefit is
   narrower and still worth it: one place to change, and future modes
   (pressure programming, spatial gradient) inherit the physics instead of
   copying it a third and fourth time — the identity check only guards the
   pair that exists today.
2. PER-SECTION LAYOUT CELLS. The single layout cell consumed 49 names and
   descended from every producer, which is why mo.stop anywhere blanked the
   whole app. Split into with_sidebar() + one cell per section + a layout
   cell that consumes 7 names. Containment is now STRUCTURAL rather than a
   convention each future producer must remember.
Both verified: all six suites PASS with the programmed suite's worst values
BIT-IDENTICAL to before (9.648e-13 tR, 9.199e-11 tauR), isolated-directory
export clean, v0.14.0.

## 2026-08-05 — App named "drylab" [HUMAN]
The placeholder is settled: the app and the project are "drylab". Changed:
the notebook module docstring, marimo's app_title, the H1 heading, the
README title, and the project directory (hplc_marimo -> drylab).
DELIBERATELY NOT CHANGED, and these are not oversights:
- The References cell's "An Advanced, Interactive, High-Performance Liquid
  Chromatography Simulator and Instructor Resources" is the TITLE OF THE
  J. Chem. Educ. 2013 PAPER. Renaming it would falsify a citation.
- README's "the **HPLC Simulator** by Paul Boswell, Peter Carr, and Dwight
  Stoll" is upstream ATTRIBUTION, not our product name.
- build_wasm_notebook.py's comment about the v0.9.1 rename to
  "Chromatography Simulator" is a historical record of why the stamp anchor
  is structural; rewriting it would make the note incoherent.
- Memory entries naming the old title are history and stay accurate.
NOTE: "hplc_marimo" appeared in NO file — it was only ever the directory
and delivery-archive name, so the rename cost one `mv`.
Incidental confirmation: the WASM version stamp still landed after the
docstring changed, because it anchors on the docstring's STRUCTURE rather
than its text (fixed 2026-08-05 after the previous rename silently broke
it). The same rename would have broken it again under the old code.
STILL CARRYING THE OLD NAME, flagged not changed: the Python package
`hplc_sim`, the distribution name `hplc-sim`, the entry-point filename
`hplc_simulator_nb.py`, the artifact prefix `hplc_simulator_wasm_nb_`, and
the `HPLC_SIM_VERSION` display variable. The human named two things; these
are five more with a much wider blast radius (imports, the builder's
MODULES paths, the embedded package registration, every validation
script), so they need their own ruling.

## 2026-08-05 — CE licensing analysis: separate GPL app is legal but buys little [ASSISTANT, for a HUMAN ruling]
Question raised: put the CE simulator in a SEPARATE app so LEMNG's GPL-3
source can be ported directly.
LEGALLY: yes, that works and is the standard answer. A standalone GPL-3
program downstream of LEMNG is exactly what the licence contemplates.
THE CONSTRAINT IT DOES NOT REMOVE: the separation has to be real. drylab is
CC BY-NC-SA 3.0 US and CANNOT be relicensed (ShareAlike inherited from
mlibby/hplc_simulator), and GPL-3 forbids added restrictions, so NC and GPL
cannot mix in either direction. A GPL CE app therefore may NOT import
drylab's plotting, config, diagnostics or notebook scaffolding — the very
infrastructure that makes drylab pleasant to extend. Two apps means two of
everything: repos, deployments, validation setups, and a split for users.
MEASURED, and this is what decides it: porting rather than reimplementing
means translating LEMNG (10,611 lines C++) PLUS its hard dependency
ECHMETCoreLibs (19,989 lines: libCAES 9,582, libECHMETShared 6,072,
libSysComp 2,161, libIonProps 1,191) = ~30,600 lines of Eigen-based,
AVX-hand-vectorised C++ into numpy. libCAES carries explicit SIMD
instruction-set specialisations that have no numpy analogue and exist for
speed the linear theory does not need at drylab's scale (measured earlier:
0.43-5.15 ms per full calculation).
ASSESSMENT: the GPL route's supposed benefit is "we can copy instead of
derive", but a line-by-line port of 30k lines of templated C++ into
vectorised Python is almost certainly MORE work than implementing the
published equations (Electrophoresis 2019, DOI 10.1002/elps.201800400),
and it would import their architecture rather than fitting drylab's
closed-form-plus-plot shape. RECOMMENDATION: stay single-app, implement
from the papers, use PeakMaster/LEMNG binaries as oracles. The separate-app
option remains open and is the right fallback IF a future need is for
dynamic simulation at a scale where reusing their solver genuinely matters.
Human ruling required; not started.

## 2026-08-05 — CE module: three rulings [HUMAN]
1. INTERACTIVITY: run button for the march, free scrubbing afterwards.
   Parameter changes do NOT auto-trigger the PDE solve; time and position
   sliders over the returned space-time field are reactive and free. BGE
   equilibrium properties stay instantly reactive since they need no march.
2. CODE SHAPE: restructure into hplc_sim/ce.py in drylab style, not a thin
   wrapper around SPYCE.py.
3. SCOPE: CZE first, then ITP/FASS.
LICENCE SEQUENCING, applied without being asked because ruling 2 makes it
load-bearing: a restructured ce.py IS a derivative work of SPYCE, which
currently carries NO licence grant at all. So ce.py's ENGINE does not enter
the repository until the authors grant one. Everything that is drylab's own
original work — the plotting classes, the notebook section, the run-button
wiring, the validation harness that DRIVES stock SPYCE as an oracle — is
unaffected and is being built now. That split also happens to de-risk the
integration first, which is what the human asked for ("make sure it works
before spinning anything up").

## 2026-08-05 — CE plotting layer landed; engine deliberately withheld [ASSISTANT]
Committed (drylab's own original work, no SPYCE derivation): plotting/ce.py
with CEProfilePlot (concentration vs POSITION at one instant, the view that
shows zones and the pH gradient, with no chromatographic analogue) and
CEElectropherogramPlot (concentration vs TIME at a fixed detector, built to
read like ChromatogramPlot with the same filled traces and legend
treatment). Both take ALREADY-COMPUTED arrays, never conditions, so neither
can trigger a solve — that is what makes the ruled "free scrubbing" free.
Secondary-axis pH/conductivity overlay reuses the GC oven-ramp pattern.
ph_from_hydronium() is named and separate because the solver works in
mol/m^3 and pH is defined on mol/L: getting that factor of 1000 wrong
shifts every pH by exactly 3 units, which reads as chemistry rather than
arithmetic. Four CE axis labels added to the canonical AXIS_LABELS.
NOT committed: hplc_sim/ce.py. Under ruling 2 it is a restructured
derivative of SPYCE, which carries no licence grant, so it waits.
VERIFIED against a REAL SPYCE field (CZE sample, 4 species x 257 nodes x 32
saved times): both plots build, the pH overlay lands on yaxis2, pH comes
out 7.90-8.09 across the capillary (sensible for the TRIS/HEPES system),
and both shape guards fire on inconsistently sliced input.
INTERACTION MODEL PROVEN in a scratch marimo notebook (/tmp/ce_proof.py,
not shipped): run button gates the march, the un-run state shows a prompt
and no figures, and after running, the time slider re-slices the stored
field with the label range computed from the data ("Time slice (0 to
75 s)"). Confirms ruling 1 is implementable as specified.

## 2026-08-05 — CE section in the UI; engine finished enough to review [HUMAN]
Two real defects in the march were fixed before wiring anything:
1. THE DIFFUSION-POTENTIAL TERM WAS STUBBED TO ZERO (a literal `* 0.0`).
   Restored properly: _spatial_properties now also returns the
   charge-weighted diffusivity sum_z z*D_z*frac_z, and the field is
   E = (j + i_diff)/sigma with i_diff = F*(sum_i zD_i dc_i/dx + H/OH terms).
   This is not cosmetic: it is part of what produces electromigration
   dispersion, which is most of what CZE teaching is about.
2. STEP CONTROL WAS UNBOUNDED — 10 steps for 20 s where the reference takes
   hundreds. The RKF45 error estimate alone does not keep an explicit
   scheme inside its stability region. Added a physical cap per step,
   CFL_MIGRATION and CFL_DIFFUSION (0.2 each, named), from the finest grid
   spacing against the largest migration velocity and diffusivity.
Also fixed: the conductivity field had been the LAST time broadcast across
all saved times, which would have been a silent lie in exactly the plot a
conductivity detector user would trust.
VERIFIED against analytic expectation, not just "it runs": with j = 1018.6
A/m2 and sigma ~0.66 S/m, E = 1543 V/m, so a mu = -30e-9 analyte should
move mu*E*t = 0.93 mm in 20 s. Measured: 0.94 mm. Mass conserved to
1.7e-09 over 66 adaptive steps; pH 7.49-7.56 for the TRIS/HEPES/chloride
system.
UI: CE is now a top-level tab with its own controls region — capillary
length and grid, current and run time, analyte mobility, detector position,
overlay picker, and a Run button. Parameter sliders do NOT trigger the
solve; the time slider afterwards re-slices the stored field and is free.
Both plots render with computed readouts (step count, detector node at
25.1 mm, t of 20 s).
BUILD GUARD kept its teeth rather than being weakened: build_wasm_notebook
now carries an EXCLUDED map with a STATED REASON per entry, so drylab/ce.py
is excluded on purpose while any other unregistered module is still a build
failure. Confirmed absent from the artifact, and the published build
degrades to an explanatory callout ("CE engine not installed") instead of
breaking.

## 2026-08-05 — CE: oracle validated, voltage control, real chemistry [HUMAN]
ORACLE RUN, the substantive result: validation/compare_ce.py reproduces
SPYCE's own shipped CZE case (pyridine + aniline in acetic acid / Tris,
30 mm, 2 uA, 75 s) and compares against a dump from stock SPYCE.
  Pyridine peak: oracle 23.81 mm, drylab 23.78 mm (0.03 mm apart)
  Aniline peak:  oracle 19.06 mm, drylab 19.07 mm (0.01 mm apart)
  Background pH: 4.932 both, to three decimals
  Mass drift: 1e-9 to 1.7e-3
Tolerances compare PHYSICAL OBSERVABLES (peak position, mass, pH), not the
raw field point by point: both sides are numerical with different adaptive
step sequences, so a 1e-8 field comparison would fail for reasons unrelated
to correctness.
A units bug in the PROBE, not the model: the first run showed a pH gap of
exactly 3.000 = log10(1000). SPYCE's saved hydronium array is already
mol/L while drylab's CERun carries mol/m^3. Henderson-Hasselbalch settled
which side was wrong before any code changed: 20 mM acetic acid neutralised
by 12 mM Tris gives 4.756 + log10(12/8) = 4.932, exactly drylab's answer.
VOLTAGE IS NOW THE PRIMARY CONTROL [HUMAN]: CEConditions takes voltage_v
(constant-voltage, what an operator sets and what a published method
quotes) or current_a (constant-current), with a guard requiring exactly
one. Current density then follows from the electrolyte's conductivity.
The guard immediately caught compare_ce.py, which needed the
constant-current branch for SPYCE's case.
REAL CHEMISTRY [HUMAN]: the demo is now K+, Na+ and Li+ (1 mM each) in
20 mM acetate / 12 mM Tris, with textbook mobilities 76.2 / 51.9 /
40.1e-9 m2/Vs. Chosen because they are fully ionised at any pH, so
migration order follows ionic mobility ALONE and the lesson is not
confounded by acid-base equilibria. Measured migration to a 15 mm
detector at 500 V: K+ 8.3 s, Na+ 11.7 s, Li+ 14.6 s — correct order,
resolved.
TRAP WORTH RECORDING: a CATION that is always charged needs a HIGH pKa
(its conjugate base never forms). Using a low pKa — correct for a strong
ACID like chloride — leaves it un-ionised and immobile, which presented as
"nothing moves" with no error.

## 2026-08-05 — CE boundary blow-up fixed; it needed TWO mechanisms [ASSISTANT]
The defect: a zone reaching the end of the capillary produced a peak
reappearing at the far end with integrated mass up 16-fold (2.9 -> 47).
FIRST FIX, necessary but NOT sufficient: Trefethen's endpoint formulae in
the Chebyshev differentiation (chebfft, Spectral Methods in MATLAB
Program 18). The interior divides the theta-derivative by -sqrt(1-xi^2),
which vanishes at xi = +-1; the previous code clamped that divisor instead
of using the closed forms. Now verified against analytic derivatives at
1e-12 INCLUDING the endpoints (exp, x^5, Runge). Applying this alone left
the blow-up completely unchanged, which is what showed a second mechanism
was involved.
SECOND FIX, the one that actually stopped it: the Hou-Li spectral filter,
exp(-36 (k/k_max)^36), applied to the state each accepted step. The
nonlinear flux multiplies truncated series and aliases energy into the top
wavenumbers; unattenuated it destroys the solution. SPYCE applies exactly
this and the omission was mine.
RESULT: the zone now ELUTES — mass 2.836 -> 0.34 -> 0.008 -> 0.0009 as it
leaves the domain, with no growth at any point. The oracle comparison also
IMPROVED: pyridine peak 0.03 -> 0.01 mm, mass drift 1.7e-3 -> 4.1e-4.
REGRESSION GUARD in compare_ce.py: check_boundary_elution() drives a fast
analyte into the wall and asserts mass never exceeds its initial value and
ends below 10% of it. Mutation-verified — removing the filter makes it
report "mass grew to 48.497 from 2.836 — the boundary blow-up has
returned". A test that exercises the boundary is the only way to keep BOTH
mechanisms, since fixing one alone looks like progress and changes nothing.
UI: run-time ceiling lifted from 40 s to 60 s now that analytes may safely
elute past the detector and out of the capillary.

## 2026-08-05 — CE sample-composition editor [HUMAN]
The BGE and analytes are no longer hardcoded. A data_editor table carries
name, valence, mobility (1e-9 m2/Vs), pKa, concentration (mM) and role
(BGE fills the capillary, Sample is injected as a plug), and the march is
built from it.
VALIDATION follows the ruled gradient/GC-program policy exactly: blank
rows are half-finished edits, dropped and reported; contradictions are
named and refused; legal-but-surprising compositions are WARNINGS that do
not block. validate_composition() in ce.py returns (errors, warnings) so
the policy lives with the model rather than in the notebook.
Errors: empty table, duplicate names, no BGE, no sample, a BGE of only
cations or only anions (not electroneutral), non-positive concentration,
zero valence.
Warnings, and the first is the important one: A CATION WITH A pKa BELOW
THE WORKING pH will be mostly neutral and barely move. That is the exact
trap that cost a debugging round on 2026-08-05 ("nothing moves", no
error), so the editor now names it as guidance rather than leaving each
user to rediscover it. Also warns when a sample exceeds 10% of the BGE
concentration, where the zone distorts its own field.
CE_ION_LIBRARY: 16 curated ions with published mobilities and pKa values
(alkali metals, common BGE co- and counter-ions, weak acids and bases,
plus SPYCE's own pyridine/aniline), so a student picks a REAL ion instead
of inventing a plausible number.
The plug is placed automatically upstream of the detector for the sample's
polarity — anionic samples at 0.8 L, cationic at 0.2 L — because getting
that backwards produces a detector trace that is exactly flat, which is
how the first version failed.
The panel's sample description, the BGE trace hiding, and the pH readout
are all DERIVED from the table now, so renaming an ion cannot silently
desynchronise them.

## 2026-08-05 — CE: electroosmotic flow added [ASSISTANT, for review]
EOF is now a CEConditions field (eof_mobility) entering the flux as PLUG
flow — the same bulk velocity for every species, charged or not — so the
observed "apparent" mobility is mu_ep + mu_eof. Exposed as a UI slider
(0-80e-9; bare fused silica gives roughly 40-70e-9 above pH 6, falling to
zero below pH 3 as silanols protonate).
WHY, given it costs oracle coverage: without EOF, anions and cations can
never reach the same detector, and a single run seeing both IS the
defining CZE experiment. A simulator that cannot show it teaches a
misleading picture of the technique.
THIS IS BEYOND THE ORACLE and that is stated in the code: SPYCE models
transport explicitly "in the absence of bulk fluid flow due to pressure
gradients and electroosmotic slip", so compare_ce.py can only validate the
eof_mobility = 0 case against it. Two INVARIANTS cover the rest:
  1. Galilean shift — switching EOF on must translate a zone by exactly
     v_eof*t and change nothing else. Measured 4.9922 mm against 5.0000
     predicted, 1.6e-03 relative (the residue is E varying slightly along
     the capillary).
  2. Apparent mobility — cation, neutral and anion must all reach ONE
     detector, ordered by mu_ep + mu_eof, with a neutral marker reporting
     mu_eof directly. Order correct, worst timing error 7.1% against an
     estimate that ignores dispersion.
Both mutation-verified: making EOF scale each ion's own mobility instead
of acting as bulk flow gives "shift 3.9429 vs predicted 5.0000 (2.11e-01)"
and "neutral never reached the detector".
CONSEQUENCE elsewhere: plug placement now follows APPARENT mobility rather
than charge sign. With strong EOF an anion still travels toward the
cathode, so placing by sign alone would inject it moving away from the
detector — the same class of error that made the first CE build record a
flat trace.
The results table now reports apparent mobility measured back out of the
run, which is what an analyst reports and what makes EOF legible.

## 2026-08-05 — SPYCE licence GRANTED; CE engine unblocked [HUMAN relayed]
Prof. Bahga (corresponding author) granted permission by email:
"Feel free to use the code however you wish, as long as it remains
available to the community for free."
READ PRECISELY: this is a grant WITH AN OBLIGATION, not an unconditional
release. drylab's CC BY-NC-SA satisfies "available to the community for
free" — it is free and public — so the condition is met, not merely
compatible. But it binds the project going forward: a future relicensing
that put the CE module behind a paywall would breach the terms under which
this code exists. Recorded in NOTICE.md, in ce.py's docstring, and in the
README so it cannot be lost.
Actions taken: drylab/ce.py removed from .gitignore; removed from the
builder's EXCLUDED map (the map itself KEPT, now empty, so the
unregistered-module check keeps its teeth); registered in MODULES;
ce.py's docstring rewritten from "MUST NOT be published" to the actual
grant terms.
VERIFIED the grant travels with the code: modules are embedded base64, so
grepping the artifact for provenance text returns nothing and looks like
stripping. Decoding the drylab.ce blob (32,799 chars) confirms the
provenance, the grant quotation and the obligation are all present in the
deployed artifact, and the stale "must not be published" warning is gone.
CAUGHT IN PASSING: the first artifact was built BEFORE the docstring was
corrected, so it shipped the stale warning. Editing a source and shipping
without rebuilding is exactly what the dist/-is-stale CI check exists to
catch; here it was caught by inspection.
NOTE for the record: the permission is an email from the corresponding
author, not a public licence on SPYCE itself, and co-author Prateek Gupta
was not party to the exchange. NOTICE.md says so plainly and points
downstream users at the authors. A public LICENSE file on SPYCE would be
firmer footing and is worth a follow-up ask.

## 2026-08-05 — Session close: state of drylab at v0.21.0
FOUR MODELS, all oracle-validated: HPLC (isocratic + gradient), Craig
countercurrent extraction, capillary GC (isothermal + temperature-
programmed), and capillary zone electrophoresis. Six validation suites,
~55,000 compared values, all passing; only two need an external runtime.
Renamed from hplc_marimo/hplc_sim to drylab throughout, with the upstream
attribution to mlibby/hplc_simulator and the J. Chem. Educ. paper title
deliberately unchanged (credit and citation, not our name).
Git repository initialised with .gitignore, .gitattributes (vendored Java
kept byte-for-byte with CRLF; minified goldens and dist/ marked
linguist-generated), two GitHub Actions workflows (validate + Pages
deploy) and DEPLOY.md.
ISSUES LEDGER CLEANED at session close: 19 OPEN -> 11, with eight entries
closed that this session had resolved but left mislabelled. A stale OPEN
is worse than no entry, since issues.md is what the next session reads to
decide what is live.

## 2026-08-17 — Classroom-exercise extensions 1–5: GO [HUMAN ruled]
Brian ruled "move forward with 1-5" on the gap analysis derived from the
POGIL exercise proposals (Wenzel Separation Science unit): (1) HPLC sweep
CSV export, (2) GC solute picker, (3) adjacent-pair Rs/alpha in the HPLC
results table, (4) GC results/trace export, (5) GC Golay sweep with
per-carrier overlay. Items 6+ (CE plate-count column, GC temperature
sweep, sweepable particle size/length, classroom presets) were explicitly
nice-to-have and are NOT ruled; presets logged as an open issue.
Implementation choices within the ruling [ASSISTANT recommended, shipped]:
- pair_metrics lives on model.Results (presentation-supporting arithmetic
  from already-validated fields; one authority for table and CSV). Rs uses
  the 4-sigma form on the model's reported sigmas; alpha=None when the
  earlier k' is not positive (undefined, not zero).
- HPLC per-compound table and results CSV now list compounds in ELUTION
  order (was sample-mix order) so "vs prev" reads as "vs previous peak".
- GC solute picker is per-phase and resets to all on phase change (the
  Blumberg fits are per-phase; carrying names across phases would carry
  labels, not solutes). Both elution arms consume ONE selection, so the
  Compare tab's same-everything-but-the-program contract now covers the
  sample. Empty selection is a carried error and outranks program errors.
- Golay view sweeps INLET PRESSURE over the inlet slider's own span
  (110-500 kPa) and plots H(u-bar) per gas, so every point is reachable
  from the real controls; a velocity grid would include unreachable
  operating points. Carrier dropdown deliberately ignored on that tab:
  all three gases on one axis IS the view. Per-gas minima marked.
- All new exports carry the figure's own operating-point stamp via a new
  public BasePlot.operating_point(); GC trace CSVs sample the plot's own
  time_axis() (promoted from _time_axis) — file and figure share one
  authority and cannot drift.
Verification: headless `marimo export html` clean (the three "NameError"
hits in the HTML are comment text, not tracebacks); five oracle suites
re-run and PASS (GC isothermal 13,770 values; GC programmed; Craig; CE;
JS golden via node; integrator cross-check) — Java suite not runnable
here (no JDK), consistent with its regenerate-on-demand status. WASM
artifact rebuilt as dist/drylab_wasm_nb_v0_22_0.py, old artifact removed
per the one-artifact convention (git history shows R099 renames each
version). Version 0.21.0 -> 0.22.0.

## 2026-08-17 — GCChromatogramPlot stamp now truthful under a program [ASSISTANT, shipped]
Found while wiring the programmed export: the operating-point stamp
hardcoded "<oven slider> degC isothermal" even when a program was
attached. Harmless before (the programmed panel hides the stamp), but the
new programmed CSV would have CERTIFIED conditions the peaks were not
produced under — a charter §4 violation. The stamp now reads
"programmed <start> -> <max> degC" when a program is present. Root fix in
the plot class (the one authority for the stamp), not in the exporter.

## 2026-08-17 — Smoke-check outcomes; classroom presets shipped [HUMAN GO; mechanism ASSISTANT-chosen]
Brian ruled "go ahead with 4 and then 2": run the exercise smoke checks,
then proceed with presets. The preset MECHANISM was not separately ruled;
the assistant chose under the delegated GO and flags it here: presets are
construction-default seeds on the section controls (marimo-idiomatic — UI
values cannot be assigned post-construction), plus ?hplc=/?gc= query-param
initialisation so an instructor can distribute a URL per exercise. No
persistence machinery; works unchanged in WASM. Unknown params fall back
to Default.
SMOKE CHECK (a) PASS [MEASUREMENT]: acetophenone / p-chlorophenol at
50 %B MeCN on the default column (Zorbax SB-C18 100 x 4.6 mm, 3 um,
2 mL/min) gives Rs = 0.65, alpha = 1.031. Lever responses: 44 %B ->
Rs 2.58; MeOH 65 %B -> Rs 7.79 (alpha 1.57); maxing BOTH N sliders
(300 mm + 1.5 um) reaches only Rs 1.56 at 2082 bar — the sqrt(N) lesson
embodied. Note for the exercise key: %B moves alpha too here (1.031 ->
1.115 at 44 %B), so the k-lever is partly an alpha-lever; say so rather
than letting students discover an inconsistency.
SMOKE CHECK (b) FAIL AS AUTHORED [MEASUREMENT]: Decane / 2-Octanone never
cross on SPB-50 in 40-250 degC (ratio 2.3x -> 1.5x, monotone). Full
pair x phase search found real crossings; chosen replacement:
Tridecane x 2-Octanone on WAX, ln k crossing ~102 degC at k ~ 1.7
(ratio 1.20 at 40 degC -> 0.90 at 250 degC — measurably distinct
slopes for the 4-point fit). Exercise document must be amended
(deliverable-revision docket).
Preset scenarios (all verified against the model this session):
HPLC Ex 3 triage (pair above, Rs 0.65 on open), Ex 4 general elution
(all 22 at 30 %B); GC Ex 4 alkane ladder C7-C15 at 120 degC (tlast
17.4 min — the GEP visible), Ex 5 ladder (C8/C10/C12), Ex 5 polarity
trio (2-Octanone < Decane < 1-Octanol on SLB5ms flips to Decane <
2-Octanone < 1-Octanol on Wax), Ex 5 co-elution hunt (Wax pair, preset
120 degC, students cool toward the 102 degC merge). Presets seed
CHEMISTRY only (analytes/phase/temperature/%B/solvent); geometry and
pneumatics stay default — a preset states the problem, never the
solution. Version 0.22.0 -> 0.23.0.

## 2026-08-17 — Exercise document v2 delivered [HUMAN ruled "revise #5"]
drylab_pogil_exercises_v2.md written against v0.23.0; every scenario and
instructor-key number regenerated from the model this session with
operating points stated. New measurements taken for the revision
[MEASUREMENT, defaults 100 x 4.6 mm 3 um Zorbax, 2 mL/min, 25 degC
unless noted]: h(flow) minimum interior at ~1.6 mL/min, h_min 6.0 um
(15.4 um at 0.2, 8.1 um at 5.0), so Ex 2's "why not run at optimum"
needs the honest near-optimal caveat; Ex 4 LC preset spans k' 1.28-352
with tlast ~188 min at 30 %B vs k' 0.22-5 in 3 min at 70 %B. The v1
document is superseded; the failed SPB-50 pair does not appear in v2.

## 2026-08-17 — Band-shape section: GO [HUMAN ruled]; model choice [ASSISTANT, flagged]
Brian ruled: add a tab with sliders/inputs capturing the band-broadening
types and the parameters behind tailing/fronting (overloaded column), for
the Wenzel lessons. This is EXTENSION PHYSICS (no upstream reference), so
the model choice was the assistant's under that GO, and is flagged here:
- New top-level "Band shape" section (drylab/bandshape.py +
  plotting/bandshape.py), two tabs. Deliberately a single-solute sandbox
  in REDUCED units (time = transfers, mass = fraction of injection),
  separate from the validated instrument models — a mechanism explorer
  that cannot be mistaken for an instrument simulator.
- Mechanisms tab: van Deemter term builder, one slider per mechanism
  (lambda, dp, Dm, Cs, Cm; gamma fixed 0.6 and said so), each limb its
  own trace, closed-form optimum marked. This FILLS the eddy-diffusion
  coverage-map gap: the A-term is finally a control.
- Peak-shape tab: discrete plate (Craig-transfer) cascade with a
  nonlinear isotherm q = aC/(1+bC); signed chi = b*C0 slider x load
  multiplier gives Langmuir tailing (sharp front, early-shifting max)
  and anti-Langmuir fronting; separate slow-site exponential tau covers
  kinetic tailing at ANY load, taught apart from overload. Anti side
  clamped at chi = -0.9 (isotherm validity); the clamp is announced in a
  callout, never silent.
- VALIDATION [MEASUREMENT]: the linear-isotherm limit of the cascade is
  EXACTLY the negative-binomial elution profile (mean N(1+k), variance
  N k (1+k)); simulator agrees pointwise to ~1e-14 across N=10..200,
  k=0.5..9, and that same closed form is the notebook's dashed "ideal"
  overlay (one function, oracle and overlay). Nonlinear behaviour
  validated by invariants (mass conservation; As and t_max monotone in
  chi, both signs, judged against the linear profile's OWN As since the
  NB is right-skewed at finite N). New suite
  validation/compare_bandshape.py, added to CI (no-runtime group).
- DEFECT FOUND AND MUTATION-VERIFIED: np.sign(0) = 0 collapsed the
  stable-quadratic root exactly where 1 + k = chi*total (chi = 3 at
  k = 2 froze the loaded plate and eluted nothing). Fixed with an
  explicit 0 -> +1 sign convention; regression cases in the suite;
  re-introducing np.sign reproduces total mass loss.
Version 0.23.0 -> 0.24.0. Follow-up docket opened: exercise document
could now gain an eddy-diffusion leg and an overload exercise.

## 2026-08-18 — Band-shape polish [HUMAN ruled]: LaTeX equations, N ceiling 1000, tab order
Brian ruled three UI changes: (1) render u_opt = sqrt(B/C) and
H_min = A + 2 sqrt(BC) properly — now LaTeX via mo.md raw strings, and
the Peak-shape isotherm q = aC/(1+bC) got the same treatment while in
there; (2) raise the overload plate ceiling — slider 200 -> 1000
(measured cost at N=1000, k=9: ~0.8 s native, ~12k transfers, so a few
seconds in WASM at the deliberate max; oracle grid extended to N=500 and
1000, agreement holds at ~3e-14); (3) top-tab order is now HPLC, GC, CE,
Band shape, Craig apparatus (Config/Diagnostics unchanged at the end).
Verification note [MEASUREMENT]: naive substring probes against the
export HTML false-negative on tab order and LaTeX — labels appear
earlier in embedded source comments and LaTeX backslashes are
JSON-escaped (\\\\mathrm) — so the check that counts is reading the
serialized _top_tabs dict and escape-aware probes. Version 0.24.1.

## 2026-08-18 — Exercises v3 + instructor key v1 delivered [HUMAN ruled]
Brian ruled: add the van Deemter section (-> Exercise 2A, Band shape
Mechanisms tab), add an overload exercise (-> Exercise 7, Peak shape
tab), and produce an instructor key so he can self-run everything.
Delivered outside the repo: drylab_pogil_exercises_v3.md and
drylab_instructor_key_v1.md, all values measured against v0.24.1.
Errors CAUGHT BY the key-writing measurement pass [MEASUREMENT]:
1. Craig homework pair D=1.5/2.5 needs n~615 transfers — beyond the
   200 slider. v3 uses D=1 vs D=4 (Rs~1.5 at n~81).
2. The CE acetate task was impossible as written twice over: acetate is
   a BGE ion in the default composition (no peak until its role is
   switched to Sample), and the plug sits at 6 mm so migration distance
   is 9 mm, not 15 — corrected arithmetic: EOF 60 -> ~31 s; within the
   20 s default run needs EOF >= ~70; within 60 s needs EOF >= ~52.
3. CE simulated times run ~10-15% later than infinite-dilution
   arithmetic (effective mobilities in the full electrolyte at 500 V,
   30 mm: K 8.3 s, Na 11.7 s, Li 14.7 s vs 7.1/10.4/13.5 arithmetic) —
   framed in both documents as a discussable systematic, not an error.
Other key anchors [MEASUREMENT, operating points in the documents]:
sweep fit A=3.00/B=2.44/C=0.922 (3 um) vs A=6.00/B=2.44/C=3.69 (6 um),
dP 173 vs 43 bar; fundamental-eq Rs 0.654 = table Rs at the Ex 3 preset;
300 mm predicted 1.13 vs measured 1.14; GC peak capacity 259 (iso 120 C)
vs 381 (default program), ratio 1.5x; Wax ln k slopes -> -dH 30.1
(Decane) / 49.9 (1-Octanol) kJ/mol; 4-point crossing prediction 101 C vs
model 102 C; Golay H_min = 0.137 mm for ALL carriers (gas-independent
minimum; u_opt 20/48/69 cm/s N2/He/H2); overload grid (N=100,k=2):
chi +1/+2/+5 -> As 1.29/1.43/1.99 with t_max 291/285/267 vs 297, N_app
150->126; tau=15 -> As 1.26 with t_max LATE (310) — the diagnostic pair.
No code changes; no version bump.

## 2026-08-19 — Student worksheets: template + two exemplars [ASSISTANT, pending rollout ruling]
Brian asked to see the student-facing document; delivered a worksheet
template and two built exemplars (Ex 3 triage, Ex 1 Craig), both PDF +
markdown master, outside the repo like the other classroom deliverables.
Template rules (transformation from exercises v3): strip everything
instructor-only (measured values, instructor notes, Wenzel-linkage
rationale, coverage map); add the POGIL apparatus — team roles, the
grading contract in student terms (wrong prediction honestly reconciled
= full credit), record-the-starting-point tables, Predict tables
physically BEFORE Run tables with a bolded STOP checkpoint, class
checkpoint tables, bordered write-in boxes, homework requiring the
stamped CSV. Instructor-note facts become discovery questions (e.g.
alpha-moves-with-%B is the triage sheet's Q6; the NB right-skew is the
overload sheet's planned baseline question). Rendering: markdown ->
weasyprint, name/group header each page. QA per sheet: (1) automated
no-leakage check that the instructor key's answer values are absent
(whitespace-normalized — line wraps false-negative naive probes), (2)
real-UI-reference presence check, (3) visual raster inspection.
Remaining seven worksheets (2A, 2, 4, 5, 6, 7) NOT yet built — awaiting
Brian's GO on the template.

## 2026-08-20 — Publication repo: validation excluded from upload [HUMAN ruled]; scope of exclusion [ASSISTANT, flagged]
Brian ruled: repackage for git deployment with validation/ excluded from
the upload, plus GitHub setup/deployment instructions. Because pushing
the development branch would upload every historical validation blob,
exclusion is implemented as a SEPARATE PUBLICATION REPOSITORY with fresh
history, built by tools/build_publish_repo.py from the dev tree. The dev
repo (full history, validation, memory) stays the session working tree;
the script is the one-way bridge, re-applying exclusions every release
so nothing drifts in by accident.
ASSISTANT interpretation under the ruling (flagged, reversible by adding
names to INCLUDE): the internal collaboration files — .context/,
MEMORY_DIRECTIVE.md, CHARTER_engineering.md, NEXT_SESSION_PROMPT.md —
are also excluded as development-process documents. NOTICE.md and
LICENSE always ship (binding obligations). Public validate.yml keeps
only the artifact-freshness job with a comment stating the seven oracle
suites (~52k values) run in the dev tree pre-release; public README's
validation bullet says the same; public .gitignore ignores validation/
outright so a local copy can never be committed.
Builder mechanics: fresh mode (git init, one release commit) and update
mode (existing .git -> tree replaced, release committed ON TOP; plain
push, no force; no-op when unchanged — verified idempotent).
VERIFIED in the built publication repo [MEASUREMENT]: imports at
v0.24.1; build_wasm_notebook reproduces byte-for-byte (clean tree);
`marimo export html-wasm` produces the 28 MB site with index.html and
.nojekyll, site/ ignored; exclusions absent, obligations present.
site/CLAUDE.md observed in the export is marimo 0.23.16's own exporter
boilerplate, not project content — noted in GITHUB_SETUP.md.
GITHUB_SETUP.md (sourced from the dev tree so the builder can never
delete it) covers identity/auth, repo creation (no-init warning, Pages
needs public on free plans), push, the Pages Source=GitHub Actions trap,
first-load expectations, the release loop, and failure triage. NOT
verified: the workflows on GitHub's actual runners.

## 2026-08-26 — README rewrite + CE references everywhere [HUMAN ruled]
Brian ruled: friendlier README about capabilities; CE references added to
README, code, and the app's References tab. Done at v0.24.2:
- README rewritten capability-first (all five sections, classroom
  features, validation summary in plain terms, a References section
  citing HPLC/CE/GC/Craig sources, licensing). The builder's
  patch_readme marker bullet retained; patch_readme FIXED to consume the
  whole multi-line bullet (it previously replaced only the first line,
  which the rewrite exposed as an orphaned-sentence bug).
- ce.py docstring gained a formal REFERENCES block; the app's References
  accordion gained CE (both SPYCE Electrophoresis 2021 papers with DOIs
  + the free-availability condition), GC (Leppert/JOSS + Blumberg note)
  and Craig (Harvey App. 16) sections after the existing HPLC entries.
- CITATION HYGIENE [ASSISTANT error caught mid-edit]: a title was
  initially written for DOI 10.1002/elps.202000259 from memory; NOTICE
  does not record that title and doi.org is outside the sandbox
  allowlist, so it was removed before commit — that paper is cited by
  journal/volume/pages/DOI exactly as NOTICE records it, with the reason
  stated in the docstring. No public SPYCE repo exists to link (GitHub
  search: zero results, 2026-08-26); the GC repo URL was verified live
  via ls-remote.
Verification: headless export clean with both DOIs and all new sections
present; compare_ce and compare_bandshape re-run PASS; dist v0_24_2;
publish patch verified against the new README.

## 2026-08-26 — Full-width layout, Craig 250-tube ceiling [HUMAN ruled]; content-sync release path
Brian ruled from a live-site screenshot: widgets don't span the window
(answer: marimo App width — "medium" pins ~1100 px; the stretch policy
is App-level, now width="full", confirmed serialized as "full" in the
export config) and the Craig tube ceiling goes to 250 (was 100; cost
nil — closed-form array, 0.3 ms at 250 tubes/200 transfers; keeps
high-D bands on-axis at the transfer maximum). Craig suite re-run PASS;
headless export clean. Version 0.24.3, dist renamed.
OPERATIONAL FACT for future releases: Brian committed the actions/uv
fixes DIRECTLY in his GitHub clone, so the public repo's history has
diverged from any sandbox-built publish repo — pushing a downloaded
publish zip would be rejected. GITHUB_SETUP.md §5 now documents the
content-sync recipe (rsync the release over the clone, --exclude .git,
commit, push); that is the standing release path unless Brian re-roots
the public history deliberately.

## 2026-08-26 — Craig worksheet advanced section [HUMAN ruled]
Brian ruled: refresh the Craig POGIL worksheet with questions for
advanced undergrads / first-year grads. Added a "Going further" section
(A1-A3), enabled by the new 250-tube ceiling, all key values verified
against the model [MEASUREMENT]:
- A1 scaling law: for D=1 vs 4, Rs = sqrt(n)/6 exactly; panel readouts
  1.18/1.67/2.36 at n=50/100/200, ratio sqrt(2) per doubling.
- A2 placement at fixed selectivity (D_B/D_A=4, n=100): symmetric Rs
  ridge 1.41/1.67/1.77/1.67/1.41/1.11 peaking at (0.5, 2) — p's
  straddling 1/2 — the Craig form of the retention window, bridging to
  the k/(1+k) saturation in the triage exercise.
- A3 volume rescue: p = D*Vu/(D*Vu+Vl); V_u/V_l = 1/8 moves (4,16) onto
  the ridge maximum exactly (Rs 1.11 -> 1.77); bridge to phase ratio
  beta, k' = K/beta.
Worksheet (5 pp) leaves all three as derivations/discoveries (leakage
check extended to the new answer values, the winning pair and the 1/8
ratio); instructor key v1 updated in place with the full answers and a
note that the advanced section requires drylab >= 0.24.3.

## 2026-08-26 — ?tab= deep link to sections [HUMAN ruled]
Brian asked how to link students straight to a section (the Craig
apparatus specifically). Shipped v0.24.4: the top-level tabs read
?tab=<key> at load via mo.query_params and pass the mapped label as
mo.ui.tabs(value=...) — keys hplc/gc/ce/band/craig/config/diagnostics,
case-insensitive, unknown/absent -> HPLC (same fallback contract as the
preset params), composable with them (?tab=hplc&hplc=ex3). README
classroom paragraph documents it. Verified: tabs signature supports
value= (marimo 0.24.0 docstring), resolution table unit-checked incl.
case and fallback, headless export clean with the key map serialized.
Note: the param sets the INITIAL tab only — marimo tabs don't write
navigation back to the URL, so a student who clicks away and reloads
the bare URL returns to HPLC; the handed-out link is the way back.

## 2026-08-26 — HOTFIX v0.24.5: tab bounce regression from the ?tab= deep link [HUMAN reported]
Brian reported from the live site: changing a parameter on any non-HPLC
tab bounced the user back to HPLC. ROOT CAUSE: v0.24.4 passed an
explicit value=<initial> to mo.ui.tabs; the layout cell re-runs whenever
ANY section panel rebuilds (every control change anywhere), and an
explicit value re-asserts the landing tab on each rebuild. Pre-0.24.4,
with no value=, marimo preserved the user's selection across rebuilds —
the deep link traded that away. FIX: controlled tab via mo.state in a
panel-independent cell — the query param seeds the state once, on_change
writes each user click back, and rebuilds re-assert the CURRENT tab.
Semantics verified for mo.state directly; headless export clean with the
wiring serialized. VERIFICATION GAP, stated plainly: the bounce is a
click-interaction behaviour that headless export cannot exercise (which
is also why v0.24.4 shipped it) — Brian must confirm on the live site:
(1) load ?tab=craig -> lands on Craig; (2) move a Craig slider -> stays;
(3) click to GC, move a GC control -> stays on GC.

## 2026-08-27 — v0.24.7: equations accordions, log velocity axis, N_app guard

**Brian's rulings this session:**

1. **Every equations block lives in a collapsed accordion** titled "The
   equations" — the two existing blocks (Craig, GC) moved, and two new
   blocks added to Band shape (Mechanisms and Peak shape tabs). Rationale:
   the tool must be complete for outside users, but the content stays off
   the visual path during class so worksheet inquiry survives.
2. **Statics-only content rule** (assistant's proposal, Brian's adoption
   via the trends redesign): equations blocks state definitions and closed
   forms only — never consequence statements ("A is absent from u_opt",
   "N_app exceeds N"). Consequences are the classroom's inventory; every
   consequence kept out of the panel is a live worksheet question.
3. **Log velocity axis is a student-switchable checkbox** ("Log velocity
   axis", Mechanisms tab), default ON (assistant's call, flagged: the fixed
   0.02-1.0 cm/s window puts typical optima at ~4% of a linear axis; log is
   the Knox-plot convention). Guard per Brian: the plot class only honours
   log_x over strictly positive velocities and degrades to linear
   otherwise; van_deemter_components independently rejects u <= 0.
4. **N_app readout guards sigma = 0**: at k = 0 the apparent-plate division
   is undefined and previously printed "nan"; it now prints
   "n/a (sigma = 0, unretained)". Found by measuring the k-slider edge
   while designing the revised exercise.

**Content note:** the Mechanisms accordion explicitly names the eddy-term
controversy (builder draws van Deemter's flat A = 2·lambda·dp; Wenzel's
text uses A·v^(1/3); some authors drop A). Without this note the
text/builder mismatch reads as a drylab bug to any student doing the
reading.

**Scope not taken:** HPLC and CE sections still have no equations blocks
(pre-existing gap, on the docket); ?tab= remains parked.

## 2026-11-09 — Exercise 8 (CE lab after the two CE lectures) [HUMAN asked; ASSISTANT design]
Brian asked for "a new drylab login exercise focusing the lessons from the CE
lectures", ~45 min. Read "login" as "lab" (flagged). Ex 6 already covers EOF
arrival order, so Ex 8 targets what the lectures added: j = kappa E (Q1),
injection- vs diffusion-limited plates (Part A), electromigration dispersion with
the imidazole co-ion (Part B), antistacking from a salty matrix (Part C);
homework: N vs l^2, K+/NH4+ pH selectivity in Tris/chloride, Joule scaling.
No preset (CE has none); students edit the Composition table. Masters:
classroom/masters/student_ws_ex8.md, key_ex8.md; measurements:
validation/ex8/ (harness.py reproduces the CE cell's readouts; measure_ex8.py
regenerates key_values.json in four <1 min sections). All four QA gates passed.

## 2026-11-09 — Ex 8 Part D (pKa/pH) and a generic worksheet → Word builder [HUMAN asked; ASSISTANT design]
Brian asked for another question using pKa and pH, and the worksheet as Word.
Part D uses pyridine (30.0, pKa 5.16) and aniline (32.5, pKa 4.80): at pH 4.93
the fully-charged order reverses (pyridine 13.95 s, aniline 18.91 s at 1000 V);
students then compute the co-migration pH (4.00 -> 3 mM imidazole) and confirm
it (app pH 4.02, 8.95 vs 8.94 s). Time plan rebalanced to 45 min (A 13, B 11,
C 8, D 6). Apparent mobilities read 3-8 % high because both bases tail (slower
than imidazolium): the key uses this as a Part B tie-in. Word: new
classroom/tools/build_worksheet_docx.js converts any standard master instead of
hand-building per exercise as Ex 1 did.

# issues

## CLOSED 2026-08-04 — Gradient elution implemented and validated
Ported from HPLCSimulatorApplet.java (mixer simulation + band marching);
26,544 values across 74 isocratic and 23 gradient cases agree with the Java
oracle (gradient tR bit-identical). Closed by human GO ruling 2026-08-04.
Original entry follows for history:

## (historical) OPEN/PARKED — Gradient elution unimplemented (2026-08-03)
The JS reference offers gradient in its UI but `f.kPrime` returns NaN in
gradient mode; `gradientStops` and dwell time exist but feed nothing. Port
raises `GradientNotImplementedError`. Unblocked by: a human ruling to
implement from primary sources (Boswell et al. / hplcsimulator.org Java
applet), since this is new physics work, not a port. Implementation will need
per-compound numerical integration over the gradient program — the numba
candidate (see decisions).

## CLOSED 2026-08-04 — Tubing broadening restored (follows Java ancestor)
Human ruled to follow the Java, which applies the term in both modes.
Implemented as formulae.tubing_time_broadening; zero-length tubing returns
exactly 0.0 so the JS goldens still pass. Original entry follows:

## (historical) OPEN/PARKED — Extra-column tubing broadening absent (2026-08-03)
The reference computes post-tubing volume but its sigma ends with
`// + dTubingTimeBroadening`; the Java formula survives only in comments
(preserved near `formulae.post_tubing_volume` docstring / reference source).
Port matches the reference: tubing inputs do not affect peaks. Unblocked by:
ruling to restore it, validated against the Java applet or literature.

## OPEN — post_tubing_diameter unit uncertain (2026-08-03)
Reference comment says "mm ?" while the conversion constant 2.54e-5 smells
of an inch-based unit (mil?). Carried verbatim so golden validation holds.
Unblocked by: checking the original Java applet's tubing units.

## OPEN — Single column preset (2026-08-03)
Only 'Agilent Zorbax SB-C18' shipped in the reference; upstream
hplcsimulator.org has many. Core accepts any `ColumnPreset` + per-run
`column_overrides`. Unblocked by: sourcing a preset table (upstream site or
applet resources).

## OPEN — Compound editor not in UI (2026-08-03)
Core already accepts arbitrary `sample_mix` (any of the 5 table compounds,
any concentrations) but the notebook exposes only the default mix.
Unblocked by: UI ruling (marimo editable table, peakachu-window-editor
style).

## OPEN — Reference `noise` input has no located consumer (2026-08-03)
`inputs.noise = 2.0` exists in the reference but neither the model nor the
chromatogram service visibly applies it (svc/chromatogram.js draws raw
series). Port's opt-in seeded noise is therefore an extension, flagged in
decisions. Unblocked by: nothing pressing; re-check reference UI code if
fidelity of noise ever matters.

## OPEN — `secondPlot` "Retention"/"Position" modes not ported (2026-08-03)
The reference lists compound-type second plots (Retention, Position) in
globals; their rendering path wasn't ported (binary-type quantities —
solvent fraction, backpressure, viscosity — are). Unblocked by: ruling on
whether these views are wanted; SweepPlot already covers k'/tR vs conditions.

## CLOSED 2026-08-04 — post_tubing_diameter unit resolved: mils
Java source converts with 0.0000254 (m) / 0.00254 (cm) per unit -> the
tubing diameter is in thousandths of an inch (mils), not mm. Docstring
updated understanding; port math unchanged (constants were already carried
verbatim). Closed by reading HPLCSimulatorApplet.java tubing block.

## CLOSED 2026-08-04 — Compound database: 22 analytes extracted from Java
Was "single-source 5 compounds"; closed by extraction from Globals.java
(see decisions 2026-08-04). Compound *picker* shipped; full per-compound
concentration editor remains OPEN (below).

## UPDATE 2026-08-04 — Gradient elution: algorithm located, awaiting ruling
HPLCSimulatorApplet.java contains the full implementation: a 1000-point
well-stirred-mixer simulation of the solvent program (mixing volume as CSTR,
non-mixing volume as plug delay; calculateGradient), linear interpolation of
phi(t), then per-compound step marching (dtstep = span/1000) of fractional
column position dX = (dtstep/k'(phi(t - integral)))/t0 to elution, with
linear interpolation at the crossing. Gradient sigma uses k' at elution and
omits injection-volume broadening (source TODO). Standing decision
2026-08-03 (isocratic-only v1) still governs; implementing requires a human
ruling and would validate against a compiled run of this applet or hand
digitization. Numba candidacy applies here.

## UPDATE 2026-08-04 — Tubing broadening: formula located, ACTIVE in Java
The Java adds dTubingTimeBroadening to sigma in BOTH modes; the JS port
commented it out — a port divergence, not an upstream choice. With default
tubing length 0 the term vanishes, so adopting the Java behavior would not
disturb golden validation at defaults, but any tubing length > 0 diverges
JS-vs-Java. Which reference wins is a human ruling (recommendation on
record: follow the Java ancestor).

## UPDATE 2026-08-04 — Column presets: NOT unblocked by the Java source
The applet also ships exactly one stationary phase ("Agilent Zorbax
SB-C18", ColumnProperties.java:313). A larger column list, if it exists,
lives in the newer web version, not in this v1.1.3 source. Still open.


## OPEN — Gradient sigma omits injection-volume term (2026-08-04)
Reproduced deliberately from the Java (whose own comment flags the gap)
so validation is meaningful. The term is implemented and switchable via
SimulationInputs.gradient_sigma_includes_injection (default False).
Unblocked by: a ruling to flip the default, ideally with a reference to
validate the corrected form against (the Java cannot validate its own gap).

## OPEN — Gradient sweeps not wired (2026-08-04)
The Sweeps tab operates on the isocratic inputs only. SweepPlot is
mode-agnostic in principle, but sweeping a gradient run means sweeping a
program (ramp slope, final %B), which needs its own parameter registry.
Unblocked by: a ruling on which gradient parameters are worth sweeping.


## CLOSED 2026-08-04 — Unviable gradient methods now fail fast and loudly
Pre-check + step budget + skip-and-report (see decisions). Refusal is ~0.7 ms
with a message naming the analyte, its k' at the strongest composition, and
four concrete remedies. Validation unaffected (budget disabled there).

## CLOSED 2026-08-05 (was OPEN; fixed before this session) — WASM builder duplicates the notebook's import list (2026-08-04)
tools/build_wasm_notebook.py restates the `from hplc_sim import (...)` names
as literals; three times now a new export broke the generated notebook until
the builder was hand-edited. Duplicated authority (charter §9). Unblocked by:
deriving the import block from the notebook source between the sentinels, or
adding a post-build check that compares the two name sets and fails loudly.
Mitigation in place meanwhile: always run the isolated-directory export of
the dist artifact and read the COMMAND output, not the HTML.

## CLOSED 2026-08-05 (was OPEN; superseded) — GC simulator port (2026-08-05)
NOTE: the session handoff referenced a prior assessment entry here; it was
never written. This entry is a fresh assessment from the upstream source
(GasChromatographyToolbox/GasChromatographySimulator.jl v0.6.1, MIT,
src/ = 4,426 lines Julia incl. docstrings; physics in Model.jl, ODE in
Solving.jl, structs in Structures.jl).

Physics that ports cleanly (all closed-form, ~considerably smaller than the
HPLC port): Blumberg/HP viscosity per gas (He/H2/N2/Ar, constants in
source); James–Martin pressure profile p(x,t); flow restriction; Pressure- and
Flow-control variants; K-centric retention model
ln k0 = (ΔCp/R + Tchar/θchar)(Tchar/T − 1) + (ΔCp/R)ln(T/Tchar), k = φ/φ₀·e^lnk0
capped at k_th (default 1e12); Golay plate height with DS = DM/10000;
Fuller–Schettler–Giddings diffusivity Cag from atom counts; piecewise-linear
T(t)/pin(t)/pout(t) programs.

The ODE system (the real work, Solving.jl odesystem_r!): per solute over
z ∈ [0, L]:  dt/dz = r(z,t);  dτ²/dz = H·r² + 2τ²·∂r/∂t, with ∂r/∂t via
ForwardDiff in Julia (source docstring prints H·r; the code and dimensions
say H·r² — code is authority). Julia default alg OwrenZen5, abstol 1e-6,
reltol 1e-3.

MEASURED lift (scipy prototype, /home/claude/gc_prototype.py pattern,
ng=true, Pressure control, Blumberg, FD for ∂r/∂t, solve_ivp at Julia's
default tolerances): 10 solutes ≈ 62 ms RK45 (6.2 ms/solute, 1352 RHS
evals), LSODA similar; pathological k>1e15 solute (glyceryl triacetate,
Tchar 719.3 K from the Julia test suite) returns finite in 20–100 ms with
tR ≈ 75 days — same absurd-but-finite failure mode as the HPLC gradient
march; the existing viability-report pattern applies. No numba case.

Branch points recorded (awaiting ruling, recommendations in session
2026-08-05): Measurements.jl uncertainty propagation; ChemicalIdentifiers.jl
lookup vs vendored compound table; UI/module layout; v1 option scope
(spatial thermal-gradient ng=false path needs in-RHS quadrature — candidate
to park); oracle validation tolerance (solver-limited, not ulp-limited —
the 1e-12 HPLC standard does not transfer).

## RESOLVED 2026-08-05 — GC simulator port (v1, isothermal) landed in v0.10.0
`hplc_sim/gc.py` (closed-form core + vendored Blumberg 2017 table),
`hplc_sim/plotting/gc.py`, notebook "GC" top-level section with its own
sidebar, `validation/compare_gc.py` (2,754 values vs golden_gc.json,
PASS at measured tolerances tR 1e-8 / τR 1e-12 / tM 1e-14),
`validation/dump_golden_gc.jl` (oracle harness; needs upstream clone path
as ARGS[1], writes golden next to itself; full run incl. the Measurements
Part B needs ~5–8 min in one process).

## CLOSED 2026-08-05 (was OPEN; superseded by the 2026-08-05 entries) — GC temperature programming (parked extension, ruled 2026-08-05)
v1 is isothermal by ruling. The extension needs the per-solute ODE march
(dt/dz = r, dτ²/dz = H·r² + 2τ²·∂r/∂t) because H is no longer constant
and ∂r/∂t ≠ 0. Groundwork already measured: scipy solve_ivp prototype ran
10 solutes in ~62 ms at the oracle's default tolerances (RK45), and the
pathological k>1e15 solute returns finite in <100 ms — no numba case.
Beware the vacuum-outlet endpoint singularity (p→0 at z=L): the naive RHS
divides by zero there; under programs it does NOT cancel away, so the
march needs either a guarded final step or the substitution u = p².
Unblocks: a ruling to proceed, plus extending dump_golden_gc.jl with
programmed cases (the harness structure already supports it).

## RESOLVED 2026-08-05 — WASM builder import-list duplication
tools/build_wasm_notebook.py no longer restates the notebook's import
list; it extracts the [[INLINE]] cell text from the notebook itself and
rewrites only the HPLC_SIM_VERSION line (guarded: the build fails loudly
if that line disappears). First exercised carrying 13 new GC imports with
zero builder edits. The failure class (three prior breakages) is gone.

## OPEN — HPLC column presets: what a second preset can honestly be (assessed 2026-08-05)
Assessment before any data entry, because the naive move is wrong:

A ColumnPreset carries ONLY geometry + efficiency (length, diameter,
particle_size, inter/intraparticle porosity, van Deemter A/B/C). It does
NOT carry retention. The retention coefficients (km/kb/sm/sb per compound
per solvent, 22 compounds x 2 solvents) live in COMPOUNDS and are
STATIONARY-PHASE-SPECIFIC — they were measured on one column.
Consequence: adding a preset for a different phase chemistry (XBridge,
Kinetex, SB-C8 vs SB-C18, ...) would silently apply this phase's retention
data to that phase. Physically wrong, and invisible in the UI. Not to be
done without a matching retention dataset.

What IS honest: different FORMATS of the SAME packing (length, diameter,
particle size). k is a property of phase + eluent + T, unchanged by column
format, so only tM, efficiency, and backpressure move — all computed, not
tabulated. Confirmed transferable because A/B/C are REDUCED coefficients
(h = A + B/nu + C*nu, dimensionless; model.py reduced_plate_height), which
is the form that carries across particle sizes for like packing quality.
Agilent publishes the format matrix (e.g. SB-C18 in 1.8/3.5/5 um, 50/100/
150/250 mm, 2.1/3.0/4.6 mm). Caveat to state in any such preset: porosity
and A/B/C are the reference simulator's FITTED values for the original
column, reused for the format variant — vendors do not publish them.

Provenance discrepancy found, NOT resolved unilaterally: the preset is
named "Agilent Zorbax SB-C18" (both reference implementations), but
Boswell/Stoll/Carr/Nagel/Vitha/Mabbott, J. Chem. Educ. 2013, 90, 198-202
describes the simulator as built on 22 compounds measured on an Agilent
Zorbax SB-**C8** column — and our table has exactly 22 compounds. A 2024
LCGC survey instead describes "more than 40 compounds on an Agilent
SB-C18". Possibilities: the applet's preset name is wrong; or the data was
re-measured on SB-C18 for a later version and our 22-compound table is the
older SB-C8 set. Unblocks: check the hplcsimulator.org site/source history
or ask the authors. Until resolved, the shipped name follows the reference.

## CLOSED 2026-08-05 (see the dynamic-version entry below) — pyproject.toml version drift
`pyproject.toml` still declares `version = "0.9.1"` while
`hplc_sim/__init__.py` declares `__version__ = "0.10.0"`. The notebook and
the WASM builder both read `hplc_sim.__version__`, so the shipped artifact
and the in-app stamp are correct and only the packaging metadata is stale —
but this is duplicated authority (charter §9) and it has already drifted
once. Its `description` is also stale ("Isocratic HPLC simulator core";
the package now ships gradient, Craig and GC). Unblocks: a ruling on the
fix — either derive the pyproject version from the package
(`[tool.setuptools.dynamic]`) so there is one source of truth, or accept
two and add a check. NOT fixed unilaterally: a version string is a
delivery decision.

## CLOSED 2026-08-05 — MODULES omission is now a build failure (guard + EXCLUDED map with stated reasons)
The import-list duplication was resolved (entry above), but
`tools/build_wasm_notebook.py` still hand-maintains `MODULES` /
`PACKAGE_INITS` — a literal restatement of the package's module inventory.
A module added to `hplc_sim/` and omitted here is embedded nowhere, and the
build does NOT catch it: `main()`'s verification step only calls
`compile()`, which never executes the embedded registration block. The
in-source comment claims more than the code does ("the embedded package
must import in a namespace where the repo package is masked" — no import or
exec follows). Failure therefore surfaces only when the exported notebook
runs, i.e. exactly where marimo's `show_tracebacks: false` hides it.
Same failure class as the four occurrences already in learnings.
Unblocks: a ruling to either derive MODULES by walking `hplc_sim/` in
dependency order, or add a real post-build check that execs the generated
inline block with the repo package masked. Meanwhile the mitigation stands:
always run the isolated-directory export and read the COMMAND output.

## CLOSED 2026-08-05 — GC section: dropdown overlap, legend space, non-eluting blank
All three reported from a screenshot + traceback; ruled by the human the
same session (see decisions 2026-08-05 "Three GC/UI rulings"). Closed by:
StationaryPhase(label, description) records with a width-constrained
caption; PlotConfig.show_legend + three per-section switches; and
gc.simulate(skip_non_eluting=True) returning GCRun with viability_report().
Verified by full-notebook export (clean) plus an isolated-directory export
of the dist artifact, both asserting on computed values. v0.10.1.

## OPEN — learnings entry of 2026-08-04 on counting rendered elements is version-bound (2026-08-05)
The "count marimo-slider / marimo-dropdown elements in the export" probe
returns 0 on marimo 0.23.16 even for a working build (see the learnings
entry of 2026-08-05). The learning has been superseded in place by the
computed-value probe, but the ORIGINAL 2026-08-04 entry still reads as
unconditional advice. Unblocks: a decision on whether to amend the older
entry in place (memory is supposed to be corrected, not appended to
indefinitely) or leave both with the later one governing. Left alone
because editing a dated entry is a memory-integrity decision, not a
mechanical fix.

## CLOSED 2026-08-05 — WASM artifacts shipped without an internal version stamp
Charter section 10 requires the version inside the artifact, not only in
its filename. The builder's stamp anchored on the old app title and had
been a silent no-op since the v0.9.1 rename; v0.9.1, v0.10.0 and v0.10.1
were all affected. Closed by re-anchoring on the module docstring's
structure with a hard guard (raises and names the problem if no anchor is
found), mutation-verified. NOTE for anyone reproducing old builds: the
dist/ artifacts for v0.9.1 and v0.10.0 still in the repo remain unstamped;
they were built by the old code and were deliberately NOT rewritten, since
editing a shipped build artifact in place would defeat the point of
versioned deliveries.

## CLOSED 2026-08-05 — dist/ pruned to the single current artifact
Human ruled that dist/ should keep only the current build, and asked that
the pruning happen in a LATER turn rather than as part of the v0.10.1
delivery. Pending action: delete dist/hplc_simulator_wasm_nb_v0_9_1.py and
dist/hplc_simulator_wasm_nb_v0_10_0.py, keeping only the newest artifact.
This settles the inconsistency on record: v0.2.0 removed its predecessor,
v0.10.0 kept it. Going forward, one artifact.
Caveat worth stating when it happens: both files due for deletion were
built before the version-stamp fix and carry no internal version marker
(see the CLOSED entry above), so once their filenames are gone nothing
identifies them — which is an argument for deleting rather than archiving
them. Unblocks: the human saying go, in a later turn.

## CLOSED 2026-08-05 — programmed GC core written, validated (11,520 values) and in the UI
golden_gc_program.json (64 cases, 1,024 values) now ships in validation/,
generated by the extended dump_golden_gc.jl on a toolchain proven to
reproduce the existing isothermal goldens byte-identically. Remaining work,
in order: (1) measure hand-rolled RK vs scipy solve_ivp for SIZE and report
it, since the human's ruling was conditional on the hand-rolled version
being smaller; (2) implement the programmed core (dt/dz = r(z,t),
dtau^2/dz = H r^2 + 2 tau^2 dr/dt) with the u = p^2 substitution for the
vacuum-outlet singularity; (3) validation/compare_gc_program.py against the
new goldens, with tolerances set by MEASUREMENT (solver-limited, not the
~1e-9 of the closed forms); (4) notebook tab plus an isothermal-vs-
programmed comparison plot. The comparison plot inherits the HPLC compare
precondition: column and pneumatics controls must be SHARED between the two
arms so they provably differ only in the elution program. Unblocks: nothing
external — this is implementation work now.

## CLOSED 2026-08-05 — WASM builder's MODULES list could silently omit a module
The hazard became concrete when hplc_sim/gc_program.py was added: the
inventory is hand-maintained, and an omission embeds the module NOWHERE
while the build reports success, surfacing only at notebook run time where
marimo hides the traceback. build_wasm_notebook.py now diffs MODULES +
PACKAGE_INITS against hplc_sim/**.py on disk and exits 1 naming any
unregistered file (and any registered file that no longer exists).
Mutation-verified by deleting the gc_program entry: build fails with the
filename. The list is still hand-maintained — deriving it in dependency
order remains possible future work — but an omission is now loud.

## CLOSED 2026-08-05 — Programmed GC has no UI
hplc_sim/gc_program.py and validation/compare_gc_program.py are done and
passing, but nothing in hplc_simulator_nb.py exposes them. Remaining: a
program editor (the HPLC gradient editor's data_editor pattern is the
precedent, including its NaN-row and sorting lessons), a GC sub-tab
structure mirroring HPLC's Isocratic/Gradient/Compare, and the
isothermal-vs-programmed overlay the human asked for. That overlay
inherits the HPLC compare precondition: column and pneumatics controls
must be SHARED between the two arms so they provably differ only in the
elution program. Unblocks: nothing external.

## CLOSED 2026-08-05 — pyproject.toml version drift
Fixed structurally rather than by syncing: `version` is now
`dynamic = ["version"]` with `[tool.setuptools.dynamic] version = { attr =
"hplc_sim.__version__" }`, so the packaging metadata cannot disagree with
the package again. Proven by building a wheel: hplc_sim-0.12.3-py3-none-
any.whl. The stale description ("Isocratic HPLC simulator core") was also
corrected — it predated gradient, Craig and GC.

## CLOSED 2026-08-05 — Programmed GC has no UI
GC now has three sub-tabs (Isothermal / Programmed / Compare) under ONE
controls region, so column, carrier and pneumatics are shared and the
Compare overlay provably differs only in the elution program. The program
editor takes ABSOLUTE times in minutes (how a method is written) and
converts to GCProgram's segment durations in one place. Row validation
follows the gradient editor's ruled policy: blank rows dropped and
reported, out-of-order rows sorted and reported, duplicate times refused
by name. An invalid program does NOT blank the isothermal tab — mo.stop is
deliberately not used there, since the two arms are independent.

## CLOSED 2026-08-05 — Stale OPEN entries in this ledger
Three entries were still headed OPEN after being resolved (GC simulator
port, WASM builder import-list duplication, the original temperature-
programming parking entry). Re-labelled CLOSED with "(was OPEN)" and the
reason rather than deleted, so the history stays readable. A stale OPEN is
worse than no entry: this file is what a future session reads to decide
what is live.

## OPEN — gc_controls and gc_panel share one cell (found 2026-08-05, flagged not fixed)
Mutation-testing the per-section split injected a raise into the GC panel
cell; HPLC and Craig kept rendering (the containment property held), but
the GC CONTROLS vanished too, because gc_controls and gc_panel are built in
the same cell. That is the same "controls must survive so the user can fix
the input" principle already applied inside the error guards, but at cell
granularity. The same shape exists for craig_controls/craig_panel. Honest
fix: build each section's controls in their own cell, upstream of the panel.
NOT fixed here — doctrine section 2, this was outside the scope of items 1
and 2 and would have made the diff unreviewable.

## CLOSED 2026-08-05 — CE module built on SPYCE, oracle-validated, licensed and shipped
Scope would be a 1D electromigration simulator after Gas & Bravenec,
Electrophoresis 2021, 42, 1291-1299 (Simul 6): continuity equations +
acid-base equilibria + electroneutrality, finite differences in x, RK in t,
with the G-function root solved for cH at every node every step.
MEASURED cost of a representative vectorised numpy kernel (arithmetic
volume and array shapes of one RK stage, 6 stages + 5 Newton iterations,
NOT validated physics — /tmp cost model, reproduce before relying on it):
  Nx=200,  N=5    ->   4.6 ms/step
  Nx=500,  N=8    ->  22.4 ms/step
  Nx=1000, N=10   ->  45.4 ms/step
  Nx=1000, N=30   -> 125.8 ms/step
  Nx=1000, N=181  -> 749.5 ms/step
Projection: teaching-scale CZE (Nx=500, 8 constituents, ~600 steps) is
~13 s native, ~34 s in WASM at an assumed 2.5x penalty — viable. The
paper's own 181-ampholyte IEF case projects ~68 min single-threaded numpy
against their 18 min in multithreaded C++ (~3.8x), i.e. NOT viable in a
browser. The verdict is therefore scope-dependent, not yes/no.
NUMBA IS NOT AN OPTION and this is decisive rather than a preference:
numba needs llvmlite, which has no Pyodide build, so the WASM target rules
it out entirely. Vectorisation across grid nodes is the only lever — which
works because the nodes are independent within a step.
LICENSING, must be settled first: Simul 6 is GPL-3. Porting its source into
this project would make the result GPL-3, which conflicts with the current
CC-BY-NC-SA-3.0-US. The project's existing pattern avoids this cleanly:
implement from the PUBLISHED EQUATIONS (equations are not copyrightable)
and use Simul 6 only as a validation-time ORACLE, exactly as the Java
applet and GasChromatographySimulator.jl are used. Do NOT read the Simul 6
source into the port.

## REFERENCE (was OPEN) 2026-08-05 — CE route comparison, kept for the ITP/linear-theory decision
Measured, both from cloned sources and from cost-model kernels:
  Simul 6 (dynamic, PDE march): 12,616 lines C++, GPL-3, Qt.
    Cost: 13 s (teaching CZE) to 68 min (paper's 181-ampholyte IEF),
    single-threaded numpy projection.
  LEMNG (linear theory, eigenzones): 10,611 lines C++, GPL-3, Eigen,
    plus a HARD dependency on ECHMETCoreLibs for equilibrium composition.
    PeakMasterNG is only a Qt GUI over it.
    Cost: 0.43 ms (3 constituents) to 5.15 ms (40) per FULL calculation.
LINEAR THEORY IS ~4-7 ORDERS OF MAGNITUDE CHEAPER, because it never
marches time: it solves the equilibrium at ONE point, builds small N x N
matrices, eigen-decomposes them for the eigenzone (system-peak) mobilities,
and evaluates HVL-R peak shapes. That is the same computational SHAPE as
this project's existing HPLC and isothermal-GC models, which are closed
forms with a plotting pass — it fits the architecture rather than
straining it, and is interactive in the browser without qualification.
THEY ANSWER DIFFERENT QUESTIONS, which is the real decision, not speed:
linear theory gives effective mobilities, BGE pH and conductivity, system
peaks and electromigration dispersion for CZE at low analyte load. It
CANNOT show stacking, ITP, IEF or any transient — those need the dynamic
simulator. Choose by which chemistry is to be taught, then accept the
performance envelope that comes with it.
LICENSING is identical for both: GPL-3, so the same rule applies — port
from the PUBLISHED EQUATIONS (LEMNG's model is published as Electrophoresis
2019, DOI 10.1002/elps.201800400) and use the binaries as validation-time
ORACLES only. Do not read either source into the port.
NOT VERIFIED: GENTRANS, SPRESSO, electroMicroTransport and the COMSOL
route were not examined; they are named here only as they appear in Gas &
Bravenec's review.

## CLOSED 2026-08-05 — SPYCE route chosen, licence granted (NOTICE.md)
SPYCE 2.0 (Gupta & Bahga; Electrophoresis 2021, DOI 10.1002/elps.202100279)
is ALREADY PYTHON: 730 lines in SPYCE.py + 34 in AnalyseData.py, against
Simul 6's 12,616 lines of C++ and LEMNG+ECHMETCoreLibs' 30,600. It solves
the FULL dynamic model (CZE, ITP, t-ITP, FASS, IEF, oscillating
electrolytes) by Chebyshev pseudo-spectral differencing on a moving mesh,
which is why it needs far fewer grid points and steps than a finite-
difference simulator.
MEASURED here, on the shipped sample inputs, realtime plotting disabled:
  CZE   (N=257,  75 s physical)   1.4 s
  FASS  (N=257)                   5.4 s
  ITP   (N=257, 300 s physical)  14.5 s
  t-ITP (N=1025)                 69.9 s
  IEF   (N=1025, 21 ampholytes)  reached t=84.7 s of 150 s in ~7 min;
                                 the paper reports 16 min total on an i7
So CZE/FASS are comfortably interactive even after a WASM penalty; ITP is
borderline; IEF is a batch job, exactly as with every other simulator.
DEPENDENCIES ARE ALMOST IDEAL FOR THIS PROJECT: numpy, matplotlib, and
scipy used in exactly ONE place — special.erf at line 395, replaceable
with math.erf. So the 35 MB scipy wheel can be dropped entirely and
matplotlib swapped for the existing plotly layer. No numba anywhere.
BLOCKER, and it is a licence problem of a DIFFERENT kind: the archive
contains NO LICENCE AT ALL — no LICENSE file, no header grant, only an
authorship line. The paper calls SPYCE open source and it is offered for
public download, but absent an explicit grant the default is all rights
reserved, which is legally MORE restrictive than Simul 6's GPL-3, not
less. Fixable by one email to the authors (bahga@mech.iitd.ac.in), who
plainly intend it to be used. Do NOT port it until that grant exists in
writing.
CODE-HEALTH NOTE if it is adopted: SPYCE.py is a single 730-line script
driven by module-level `global` statements and exec'd text input files,
with a debug `from pdb import set_trace` left in. It works, but it is the
opposite of this project's structure, so adoption means restructuring, not
dropping it in.

## CLOSED 2026-08-05 — run button plus free scrubbing, as ruled and implemented
Human requirement: the CE module must slot into drylab's plotting/config
layer with sliders and interactive results "similar to the LC and GC
modules".
THE TENSION, measured: LC and GC are CLOSED FORMS — a slider move
recomputes in microseconds, which is why marimo's reactive re-execution
feels instant there. SPYCE marches a PDE: 2.7 s for the CZE sample
(N=257, 75 s physical) back-to-back on this machine, and 2-3x that under
WASM. A slider that re-runs the march on every drag is a 5-8 s stall per
tick, which is a different interaction model, not a slower version of the
same one.
WHAT RESCUES IT: the march already returns the FULL space-time field —
arr_2 is (species, grid points, saved times). So scrubbing time or
position AFTER a run costs nothing. The genuinely interactive part is
free; only changing a PHYSICAL parameter is expensive. save_frequency in
the input file controls how many time slices are kept.
PROPOSED SHAPE (needs a ruling): three regions in the CE section —
  (a) instantly reactive: BGE properties (pH, conductivity, effective
      mobilities). These are the equilibrium solve alone, no march, so
      they are closed-form-fast and behave exactly like LC/GC.
  (b) explicit Run: the dynamic simulation, gated behind mo.ui.run_button
      so a half-typed parameter never triggers a 5 s march.
  (c) free scrubbing: time and position sliders over the returned field,
      driving the plots. This is where it will FEEL like LC/GC.
PLOTTING: two new BasePlot subclasses — an electropherogram (detector
trace c_i(t) at fixed x, directly analogous to ChromatogramPlot, same
fill/legend/sum treatment) and a spatial profile (c_i(x) at the selected
time). Both get pH and conductivity on the SECONDARY AXIS, reusing the
overlay pattern built for the GC oven ramp; the paper's Fig. 5 is exactly
that plot.
VERIFIED so far: SPYCE runs with scipy AND matplotlib hard-blocked at
import (numpy only); scipy.special.erf -> math.erf via np.vectorize costs
nothing in time (2.67 s vs 2.75 s back-to-back) and agrees to 6.9e-09 of
full scale. SPYCE is bit-deterministic run to run, so that residual is
the erf swap perturbing RKF45's adaptive step decisions, amplified within
the solver's own tolerance of 1e-3.
CONSEQUENCE FOR VALIDATION: SPYCE's default RKF45 tolerance is 1e-3, so
compare_ce.py tolerances must be set from the solver's OWN convergence,
exactly as compare_gc_program.py's were. Do not copy the 1e-8 used by the
closed-form suites.

## CLOSED 2026-08-05 — CE engine: boundary wraparound (endpoint formulae + Hou-Li filter; regression-guarded in compare_ce.py)
MEASURED failure: an analyte migrates at exactly the predicted rate
(26.0 -> 2.5 mm over 55 s at mu*E*t) and then, on reaching the end of the
domain, the solution BLOWS UP — the peak reappears at 28.4 mm and the
integrated mass jumps 16-fold (-2.9 -> -47.6).
CAUSE: _cheb_diff differentiates via an even extension and FFT, which is
periodic, so a feature leaving one end re-enters at the other. Bahga &
Gupta state explicitly that df/dx "can be calculated using Equation (7)
with special formulae for the endpoints, xi = +-1" — those endpoint
formulae were never implemented. Adding dc/dt = 0 at the boundaries did
NOT fix it, which confirms the fault is in the differentiation, not the
boundary condition.
CURRENT MITIGATION, not a fix: the shipped defaults keep every analyte
clear of the boundary for the whole run (inject at 0.87 L, detector at
12 mm, 60 s), so the demonstration stays inside the regime where the
scheme is sound. A user who raises the current or the run time far enough
WILL leave that regime and get nonsense, with no warning.
UNBLOCKS: implement the endpoint formulae, then compare_ce.py against the
SPYCE fixture, which is what would have caught this systematically instead
of by inspection.

## OPEN — ITP does not work; measured, not assumed (2026-08-05)
Tested the static-grid CZE solver on a standard ITP configuration
(chloride LE 100 mM / HEPES TE 100 mM, Tris counter-ion, analytes of
intermediate mobility sandwiched at the LE-TE boundary).
It RUNS stably and conserves mass to 3 decimals at N = 129/257/513, so the
numerics are sound — but it does NOT reproduce ITP. All three defining
signatures fail:
  1. COMMON VELOCITY: analytes travelled at -0.087 and -0.054 mm/s. In ITP
     every zone moves at the LE velocity by definition; these are simply
     separating, i.e. zone electrophoresis.
  2. SELF-SHARPENING: zone sigma grew 0.566 -> 1.98 mm. ITP zones sharpen
     against diffusion because a slower ion drifting ahead meets a higher
     field and catches up. Longer runs and higher current made it worse,
     not better (sigma 0.57 -> 2.84 mm by 108 s, peak 20 -> 2.8 mM, and
     essentially dispersed to nothing by 230 s).
  3. PLATEAU CONCENTRATIONS: analyte peaks fell 20 -> 5 mM rather than
     adjusting to a Kohlrausch-regulated plateau set by the LE.
So the moving mesh is NOT the blocker, which was the prior assumption
(recorded 2026-08-05, "the moving mesh exists to resolve the sharp
self-sharpening fronts of ITP"). Something upstream of resolution is
missing, because the fronts never sharpen in the first place. Candidates,
untested: the Kohlrausch regulating function is not being conserved by
this discretisation; the counter-ion treatment; or the initial condition
not being a true LE/TE step in electroneutral equilibrium.
FASS was not tested and should not be assumed to work either — it depends
on the same conductivity-step stacking mechanism.
DO NOT SHIP an ITP mode until this is diagnosed. The honest status is that
drylab does CZE, validated, and does not do ITP.

## CLOSED 2026-08-17 — GC controls NameError when the run fails
_phase_caption was built inside the isothermal panel's success branch but
consumed unconditionally by gc_controls, so ANY carried GC error raised
NameError in the panel cell and blanked the section's controls — the exact
defect the "controls outside the guard" comment claimed to prevent. Latent
until 2026-08-17 because default inputs always simulate; exposed by the
new empty-selection guard. Fixed by building the caption before the guard.

## CLOSED 2026-08-17 — Classroom presets shipped (construction-default seeds + query params)
Closed by Brian's GO ("go ahead with 4 and then 2"); mechanism chosen by
the assistant under that delegation (see decisions 2026-08-17): preset
dropdowns seed control construction defaults, ?hplc=/?gc= params select
presets by short key. Original entry follows:

## (historical) OPEN — Classroom presets (2026-08-17)
The POGIL exercises need every group to start from an identical scenario
(e.g. a deliberately failing pair for resolution triage; a wide-volatility
GC mix). Nothing in the notebook can save/load a parameter state. Options
sketched, none ruled: preset buttons per exercise, query-param state, or a
downloadable settings file. Unblocked by: a ruling on mechanism.

## CLOSED 2026-08-17 — Exercise authoring smoke checks run; (b) failed and was fixed by substitution
(a) PASS: acetophenone/p-chlorophenol, Rs 0.65 at the Ex 3 preset.
(b) FAIL as authored: no Decane/2-Octanone crossing on SPB-50 in range;
replaced with Tridecane/2-Octanone on Wax (~102 degC). Numbers in
decisions 2026-08-17. Spawns the follow-up below. Original entry follows:

## (historical) OPEN — Exercise authoring smoke checks (2026-08-17)
Before the exercises ship to students: (a) confirm a default-mix compound
pair lands Rs < 1.5 somewhere reachable for the triage exercise; (b)
confirm the Decane / 2-Octanone ln k intersection on SPB-50 falls inside
the 40-250 degC oven range. Authoring work on the exercise document, not
code. Unblocked by: an hour with the running notebook.

## CLOSED 2026-08-17 — Exercise document revised (v2, against v0.23.0)
Delivered as drylab_pogil_exercises_v2.md (outside the repo, like v1).
All planned amendments landed: co-elution pair substituted
(Tridecane/2-Octanone on Wax, ~102 degC), preset keys and shipped UI
names (Golay tab, Sweep data CSV, Peak results CSV, Rs/alpha columns)
baked into every setup line, alpha-moves-with-%B stated in the Ex 3 key,
and measured instructor-key values with operating points throughout
(triage levers; 30/70 %B general-elution numbers; verified polarity-trio
orders on both phases; h-minimum at ~1.6 mL/min with the honest caveat
that the default flow is near-optimal at 3 um, so the classic
run-above-optimum answer needs the temperature or particle-size variant).
Original entry follows:

## (historical) OPEN — Exercise document revision against v0.23.0 (2026-08-17)
drylab_pogil_exercises.md (delivered outside the repo) still names the
failed SPB-50 co-elution pair and predates the Golay tab, the exports,
the Rs/alpha columns and the presets. Needs: pair substitution
(Tridecane/2-Octanone on Wax, ~102 degC), control names updated to the
shipped UI, preset keys (?hplc=ex3 etc.) baked into each exercise's
setup line, and the alpha-moves-with-%B note added to the Ex 3 key.
Unblocked by: nothing — next deliverable-writing session.

## CLOSED 2026-08-18 — Band-shape exercise coverage shipped (v3: Ex 2A + Ex 7)
Closed by Brian's ruling; v3 adds Exercise 2A (mechanism builder) and
Exercise 7 (overload/asymmetry), coverage map updated (eddy diffusion and
peak asymmetry now Full). Instructor key v1 delivered alongside with
measured values for every exercise. Original entry follows:

## (historical) OPEN — Exercise coverage for the new Band-shape section (2026-08-17)
v0.24.0's Band-shape section changes the coverage map: eddy diffusion is
now explorable (Mechanisms tab) and overload tailing/fronting is
simulatable (Peak-shape tab) — neither appears in
drylab_pogil_exercises_v2.md, whose coverage map still lists eddy
diffusion as out of scope. A v3 revision (or an Ex 7) could add: a
one-mechanism-at-a-time van Deemter build matching Wenzel's Set #2
sequencing, and an overload exercise (predict tailing vs fronting from
isotherm curvature; watch t_max shift with load; distinguish overload
tailing from slow-site tau tailing). Unblocked by: a deliverable-writing
session; Brian's call on v3 vs Ex 7 addendum.


## OPEN — Remaining student worksheets (updated 2026-08-26)
Built: Ex 1 (Craig, incl. advanced A1-A3, PDF + docx), Ex 3 (triage).
Remaining: 2A, 2, 4, 5, 6, 7. Everything needed now lives in
classroom/ (masters, render pipelines, template rules, QA gates,
measured anchors — see classroom/README.md). Sub-decision for Brian:
Ex 5 (three presets) as one sheet or two. Do NOT link worksheets to
?tab= URLs (parked issue below); preset URLs are safe.
Unblocked by: Brian's GO (and the Ex 5 split call).

## OPEN — Publishing state (updated 2026-08-26)
Public repo is live at Brian's GitHub with HIS history (actions/uv fixes
committed there directly) — releases go by CONTENT SYNC (GITHUB_SETUP.md
§5), never by pushing a sandbox-built publish repo. Deployed version
lags: v0.24.6 publish zip delivered (tab revert) but push + the
three-click live test (land, move slider, switch tab + move control)
are pending. Historical entry follows:

## (historical) OPEN — Publishing state (updated 2026-08-20)
Publication repo built (drylab_publish_v0_24_1.zip; single-commit public
history, validation and internal files excluded). Brian's actions, per
GITHUB_SETUP.md in that repo: create the GitHub repo, push, set Pages
Source to GitHub Actions, verify the site loads (first load is slow —
Pyodide wheels). The instructor key and v3 exercises cite v0.24.1, so
this deploy should precede classroom use. First-run-on-GitHub of both
workflows is unverified. Unblocked by: Brian pushing.

## Standing nice-to-haves (unruled, carried)
CE plate-count column; GC temperature sweep; particle_size/length in
HPLC SWEEPABLE_INPUTS. None block classroom use; listed 2026-08-17.


## OPEN — ?tab= deep link PARKED after two failed attempts (2026-08-26)
Brian reported tab-bounce on the live site under BOTH implementations:
v0.24.4 (explicit value= on mo.ui.tabs — diagnosed: re-asserted on every
layout-cell rerun) and v0.24.5 (controlled mo.state + on_change — the
diagnosed-correct pattern, verified for mo.state semantics locally, STILL
bounced in the deployed WASM app; root cause unknown — hypotheses: the
WASM/run-mode round-trip recreates the element before on_change lands, or
state writes from on_change don't propagate the same way under Pyodide,
or a marimo-version behaviour difference between the sandbox's 0.24.0 and
the runner-installed release). v0.24.6 REVERTS to the element-managed
construction (byte-identical tabs block to v0.24.3, confirmed against
git); ?tab= is ignored (falls through harmlessly), ?hplc=/?gc= presets
unaffected (construction-default seeding never had this problem).
Unblocked by: browser-side debugging on the live deployment (marimo
version pin + console inspection), or an upstream marimo issue/answer on
controlled tabs under html-wasm run mode. Do NOT reintroduce value= on
the top tabs without a live-site click test in the same session.

## RESOLVED in v0.24.7 — van Deemter builder axis composition
Opened and closed same session (2026-08-27). The builder's fixed linear
0.02-1.0 cm/s axis put the default optimum at 4.4% of the plot width with
the y-axis stretched by the C limb. Resolved: "Log velocity axis"
checkbox, default on, positivity-guarded (decisions.md 2026-08-27).

## RESOLVED in v0.24.7 — Peak shape readout printed "nan" at k = 0
Apparent plates N_app = mu^2/sigma^2 is undefined for an unretained
analyte (sigma = 0); the readout leaked a float nan exactly where the
revised Ex 2A invites students to explore the k -> 0 divergence. Now
prints "n/a (sigma = 0, unretained)".

## OPEN — HPLC and CE sections have no equations block
Craig, GC, and (as of v0.24.7) both Band shape tabs carry "The equations"
accordions; HPLC and CE do not. Same house pattern applies when taken up
(statics-only content rule, decisions.md 2026-08-27).

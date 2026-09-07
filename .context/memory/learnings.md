# learnings

## 2026-08-03 — Reference has stale-coefficient bug on solvent change [MEASUREMENT]
Mechanism: the JS `Simulator` constructs its `Compound` objects once, with
the *initial* solvent's km/kb/sm/sb; later assignment to `secondarySolvent`
triggers `update()` but never re-resolves those coefficients, so retention
math silently uses the old solvent's compound table. General rule: when a
selection input indexes a lookup table, changing the selection must re-run
the lookup — audit every "resolve once in constructor" against every input
that can change the key. (Worked around in `dump_golden.js` by rebuilding
coefficients; the Python port resolves compounds inside `compute()` every
call, so it is structurally immune.)

## 2026-08-03 — Same-formula double math cross-language agrees to ~5e-16 [MEASUREMENT]
Mechanism: JS and CPython both use IEEE-754 doubles and the same libm-class
functions; a faithful port disagrees only at accumulated-ulp level. General
rule: for a line-for-line port, set golden tolerance ~1e-12 — anything looser
hides transcription errors (a wrong constant passes at 1e-3), anything at
exact-equality fails on benign exp/pow ulps.

## 2026-08-03 — Container shell is not bash; brace expansion silently degrades [MEASUREMENT]
Mechanism: `mkdir -p root/{a,b/c}` created a literal `{a` directory — the
command string runs under a shell without brace expansion, and mkdir -p
happily creates the brace-literal path, so the failure surfaces later as
"No such file or directory" on the *intended* path. General rule: in this
environment use explicit loops or repeated paths, never brace expansion; and
after any mkdir/cp scaffold step, `ls` the result before building on it.

## 2026-08-03 — `marimo export html` is a headless full-notebook test [MEASUREMENT]
Mechanism: the export executes every cell server-side; a cell exception
lands in the HTML. General rule: after any notebook change, run the export
and grep the output for error markers (mind false positives: marimo embeds a
`show_tracebacks` config key, so match on traceback *content*, not the bare
word). Same trick verifies the generated WASM notebook from an isolated
directory, which proves the embedded package actually loads.

## 2026-08-03 — Inline by importlib registration, not text splicing [ASSISTANT RECOMMENDATION, adopted]
Mechanism: concatenating module sources breaks on intra-package imports
(`from . import formulae as f` needs a real module object), and regex import
stripping is brittle. Registering embedded sources via
`importlib.util.spec_from_loader` + `exec` into module dicts, parents first
with `is_package=True`, makes relative imports work verbatim — the embedded
code is byte-identical to the package. General rule: when code must be
self-contained, embed and register modules; never rewrite their imports.

## 2026-08-04 — Plotly update_yaxes without a selector patches every y-axis [MEASUREMENT]
Mechanism: `fig.update_yaxes(title_text=...)` applies to yaxis, yaxis2, ...;
a base class calling it after a subclass labels a secondary axis silently
clobbers that label (user-visible as "Signal (umol/L)" on the viscosity
axis). General rule: shared layout code must target axes explicitly
(`update_layout(yaxis=dict(...))` or a selector); verified by mutation —
re-introducing the unselected call reproduces the clobber on the executed
figure. Corollary: layered figure builders should be checked with a
secondary-axis case, not only the single-axis happy path.

## 2026-08-04 — Unit forensics via conversion constants [MEASUREMENT]
Mechanism: an undocumented input unit can be recovered from the conversion
factor applied to it — the Java tubing code multiplies diameter by 2.54e-5
to reach meters, uniquely identifying mils (0.001 inch). General rule: when
a legacy input's unit is unknown, solve the conversion constant for the
unit instead of guessing from variable names or comments.

## 2026-08-04 — Bulk regex over a table silently drops rows; parse per labeled row [MEASUREMENT]
Mechanism: one findall over a 22-row block matched 21 rows (a formatting
variation defeated the row pattern) and only a count assertion caught it.
General rule: extract tabular source data line-by-line with an anchored
pattern per row, assert per-line match AND total count AND label/order
agreement against an independent list; never trust a single bulk regex.

## 2026-08-04 — A port's commented-out code is a divergence marker [MEASUREMENT]
Mechanism: the JS carried the Java tubing-broadening formula only as a
comment; the ancestor has it live — the port silently changed physics.
General rule: when auditing a port, treat every commented-out block as a
question ("is this active in the ancestor?") and check the ancestor before
classifying behavior as intended.

## 2026-08-04 — An unbounded loop's real failure mode may be absurd output, not a hang [MEASUREMENT]
Mechanism: the Java gradient march is `while (!eluted)` with no bound, so a
guard against infinite looping seemed sufficient. Measurement showed the
pathological case (0% B, n-butylbenzene) does terminate — after ~855k steps
and 1.2 s — returning tR = 76.8 h for a 5-minute run. An iteration cap would
never have fired; the user would have seen an empty chromatogram with no
explanation. General rule: when guarding a convergence loop, ask what the
loop *returns* in the bad case, not only whether it ends. Guard the physics
(is this answer within the requested window?) as well as the iteration count,
and report the finite-but-meaningless result as loudly as the divergent one.

## 2026-08-04 — Validate the oracle before trusting the oracle [MEASUREMENT]
Mechanism: the Java harness was hand-lifted out of a Swing applet; a
transcription slip would have silently produced wrong gradient "ground
truth" with nothing to catch it (the JS reference returns NaN there). Gating
the harness on reproducing the already-JS-validated ISOCRATIC goldens
(2304 values, worst 4.4e-16) proves the extraction before its unvalidatable
outputs are used. General rule: a new oracle must first reproduce a result
you already trust, on a path that exercises the same extracted code, before
its novel outputs count as ground truth.

## 2026-08-04 — Sequential recursions resist vectorization; measure before reaching for numba [MEASUREMENT]
Mechanism: both the stirred-tank mixer (1000 steps) and the band march are
inherently sequential — each step depends on the previous — so numpy cannot
help. Measured cost: 5.7 ms for 5 compounds, 31 ms for all 22 — well inside
interactive latency, so numba stays unused. General rule: a loop being
non-vectorizable is not by itself a reason to compile it; measure against
the latency budget first, since the dependency that blocks vectorization
often also caps the iteration count.

## 2026-08-04 — An optimistic estimator may refuse but must never certify [MEASUREMENT]
Mechanism: estimating march steps from k' at the program's strongest solvent
under-predicts benign methods by 40-80x (the band spends its early life in
weak solvent) but tracks pathological ones within 0.24-1.0x. So the estimate
is sound as a REFUSAL trigger at a large threshold and unsound as an
acceptance test. General rule: when a cheap proxy bounds a cost in only one
direction, wire it only to the decision that direction supports, and say so
where it is defined -- otherwise a later caller will use it for the
unsupported half.

## 2026-08-04 — Separate interactive policy from reference fidelity with a named switch [ASSISTANT]
Mechanism: a step budget that protects the UI would, if unconditional, make
the port disagree with the oracle on exactly the pathological cases the
oracle was built to pin down. Exposing it as march_step_budget (None =
disabled) let the app be safe while validation stays exact. General rule:
when a safeguard changes what the system returns, make it a named parameter
with an explicit off switch and have validation run with it off; a
safeguard baked into the computation silently redefines ground truth.

## 2026-08-04 — marimo export HTML does not contain cell errors; trust the command output [MEASUREMENT]
Mechanism: marimo ships `show_tracebacks: false`, so a failing cell renders
as an empty output and the exported HTML contains NO error text. Grepping
the HTML for "MarimoExceptionRaisedError" therefore returned 0 for a build
that had in fact failed with a NameError -- the failure was visible only in
the export command's own stdout ("some cells failed to execute"). General
rule: verify against the tool's own report, not an artifact it produced;
when a check can only ever return "clean", it is not a check. Corollary
already bitten twice here: the earlier grep-for-traceback approach was
matching a config key, and now missed a real error -- both times because
the artifact was the wrong place to look.

## 2026-08-04 — Duplicated import lists drift; the generator must be updated with the source [MEASUREMENT]
Mechanism: the WASM builder re-declares the notebook's `from hplc_sim...`
import list as literal strings, so every new export (COMPOUNDS, then
ElutionMode/GradientProgram, then THEMES) silently broke the generated
notebook until the builder was edited too. Third occurrence of the same
defect. General rule: when a generator restates a list that also lives in
the source, it is duplicated authority -- either derive it from the source
or add a check that the generated artifact imports what the original does.
Standing follow-up recorded in issues.md.

## 2026-08-04 — "The units look wrong" may be a labelling defect, not a maths defect [MEASUREMENT]
Mechanism: a suspicious y-axis (umol/L) turned out to be dimensionally
correct once the input convention was traced -- concentrations are
micromolar (only discoverable from a Swing JLabel reading "\u03BCM"), and
umol / (s * L/s) = umol/L. The real fault was that nothing in the UI or the
docstrings stated the convention. General rule: when a unit looks wrong,
derive it from the inputs before changing any arithmetic; if the derivation
holds, the bug is in what the interface tells the user, and the fix is
labels and documentation -- changing the maths would have introduced a real
error while "fixing" a cosmetic one.

## 2026-08-04 — Test a reporting feature by causing the failure it reports [MEASUREMENT]
Mechanism: a Diagnostics panel that renders "no errors" proves nothing --
it looks identical whether the capture works or is never invoked. Injecting
a real fault (a duplicate-time gradient program) confirmed all three legs at
once: the message reached stderr, the panel listed it, and the traceback was
retained. Also exposed a bad check of my own: greping the export for "No
errors recorded" always matches, because marimo embeds the notebook SOURCE
in the HTML. General rule: verify observability features with an induced
fault, and prefer asserting on strings that can only exist at runtime.

## 2026-08-04 — Editable tables emit NaN mid-edit; treat as unfinished input, not error [MEASUREMENT]
Mechanism: mo.ui.data_editor creates new rows with NaN cells, so a validator
that only checks ranges reports "%B must be within 0-100, got nan" and the
whole view dies while the student is still typing. General rule: any widget
the user builds up incrementally will emit partial state on the way to valid
state; validate for *completeness* first and treat incomplete input as a
prompt ("finish this row"), reserving errors for input that is complete and
wrong.

## 2026-08-04 — Fixed-width widgets overflow narrow layout columns [MEASUREMENT]
Mechanism: marimo sliders/dropdowns default to an intrinsic width, so a
3:8-style hstack column narrower than that width lets controls spill over
the neighbouring panel -- the visible symptom was sliders drawn on top of
the chromatogram in every tab. Fix is full_width=True on each control so it
sizes to its container. General rule: in any two-column layout, make the
controls fluid rather than trusting the column ratio to contain them.

## 2026-08-05 — Don't restyle a host you don't control; set only what it documents [MEASUREMENT]
Mechanism: a dark theme that set background/text colours on generic
containers looked broken because marimo styles its own widgets from its own
theme setting -- the two layers disagreed per-element (dark page, light
tab bar, unreadable headings). Removing all colour overrides and setting
only the three documented font variables removed the clash entirely.
General rule: when theming inside a host application, restrict yourself to
its published extension points and let it own everything else; partial
overrides of an unowned design system produce a worse result than no
override at all.

## 2026-08-05 — Interactive editors need order-independent validation [MEASUREMENT]
Mechanism: users append rows to a table in whatever order they think of
them, so a validator demanding monotonic times crashed on a 7 min row typed
after a 10 min row -- and the error was unrecoverable from inside the UI,
because the only way out was an edit the crashed cell no longer allowed.
General rule: for any collection whose semantics imply an order, normalise
(sort) at the boundary and report the normalisation; reserve errors for
conditions normalisation cannot resolve, such as duplicate keys. A
validation error the user cannot act on from where they are is a design
defect, not a safety feature.

## 2026-08-05 — Two failed layouts, one root cause: unverifiable containment [MEASUREMENT]
Mechanism: attempt 1 put controls in a flex column with full_width=True --
the widgets sized to the NOTEBOOK width, not the column, and overlapped the
plots. Attempt 2 used mo.sidebar, which rendered as a collapsed/absent panel
in app view and hid the controls entirely. Both failures shared a cause: I
chose a container whose rendered behaviour I could not verify in this
environment. The fix that worked is the one with no container to get wrong --
a wrapping row of natural-width groups stacked vertically above the content.
General rule: when rendering cannot be observed, prefer layouts whose
correctness follows from structure (vertical stacking, content-sized
elements, wrap) over layouts that depend on a container honouring a width
contract.

## 2026-08-05 — Check a widget's DEFAULT state before using it to hold required UI [MEASUREMENT]
Mechanism: mo.accordion's signature is (items, multiple, lazy) -- there is no
open-by-default parameter, so it always starts collapsed. Wrapping the shared
controls in one would have re-created the exact "controls are gone" bug that
was being fixed. Caught by reading the signature before shipping. General
rule: for any disclosure widget (accordion, tab, popover, sidebar), confirm
its initial state before putting required controls inside it; "the user can
open it" is not the same as "the user can find it".

## 2026-08-05 — Presence of a label in exported HTML does not prove it rendered [MEASUREMENT]
Mechanism: marimo embeds the notebook SOURCE in the export, so grepping for a
control's label matches the source line even when the widget never rendered.
Counting rendered custom elements (marimo-slider, marimo-dropdown, ...)
distinguishes the two. General rule: assert on artefacts only the renderer
can produce, not on strings that also exist in the input.

## 2026-08-05 — Flex children default to min-width:auto and will not shrink [MEASUREMENT]
Mechanism: three successive two-column layouts overflowed or hid content. The
cause was never the width ratio: a CSS flex item's default min-width:auto
prevents it shrinking below its content's intrinsic size, so whichever column
had wide content pushed into its neighbour regardless of the declared
proportions. Pinning one column (flex: 0 0 <w>) and setting min-width: 0 on
the other fixed it immediately. General rule: in any flex layout where a
child can contain wide content (plots, tables, long labels), set min-width: 0
on the flexible child; treat "adjust the ratio" as a symptom-level fix.

## 2026-08-05 — A textbook appendix can be a complete validation oracle [MEASUREMENT]
Mechanism: the supplied Craig source carried a symbolic table (A16.1, first
four steps), three fully worked numeric examples, and closed-form moments --
enough to check 108 values without any external reference implementation, and
enough to expose a typo in the source itself (q_B printed as 0.200 where its
own p_B implies 0.667). General rule: when a specification includes worked
examples, encode all of them as tests before writing the feature; they
validate the implementation AND cross-check the specification's internal
consistency, which is how source errata get caught rather than propagated.

## 2026-08-05 — An "unreachable" reference may be reachable by another route [MEASUREMENT]
Mechanism: the Craig applet page could not be fetched (dead-Java notice only),
so its algorithm looked unavailable and the work proceeded from a textbook
alone. The user then pasted the page's embedded script from browser dev
tools, which contained the full algorithm. General rule: when a web fetch
returns a stub, the artefact may still exist client-side; ask for the page
source (or a screenshot of the relevant panel) before concluding a reference
is unavailable. Obfuscated JS is still readable -- a string table plus
index-substitution recovers the logic in minutes.

## 2026-08-05 — Two sources agreeing is worth more than either alone [MEASUREMENT]
Mechanism: the applet's C(n,i)*D^i/(D+1)^n and the textbook's C(n,r)p^r q^(n-r)
look different but are algebraically identical; checking them against each
other (1.2e-14 over 4 D values, n<=60) confirmed both my reading of the
textbook AND the implementation, and additionally supplied behaviour the
textbook omits (elution past the last tube). General rule: when a second
independent statement of the same model appears, encode it as a separate
oracle rather than picking one -- disagreement localises a misreading, and
agreement across different algebraic forms is strong evidence of correctness.

## 2026-08-05 — Control placement should follow the model boundary [ASSISTANT]
Mechanism: the Craig tab was added under the existing mode tabs, so it
inherited a sidebar full of HPLC settings (column, solvent, injection) that
its model does not use, while its own controls sat alongside them applying to
nothing else. The code boundary was already correct -- hplc_sim.craig shares
no state with hplc_sim.model -- but the UI did not mirror it. General rule:
when a feature is deliberately independent at the model level, give it its
own control region at the UI level; a shared panel silently asserts a
relationship the code denies.

## 2026-08-05 — Refactoring layout leaves double-applied styles behind [MEASUREMENT]
Mechanism: when the two-column layout was factored into a _with_sidebar
helper, the old .style() on the controls column was not removed, so the
column was styled twice and the inner overflow-x:hidden clipped a dropdown.
The outer rule looked correct in isolation; only grepping for every
overflow/max-height rule in the file found the stale one. General rule: after
extracting layout into a helper, search the whole file for the properties the
helper now owns and delete every other occurrence -- two styles on one
element is duplicated authority and the loser is invisible until it clips
something.

## 2026-08-05 — Julia toolchain works in-sandbox via S3 tarball + GitHub-only Pkg [MEASUREMENT]
Mechanism: the domain allowlist is fixed when a sandbox starts, so an
allowlist edit is invisible until the next session. With
julialang-s3.julialang.org allowed: binary tarball installs (1.12.6), and
with JULIA_PKG_SERVER="" the General registry clones from
github.com/JuliaRegistries/General and JLL binary artifacts download from
GitHub releases (verified with Zlib_jll) — pkg.julialang.org is not needed.
General rule: for Julia in a domain-restricted sandbox, disable the Pkg
server and let everything resolve through GitHub; verify with a tiny JLL
before committing to a large dependency tree.

## 2026-08-05 — A session's assessment that is not written to memory does not exist [MEASUREMENT]
Mechanism: the handoff prompt referenced a "GC simulator port" entry in
issues.md (scope, physics, ODE assessment) that is absent from the v0.9.1
zip — the previous session's assessment was never banked, so it was redone
from the upstream source. The directive already states the rule ("memory
written later is memory lost to a reset"); this is the concrete instance.
General rule: treat handoff-prompt claims about memory contents as claims to
verify, and when memory and prompt disagree, say so before working.

## 2026-08-05 — Background processes do not survive across tool calls; and a poll can match itself [MEASUREMENT]
Mechanism: a nohup'd Julia install died as soon as its tool call returned
(log 0 bytes), while the liveness check `ps aux | grep -c "[j]ulia"` kept
returning 1 — it was matching the literal `[j]ulia` inside its own /bin/sh
wrapper's command line, so the death was invisible for ~18 min. General
rules: (1) in this sandbox, run long jobs in the FOREGROUND with a timeout
and resume across calls from on-disk progress — backgrounding is a silent
kill; (2) a liveness probe must be validated against the dead state once
(kill the target, confirm the probe reads 0) before trusting it — the
bracket trick fails when the pattern itself rides inside a wrapper's argv.

## 2026-08-05 — Isothermal ng=true GC has exact closed forms; the ODE is only needed for programs [MEASUREMENT]
Mechanism: with T constant in time and space, rM = A·p(z) and DM = B/p(z),
so every Golay term's p-dependence cancels and plate height H is constant
along the column; dt/dz = A(1+k)p(z) and dτ²/dz = H·A²(1+k)²·p²(z)
integrate analytically (p² linear in z). tR = A(1+k)(2L/3)(pin³−pout³)/Δp²,
τ² = H·A²(1+k)²·L(pin²+pout²)/2; the k=0 limit reproduces the package's
holdup_time formula exactly. The vacuum-outlet endpoint singularity (p→0)
that kills a naive ODE march cancels in these forms. Measured vs the Julia
oracle (162 cases, Vern9 1e-10/1e-8): tM bit-identical, τR ≤ 1.0e-15,
tR ≤ 6.7e-9 (median 1e-10) — and the pattern proves the residual is the
ORACLE's solver error: dτ²/dz is polynomial in z (any RK exact → 1e-15)
while dt/dz is a square root (→ oracle's ~1e-9 at reltol 1e-8).
General rule: before porting an ODE system, check whether the shipped
regime degenerates to quadrature — the singular/stiff machinery may belong
to the unshipped extension, not v1.

## 2026-08-05 — Measurements.jl propagation quantified; parameter uncertainty >> port disagreement [MEASUREMENT]
Reference case (Octane, SLB5ms, He, 120 °C, 250/101.3 kPa,
30 m × 0.25 mm × 0.25 µm), inputs Tchar ± 0.5 K, θchar ± 0.3,
ΔCp ± 5 J/mol/K: tR = 94.25 ± 0.36 s (±0.38 %), τR = 0.2003 ± 0.0010 s;
θchar dominates (±0.30 s), then Tchar (±0.19), ΔCp (±0.09). Requires
promoting the ODE initial state to Measurement (t₀ = 0.0 ± 0.0), else
Float64 conversion errors. Seven orders of magnitude above the port's
numerical disagreement — the ruling to not port propagation costs little,
and the number is measured, not assumed.

## 2026-08-05 — A verification probe can rot with the host version; re-validate the probe, not just the artifact [MEASUREMENT]
Mechanism: the standing check "count rendered custom elements
(marimo-slider, marimo-dropdown) in the export" returned ZERO on marimo
0.23.16 for a build that was fully working — the widgets are present (14
marimo-switch, 44 marimo-slider, 24 marimo-dropdown occurrences) but no
longer emitted as literal `<marimo-slider` opening tags. Trusting the probe
alone would have read a good build as broken, the exact mirror of the 2026-
08-04 failure where a probe read a broken build as good. General rule: a
probe that asserts on a HOST's output format is only valid for the host
version it was written against; when a probe returns an extreme result
(zero, or everything), suspect the probe before the artifact, and confirm
it can still produce a positive on a known-good case. Durable replacement
here: assert on COMPUTED values whose digits cannot come from the source
(rendered "hold-up 78.7 s", "tM 78.73 s"), which is format-independent.

## 2026-08-05 — Only the selected branch of a reactive lookup renders; use that as the probe [MEASUREMENT]
Mechanism: probing the export for the Wax phase description returned False
and looked like a failure, but only the SELECTED phase's caption is ever
rendered — its absence is correct behaviour, and the SLB5ms description
being present (a string that exists only in hplc_sim/gc.py, never in the
notebook source) proved the caption is a live runtime lookup rather than
static text. General rule: in a reactive UI, a per-selection artefact is a
sharper correctness probe than a whole-table one — presence of the selected
value plus absence of the unselected values distinguishes "computed from
state" from "dumped verbatim", which no single-string grep can do.

## 2026-08-05 — Derive one config per section rather than threading a flag through every call site [ASSISTANT]
Mechanism: adding a legend switch meant touching seven `replace(plot_config,
...)` sites spread over six cells; each is an independent chance to miss one,
and a missed site fails silently (that figure just keeps its legend). Deriving
hplc/craig/gc_plot_config once and having each section's cells consume its own
made the switch's authority single per section, and a missed site is then a
NameError, not a silent divergence. General rule: when a new option must reach
N existing call sites, insert one derived object upstream instead of editing N
sites — it converts a silent-omission failure mode into a loud one. Same
defect family as the WASM builder's restated import list.

## 2026-08-05 — str.replace on a missing anchor is a silent no-op; guard every anchored rewrite [MEASUREMENT]
Mechanism: the WASM builder stamped the version into the artifact by
`out_src.replace('"""HPLC Simulator (marimo)', ...)`. The v0.9.1 rename to
"Chromatography Simulator" invalidated that anchor, and because replace()
returns the string unchanged rather than raising, THREE artifacts (v0.9.1,
v0.10.0, v0.10.1) shipped with no internal version stamp and no signal of
any kind. Found only by grepping the artifact for its own version after a
build that reported success. General rule: every anchored rewrite
(replace, regex sub, splice) must assert the anchor was found and raise
naming it when not — an edit that "succeeds" without matching is the
quietest failure a generator can have. Corollary: anchor on STRUCTURE
(a docstring opening at column 0) rather than on PROSE (a title), because
prose is renamed by people who have no reason to know a build depends on
it. Fix mutation-verified: removing the docstring makes the builder exit 1
with the diagnostic; restoring it produces the stamp.

## 2026-08-05 — A style constant shared by two models needs a per-model name once one model's density changes [ASSISTANT]
Mechanism: the sum-trace width was one shared PlotConfig value because both
chromatograms looked alike. Once the GC figure gained 17 filled component
traces, the same 2.0 line read as heavy there and correct in HPLC — the
value had quietly become two different requirements wearing one name.
Thinning the shared field would have changed HPLC figures nobody complained
about. General rule: when a shared style value starts needing different
answers per consumer, split it into named per-consumer fields rather than
retuning the shared one or overriding at the call site; the call-site
override hides the divergence where no one will find it, and retuning
changes consumers that never asked.

## 2026-08-05 — Judge a colour at its RENDERED alpha, not at its hex [MEASUREMENT]
Mechanism: the palette's pale yellow looked merely light by its hex value
(contrast 1.05 on white) but traces are drawn at compound_fill_opacity
0.25, and composited over the canvas it lands at 1.015 — the line and its
fill are effectively the background. Computing contrast from the raw hex
would have understated the problem and, worse, would have "cleared" three
other pale members that composite to 1.108-1.190 and are genuinely
readable. General rule: evaluate any visual property in the state the user
actually sees it — after opacity, blending and scaling — because a style
value and its rendered result are different quantities, and a threshold
set on the wrong one both misses real faults and manufactures false ones.

## 2026-08-05 — A UI complaint about one view is usually a defect in the shared layer [MEASUREMENT]
Mechanism: the human reported the box-select drag mode on the GC plot.
Checking the other figures showed all eight mo.ui.plotly instances have
it, and grepping for consumers showed NO cell reads any figure's .value —
so the gesture was inert project-wide, and GC was simply where it got
noticed. Fixing only GC would have satisfied the report while leaving
seven identical dead controls. General rule: before scoping a UI fix to
the view it was reported against, check whether the surrounding views
share the mechanism; the report locates a symptom, and the shared layer is
usually where the defect lives (charter section 5).

## 2026-08-05 — The Julia cost is the DEPENDENCY CLOSURE, not Julia; the "~25 min" note was wrong [MEASUREMENT]
Measured breakdown on a cold sandbox: Julia 1.12.6 binary tarball download
9 s, unpack 16 s, upstream git clone 21 s — Julia itself is a MINUTE. The
cost is precompiling GasChromatographySimulator's tree: cache count went
173 -> 436 packages, with NonlinearSolve alone 216 s, CSV 63 s,
QuasiMonteCarlo 37 s, OrdinaryDiffEq's own group 214 s. Total well over an
hour of wall time, spread across many tool calls. General rule: when
estimating a toolchain setup, time the DEPENDENCY GRAPH, not the runtime
being installed; and record the breakdown, because a single aggregate
figure that is 3x low will read as a hang to the next session and provoke
a restart that throws away on-disk progress.
Operational notes that made it survivable: the tool-call ceiling sits
between 161 s and 560 s, so 200-240 s internal timeouts are the workable
chunk size; every chunk persists its cache, so repeated identical
`using X` calls RESUME rather than restart. A SIGTERM into a precompile
worker prints a pthread_cond_wait/ijl_task_get_next stack trace — that is
the timeout landing, NOT a package crash; judge progress by the cache
count, not by the trace.

## 2026-08-05 — Regenerating an EXISTING golden is a free environment-integrity test; take it [MEASUREMENT]
Mechanism: before adding programmed cases, the harness was run whole, so it
rewrote the 162 isothermal cases as well. Those came back BYTE-IDENTICAL to
the shipped file (same md5, 2,754 values at 0.000e+00 relative difference),
and the Measurements case reproduced tR = 94.25 +/- 0.36 exactly. That
turns "I installed a toolchain and got some new numbers" into "this
toolchain provably reproduces the reference this project already trusts",
so the NEW numbers inherit that standing. General rule: when an oracle
environment is rebuilt, regenerate something already validated first and
diff it; if it does not reproduce, every new number from that environment
is suspect and you have learned so before depending on it. Corollary used
here: after editing the harness (adding `local` to silence scope
warnings), re-running and confirming both files were bit-identical proved
the edit inert — a code change to a validated oracle must be shown to
change nothing.

## 2026-08-05 — When both sides of a validation are numerical, measure the reference against ITSELF first [MEASUREMENT]
Mechanism: the isothermal suite compares a Python CLOSED FORM against a
Julia ODE solve, so ~1e-9 agreement is an absolute statement about the
port. Under a temperature program both sides integrate, and the achievable
agreement is floored by the oracle's own discretisation error — which
nobody had measured. Re-dumping the same 64 cases at three tolerances and
comparing successive refinements put a number on it: the loose dump
(1e-10/1e-8) carries 7.8e-08, the tight dump (1e-14/1e-12) carries
8.0e-10. General rule: before setting a tolerance against a NUMERICAL
reference, refine the reference and difference it with itself; a tolerance
asserted tighter than that floor is asserting agreement with the
reference's noise, and it will either fail mysteriously or pass for the
wrong reason. Corollary found here: doing this BEFORE writing the compare
script also revealed the wrong dump had been shipped, when the better one
cost 129 s.

## 2026-08-05 — A cheap-looking block can dominate a run through TYPE specialisation, not arithmetic [MEASUREMENT]
Mechanism: short 16-case convergence chunks appeared to hang, while timing
said all 512 solves should take ~143 s. The cause was an unrelated block
further up the harness that solves ONE case with Measurements.jl types:
that forces Julia to JIT-specialise the entire ODE solver stack for a
second element type, costing minutes on every invocation regardless of how
few cases the run asks for. Guarding it out under --prog-only made the
full dump run in 129 s. General rule: in a JIT/generic-dispatch language,
per-run cost scales with the number of distinct TYPE combinations
compiled, not just the amount of work requested; when a small job takes as
long as a big one, look for a block that instantiates a new element type
rather than for a slow loop.

## 2026-08-05 — A validation tolerance is only defensible over the grid it was set on [MEASUREMENT]
Mechanism: compare_gc.py's 1e-8 held for 162 comfortable cases. Extending
the grid to 810 reached 0.53 mm bore with vacuum outlet, where the ORACLE's
own solve at abstol 1e-10 was off by 1.12e-08 — and the failure looked like
a port bug. The distinguishing probe: refine the reference and see which
value it moves toward. It converged onto the Python closed form
(1.12e-08 -> 3.38e-11 -> 2.89e-13), so the port was exact and the reference
was under-resolved. General rule: when a comparison fails marginally,
establish WHICH side is wrong by refining the reference before touching
either the code or the tolerance; and treat a tolerance as scoped to the
parameter range it was measured over, because widening coverage silently
invalidates it. Loosening the tolerance would have enshrined a known-wrong
reference.

## 2026-08-05 — Audit the UI's reachable parameter space against oracle coverage; the gap is invisible from either side alone [MEASUREMENT]
Mechanism: every suite passed while the Wax stationary phase — selectable
in the app, 17 solutes in the vendored table — had never appeared in a
single oracle case, and a continuous film-thickness slider was validated at
one point. Nothing in the code or the test output could reveal this; it
only appears when the CONTROLS are diffed against the GOLDENS. General
rule: periodically enumerate what the UI lets a user reach and intersect it
with what validation covers. Passing suites measure the cases you thought
to write, not the cases a user can produce, and the difference between
those two sets is where unvalidated behaviour hides.

## 2026-08-05 — A study pinned to a snapshot of a grid breaks when the grid grows; key it to the grid instead [MEASUREMENT]
Mechanism: oracle_convergence_gc.py compared three tolerance dumps by
requiring identical case-id sets. Extending the programmed grid 432 -> 720
left the coarse dumps on the old ids and the study died with "dumps cover
different case ids" — a passing suite turned into a broken one by a change
that had nothing to do with it. Fixed by intersecting on shared ids and
regenerating the coarse dumps over a RANGE of the current grid. Worth
noting the result: the floor came back at 7.9e-10 on a completely
different 64-case subset, versus 8.0e-10 before, which is itself evidence
the floor is a property of the SOLVER rather than of the cases sampled.
General rule: an auxiliary study that samples a subset should be keyed to
a reproducible slice of the live grid (a range), not to a frozen copy of
ids; otherwise every extension of the main artifact silently invalidates
it, and the failure appears far from its cause.

## 2026-08-05 — mo.stop halts every DESCENDANT, so in a single-layout notebook it blanks the whole app [MEASUREMENT]
Mechanism: the gradient cell used mo.stop to refuse duplicate row times. The
top-level layout cell consumes grad_results, gc_panel, craig_panel and the
rest, so it DESCENDS from every producer — and mo.stop in any one of them
removed the entire interface, sidebars included. The user could see the
error but not the editor that caused it, so the input was unfixable without
a reload. Six sites had this shape, including "deselect every analyte".
Replaced throughout by carrying an error value forward and rendering it in
the panel that owns it, with CONTROLS built outside the guard so they always
survive. General rule: in a reactive notebook with one root layout cell,
mo.stop is not local — its blast radius is the transitive closure of
consumers, which is usually everything. Use it only where the halted cell
has no descendants; otherwise carry the error. Corollary: the test for an
input-validation path is whether the CONTROL that produced the bad input is
still on screen afterwards.

## 2026-08-05 — A guard that indents an existing block can swallow code that must stay unconditional [ASSISTANT]
Mechanism: wrapping the Craig and GC panel bodies in "if error ... else"
by indenting the whole block also indented the CONTROLS construction, so on
the error path craig_controls/gc_controls would have been undefined —
converting a handled error into a NameError, and again removing the controls
the user needs. Caught by reading the indented result rather than trusting
the transformation. General rule: when introducing a conditional around
existing code, enumerate what the block DEFINES, not just what it renders;
anything downstream depends on unconditionally must be hoisted out first.

## 2026-08-05 — Mutation-test the AUTHORITY claim, not just the fix [MEASUREMENT]
Mechanism: to show that extracting the shared GC physics actually created
one authority, the test was to perturb the SINGLE plate_height by 1e-7 and
confirm BOTH the isothermal and programmed suites fail — they did. Running
the same perturbation against the PRE-refactor tree was the more valuable
half: it also failed both, revealing that the duplication had never been
silent, because the flat-program identity check already cross-checked the
pair. General rule: when justifying a structural refactor, mutate the
pre-change tree too. The claimed hazard is only real if the old code fails
to detect it; otherwise the benefit is different from the one you argued,
and the honest justification is narrower.

## 2026-08-05 — A near-zero denominator makes a relative-error probe lie; check the ABSOLUTE scale [MEASUREMENT]
Mechanism: three separate times this session a relative-difference probe
reported alarming numbers that meant nothing. Removing scipy from SPYCE
"changed" an array by 51x — computed on values of 1e-13 against a field
whose scale was 20.6, i.e. 6.9e-09 of full scale. The programmed-GC and CE
comparisons hit the same shape. General rule: before believing a relative
error, print the ABSOLUTE difference and the magnitude it is relative to.
A relative tolerance is only meaningful where the denominator is a real
signal; near zero it measures rounding. Practical form used here: report
max|a-b| / max|b| over the whole array (fraction of full scale) alongside
the pointwise relative figure, and compare the two.

## 2026-08-05 — When an exact power-of-ten discrepancy appears, suspect UNITS and settle it with independent physics [MEASUREMENT]
Mechanism: the first CE oracle run showed a pH gap of exactly 3.000 =
log10(1000). Rather than adjust either side, Henderson-Hasselbalch settled
which was wrong: 20 mM acetic acid neutralised by 12 mM Tris gives 4.756 +
log10(12/8) = 4.932, exactly what drylab returned. SPYCE's saved hydronium
array was already mol/L while drylab's carries mol/m^3, so the PROBE was
double-converting. General rule: a discrepancy that is exactly 10^n, or
exactly a factor of 2, pi, or 60, is almost never physics — it is a unit,
a convention, or an off-by-one. Resolve it with a closed-form check that
depends on neither implementation, because otherwise there is a 50% chance
of "fixing" the correct side.

## 2026-08-05 — Fixing one of two contributing mechanisms looks like failure; keep the fix and keep looking [MEASUREMENT]
Mechanism: the CE boundary blow-up needed BOTH Trefethen's endpoint
derivative formulae AND the Hou-Li spectral filter. Implementing the
endpoints alone left the failure bit-for-bit identical, which is a strong
temptation to revert a correct change as ineffective. The endpoint fix was
independently verifiable (analytic derivatives to 1e-12 at the
boundaries), which is what justified keeping it while hunting the second
cause. General rule: verify each candidate fix against its OWN criterion,
not against the symptom. A change that provably does what it claims stays
even if the bug survives, because compound bugs are common and reverting
half a fix guarantees the next attempt fails too. Corollary: a regression
test must exercise the SYMPTOM, since only that keeps both mechanisms.

## 2026-08-05 — A negative result is a deliverable; measure the signatures rather than shipping something plausible [MEASUREMENT]
Mechanism: ITP was expected to need the moving mesh. Testing it against
the three DEFINING signatures — common zone velocity, self-sharpening,
Kohlrausch plateau concentrations — showed it fails all three while
running stably and conserving mass to three decimals. So the moving mesh
is not the blocker, and the prior assumption recorded in issues.md was
wrong. Had "it runs and conserves mass" been the acceptance test, a
physically wrong ITP mode would have shipped and students would have
learned the wrong thing with no signal at all. General rule: for a
physical model, acceptance criteria must be the phenomenon's defining
behaviours, not numerical health. Numerical health is necessary and says
nothing about whether the right physics is present.

## 2026-08-05 — An assertion before write_text discards the WHOLE edit script, not just the failed edit [MEASUREMENT]
Mechanism: a five-edit patch script asserted on each anchor and wrote once
at the end. One anchor was slightly wrong (a line began "+ f\"" not "f\""),
so the assertion fired, nothing was written, and the four GOOD edits were
lost silently — but the console had already printed progress, so it looked
partially applied. Verifying afterwards showed zero of five present.
General rule: when a batch edit fails, re-check the whole batch rather
than only the reported anchor; and prefer asserting all anchors BEFORE
applying any, so the failure mode is obviously all-or-nothing.

## 2026-08-17 — "Built outside the guard" must be structural, not asserted [MEASUREMENT]
Mechanism: a comment claimed controls were guard-independent, but one
control (_phase_caption) was defined inside the success branch and read
after it — a NameError lying dormant because default inputs never failed.
General rule: a claim that code runs regardless of a guard is only true of
code POSITIONED before the guard; verify by forcing the failure branch
(here, an empty solute selection) rather than trusting placement comments.
Corollary: adding a new way to fail (the picker) is exactly when such
latent branches surface — walk every consumer of the failure path when one
is added.

## 2026-08-17 — Exports must read the figure's own data, or they will drift [ASSISTANT RECOMMENDATION, adopted]
Mechanism: a CSV built by re-running the model alongside a plot duplicates
the sweep grid, the time axis and the operating point — three chances to
disagree with what was on screen. General rule: give the plot object a
public data accessor (data_columns / time_axis / operating_point) and
build every export from the SAME instance the figure came from; the file
then cannot contradict the figure by construction.

## 2026-08-17 — An assumed operating point is a fabricated one [ASSISTANT ERROR, banked]
Mechanism: a probe script labelled its baseline "250x4.6 mm, 5 um" from
the analyst's memory of the real Zorbax product, while the model's preset
is 100 mm / 3 um — so two "anomalies" (N x5 for L x2; particle override
no-op) were artifacts of a wrong assumed baseline, and the printed label
actively certified conditions that were not in force. General rule: every
probe must print the operating point FROM THE RESULT OBJECT
(results.operating_point()), never from a hand-typed label; the charter's
"a certified number carries its operating point" applies to throwaway
scripts exactly as much as to shipped exports, because throwaway numbers
are what decisions get made from.

## 2026-08-17 — marimo serialized signatures are cosmetic; dataflow comes from the body [MEASUREMENT]
Mechanism: a pre-existing cell consumes hplc_error without it appearing in
either the defining cell's return or the consumer's signature, yet the app
works — marimo derives the dependency graph by AST analysis of cell
bodies at load time; the def _(...) signatures and return tuples are
serialization artifacts regenerated by the editor. General rule: when
hand-editing a marimo file, keep signatures tidy for the human reader but
do not treat them as verification of wiring in either direction; the
executable truth is `marimo export html` (which runs the real graph), and
`python -c "import nb"` checks syntax only.

## 2026-08-17 — np.sign(0) is 0: never use it to pick a quadratic branch [MEASUREMENT]
Mechanism: the cancellation-stable quadratic form q = -(b + sign(b)*sqrt(D))/2
silently returns q = 0 when b = 0 under numpy's three-valued sign, and
b = 0 was a REACHABLE parameter combination (1 + k = chi*T), so the model
froze with zero mass transport — caught only because an invariant sweep
crossed the exact value. General rule: branch selection needs a two-valued
sign (where(b >= 0, 1, -1)); and parameter sweeps in validation should
include algebraically special points (term cancellations, discriminant
zeros), not just round numbers.

## 2026-08-17 — Verify embedded artifacts by executing the inline block, not importing the file [MEASUREMENT]
Mechanism: a marimo WASM artifact registers its embedded modules inside a
cell body, which `import artifact` never executes — so a probe that
imports the file and then imports drylab reports ModuleNotFoundError and
looks like a broken artifact when the artifact is fine. General rule: to
smoke-test an embedded-module artifact outside marimo, extract and exec
the [[INLINE]] block itself (or run `marimo export html` on the
artifact); a plain import proves only that the file parses.

## 2026-08-19 — PDF verification needs two layers: extraction for content, raster for layout [MEASUREMENT]
Mechanism: text extraction confirmed every content probe in a generated
PDF while two bullet lists had silently collapsed into run-on prose (a
missing blank line between a bold lead and a markdown list) — invisible
to extraction, obvious in a rasterized page. And the inverse failure:
a naive substring probe FALSE-NEGATIVED on a phrase that merely wrapped
across a line break. General rules: (1) verify generated PDFs by BOTH
extracting text (whitespace-normalized before any substring check) and
rasterizing at least one dense page for visual inspection; (2) in
markdown destined for rendering, a list must be preceded by a blank
line or it fuses into the paragraph above.

## 2026-08-19 — Writing the answer key IS the test [PROCESS]
Mechanism: producing the instructor key forced a measured walkthrough of
every exercise step, which caught three classroom-breaking defects the
exercise documents had shipped with across two revisions: a Craig pair
whose answer lay beyond the slider range (n~615 vs max 200), a CE task
that was impossible twice over (the target ion was BGE, not Sample; and
the plug position changed every threshold), and a systematic sim-vs-
arithmetic offset that would have read as student error. General rule:
for any student-facing task with a numeric answer, generating the key
from the model is not documentation AFTER authoring — it is the
acceptance test FOR authoring, and it belongs before delivery
(generalizes the 2026-08-16 "smoke-test classroom content" rule from
single scenarios to whole documents).

## 2026-08-19 — Deliverables outside the repo need an inventory inside it [PROCESS]
Mechanism: the classroom documents (exercises v1-v3, instructor key,
worksheets) live in chat outputs, not the repo, so nothing in git records
what exists, which version is current, or what supersedes what — memory
entries mention them but scattered across dockets. General rule: when a
project accumulates out-of-repo deliverables, the handoff must carry an
explicit inventory (name, version, status, supersedes) or the next
session cannot know what the user already holds.

## 2026-08-26 — Pin GitHub Actions majors by checking, not remembering; git ls-remote beats the rate-limited API [MEASUREMENT]
Mechanism: the deploy run warned that checkout@v4/setup-python@v5 target
deprecated Node 20 (forced onto Node 24 by the runners — a warning, not a
failure). Verifying current majors: api.github.com is rate-limited
unauthenticated from the sandbox, but `git ls-remote --tags
https://github.com/actions/<name>` is not, and yields every tag. As of
2026-08-26: checkout v7, setup-python v7, upload-pages-artifact v5,
deploy-pages v5. General rules: (1) action versions in shipped workflows
go stale between sessions — verify against the live repo at release
time; (2) the pins live in THREE places here (deploy.yml, validate.yml,
and the PUBLIC_VALIDATE_YML string inside build_publish_repo.py) — a
version bump must touch all three or the public repo regresses on the
next release build.

## 2026-08-26 — CI runners run tomorrow's tools; sandbox verification has a ceiling [MEASUREMENT]
Mechanism: the Pages deploy failed with "uv must be installed to resolve
local imports for html-wasm export" from a marimo release NEWER than the
sandbox's index offers (0.24.0 here exports the same artifact with no
uv), so the exact failure was not locally reproducible — the fix
(install uv alongside) was taken from the tool's own stated remedy and
verified only for non-regression on the newest locally installable
marimo. General rules: (1) any workflow step that pip-installs an
unpinned tool will eventually run a version the dev sandbox has never
seen — treat first-runner failures as environment drift before
suspecting the project; (2) when a failure cannot be reproduced, say so
in the commit and verify the two adjacent things that CAN be: the fix's
non-regression locally, and that the change matches the tool's own
error-message remedy verbatim.

## 2026-08-26 — Print-pipeline math: mathtext SVGs, and three markdown traps [MEASUREMENT]
Mechanism: "MathJax" in a weasyprint pipeline means server-side typesetting
(no JS engine); matplotlib mathtext -> vector SVG -> data-URI <img> gives
font-matched, fully offline display math. Traps hit, in order: (1)
mathtext dialect differs from LaTeX (\geq not \ge; no \xrightarrow — use
\overset; no \!) — pre-flight parse EVERY block with MathTextParser so all
failures surface at once; (2) a failed render leaves the PREVIOUS PDF on
disk, so post-checks must run only after a confirmed write or they
validate stale output; (3) python-markdown list mechanics around inserted
blocks: an equation at column 0 terminates the enclosing list (indent it
4 spaces into the item), and a "- " item directly after indented content
lazily continues the previous paragraph as literal text (blank line
required before it). Verify list integrity structurally: assert no
extracted text line starts with "- ". Renderer preserved as a reusable
script (render_key.py, chat-side) with these notes in its docstring.

## 2026-08-26 — Explicit value= on a rebuilt element is a re-assertion, not a default [MEASUREMENT, regression]
Mechanism: in marimo, a cell that composes every section's panel re-runs
on ANY control change; a UI element recreated in that cell keeps the
user's state only while its constructor stays agnostic about it — pass an
explicit value= and every rebuild re-selects it (the v0.24.4 tab-bounce).
General rules: (1) initial-from-URL + user-navigable selection is the
CONTROLLED pattern: mo.state seeded once from the param, on_change
writing back, value=get() — the state cell must not depend on the panels;
(2) headless `marimo export html` cannot exercise click interactions, so
any change to how a stateful element is constructed needs a
human-in-the-browser check before it ships — the export being clean is
exactly how this regression got through.

## 2026-08-26 — Two failed fixes = revert to known-good, and park the feature [PROCESS]
Mechanism: the tab deep link failed in deployment twice — once for a
diagnosed reason (explicit value= re-asserts on rerun) and once with the
pattern that SHOULD be correct (mo.state controlled selection), meaning
the remaining unknown lives somewhere the sandbox cannot observe (the
WASM run-mode client). General rules: (1) when the second, diagnosed-
correct fix also fails in the only environment that matters, stop
iterating blind — revert to the byte-identical known-good construction
(verify against git, not memory of it) and park the feature with the
hypotheses written down; (2) a feature whose failure mode is invisible to
every available test (headless export was clean for all three states:
working, broken, broken) must carry a live-environment test requirement
in its issue entry before any reattempt.

## 2026-08-26 — A verification that cannot fail the pipeline is not verification [MEASUREMENT]
Mechanism: the byte-identical-revert assertion FAILED, but the commit and
packaging ran anyway because the shell steps were chained with newlines,
not && — so a commit shipped claiming a verification that had not passed
(caught only by reading the tool output; the residue was a functionally
harmless trailing comma, but the process hole was not harmless). Second
instance same day: the preserved render_key.py had a SyntaxError from
birth (\x in a non-raw docstring) because the file was created but never
executed — creation was mistaken for verification. General rules: (1)
gate multi-step shell verification with && or set -e so a failed check
stops everything after it; (2) a script is verified when it has RUN from
where it will live, not when it has been written; (3) after any
assertion-carrying step, read its output before believing the steps that
followed it.

## 2026-08-26 — Out-of-repo deliverables, structural fix [PROCESS]
Mechanism: the 2026-08-19 learning (deliverables outside the repo need an
inventory inside it) is now solved structurally: classroom/ holds the
masters, pipelines, QA gates, design logic, measured anchors and work
docket in one place inside the dev tree, and the publication builder's
explicit-include list keeps it out of the public repo automatically.
General rule: when the same inventory keeps being reconstructed in
handoffs, move the artifacts themselves into the versioned tree and let
the handoff point at the folder.

## 2026-08-27 — Check exercise content against the course's source text, not just the app

The Ex 2A draft treated the flat eddy term as settled ("does your
expression contain u anywhere? No."). Wenzel's own text — the reading the
students do — writes h = A·v^(1/3) + B/u + Cs·v + Cm·v and calls the
question unresolved. A worksheet QA'd only against the simulator would
have contradicted the assigned reading. Lesson: the UI-reference gate
checks worksheet-vs-app; there is an equivalent worksheet-vs-source-text
check, and it caught a real conflict here. (Resolved by naming the
controversy in the panel and turning it into an inquiry question: a
v^(1/3) eddy term makes the optimum packing-dependent — dH/du gains a
positive term, shifting u_opt left.)

## 2026-08-27 — Headless notebook QA: `await app.embed()` executes every cell

`python -m py_compile` only proves syntax. Importing the notebook module
and running `asyncio.run(app.embed())` executes the full marimo cell
graph in-process (marimo 0.24 in this sandbox): missing cell parameters,
broken md strings, and bad wiring all surface. All five sections
constructed after the v0.24.7 edits. Cheap enough to be the standard
post-edit gate for drylab_nb.py.

# drylab exercises for the Wenzel Separation Science unit

**Revision 3 — written against drylab v0.24.1.** Adds Exercise 2A (van
Deemter mechanism builder) and Exercise 7 (column overload and peak
asymmetry) on the new Band shape section, and fixes a Craig
homework pair that revision 2's own instructor-key pass caught as
unreachable (D = 1.5/2.5 needs n ≈ 600 transfers; the slider stops at
200). A companion **instructor key** (drylab_instructor_key_v1.md)
carries measured expected values for every step of every exercise.

**Revision 2 note — Every scenario, retention
order, and number below was verified against the shipped model (2026-08-17);
instructor-note values carry the operating point they were measured at. The
first revision's Ex 5 co-elution pair (Decane/2-Octanone on SPB-50) failed
verification — those solutes never co-elute in the oven range — and has been
replaced with a measured pair.

**Basis:** drylab v0.23.0 (HPLC isocratic/gradient with sweeps, band tracks,
Rs/α results columns and CSV exports; Craig apparatus; GC
isothermal/programmed with solute picker, Compare and Golay tabs and CSV
exports; CZE) mapped against Wenzel's POGIL materials (Learning Objectives,
In-Class Problems, Out-of-Class Problems, Instructor's Manual, Text).

**Design philosophy.** Wenzel's problems are guided inquiry: students
confront a model, predict, then justify, in facilitated groups of 3–4.
drylab is the *model-generating instrument*: every exercise follows a
**Predict → Simulate → Reconcile → Extend** loop, where the prediction is
committed on paper *before* the slider moves. The simulator never replaces
the reasoning step — it adjudicates it.

**Classroom presets.** Each section's sidebar has a **Classroom preset**
dropdown that seeds the scenario's chemistry (analytes, phase, temperature,
%B, solvent B); instrument geometry and pneumatics stay at defaults, so a
preset states the problem, never the solution. Presets are also
URL-selectable, so each group can be handed a link:

| Exercise | Preset | URL parameter |
|---|---|---|
| Ex 3 — Resolution triage | HPLC: acetophenone + p-chlorophenol, 50 %B | `?hplc=ex3` |
| Ex 4 — General elution (LC) | HPLC: all 22 compounds, 30 %B | `?hplc=ex4` |
| Ex 4 — General elution (GC) | GC: alkane ladder C7–C15, SLB-5ms, 120 °C | `?gc=ex4` |
| Ex 5 — Alkane ladder | GC: C8/C10/C12, SLB-5ms, 120 °C | `?gc=ex5a` |
| Ex 5 — Polarity trio | GC: Decane, 1-Octanol, 2-Octanone, SLB-5ms, 120 °C | `?gc=ex5b` |
| Ex 5 — Co-elution hunt | GC: Tridecane + 2-Octanone, Wax, 120 °C | `?gc=ex5c` |

Parameters combine (`?hplc=ex3&gc=ex5b`); unknown keys fall back to Default.

**Interpretation flags (Brian):**

1. "Key aspects of chromatography" interpreted as the topics Wenzel's unit
   *and* drylab both cover. Wenzel topics drylab cannot simulate — eddy
   diffusion (the GC model is open-tubular Golay with A = 0, itself a
   teachable line matching Wenzel's LO that open tubular columns show no
   eddy diffusion; the HPLC a-term is fixed), steric exclusion, ion
   exchange, and the wet-lab extraction schemes — are noted in the coverage
   map rather than forced.
2. Six exercises spanning all four drylab sections, each with a conceptual
   in-class leg and a quantitative out-of-class leg. Trim at will.
3. Instructor-facing, with student-facing prompts inline in quotes.
   Expected outcomes carry measured values with operating points, so answer
   keys can be regenerated from the sim itself.

---

## Exercise 1 — From separatory funnel to column: the Craig apparatus as the missing link

**Wenzel linkage:** Extraction problem set → theoretical plate / HETP
objectives. The unit jumps from funnel extractions to plate theory; the
Craig section makes that jump visible.

**drylab setup:** Craig apparatus section (no preset needed — the controls
are few). Two solutes with editable distribution ratios D, editable phase
volumes, transfer count 0–200, per-tube results table, optional normal-
approximation overlay.

**Conceptual (in-class, groups):**

- Set D = 4 and D = 0.25, equal phase volumes. "Before running: after one
  transfer, what fraction of each solute is in the mobile-phase tube? After
  two?" Groups compute the binomial split by hand for n = 2, then run at
  n = 2 and reconcile against the per-tube table.
- Increase transfers stepwise: 5 → 25 → 100. "Describe what happens to
  (a) the separation between the two bands and (b) the width of each band.
  Which grows faster?" Target invention: band centers separate linearly in
  n while widths grow as √n — the entire justification for columns, and the
  conceptual root of Rs ∝ √N in Exercise 3.
- Toggle the normal-approximation overlay at n = 100. "Where did the
  Gaussian come from — what assumption in the model produced it?"
  (Binomial → Gaussian; each transfer is an equilibration = one plate.)

**Quantitative (out-of-class):**

- For D = 1 and equal volumes, derive the tube of maximum concentration
  after n transfers (r_max = n·D/(D+1)) and the fraction in that tube;
  verify against the per-tube table at n = 50. Then predict r_max for D = 3
  with V_upper = 2·V_lower (forces correct use of D vs. the volume-weighted
  partition ratio — a distinction the extraction learning objectives call
  out).
- Compute the minimum n for which bands with D = 1 and D = 4 reach
  Rs ≈ 1.5 using the √n width growth (centers separate as n·Δp, widths as
  2√(np q) each), then find it empirically with the slider. Reconciling
  the estimate with the observed n *is* the assessment. (Revision 3 note:
  the pair was chosen so the answer lands inside the 200-transfer slider;
  closer D pairs push n into the hundreds — itself worth mentioning as
  the cost of small selectivity.)

---

## Exercise 2 — Building the van Deemter curve before naming it

**Wenzel linkage:** In-Class Problem Set #2 (longitudinal diffusion, mass
transport broadening) and the "draw h vs. v and rationalize it" objectives.
Wenzel develops each broadening term as a separate thought experiment; here
students *discover the shape empirically* first, then attach his mechanisms
to its limbs.

**drylab setup:** HPLC section, Default preset, **Sweeps tab**. Sweep
parameter = flow_rate, output = hetp. Default column (Zorbax SB-C18,
100 × 4.6 mm, 3 µm).

**Conceptual (in-class, run *after* Wenzel's problem set #2, as its
consolidation):**

- Before plotting: "You've argued that longitudinal-diffusion broadening
  falls with flow rate and mass-transport broadening rises with it. Sketch
  h vs. v." Then run the sweep. Groups annotate the curve with *which
  mechanism owns which limb* and mark the optimum.
- Temperature probe: re-run the sweep at 10 °C and at 70 °C (temperature
  slider, then re-open the Sweeps tab). "The minimum moved. Which
  broadening term is temperature acting through, and how?" (D_m rises with
  T → B-limb rises, C-limb falls, optimum shifts right — connects Wenzel's
  diffusion problems to an observable.)
- The tradeoff question Wenzel asks verbatim ("why are most analyses not
  run at the optimum flow rate?"): switch the sweep output to t_r over the
  same range and have groups defend an operating point using both plots.
  *Instructor note:* at the default conditions the minimum sits at
  ~1.6 mL/min with h_min ≈ 6.0 µm (h ≈ 15.4 µm at 0.2 mL/min, 8.1 µm at
  5.0 mL/min; measured at 50 %B MeCN, 25 °C, default column) — so the
  default 2.0 mL/min is *already near-optimal*, and the honest answer here
  is "we nearly do, at this particle size"; the classic run-fast-above-
  optimum tradeoff appears when they lower the temperature or raise the
  particle size, both of which they can test.

**Quantitative (out-of-class):**

- In the Sweeps tab, press **Sweep data (CSV)** — the file carries the
  swept parameter, the output, and the operating-point stamp. Fit
  h = A + B/v + C·v (any tool) and report A, B, C with units; compute
  v_opt = √(B/C) and h_min = A + 2√(BC) from the fit and compare with the
  plotted minimum. This converts "write an appropriate term for the van
  Deemter equation" (a stated learning objective) into an operational
  skill. (The sweep's x is flow rate, not linear velocity; either fit in
  flow-rate units or convert via the void time in the Results tab's System
  table — deciding which, and saying so, is part of the exercise.)
- Particle-size epilogue: set the particle slider from 3 µm to 6 µm,
  re-sweep, re-fit. "Report how A, B, C each moved, then check the
  backpressure in the System table. State the tradeoff in one sentence."
  (Ties to Homework 1, question 3c, and sets up why UHPLC exists —
  h_min scales with d_p but ΔP with 1/d_p².)

---

## Exercise 2A — One mechanism at a time: the van Deemter term builder

**Wenzel linkage:** the heart of In-Class Problem Set #2, which develops
eddy diffusion, longitudinal diffusion, and the two mass-transfer terms as
*separate* thought experiments before ever summing them. Exercise 2 meets
the curve as an emergent property of a full instrument model; this
exercise builds it limb by limb first. Run 2A immediately before 2.

**drylab setup:** **Band shape → Mechanisms (van Deemter)** tab. One
slider per mechanism: particle size d_p and packing factor λ (the A term),
diffusion coefficient D_m (the B term; γ fixed at 0.6 and labeled), and
the two C coefficients C_s and C_m entered directly in ms. Each term is
its own curve under the bold total; the diamond marks the closed-form
optimum \(u_{opt} = \sqrt{B/C}\), \(H_{min} = A + 2\sqrt{BC}\).

**Conceptual (in-class):**

- Zero everything you can: set C_s = C_m = 0 and note what remains and
  how it varies with u (A flat, B/u falling — and no optimum exists; the
  operating-point stamp says so). "Why does an open-tubular GC column
  have no A term?" (No packing — nothing to take multiple paths around;
  Wenzel's LO on open-tubular columns, now demonstrable by construction.)
- Restore C_s = 2 ms, C_m = 1 ms. Predict, then verify with the sliders:
  what does doubling d_p do to which limb? Halving λ (a better-packed
  column)? Doubling D_m (a hotter, thinner mobile phase)? The last one
  moves *two* limbs in opposite directions — B up, effective C down is
  NOT what this builder does (C is entered directly), and noticing that
  the builder's C sliders don't respond to D_m is the setup for the
  question: "which physical variables does each C term actually contain?"
  Groups write the C_s and C_m expressions from lecture (d_f²/D_s,
  d_p²/D_m) and state which slider in the *HPLC* section would move them.
- Sum question: "Two columns have the same H_min but different shapes.
  Which would you rather run fast, and what number tells you?" (The C sum
  — flat curves forgive speed; this is the same reading as the GC Golay
  tab's carrier comparison, and saying so links the sections.)

**Quantitative (out-of-class):**

- Export **Term curves (CSV)**. Verify numerically that the total's
  minimum sits at \(\sqrt{B/C}\) and equals \(A + 2\sqrt{BC}\), using A, B, C
  recovered from the exported columns (A is the flat column; B from
  B/u · u at any point; C from the slope of the rising limbs). This is
  the same identity Exercise 2's fit will extract from a *simulated
  instrument* — done here on curves the student built, so nothing is
  hidden.
- Sketch (no simulator): the same decomposition for an open-tubular GC
  column. Which limbs survive, and what replaces d_p in the C_m term?
  (Golay: A = 0, C_m carries d_c²/D_m — bridges to Exercise 5's coda.)

---

## Exercise 3 — Triage with the fundamental resolution equation

**Wenzel linkage:** In-Class Problem Set #3 verbatim ("examine a
chromatogram with unacceptable resolution and determine which term of the
three is the best one to alter"), plus the k′-tradeoff objectives.

**drylab setup:** HPLC section, **preset "Ex 3 — Resolution triage"**
(`?hplc=ex3`): acetophenone + p-chlorophenol at 50 %B acetonitrile on the
default column. Opens at **Rs = 0.65, α = 1.031** — visibly fused, honestly
salvageable. The **Rs (vs prev)** and **alpha (vs prev)** columns in the
Results tab adjudicate every attempt live.

**Conceptual (in-class):**

- Present the failing chromatogram. Groups get one "budget line" each:
  **N-team** may only change length/particle size/flow; **k-team** only
  %B/temperature; **α-team** only the solvent (MeCN ↔ MeOH). Each team
  predicts *in writing* what its lever will do to Rs, tR, and backpressure,
  then tests it. Whole-class reconciliation ranks the levers.
  *Instructor key (all measured on the preset, other conditions default):*
  the N-team maxing **both** sliders (300 mm + 1.5 µm) reaches only
  **Rs = 1.56 at 2082 bar** — a number no pump survives, and the √N lesson
  embodied; the k-team at 44 %B gets **Rs = 2.58** in one move; the α-team
  with methanol at 65 %B gets **Rs = 7.79 (α = 1.57)**. Chemistry wins.
- *Instructor note, worth stating rather than letting groups discover an
  inconsistency:* on this pair, %B moves α as well as k (α = 1.031 at
  50 %B → 1.115 at 44 %B), because the two solutes' S coefficients differ.
  That is real reversed-phase behavior: the "three independent levers" of
  the fundamental equation are a *decomposition*, not a promise that one
  knob touches one term.
- Diminishing-returns probe for the k-team: Sweeps tab, k_prime vs.
  solvent_percent. "Where does further retention stop buying resolution?"
  Target: the k/(1+k) factor saturates — retention past k ≈ 5–10 costs
  time, not separation (Wenzel's "limits to the effect of increasing the
  retention factor").

**Quantitative (out-of-class):**

- From the Results table at the preset condition, record N (System table),
  α and the tabulated Rs. Compute Rs from the fundamental equation and
  compare with the table's value — they will not match exactly, because the
  table's Rs is built from the model's full peak widths, extra-column
  broadening included; explaining the discrepancy is part (b). The
  **Export tab's compound-results CSV** carries `rs_vs_prev` and
  `alpha_vs_prev` with the operating-point stamp, so the homework travels
  with its evidence.
- Predict Rs and tR if the column is lengthened from 100 mm to 300 mm
  (Rs ∝ √N, t ∝ L), then verify with the length slider. One-sentence
  verdict: when is tripling the column *ever* the right first move?

---

## Exercise 4 — The general elution problem, twice: gradient LC and programmed GC

**Wenzel linkage:** In-Class Problem Set #3 problem 2 — the chromatogram
with crowded early peaks and flat late peaks; "propose a way in gas
chromatography / in liquid chromatography to eliminate both problems."
drylab shows both proposals working, side by side, which no static problem
set can.

**drylab setup:** (a) HPLC, **preset "Ex 4 — General elution"**
(`?hplc=ex4`): all 22 compounds at 30 %B. (b) GC, **preset "Ex 4 — General
elution"** (`?gc=ex4`): the alkane ladder Heptane→Pentadecane on SLB-5ms at
120 °C, using the Programmed and Compare tabs.

**Conceptual (in-class):**

- LC leg: run the preset as-is at 30 %B, then push the slider to 70 %B.
  "Neither works. State, using the term from lecture, why not."
  *Instructor key (measured, default column):* 30 %B spans k′ 1.3–352 with
  the last peak near **188 min**; 70 %B compresses everything to k′
  0.22–5 inside 3 min — the two failure modes of the general elution
  problem in one slider throw. Then hand over the gradient editor (Gradient
  tab): groups design a program that gets every k′ into the useful window.
  The **Band tracks** view (k′ vs. time) is the payoff — students watch
  each band's k′ collapse as the gradient front reaches it, the mechanism
  Wenzel's text describes in words.
- GC leg: same logic with the oven. Isothermal 120 °C (17.4 min for nine
  alkanes, early ones crowded, C15 flat and late) vs. a group-designed ramp
  on the **Compare** tab, which holds column, carrier and pneumatics fixed
  so the two traces provably differ only in the elution program. "Why does
  the programmed run *sharpen* the late peaks rather than just moving
  them?" (Late solutes sit parked near the inlet until the oven catches up
  — the band-compression argument.)
- Synthesis question, answered without the sim: "State in one sentence what
  a %B-gradient and temperature-programming have in common." (Both ramp the
  effective k′ of everything downward during the run.)

**Quantitative (out-of-class):**

- Dwell-volume forensics (LC): change the mixing/non-mixing volumes in the
  Gradient tab and measure the shift in early-peak retention against the
  Solvent-profile view. Compute the expected delay t_dwell = V_dwell/F and
  compare. (Instrument realism that transfers directly to lab hardware.)
- Peak-capacity estimate (GC): from the **Peak results (CSV)** exports of
  the isothermal and programmed runs (both arms have export buttons under
  their tables), compute n_c ≈ 1 + (√N/4)·ln(t_last/t_first) for the
  isothermal run vs. the gradient-mode estimate for the program, and report
  the ratio. The number makes "programming fixes the general elution
  problem" quantitative.

---

## Exercise 5 — What retains a molecule in GC: boiling point, polarity, and ln k vs. 1/T

**Wenzel linkage:** In-class GC problems (pentane vs. pentanol boiling
points, retention-order prediction), Homework 2 problem 1 (esters on polar
vs. non-polar phases: does *order* change? do *times* change?), and the
"predict the retention order in GC" objective.

**drylab setup:** GC isothermal, three presets in sequence, plus the
**Golay tab** for the carrier-gas coda. The solute picker keeps each round
to the compounds under discussion.

**Conceptual (in-class):**

- Round 1 (volatility axis), **preset "Ex 5 — Alkane ladder"**
  (`?gc=ex5a`): Octane, Decane, Dodecane on SLB-5ms at 120 °C. Predict the
  order — easy — then: "Retention doesn't just increase, it increases
  *multiplicatively* per CH₂. Propose why." (Free energy is additive per
  methylene → k is multiplicative; the molecular version of the ln k
  linearity they'll measure below.)
- Round 2 (polarity axis), **preset "Ex 5 — Polarity trio"** (`?gc=ex5b`):
  Decane (bp 174 °C), 1-Octanol (bp 195 °C), 2-Octanone on SLB-5ms; groups
  predict, run, then switch the phase dropdown to Wax and predict again
  before running. *Instructor key (measured at 120 °C, default column):*
  on SLB-5ms the order is **2-Octanone < Decane < 1-Octanol**; on Wax it
  becomes **Decane < 2-Octanone < 1-Octanol** — the alkane vaults from the
  middle to first out as the polar phase releases it, while the H-bonding
  alcohol stays anchored last on both. "Which property set the order on
  each phase? Whose *absolute* retention changed most?"
- Carrier-gas coda (bridges back to Exercise 2): open the **Golay tab** —
  plate height vs. average carrier velocity for one solute, all three
  gases on one axis, diamonds marking each gas's optimum, swept over the
  inlet-pressure control's own range. "Wenzel's problem set says
  longitudinal diffusion matters more in gases. Read the plot: which
  carrier suffers most at low velocity, which has the flattest fast side,
  and which would you buy?" (N₂'s low sharp optimum against H₂'s flat fast
  curve is the textbook argument, now read directly off the figure; the
  **Golay sweep data (CSV)** button exports the curves.)

**Quantitative (out-of-class):**

- Pick one solute; record k from the results table at four oven
  temperatures spanning ~40 °C (the **Peak results (CSV)** export stamps
  each file with its temperature). Plot ln k vs. 1/T, extract the slope,
  and interpret it as −ΔH°/R for transfer into the stationary phase.
  Compare the ΔH ranking of Decane vs. 1-Octanol on Wax with Round 2's
  conclusion. (The K-centric model the sim runs on makes this linearity
  real, not decorative.)
- Co-elution hunt, **preset "Ex 5 — Co-elution hunt"** (`?gc=ex5c`):
  Tridecane and 2-Octanone on Wax, opening at 120 °C where the alkane
  elutes first. From two 4-point ln k vs. 1/T fits, predict the
  temperature at which the pair co-elutes, then verify by walking the oven
  slider down. *Instructor key (measured):* the ln k lines cross near
  **102 °C** at k ≈ 1.7 — comfortably observable — and the order is
  inverted on the far side. A co-elution temperature as an *intersection
  of thermodynamic lines* is a high-value concept the static problem sets
  cannot reach.

---

## Exercise 6 — Why the CE detector sees everything: EOF as a controllable variable

**Wenzel linkage:** CE In-Class Problems 1–12 nearly verbatim — silanol
chemistry, EOF vs. pH, the "anions, cations and neutrals are all detected —
explain" question, and the five-substance electropherogram prediction. Also
the CE out-of-class amino-acid question.

**drylab setup:** CZE section (no preset — the defaults are the scenario).
The EOF-mobility slider (0–80 ×10⁻⁹ m²/Vs) is the pedagogical control: it
is exactly the "pH knob" of Wenzel's problems 2 and 7, since bare-silica
EOF falls toward zero at low pH. The default composition already carries
K⁺, Na⁺, Li⁺ over acetate/Tris.

**Conceptual (in-class):**

- EOF = 0 (a "pH 2.5 capillary"): run. Only cations reach the detector.
  Groups explain, then predict what EOF = 60 ×10⁻⁹ (a "pH ~9 capillary")
  changes — committing the predicted arrival order of a cation, a neutral,
  and an anion to paper — then run and reconcile. This *is* Wenzel
  problem 11, with the mechanism exposed as a slider instead of asserted.
- K⁺ / Na⁺ / Li⁺ order: "All +1. Crystal-radius order says Li⁺ is
  smallest — why is it slowest?" (Hydrated radius vs. crystal radius —
  mirrors the ion-exchange retention-order reasoning in Problem Set #4, a
  deliberate echo worth naming for the class.)
- Broadening callback: "Of the band-broadening mechanisms from the van
  Deemter work — eddy, longitudinal, stationary-phase and mobile-phase mass
  transport — which survive in CE?" Then raise the voltage until the peaks
  visibly degrade and ask what new mechanism appeared (Joule heating; the
  sim reports it).

**Quantitative (out-of-class):**

- From μ_app = μ_ep + μ_EOF, predict the migration times of K⁺, Na⁺ and
  Li⁺ at the defaults (500 V over 30 mm; detector at 15 mm) — noting that
  the injected plug is centered at 6 mm, so the migration distance is
  9 mm, not 15 — and compare with the simulated peak times. The simulated
  times run ~10–15 % longer than infinite-dilution arithmetic because the
  model computes effective mobilities in the full electrolyte; explaining
  that systematic (order and ratios right, absolute times slower) is part
  of the answer, not an error to hide. Then the acetate problem: in the
  default composition acetate is a **BGE** ion — it fills the capillary
  and shows no peak, so first switch its role to Sample in the
  composition editor (realizing *why* nothing eluted is part of the
  exercise). With the plug at 6 mm, compute the minimum EOF for acetate
  (μ_ep = −42.4) to reach the detector within the default 20 s run, and
  the (smaller) minimum for a 60 s run; verify both by bracketing with
  the slider.
- Resolution vs. voltage: N in CE grows linearly with V (until heating).
  Run three voltages, compute plate counts for one peak from the reported
  migration time and FWHM (N = 5.54(t/w½)² — deliberately left as hand
  arithmetic), identify where linear scaling breaks, and correlate with the
  Joule-heating report.

---

## Exercise 7 — When the column is full: overload, tailing, and fronting

**Wenzel linkage:** the peak-shape and column-capacity discussion — why
real peaks tail, what "overload" means thermodynamically, and why an
asymmetric peak still carries information. This is the exercise the unit
could not previously run: no static problem set can show an isotherm
*bending* a peak.

**drylab setup:** **Band shape → Peak shape (overload)** tab, at its
defaults (N = 100, k = 2, curvature 0, load 1). The dashed curve is the
exact linear-isotherm profile at the same N and k — the honest baseline —
and the readout table reports t_max, As at 10 % height (for both the
simulated and the ideal profile), apparent vs. built-in plate count, and
mass recovery. Time is in transfers (one transfer = one plate volume);
the reduced units are the point: every effect shown is scale-free.

**Conceptual (in-class):**

- Baseline literacy first: at the defaults the simulated and ideal curves
  coincide, and the *ideal* profile's own As reads ≈ 1.18, not 1.00.
  "Nothing is overloaded — where is the asymmetry coming from?" (A
  100-plate column is a 100-event random process; the plate model's
  profile is skewed at finite N and only becomes Gaussian as N grows.
  Raise N toward 1000 and watch As_ideal fall toward 1. Asymmetry only
  means something against this baseline — which is why the table prints
  both.)
- Commit predictions, then push **curvature positive** (Langmuir, the
  isotherm bending toward saturation): which side of the peak sharpens,
  and does t_max move early or late? Then negative. Reconcile with the
  isotherm argument: velocity of a concentration goes as
  1/(1 + F·dq/dC); Langmuir's dq/dC *falls* with C, so the top of the
  band outruns the base — sharp front, diffuse rear (tailing), maximum
  arriving earlier. Anti-Langmuir is the mirror (fronting, maximum
  later).
- The two tailings: set curvature back to 0 and raise the **slow-site τ**
  slider instead. The peak tails again — with t_max moving *later*, not
  earlier, and at *any* load. "Your real column shows a tailing peak.
  Name an experiment that tells overload tailing from slow-site tailing."
  (Cut the load: overload tailing dies, kinetic tailing doesn't — and the
  t_max direction differs. This is a genuinely diagnostic pair of
  observables.)
- Load ladder: curvature 0.5, load 1 → 4 → 10. Watch As climb, t_max walk
  earlier, and apparent N fall below the built-in 100. "The column didn't
  change — why did it 'lose' plates?" (It didn't; the moment-based plate
  count assumes a symmetric peak, and overload broke the assumption. What
  a number *means* depends on the model behind it.)

**Quantitative (out-of-class):**

- Export the **Profile (CSV)** at curvature 0, +2, and −0.6 (load 1,
  N = 100, k = 2). For each, compute As at 10 % height from the exported
  points and the first-moment retention; tabulate against the on-screen
  readouts. Then state, from the +2 profile alone, whether the *front* or
  the *rear* of the band carries the isotherm information, and why the
  tail of a Langmuir-overloaded peak points at the linear-isotherm
  retention time.
- Design question (no simulator): a QC method reports "plate count" from
  a moment fit and flags the column as degraded whenever N_app drops 20 %.
  The instrument is also used for a high-load prep separation. Explain,
  with the numbers from the load ladder, how this flag can fire on a
  healthy column — and what second readout (As, and t_max direction)
  distinguishes the cases.

---

## Coverage map and honest gaps

| Wenzel unit topic | drylab exercise | Status |
|---|---|---|
| Extraction / partition | Ex. 1 (Craig) | Conceptual bridge; wet-lab schemes stay on paper |
| Longitudinal diffusion, mass transport, van Deemter/Golay | Ex. 2A, Ex. 2, Ex. 5 coda (Golay tab) | Full |
| Eddy diffusion | Ex. 2A (Mechanisms tab) | Full since v0.24.0: the A-term is a live control (λ, d_p); its absence in open-tubular GC is demonstrated by construction |
| Fundamental resolution equation | Ex. 3 | Full, with live Rs/α columns |
| General elution problem / gradients / T-programming | Ex. 4 | Full |
| GC retention order & thermodynamics | Ex. 5 | Full, incl. a verified co-elution crossing |
| Steric exclusion, ion exchange | — | Not simulatable in drylab; Wenzel's paper problems stand alone (Ex. 6 echoes the IEC hydrated-radius argument) |
| CE | Ex. 6 | Full (CZE; no ITP/stacking, consistent with the ruled CE scope) |
| Peak asymmetry: overload (isotherm curvature) and kinetic tailing | Ex. 7 (Peak shape tab) | Full since v0.24.0; the two tailing mechanisms are separate controls and taught apart |

**Sequencing suggestion:** Ex. 1 immediately after the extraction unit;
Ex. 2A then Ex. 2 as the consolidation of In-Class Set #2; Ex. 7 directly
after Ex. 2 while the plate picture is fresh (or with the GC block); Ex. 3–4 with Set #3; Ex. 5
with the GC lecture block; Ex. 6 with the CE block. Each in-class leg is
sized for one 50-minute facilitated session in Wenzel's 3–4-student
groups; each quantitative leg is one homework problem with its CSV
evidence attached — every export drylab produces is stamped with the
operating point that generated it, so "attach your CSV" is also "state
your conditions."

**Assessment rubric hook (all exercises):** grade the
*prediction–reconciliation delta*, not the final answer — full credit
requires the written pre-simulation prediction, the observed result, and an
explicit statement of what changed in the student's model when they
disagreed. That is the POGIL contract, and it is what distinguishes these
from "play with the simulator" exercises.

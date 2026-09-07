# Instructor Key — Exercise 2A: Building the van Deemter Curve One Mechanism at a Time

**Every value below was measured against `drylab.bandshape` at v0.24.7 —
this revision requires the v0.24.7 app** (equations accordions, log
velocity axis, guarded N_app readout).
Section: **Band shape**, tabs **Mechanisms (van Deemter)** and **Peak
shape (overload)**. No CSV export is used anywhere; every number the
students need is on screen, in the grey operating-point stamp under the
plot or in the Peak shape readout table.

**Setting A** (the sheet's baseline): dp 3.0, λ 1.00, Dm 1.0, Cs 2.00,
Cm 1.00. Its stamp reads exactly:

`dp 3 um, lambda 1, Dm 1e-5 cm2/s, gamma 0.6, Cs 2 ms, Cm 1 ms | u_opt 0.063 cm/s, H_min 9.79 um`

**Rev 2 (2026-08-27).** Trends redesign after the equations accordions
were added: the panel now publishes the closed forms (statics only), and
every question interrogates behaviour the formulas state nothing about.
New: Q4(b) eddy controversy, Q5 coupling follow-up, Q7 crossover, Q8
symmetric miss, Q11 k-trend with the k = 0 edge, Q13 Wenzel Homework 1
tie-in. The velocity axis defaults to log in v0.24.7; the worksheet says
to leave it on.

---

## Q1 — What the Craig apparatus doesn't do

Any three of the following, with the direction of the effect:

- **Flow takes time; molecules diffuse while it happens.** Craig
  transfers are instantaneous. Longitudinal diffusion spreads the band —
  **wider**, and worse the slower you go.
- **Equilibrium is not instantaneous.** A real analyte needs time to
  cross into and out of the stationary phase. Molecules that haven't
  finished get carried ahead — **wider**, and worse the faster you go.
- **There is more than one path through a packed bed.** Craig has a
  single file of tubes. Real packing offers routes of different lengths
  — **wider**, and independent of speed.
- **A real column has no discrete stages at all** — the tube boundaries
  are a fiction.

**The point to land before they open the simulator:** the first three map
one-to-one onto the three terms they are about to build, and two of them
are *velocity-dependent in opposite directions*. That opposition is the
whole reason an optimum exists. Students who get all three usually
predict the minimum correctly in Q3 without being told.

**Watch for** the answer "the column is longer." Length changes N, not
H — that's the confusion Q8 is built to separate.

---

## Q2 — The A term by hand

$$A = 2 \lambda d_p = 2(1.00)(3.0\ \mathrm{\mu m}) = 6.0\ \mathrm{\mu m}$$

**No, there is no u in it.** That is the answer that matters, and it is
why the A trace is drawn flat (legend: `A (eddy)`). Eddy diffusion
happens because the packed bed offers paths of different lengths; the
spread that produces is a fixed fraction of the distance travelled
regardless of how fast you push.

---

## Q3 — Zeroing the mass-transfer terms

**Predicted:** the flat `A (eddy)` trace and the falling
`B/u (longitudinal)` trace remain; both `Cs·u` and `Cm·u` collapse onto
zero. **No minimum exists** — H falls monotonically and approaches A
from above as u increases.

**Measured** (dp 3.0, λ 1.00, Dm 1.0, Cs 0, Cm 0): H = 12.00 µm at
u = 0.02, 6.24 µm at u = 0.5, 6.12 µm at u = 1.0. The stamp ends with

`... Cs 0 ms, Cm 0 ms | no optimum (C = 0)`

The app **says so in words**. Students do not have to infer the absence
of a minimum from a curve that is still visibly falling at the right-hand
edge, and they should be pushed to quote the stamp rather than eyeball
the trace.

**Follow-up — the ladder of missing terms.**

(a) **Capillary GC: A must be exactly zero.** There is no packing, so
there are no alternative flow paths of differing length; every molecule
travels down one open tube. This is the Golay case, and it is why
capillary GC columns reach plate heights a packed column cannot. The
film is still there, so C_s and C_m survive. (If a group asks what
replaces the C_m term's dp: the column radius. That is Exercise 5's
coda — acknowledge and move on.)

(b) **CE: only B survives.** No packing kills A; no stationary phase
kills C_s outright — and C_m too, because mobile-phase mass-transport
broadening is the cost of *reaching* stationary phase that isn't there.
This is straight from Wenzel's CE development, and it is the reason CE
plate counts are so high: longitudinal diffusion is the only broadening
mechanism left. A group that parks C_m in the "survives" column has
missed what C_m is *for* — worth pressing on.

---

## Q4 — The A term does not move the optimum

| Change | Observed u_opt | Observed H_min |
|---|---|---|
| Setting A | 0.063 cm/s | 9.79 µm |
| dp 3.0 → 6.0 | **0.063 cm/s** | 15.79 µm |
| λ 1.00 → 0.50 | **0.063 cm/s** | 6.79 µm |

**u_opt does not move. At all.** Most groups predict that coarser
particles should shift the optimum to lower velocity, and it is worth
letting them commit to that in writing before they run it.

The A term sets **how high the whole curve sits**, not **where its
minimum is**. Formally, A is an additive constant in
H = A + B/u + C·u, so it vanishes on differentiation — u_opt = √(B/C)
contains no A. Changing dp from 3 to 6 doubled A from 6.00 to 12.00 µm
and pushed H_min up by exactly 6.00 µm, leaving u_opt untouched.

**The reconciliation to demand:** packing quality and particle size buy
you a *better column at every velocity*. They do not buy you a *faster*
column. That distinction is the one Q9 then prices.

**Caution.** In a real instrument dp and C_m are physically linked
(C_m contains dp²/D_m), so a real particle-size change does move the
optimum. This builder deliberately decouples them so one mechanism can
be moved at a time — say so if a sharp student objects, because the
objection is correct and is the setup for Q5's follow-up.

**(b) The eddy controversy — Wenzel's A·v^(1/3).** If the eddy term
rises with velocity, it stops being an additive constant and starts
behaving partly like a C term: the rising side of the curve gets an
extra positive contribution, so the balance point between falling and
rising limbs moves **left** — u_opt decreases. And since that extra
rising term carries the packing parameters, **packing quality would now
move the optimum**, which the flat-A builder says it cannot. That is
the answer to accept: under van Deemter's flat A the Q4 result is
exact; under Wenzel's v^(1/3) form it is only approximate, and the two
pictures are *distinguishable in principle* by measuring u_opt against
λ or dp. Wenzel is explicit that the literature never settled this —
some authors even drop A entirely — so the honest close is that the
student has just located a live disagreement, not a solved exercise.
(A1 makes the direction rigorous: the derivative gains the positive
term (a/3)u^(-2/3).)

---

## Q5 — The B term does move it

| Change | Observed u_opt | Observed H_min |
|---|---|---|
| Setting A | 0.063 cm/s | 9.79 µm |
| Dm 1.0 → 4.0 | **0.126 cm/s** | 13.59 µm |

Fourfold in D_m, **twofold** in u_opt, because u_opt = √(B/C) and
B = 2γD_m — the square root halves the exponent. Expect predictions of
"four times"; the factor-of-two observation is the reconciliation.

Direction reasoning: more diffusion makes the *slow* end worse, so the
penalty for dawdling grows and the best compromise moves toward higher
velocity. H_min rises too (9.79 → 13.59 µm) — you do not get the shift
for free.

**The coupling follow-up.** The accordion gives the physical content
(C_s ~ d_f²/D_s, C_m ~ d_p²/D_m); the assessable work is mapping
symbols to instrument controls, and the map spans two sections:

- **Particle size (µm)** — HPLC section — moves C_m (and A).
- **Film thickness (µm)** — **GC** section; the HPLC section has no
  film control, and noticing that is part of the answer (in
  bonded-phase LC the film is set by the chemistry, not a knob).
- **Temperature (°C)** — HPLC section — is the one that moves **two
  terms in opposite directions**: raising T raises D_m, which raises
  B = 2γD_m and *lowers* C_m ~ d_p²/D_m. The optimum's response to
  temperature is therefore a competition, which is exactly the probe
  Exercise 2 runs on the full instrument model.

Accept dp for the "two terms" answer only with the sign caveat: dp
moves A and C_m in the *same* direction (both worse when bigger), so it
fails the "opposite directions" clause. That is the bridge to
Exercise 2.

---

## Q6 — Verifying u_opt = √(B/C) with no export

The unit handling is the assessable part.

$$B = 2 \gamma D_m = 2(0.6)(1.0 \times 10^{-5}\ \mathrm{cm^2/s}) = 1.2 \times 10^{-5}\ \mathrm{cm^2/s}$$

$$C = C_s + C_m = 2.00 + 1.00 = 3.00\ \mathrm{ms} = 3.0 \times 10^{-3}\ \mathrm{s}$$

$$u_{opt} = \sqrt{\frac{B}{C}} = \sqrt{\frac{1.2 \times 10^{-5}}{3.0 \times 10^{-3}}} = \sqrt{4.0 \times 10^{-3}} = 0.0632\ \mathrm{cm/s}$$

Stamp reads **0.063 cm/s**. Agreement to the printed precision.

For completeness, the height:

$$H_{min} = A + 2\sqrt{BC} = 6.00 + 2\sqrt{(1.2 \times 10^{-5})(3.0 \times 10^{-3})} \times 10^4 = 6.00 + 3.79 = 9.79\ \mathrm{\mu m}$$

**Two failure modes, both worth catching at the checkpoint.** Students
who leave C in milliseconds get u_opt = 0.002 cm/s, off by √1000. Students
who forget the 10⁻⁵ on D_m get 6.3 cm/s. Both are a factor the stamp
will immediately contradict, which is the point of making them check.

---

## Q7 — The crossover: where the optimum lives

With Cs = 3.00, Cm = 0.00, the total C is unchanged (3.0 ms), so the
stamp still reads u_opt 0.063, H_min 9.79 — and now the whole rising
limb is a single hoverable trace.

**The limbs contribute equally at exactly u_opt**: B/u = C·u solves to
u = √(B/C), which *is* the optimum. Measured at u = 0.063 cm/s, each
limb reads **1.897 µm** (= √(BC), 10⁴-scaled), directly under the
diamond, and the total there is A + 2√(BC) = 9.79.

**The sentence to land:** the optimum is not a mystery point — it is
where longitudinal diffusion and mass transfer *trade places* as the
dominant broadening mechanism. Below it, diffusion owns the peak; above
it, mass transfer does.

**Follow-up if a group is fast:** why does the flat A trace have no say
in where the crossing sits? Because the crossing condition B/u = C·u
never mentions A — which is Q4 again, seen geometrically.

---

## Q8 — Missing the optimum: the symmetric surprise

| | u (cm/s) | H (µm) |
|---|---|---|
| u_opt ÷ 2 = 0.032 | 0.0316 | **10.74** |
| u_opt × 2 = 0.126 | 0.1265 | **10.74** |

**Identical, to the hover's precision (10.7434 both sides).** Nearly
every group predicts the slow side is worse — "B/u blows up" — and the
steep-left/shallow-right picture on a *linear* axis feeds that
intuition. But H(α·u_opt) = A + √(BC)(α + 1/α) is exactly symmetric
under α ↔ 1/α: any *multiplicative* miss costs the same H in either
direction. (On the log axis the curve is visibly symmetric about the
diamond — the v0.24.7 default makes this plain.) A 2× miss costs 9.7 %
of H_min; a ±20 % pump error costs **0.65 %** — the minimum is
quadratically flat.

**The operator's answer.** If H is symmetric, time is not: running at
2·u_opt finishes the separation **4× sooner** than u_opt/2 for the same
plate height. That, and only that, is why every practical method errs
fast. Wenzel gives the numbers: a packed GC column optimizes around
15–20 mL/min and is routinely run at ~30, trading a little efficiency
for time; LC's optimum is so slow it is simply not practical to sit on.
This is Wenzel's learning objective "explain why most analyses are not
performed at the flow rate that optimizes the efficiency of the
column" — answered with a measurement instead of a slogan.

---

## Q9 — Same H_min, different tolerance for speed

| | u_opt (cm/s) | H_min (µm) | H at u = 0.5 cm/s |
|---|---|---|---|
| Setting A (dp 3.0, λ 1.00, C = 3.0 ms) | 0.063 | **9.79** | 21.24 |
| Setting B (dp 2.0, λ 1.90, C = 1.0 ms) | 0.110 | **9.79** | 12.84 |

**First observation: the two H_min values are identical** — both stamps
read 9.79 µm. The columns are exactly equally efficient *if you run each
at its own optimum*.

**Second: you want Setting B**, and the number that says so is the
**H at 0.5 cm/s** column — 12.84 against 21.24 µm. Setting B is the flat
column; it costs you 3.05 µm to run at 0.5 cm/s where Setting A costs
11.45 µm. Accept "u_opt is higher" as a partial answer, but push for the
H comparison: a higher optimum is not the same claim as a gentler
penalty for exceeding it.

**Third: the C sliders.** C = 1.0 ms versus 3.0 ms. C is the slope of
the rising limb, so it alone decides how fast the curve climbs once you
pass the optimum. Setting B pays for that flatness with a worse A term
(7.60 versus 6.00 µm) — a finer particle in a worse-packed bed — and the
two effects happen to cancel exactly at the minimum.

**The sentence to get on the board:** H_min tells you how good a column
can be; C tells you how much it costs to hurry. Two columns can agree on
the first and disagree completely on the second. This is the same
reading as the GC Golay tab's carrier-gas comparison — say so.

---

## Q10 — Fourfold N

| N | Sigma | First moment | Sigma ÷ moment |
|---|---|---|---|
| 100 | 24.49 | 300.0 | 0.0816 |
| 400 | 48.99 | 1200.0 | 0.0408 |

**Sigma doubled** (ratio exactly 2.0000) — the peak got *wider* in
absolute terms, which is the prediction most groups get wrong. **The
relative width halved** (ratio exactly 0.5000), and that is the quantity
that matters.

**The factor is √4 = 2, and they met it in Exercise 1**, where band width
grew as √n while band position grew as n. Identical theorem, now
measured on an elution profile rather than a tube train: variance is the
additive quantity, so σ ∝ √N and σ/t_R ∝ 1/√N.

**Reconciliation to demand in writing:** "wider" and "better" are not
contradictory, because the peak also eluted four times later. Anyone who
predicted the peak would get narrower should say explicitly what they
were holding fixed.

---

## Q11 — Reading N_app = N(1+k)/k as a trend

**The sketch to expect:** a curve that **diverges as k → 0** and falls
monotonically toward a **horizontal asymptote at N** as k grows. Both
limits are readable straight off the published formula — (1+k)/k → 1/k
near zero, → 1 at large k — and the point of asking for the sketch
first is that many students can manipulate the formula yet still draw
it approaching zero, or crossing N.

| k | Built-in N | Apparent N_app | First moment |
|---|---|---|---|
| 0.5 | 100 | 300 | 150.0 |
| 2.0 | 100 | 150 | 300.0 |
| 9.0 | 100 | 111 | 1000.0 |

All three rows match N(1+k)/k to the printed digit.

**At k = 0 the readout says:** `n/a (sigma = 0, unretained)` — not a
number, and (as of v0.24.7) not a NaN either. **The physics:** in this
cascade the *only* broadening mechanism is the stochastic partitioning.
An unretained analyte never enters the stationary phase, never
randomises, and exits as a spike: σ = 0, so μ²/σ² is undefined —
"infinitely efficient" in the model's terms.

**What the model leaves out** (the honest second half): a real
unretained peak still broadens — longitudinal diffusion, injection
width, and every extra-column volume act on it regardless of retention.
The model's answer is a statement about *which mechanism this simulator
contains*, not about real peaks. A student who answers "real N_app is
infinite at k = 0" has confused the sandbox with the instrument; a
student who names diffusion as the surviving mechanism has just
re-derived why the *B* term exists — and, from Q3(b), why CE peaks are
sharp but not infinitely so.

**Which number to quote in a paper:** N_app, because it is what the
peak actually delivers — but it is analyte-specific, so it must be
reported **with the k it was measured at**. A bare plate count without
the test probe is meaningless.

---

## Q12 — The ideal peak is already skewed

| N | As (10 %) |
|---|---|
| 10 | 1.74 |
| 100 | 1.18 |
| 800 | 1.06 |

Curvature is 0.00 and load is 1.0 throughout — **nothing is overloaded**,
and `Mass recovered` reads 1.0000. The readout's `Ideal-profile As (10 %)`
matches the simulated `As` exactly, which is the tell.

**Why.** The exit profile is a negative binomial, which is intrinsically
right-skewed at finite N. It only becomes Gaussian in the large-N limit —
the same de Moivre–Laplace argument from Exercise 1 Q7, where the
binomial needed large np and nq before the normal overlay was allowed to
appear. Here N plays that role: the skew decays as N grows, 1.74 → 1.06.

**The lesson, and it is a practical one:** As > 1 does **not** by itself
mean a peak is tailing. It has to be judged against the asymmetry an
ideal peak of the same efficiency would already have. This is exactly
why the panel always draws the ideal profile as a dashed line and always
prints its As — the baseline is not optional. An analyst who calls a
1.18 peak at N = 100 "tailing" is reporting the plate count, not a
chemical problem.

---

## Q13 — Two effects, one slider (Wenzel, Homework 1, Question 1)

This is Wenzel's first out-of-class problem — "what would be the effect
on a gas chromatographic peak of introducing the sample at too slow a
rate?" — run on the simulator instead of argued in the abstract. Point
students at that connection explicitly: their homework answer should
cite these numbers.

| Injection width | Sigma | First moment | N_app |
|---|---|---|---|
| 1 | 24.49 | 300.0 | 150 |
| 10 | 25.44 | 286.5 | 127 |
| 20 | 29.02 | 271.5 | 88 |

**Effect one: the peak broadens.** Sigma rises 24.49 → 29.02, and N_app
collapses 150 → 88 even though `Built-in plates N` still reads 100. The
column did not get worse; the measurement did.

**Effect two: the peak arrives earlier.** The first moment falls
300.0 → 271.5. Sample injected onto plate j only has (N − j) plates left
to cross, so a wide injection puts some of the sample partway down the
column at t = 0.

**Extra-column effect: both of them.** The injector is not part of the
column, and this is the model's version of injection-volume overload —
the most common real cause of a plate count that disappoints. Group the
answer with tubing volume, detector cell volume, and connector dead
volume.

**`Mass recovered` = 1.0000 throughout**, which rules out **loss** as an
explanation. Whatever is happening to the peak, none of the analyte went
anywhere. Students who reached for "sample was lost on the column" have
a number in front of them that says otherwise.

---

# Going further — worked

## A1 — The optimum by calculus

$$H(u) = A + \frac{B}{u} + Cu \qquad
\frac{dH}{du} = -\frac{B}{u^{2}} + C$$

Setting the derivative to zero:

$$C = \frac{B}{u^{2}} \;\Longrightarrow\; u_{opt} = \sqrt{\frac{B}{C}}$$

It is a minimum, since the second derivative $2B/u^{3}$ is positive for
all u > 0. Substituting back:

$$H_{min} = A + \frac{B}{\sqrt{B/C}} + C\sqrt{\frac{B}{C}}
= A + \sqrt{BC} + \sqrt{BC} = A + 2\sqrt{BC}$$

**The Q4 result, proved.** A appears in H as an additive constant, so it
is annihilated by d/du before u_opt is ever computed:

$$\frac{\partial u_{opt}}{\partial A} = \frac{\partial}{\partial A}\sqrt{\frac{B}{C}} = 0$$

With Wenzel's A·u^(1/3) instead, the derivative becomes
(a/3)u^(−2/3) − B/u² + C: the new term is strictly positive, so the
zero moves to smaller u — the Q4(b) direction, forced by one sign.

In words: a flat eddy term contributes the same plate height at every
velocity, so it cannot change *which* velocity is best. It raises the
whole curve rigidly. A column can have an enormous A term and still have
its optimum in exactly the same place — which is precisely what the
dp 3 → 6 run demonstrated, u_opt fixed at 0.063 cm/s while H_min moved
6.00 µm.

## A2 — Reduced parameters and the case for UHPLC

$$h = \frac{H}{d_p}, \qquad \nu = \frac{u\,d_p}{D_m}$$

The A term becomes

$$h_A = \frac{2\lambda d_p}{d_p} = 2\lambda$$

**a pure number**, carrying no particle size at all. That is the whole
argument: in reduced coordinates every well-packed column is the *same
column*, and h_min ≈ 2 is a statement about packing quality rather than
about dimensions.

If h_min is a constant, then

$$H_{min} = h_{min}\,d_p \;\propto\; d_p$$

so plate height scales linearly with particle size, and for a fixed
column length $N = L/H_{min} \propto 1/d_p$. Halving the particle
doubles the plate count. But the Kozeny–Carman result gives

$$\Delta P \;\propto\; \frac{1}{d_p^{2}}$$

so the same halving **quadruples** the backpressure.

**What the trade buys.** Resolution goes as √N, so halving dp buys a
factor of √2 ≈ 1.41 in resolution — or, held at constant resolution, lets
you shorten the column by half and finish in half the time. You pay 4× in
pressure for it. That ratio is the entire engineering case for UHPLC: the
chemistry is unchanged, the column is just smaller and the pump is much
angrier.

## A3 — Injection width by the law of total variance

Let the sample enter uniformly across plates $j = 0 \ldots w-1$. A
molecule starting at plate j has $N - j$ plates left, so conditionally

$$E[t \mid j] = (N - j)(1 + k), \qquad \mathrm{Var}[t \mid j] = (N - j)\,k(1 + k)$$

For j uniform on w values, $E[j] = (w-1)/2$ and
$\mathrm{Var}[j] = (w^{2}-1)/12$. The law of total variance gives

$$\mathrm{Var}[t] = E\left[\mathrm{Var}[t \mid j]\right] + \mathrm{Var}\left[E[t \mid j]\right]$$

$$\sigma^{2} = \left(N - \frac{w-1}{2}\right)k(1+k) \;+\; \frac{w^{2}-1}{12}(1+k)^{2}$$

$$E[t] = \left(N - \frac{w-1}{2}\right)(1+k)$$

**Prediction at N = 100, k = 2, w = 10:**

$$\sigma^{2} = (100 - 4.5)(6) + (8.25)(9) = 573.00 + 74.25 = 647.25
\;\Longrightarrow\; \sigma = 25.44$$

$$E[t] = (95.5)(3) = 286.5$$

**Measured: Sigma 25.4411, first moment 286.50.** Exact.

Verification across the slider range:

| w | Predicted σ² | Measured σ² | Predicted mean | Measured mean |
|---|---|---|---|---|
| 1 | 600.00 | 600.00 | 300.0 | 300.0 |
| 10 | 647.25 | 647.25 | 286.5 | 286.5 |
| 20 | 842.25 | 842.25 | 271.5 | 271.5 |

**Which term is whose.** The first term is the **column's** own
broadening, slightly *reduced* because the average molecule traverses
fewer plates. The second is the **injector's**, and it is pure penalty —
it grows as w² and belongs to no part of the separation. At w = 20 the
injector contributes 299.25 of the 842.25 total variance, 36 % of the
peak's spread, contributed by an instrument component that does no
chemistry at all.

That is the closing point of the exercise: the same "variances add" rule
that built H out of three mechanisms also lets you add the plumbing to
the column, and the plumbing can dominate.

---

## Answer summary

| Item | Answer |
|---|---|
| Q2 | A = 2λdp = 6.0 µm; contains no u; flat trace |
| Q3 | A and B/u survive; stamp reads `no optimum (C = 0)`; capillary GC ⇒ A = 0; CE ⇒ only B |
| Q4 | u_opt = 0.063 unchanged by both; H_min 9.79 → 15.79 (dp) and → 6.79 (λ); (b) under A·v^(1/3), u_opt shifts left and packing moves it |
| Q5 | Dm ×4 ⇒ u_opt 0.063 → 0.126 (×2); H_min → 13.59; Temperature moves B and C_m oppositely; film control lives in GC |
| Q6 | B = 1.2e−5 cm²/s, C = 3.0e−3 s, u_opt = 0.0632 cm/s |
| Q7 | limbs equal at u_opt; 1.897 µm each, under the diamond |
| Q8 | H(u_opt/2) = H(2u_opt) = 10.74; 2× miss 9.7 %, ±20 % miss 0.65 %; err fast because time is 4× asymmetric |
| Q9 | Both H_min = 9.79; H(0.5) = 21.24 vs 12.84; choose B; C decides |
| Q10 | σ 24.49 → 48.99 (×2); relative 0.0816 → 0.0408 (÷2) |
| Q11 | 300 / 150 / 111; asymptote N, divergence at 0; k = 0 reads `n/a (sigma = 0, unretained)` |
| Q12 | As 1.74 / 1.18 / 1.06; ideal profile is already skewed at finite N |
| Q13 | σ 24.49 → 29.02, moment 300.0 → 271.5, N_app 150 → 88; recovery 1.0000; = Wenzel HW1 Q1 |
| A1 | u_opt = √(B/C), H_min = A + 2√(BC), ∂u_opt/∂A = 0; A·u^(1/3) adds (a/3)u^(−2/3) > 0 ⇒ optimum left |
| A2 | h_A = 2λ; H_min ∝ dp, ΔP ∝ 1/dp² |
| A3 | σ² = (N − (w−1)/2)k(1+k) + ((w²−1)/12)(1+k)²; σ = 25.44 at w = 10 |

*All values measured against drylab v0.24.7. Re-measure on any
model-touching release (classroom QA gate 4).*

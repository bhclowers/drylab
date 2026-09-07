# Why H Is Not a Constant — Building the van Deemter Curve One Mechanism at a Time

**Team roles for today** (rotate from last session): Manager keeps the
group on the current question — no running ahead to the simulator.
Recorder writes the group's predictions and reconciliations on this
sheet. Presenter reports at the checkpoints. Reflector notes where the
group's thinking changed.

**How this is graded:** full credit requires, for every numbered
question, your **written prediction before touching any control**, the
**observed result**, and — where they disagree — a sentence on **what
changed in your thinking**. A wrong prediction honestly reconciled earns
full credit; a correct answer with no prediction does not.

**One rule about the equations.** The panel carries a collapsed
**"The equations"** section under each plot. It is not hidden from you —
open it whenever you want. But it only tells you what the formulas
*are*. Every question below asks what they *do*, and that part is on
you.

---

## Where we left the Craig apparatus

In Exercise 1 you found that a band's variance grows in proportion to
the distance it travels, and that the constant of proportionality — the
plate height H — was just the stationary fraction q. It was a **single
number**. Nowhere in it did the speed of the machine appear.

**Q1 — No simulator. Two minutes, as a group.** The Craig apparatus has
no clock: each transfer is instantaneous, complete, and every tube
reaches true equilibrium before the next transfer. List **three things a
real packed column does that the Craig apparatus does not**, and for
each one say whether you'd expect it to make bands wider or narrower.

<div class="answer tall"></div>

**STOP — one sentence from each group before you open the simulator.**

---

## Getting started

Open drylab → **Band shape** → **Mechanisms (van Deemter)** tab. Set the
five sliders to:

| Control | Setting |
|---|---|
| Particle size dp (µm) | 3.0 |
| Packing factor λ (eddy) | 1.00 |
| Diffusion Dm (×10⁻⁵ cm²/s) | 1.0 |
| Cs — stationary-phase MT (ms) | 2.00 |
| Cm — mobile-phase MT (ms) | 1.00 |

Leave **Log velocity axis** checked (it is on by default). Call this
**Setting A**. Note the grey **stamp underneath the plot** — it repeats
every slider value and adds two numbers the panel has worked out for
you. You will use that stamp all period; you never need to export
anything.

**Q2 — By hand first.** The eddy-diffusion term is A = 2·λ·dp. Compute
it for Setting A, with units. Then answer: does your expression contain
the velocity u anywhere, and what should that mean for the shape of the
A trace on the plot?

<div class="answer"></div>

---

## One mechanism at a time

**Q3 — Predict, then run.** Set **both** Cs and Cm to 0. Before you
touch anything: which curves will still be on the plot, and will the
total still have a minimum? Sketch your prediction, then run it and read
what the stamp says at the far right.

<div class="answer tall"></div>

Follow-up — two real columns, one sentence each. (a) An open-tubular GC
capillary has a stationary-phase film on its wall but **no packing**.
Which term must be exactly zero for it, and why? (b) A capillary
electrophoresis column has no packing **and no stationary phase at
all**. Which terms survive there? (Your reading develops exactly this
case.)

<div class="answer"></div>

**Q4 — The one that surprises people.** Restore Cs = 2.00 and
Cm = 1.00. Now predict *before moving anything*: if you make the
particles bigger (dp 3.0 → 6.0), does the velocity at which H is
smallest move left, move right, or stay put? Same question for packing
the column better (λ 1.00 → 0.50). Commit to an answer, then run each
and read u_opt off the stamp.

| Change | Predicted u_opt | Observed u_opt | Observed H_min |
|---|---|---|---|
| dp 3.0 → 6.0 | &nbsp; | &nbsp; | &nbsp; |
| λ 1.00 → 0.50 | &nbsp; | &nbsp; | &nbsp; |

(a) What does the A term control, and what does it *not* control? The
formula that settles this has been in "The equations" the whole time —
find it and say what feature of it explains your observation.

<div class="answer"></div>

(b) Your reading (Wenzel) writes the eddy contribution as **A·v^(1/3)**
and notes that the literature has never settled the question; this
builder draws van Deemter's original flat A. Suppose the v^(1/3) version
is right. Would packing quality then move the optimum velocity? Which
way? (Reason from the shape of the terms — no calculation needed.)

<div class="answer"></div>

**Q5 — Now move the B term.** Return to Setting A, then raise Dm from
1.0 to 4.0 (a hotter, less viscous mobile phase). Predict the direction
u_opt moves and by roughly what factor, then check the stamp.

| | Predicted | Observed u_opt | Observed H_min |
|---|---|---|---|
| Dm 1.0 → 4.0 | &nbsp; | &nbsp; | &nbsp; |

Follow-up. You just quadrupled Dm, and only the B limb moved — yet
"The equations" says Cm physically contains dp²/Dm. The builder's C
sliders are deliberately lumped, so *you* have to supply the coupling:
name one control in the **HPLC** section and one in the **GC** section
that would move Cs or Cm in a real instrument, and identify the one
control that moves **two van Deemter terms at once, in opposite
directions**.

<div class="answer tall"></div>

**Q6 — Earn the number.** "The equations" gives you
u_opt = √(B/C) — so the formula is free. The work is the **units**:
B = 2·γ·Dm with γ = 0.6, but Dm is displayed in units of 10⁻⁵ cm²/s,
and the C sliders are in **ms**. Compute u_opt for Setting A in cm/s,
showing the unit conversions, and compare with the stamp.

<div class="answer tall"></div>

**STOP — instructor checkpoint. Do not go on until your Q6 number
matches the stamp.**

---

## Reading the curve like an operator

**Q7 — Where the optimum actually lives.** Set Cs = 3.00 and Cm = 0.00
(same total C as Setting A, all in one slider). Predict: at what
velocity do the falling B/u limb and the rising Cs·u limb contribute
**equally** to H — and where is that point relative to the diamond?
Then hover both limbs to check, and record the value each contributes
there.

<div class="answer"></div>

**Q8 — Missing the optimum.** Back to Setting A. Predict which mistake
costs more plate height: running at **half** u_opt, or at **double**
u_opt? Commit, then hover the H total at both velocities (the stamp
gives u_opt; double and halve it).

| | u (cm/s) | H (µm) |
|---|---|---|
| u_opt ÷ 2 | &nbsp; | &nbsp; |
| u_opt × 2 | &nbsp; | &nbsp; |

Reconcile what you find. Then the operator's question: if the two
mistakes cost the same H, why does every practical method — your
reading gives GC numbers — deliberately run **above** the optimum
rather than below it?

<div class="answer tall"></div>

**Q9 — Which column would you rather own?** Set the sliders to
**Setting B**: dp = 2.0, λ = 1.90, Cs = 0.50, Cm = 0.50. (Read that as a
finer particle in a badly packed bed.) Record the stamp for both
settings, then hover the bold **H total** curve at u = 0.5 cm/s in each.

| | u_opt (cm/s) | H_min (µm) | H at u = 0.5 cm/s |
|---|---|---|---|
| Setting A (dp 3.0, λ 1.00) | &nbsp; | &nbsp; | &nbsp; |
| Setting B (dp 2.0, λ 1.90) | &nbsp; | &nbsp; | &nbsp; |

First: what do you notice about the two H_min values? Second: if your
job is to run this separation **as fast as possible**, which column do
you want, and which single number in the table told you? Third: which
slider group is responsible for that difference?

<div class="answer tall"></div>

---

## What H does to a peak you can see

Switch to the **Peak shape (overload)** tab. Set: Plates N = 100,
Retention factor k = 2.0, Isotherm curvature = 0.00, Sample load = 1.0,
Injection width = 1, Slow-site tailing τ = 0. Nothing is overloaded
today — the isotherm is perfectly linear, so every effect you see below
is broadening, not distortion.

A column of length L packed to plate height H has N = L/H plates. Making
H smaller and making the column longer are two different routes to the
same N.

**Q10 — Predict, then run.** You are about to change N from 100 to
400 — a fourfold gain, as if you had quartered H. Predict what happens
to the peak's **Sigma** and to its **relative** width (sigma divided by
the first moment). Then read both off the readout table.

| N | Predicted sigma | Observed Sigma | First moment | Sigma ÷ moment |
|---|---|---|---|---|
| 100 | &nbsp; | &nbsp; | &nbsp; | &nbsp; |
| 400 | &nbsp; | &nbsp; | &nbsp; | &nbsp; |

Which of the two got better, and by exactly what factor? Where have you
seen this factor before?

<div class="answer"></div>

**Q11 — Read a formula like a trend.** "The equations" on this tab gives
N_app = N·(1+k)/k. Back at N = 100: **before touching the k slider**,
sketch N_app against k from 0 to 9. Mark on your sketch: what value does
it approach at large k, and what happens as k → 0? Then verify at
k = 0.5, 2.0 and 9.0.

| k | Built-in N | Apparent N_app | First moment |
|---|---|---|---|
| 0.5 | &nbsp; | &nbsp; | &nbsp; |
| 2.0 | &nbsp; | &nbsp; | &nbsp; |
| 9.0 | &nbsp; | &nbsp; | &nbsp; |

Now slide k all the way to 0 and write down exactly what the readout
says. Explain *physically* why this model gives that answer for an
unretained analyte — and what a real column would still do to that peak
that this model leaves out.

<div class="answer tall"></div>

**Q12 — Nothing is overloaded, so why isn't it symmetric?** Return to
k = 2.0. The curvature is still 0.00 and the load is still 1.0. Read
**Asymmetry As (10 %)** and **Ideal-profile As (10 %)**. Then set N to
10, and to 800, reading As each time.

| N | As (10 %) |
|---|---|
| 10 | &nbsp; |
| 100 | &nbsp; |
| 800 | &nbsp; |

Explain the trend using the theorem you met in Exercise 1. What does
this tell you about calling a peak "tailing" because As > 1?

<div class="answer"></div>

**Q13 — Broadening the column is not responsible for.** Homework 1 asks
what a **too-slow injection** does to a GC peak. Answer it with the
simulator: at N = 100, k = 2.0, step **Injection width (plates)** from 1
to 20, watching both Sigma and the First moment.

| Injection width | Sigma | First moment | N_app |
|---|---|---|---|
| 1 | &nbsp; | &nbsp; | &nbsp; |
| 10 | &nbsp; | &nbsp; | &nbsp; |
| 20 | &nbsp; | &nbsp; | &nbsp; |

Two separate things happened. Name both, and say which one a
chromatographer would call an extra-column effect. Check **Mass
recovered** while you are here — what does it rule out as an
explanation?

<div class="answer tall"></div>

---

## Going further — for the ambitious

**A1 — Own the optimum.** Starting from H = A + B/u + C·u, use calculus
to derive u_opt and H_min. Then prove the result you discovered in Q4:
show that ∂u_opt/∂A = 0 exactly. Finally, redo the derivative with
Wenzel's eddy term A·u^(1/3) in place of the flat A and show that your
Q4(b) prediction about the direction of the shift was forced by the
sign of one term.

<div class="answer tall"></div>

**A2 — Why UHPLC exists.** Define the reduced plate height h = H/dp and
reduced velocity ν = u·dp/Dm. Rewrite the A term in these variables and
show it becomes a pure number, independent of particle size. Given that
a well-packed column reaches h_min ≈ 2 whatever its particle size,
explain why H_min scales as dp while column backpressure scales as
1/dp², and what that trade buys.

<div class="answer tall"></div>

**A3 — Variances add, one more time (homework).** In Q13 the injection
spread the sample over the first w plates. Model this: a molecule
entering at plate j only has (N − j) plates left to traverse, and j is
uniform on 0…w−1. Using the law of total variance, derive an expression
for the peak variance in terms of N, k and w. Predict Sigma at w = 10
and N = 100, k = 2, then check it against the readout. State which term
is the column's own broadening and which is the injector's.

<div class="answer tall"></div>

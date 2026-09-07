# From Separatory Funnel to Column — The Craig Apparatus

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

---

## Getting started

Open drylab → **Craig apparatus** tab. Set the controls to:

| Control | Setting |
|---|---|
| D for analyte A | 4.0 |
| D for analyte B | 0.25 |
| Upper (mobile) volume | 1.0 |
| Lower (stationary) volume | 1.0 |
| Number of tubes | 20 |
| Transfers (n) | leave at 0 for now |

You did extractions like this by hand in a separatory funnel. This
machine does the same equilibrate-and-transfer step over and over: each
transfer moves every tube's **upper (mobile) phase** one tube to the
right, then every tube re-equilibrates.

**Q1 — By hand first (no simulator).** For analyte A (D = 4, equal
volumes): what fraction of the analyte sits in the mobile phase of a
tube after equilibration? Write the expression in terms of D and the
volumes, then the number.

<div class="answer"></div>

**Q2 — Predict n = 2.** Starting with everything in tube 0, work out on
paper where analyte A is after **two** transfers. Fill in your predicted
fractions (they must sum to 1):

| | Tube 0 | Tube 1 | Tube 2 |
|---|---|---|---|
| Predicted fraction of A | &nbsp; | &nbsp; | &nbsp; |
| Predicted fraction of B | &nbsp; | &nbsp; | &nbsp; |

*Hint you may use: each transfer either advances the mobile fraction p
or leaves the stationary fraction behind — what family of distribution
is "k advances in n tries"?*

**STOP — show your table to the instructor before running.**

**Q3 — Run n = 2 and reconcile.** Set Transfers to 2 and read the
per-tube table. Record the simulator's fractions next to yours above
(use a different pen/color). Where they differ, what step of your hand
calculation was wrong?

<div class="answer"></div>

---

## Why columns beat funnels

**Q4 — Predict before moving the slider.** As n grows from 5 to 100,
two things happen to each band: its **center moves** and its **width
grows**. Circle one prediction for each and give a reason:

| Quantity | grows like n / like √n / stays fixed | Why |
|---|---|---|
| Position of band center | &nbsp; | &nbsp; |
| Width of the band | &nbsp; | &nbsp; |
| Gap between the A and B centers | &nbsp; | &nbsp; |

**Q5 — Run it.** Set **Number of tubes to 100**, then step Transfers
through the values below. For each, record the center tube of each band
(tube of maximum, from the per-tube table), and estimate each band's
width by counting tubes at roughly half the peak height:

| n | Center of B | Center of A | Gap (tubes) | Width of A (tubes) | Gap ÷ Width |
|---|---|---|---|---|---|
| 5 | &nbsp; | &nbsp; | &nbsp; | &nbsp; | &nbsp; |
| 25 | &nbsp; | &nbsp; | &nbsp; | &nbsp; | &nbsp; |
| 100 | &nbsp; | &nbsp; | &nbsp; | &nbsp; | &nbsp; |

**Q6 — The whole argument in one ratio.** Look at your Gap ÷ Width
column, and at the panel's **"Resolution on the tube axis"** readout at
each n. Both improve with n even though the bands keep getting wider.
Reconcile this with your Q4 predictions: which grows faster, and by what
factor does the ratio improve when n goes up 4× (25 → 100)?

<div class="answer tall"></div>

**Q7 — Where did the Gaussian come from?** At n = 100, switch on the
**normal approximation** overlay. The match is close — yet nothing in
this machine "knows" about Gaussians; it only equilibrates and
transfers. What theorem connects your Q2 distribution to the overlaid
curve, and what has to be large for it to apply?

<div class="answer"></div>

**Q8 — The bridge to chromatography** (whole-class checkpoint). In a
packed column there are no tubes and no discrete transfers — yet we
describe columns with a "number of theoretical plates." State the
mapping in two sentences: what plays the role of one tube, and what
plays the role of one transfer, in a real column?

<div class="answer"></div>

---

## Going further — for the ambitious (advanced undergrad / graduate)

These use the same apparatus, pushed harder. Show derivations; the
simulator is the arbiter, not the argument. (Set **Number of tubes to
250** for this section so nothing runs off the axis.)

**A1 — Own the scaling law.** The panel's readout defines
Rs = |μ_B − μ_A| / [2(σ_A + σ_B)]. For two analytes with mobile
fractions p_A and p_B, write Rs as an explicit function of n (means and
variances of the binomial do all the work), and reduce it for the D = 1
vs D = 4 pair to the cleanest closed form you can. Then test it: record
the panel's Rs at n = 50, 100, and 200 and compare with your formula at
each n. What single number should the ratio of successive readings give,
and does it?

<div class="answer tall"></div>

**A2 — Where should the chemistry sit?** Selectivity is fixed by the
chemistry: suppose D_B/D_A = 4 always. But *where* the pair sits on the
D axis is a choice. Before running: using your A1 expression, argue
where on the axis Rs should be largest — what is being traded as both
D's grow together? Then scan at n = 100, recording the panel's Rs for
each pair:

| (D_A, D_B) | (0.125, 0.5) | (0.25, 1) | (0.5, 2) | (1, 4) | (2, 8) | (4, 16) |
|---|---|---|---|---|---|---|
| Rs | &nbsp; | &nbsp; | &nbsp; | &nbsp; | &nbsp; | &nbsp; |

State where the maximum sits, in terms of the p's rather than the D's —
and connect it to the chromatographer's rule you will meet again in the
HPLC exercises: why is there a *useful window* of retention, with
penalties on both sides?

<div class="answer tall"></div>

**A3 — When you can't change the chemistry, change the instrument.**
The pair (D_A, D_B) = (4, 16) sits badly on the axis — your A2 scan
says so. The D's are thermodynamics; you cannot vote on them. But the
*phase volumes* are yours. Derive how the mobile fraction p depends on
D **and** the volume ratio V_upper/V_lower, solve for the volume ratio
that moves this pair onto your A2 optimum, and verify with the
simulator at n = 100 (report the Rs you recover). Close with the
bridge: in a real column, what plays the role of the volume ratio, and
which instrument parameters move it? (You will meet this quantity as
the phase ratio β, with k′ = K/β.)

<div class="answer tall"></div>

---

## Homework (individual)

Bring numbers, not adjectives — the Craig panel's CSV exports carry the
operating point so every value you report is traceable.

**H1.** For D = 1 and equal volumes, derive the tube of maximum amount
after n transfers, r_max, in terms of n and the mobile-phase fraction p.
Verify with the simulator at n = 50 (also record the fraction in that
tube). Then predict r_max for **D = 3 with the upper volume set to 2.0
and the lower to 1.0**, and verify. If your prediction missed, identify
the exact quantity you computed wrong — this one has a famous trap.

**H2.** Two analytes, D = 1 and D = 4, equal volumes. Using your Q4/Q6
scaling (centers separate ∝ n, widths grow ∝ √n), estimate the smallest
n at which the pair reaches Rs ≈ 1.5. Show the inequality you solved.
Then find the answer empirically with the Transfers slider (report the
"Resolution on the tube axis" readout at your n). Reconcile estimate vs.
observation.

**H3.** In two sentences: using the H2 result, explain why nobody
separates mixtures with 80 sequential funnel extractions — and why a
column, which does effectively thousands of "transfers," is not merely
80 funnels' worth of work for free. What is the cost that √n growth
imposes?

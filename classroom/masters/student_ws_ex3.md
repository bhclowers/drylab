# Fixing a Failed Separation — Resolution Triage

**Team roles for today** (rotate from last session): Manager keeps the
group on the current question — no running ahead to the simulator.
Recorder writes the group's predictions and reconciliations on this
sheet. Presenter reports to the class at the checkpoints. Reflector notes
where the group's thinking changed.

**How this is graded:** full credit requires three things for every
numbered question — your **written prediction before touching any
control**, the **observed result**, and, where they disagree, a sentence
on **what changed in your thinking**. A correct answer with no prediction
earns partial credit; a wrong prediction honestly reconciled earns full
credit.

---

## Getting started

Open drylab and load the scenario — either pick **"Ex 3 — Resolution
triage"** from the *Classroom preset* menu in the HPLC sidebar, or use
the link your instructor gave you (it ends in `?hplc=ex3`).

You are looking at a two-compound separation that has failed. Open the
**Results** tab and record the starting point:

| Quantity (from the Results tab) | Value |
|---|---|
| Resolution Rs (vs prev), second row | &nbsp; |
| Selectivity alpha (vs prev) | &nbsp; |
| Plates N (System table) | &nbsp; |
| k′ of the later peak | &nbsp; |
| Retention time of the later peak (s) | &nbsp; |
| Backpressure (bar) | &nbsp; |

**Q1.** A separation needs Rs ≥ 1.5 to be quantifiable. In one sentence:
what does the chromatogram *look like* that the number Rs is capturing?

<div class="answer"></div>

---

## The three levers

From lecture, resolution factors into three independent-looking terms:

> Rs = (√N / 4) · ((α − 1)/α) · (k′/(1 + k′))

Your instructor will assign your group **one** budget line. You may only
touch the controls on your line:

| Team | Controls you may touch | Controls you may NOT touch |
|---|---|---|
| **N-team** | column length, particle size, flow rate | %B, temperature, solvent B |
| **k-team** | Solvent B (%), temperature | length, particle size, solvent identity |
| **α-team** | Solvent B identity (MeCN ↔ MeOH), then %B to re-tune | length, particle size |

**Q2 — Predict first (nothing gets moved yet).** As a group, write what
your lever will do to each of the four quantities when you push it hard
enough to *fix* the separation. Circle a direction (↑ / ↓ / ≈) and give a
one-line reason for each:

| Quantity | Prediction (↑ / ↓ / ≈) | Why |
|---|---|---|
| Rs | &nbsp; | &nbsp; |
| Retention time of the last peak | &nbsp; | &nbsp; |
| Backpressure | &nbsp; | &nbsp; |
| Which term of the equation you're moving | &nbsp; | &nbsp; |

**STOP — show your predictions to the instructor before running.**

**Q3 — Now run it.** Adjust only your team's controls until Rs ≥ 1.5, or
until you conclude your lever cannot reasonably get there. Record your
best attempt:

| Quantity | Your best attempt |
|---|---|
| Settings you changed (list each, with values) | &nbsp; |
| Rs achieved | &nbsp; |
| Retention time of the last peak (s) | &nbsp; |
| Backpressure (bar) | &nbsp; |

**Q4 — Reconcile.** Where did the outcome differ from your Q2 prediction?
What in your model of the separation changed?

<div class="answer tall"></div>

---

## Class checkpoint — ranking the levers

Each Presenter reports: settings, Rs, time, pressure. Fill in the class
results:

| Team | Rs achieved | Time cost | Pressure cost | Verdict |
|---|---|---|---|---|
| N | &nbsp; | &nbsp; | &nbsp; | &nbsp; |
| k | &nbsp; | &nbsp; | &nbsp; | &nbsp; |
| α | &nbsp; | &nbsp; | &nbsp; | &nbsp; |

**Q5.** One lever fixed the separation for almost nothing; one fixed it
at a price no real pump would survive. Using the *form* of the resolution
equation (which term is under a square root? which term saturates?),
explain why the ranking came out the way it did.

<div class="answer tall"></div>

**Q6.** The k-team likely noticed that alpha moved too, not just k′.
Does that break the claim that the equation has three *independent*
levers? What kind of statement is the resolution equation — a law about
knobs, or a decomposition of a number?

<div class="answer"></div>

---

## The diminishing-returns probe (k-team's encore, everyone watches)

In the **Sweeps** tab, set the sweep to `solvent_percent` → `k_prime`.

**Q7 — Predict:** sketch the shape you expect for the factor
k′/(1 + k′) as k′ grows from 0 to 20. At what k′ is 90 % of the maximum
reached?

<div class="answer"></div>

**Q8 — Run and conclude:** using the sweep and the factor you sketched,
state the practical rule: past roughly what k′ does added retention buy
time instead of resolution?

<div class="answer"></div>

---

## Homework (individual, bring the CSV)

From the **Export** tab at the *original preset condition*, download the
compound-results CSV — note it carries an `operating_point` column;
every number you report below must be traceable to it.

**H1.** Using N (System table), α, and k′₂ from your starting-point
table, compute Rs from the resolution equation. Compare with the table's
Rs. Report both numbers and the percent difference.

**H2.** Predict Rs and the last-peak retention time if the column were
lengthened from 100 mm to 300 mm, using proportionality arguments only
(state them). Then set the length slider to 300 mm and record what the
simulator gives. Reconcile.

**H3.** In two sentences: when is tripling the column length the right
*first* move for a failed separation — and what should be tried first?

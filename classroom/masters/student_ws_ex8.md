# CE Lab: Plates, Peak Shape and the Sample's Own Conductivity

**Team roles for today** (rotate from last session): Manager keeps the
group on the current question, with no running ahead to the simulator.
Recorder writes the group's predictions and reconciliations on this
sheet. Presenter reports to the class at the checkpoints. Reflector notes
where the group's thinking changed.

**How this is graded:** full credit requires three things for every
numbered question: your **written prediction before touching any
control**, the **observed result**, and, where they disagree, a sentence
on **what changed in your thinking**. A correct answer with no prediction
earns partial credit. A wrong prediction honestly reconciled earns full
credit.

| Part | Topic | Minutes |
|---|---|---|
| Getting started | Conditions, current and conductivity | 5 |
| A | Where do the plates come from? | 13 |
| B | Peak shape from the sample's own conductivity | 11 |
| C | A salty sample | 8 |
| D | pK_a, pH and migration order | 6 |
| Wrap-up | Class checkpoint | 2 |

---

## Getting started (5 min)

Open drylab and choose the **CE** tab. Change only these settings:

- **Grid points:** 257. Sharp zone edges need the finer grid. Each run
  takes about 10 s.
- **Composition:** set `concentration_mM` of the three Sample rows
  (potassium K+, sodium Na+, lithium Li+) to **0.1**.

Leave everything else at its default (Capillary length 30 mm, Applied
voltage 500 V, Run time 20 s, Detector position 15 mm, EOF mobility 0).
Press **Run CE simulation**.

Two facts about the injection that you will need: the sample plug is
centered at **6 mm**, so the migration distance to a detector at 15 mm is
ℓ = 9 mm. The plug has a Gaussian profile with a standard deviation of
**σ_inj = 0.57 mm**.

| Quantity | Where to find it | Value |
|---|---|---|
| Field E (V/m) | text line under the electropherogram | &nbsp; |
| Current density j (A/m²) | grey stamp under either plot (`j = …`) | &nbsp; |
| Joule heating (W/m) | text line under the electropherogram | &nbsp; |
| Background pH | text line under the electropherogram | &nbsp; |

| Analyte | Migration time t (s) | Peak width FWHM (s) | N = 5.54 (t / FWHM)² |
|---|---|---|---|
| potassium K+ | &nbsp; | &nbsp; | &nbsp; |
| sodium Na+ | &nbsp; | &nbsp; | &nbsp; |
| lithium Li+ | &nbsp; | &nbsp; | &nbsp; |

**Q1.** The power supply sets the voltage, and the buffer sets the
current. Compute the conductivity of the background electrolyte from
κ = j / E. Then check it: set **Overlay** to *Conductivity*, move the
**Time slice** slider one step to the right of zero, and read the
conductivity well away from the sample plug. (Skip slice 0, which shows
the state before the buffer equilibrium is solved.) Do the two agree?

<div class="answer"></div>

---

## Part A: Where do the plates come from? (15 min)

If diffusion along the capillary were the only source of spreading, the
plate count would be

> N = zeVℓ / (2 k_B T L), with k_B T / e = 0.02569 V at 298 K

where z is the charge, V the applied voltage, ℓ the migration distance and
L the capillary length.

**Q2. Predict first.** Use the equation to predict N for K⁺ at 500 V and
at 1500 V. What does it say happens to N when the voltage triples?

| Quantity | Your prediction |
|---|---|
| N for K⁺ at 500 V (diffusion only) | &nbsp; |
| N for K⁺ at 1500 V (diffusion only) | &nbsp; |
| Predicted ratio N(1500 V) / N(500 V) | &nbsp; |

**STOP: show your predictions to the instructor before running.**

**Q3. Run it.** Set Applied voltage to 1000 V (Run time 12 s), run, then
1500 V (Run time 8 s), run.

| Voltage (V) | t for K⁺ (s) | FWHM for K⁺ (s) | N for K⁺ | Joule heating (W/m) |
|---|---|---|---|---|
| 500 (from the start table) | &nbsp; | &nbsp; | &nbsp; | &nbsp; |
| 1000 | &nbsp; | &nbsp; | &nbsp; | &nbsp; |
| 1500 | &nbsp; | &nbsp; | &nbsp; | &nbsp; |

**Q4. Reconcile.** Independent sources of spreading add as variances.
For K⁺ at 500 V, compute the diffusion variance σ_diff² = 2Dt, with
D = μ_ep k_B T / e and μ_ep = 76.2 × 10⁻⁹ m² V⁻¹ s⁻¹. Compare it with
σ_inj². Which one dominates? Use N = ℓ² / (σ_inj² + σ_diff²) to predict
N at 500 V and compare it with your measurement. Explain why the voltage
barely mattered.

<div class="answer tall"></div>

**Q5. Predict.** Return to 500 V. You will now move the **Detector
position** from 15 mm to 25 mm (Run time 36 s). What is the new ℓ? Using
the variance sum, predict N for K⁺. Will the K⁺ peak width in *seconds*
grow, shrink or stay about the same? Why?

| Quantity | Your prediction |
|---|---|
| New migration distance ℓ (mm) | &nbsp; |
| N for K⁺ | &nbsp; |
| FWHM for K⁺ (↑ / ↓ / ≈), with reason | &nbsp; |

**STOP: show your predictions to the instructor before running.**

**Q6. Run and reconcile.** Record t, FWHM and N for K⁺ at the 25 mm
detector. When the injection dominates the variance, what control
actually raises N, and why does the width in seconds stay nearly fixed?

| Detector (mm) | t for K⁺ (s) | FWHM for K⁺ (s) | N for K⁺ |
|---|---|---|---|
| 25 | &nbsp; | &nbsp; | &nbsp; |

<div class="answer"></div>

---

## Part B: Peak shape from the sample's own conductivity (13 min)

Set Detector position back to 15 mm and Run time to 20 s. In the
Composition table, change the **Tris** row into **imidazole**: name
`imidazole`, mobility_e9 `52.0`, p_ka `7.05` (keep valence 1, 12 mM and
role BGE). Run once with the samples still at 0.1 mM and record:

| Analyte | μ_ep (×10⁻⁹) | t (s) | FWHM (s) | Peak shape (symmetric?) |
|---|---|---|---|---|
| potassium K+ | 76.2 | &nbsp; | &nbsp; | &nbsp; |
| sodium Na+ | 51.9 | &nbsp; | &nbsp; | &nbsp; |
| lithium Li+ | 40.1 | &nbsp; | &nbsp; | &nbsp; |

Imidazolium (μ = 52.0) is now the **co-ion**: the BGE cation that the
sample cations displace to keep each zone electroneutral.

**Q7. Predict.** Each sample ion will be raised to **2 mM**. For each
analyte, decide whether it is faster than, matched to, or slower than the
co-ion. Then predict its peak shape and whether its time at the maximum
moves earlier, later or stays the same.

| Analyte | Faster / matched / slower than imidazolium | Predicted shape (diffuse front + sharp rear, symmetric, or sharp front + diffuse rear) | t at maximum (earlier / later / same) |
|---|---|---|---|
| K⁺ | &nbsp; | &nbsp; | &nbsp; |
| Na⁺ | &nbsp; | &nbsp; | &nbsp; |
| Li⁺ | &nbsp; | &nbsp; | &nbsp; |

**STOP: show your predictions to the instructor before running.**

**Q8. Run it.** Set the three Sample concentrations to 2 and run.

| Analyte | t (s) | FWHM (s) | Peak height (mM) | Observed shape |
|---|---|---|---|---|
| K⁺ | &nbsp; | &nbsp; | &nbsp; | &nbsp; |
| Na⁺ | &nbsp; | &nbsp; | &nbsp; | &nbsp; |
| Li⁺ | &nbsp; | &nbsp; | &nbsp; | &nbsp; |

**Q9. Reconcile.** Explain the K⁺ peak in terms of conductivity and
field: is the field inside the K⁺ zone higher or lower than in the BGE?
What happens to a K⁺ ion that diffuses out ahead of the zone, and to one
that falls behind? Then explain in one sentence why Na⁺ stayed symmetric.

<div class="answer tall"></div>

---

## Part C: A salty sample (10 min)

Keep the imidazole BGE. Change the Composition so the sample is a trace
of K⁺ in a salt solution:

- potassium K+: `0.1` mM
- sodium Na+: `30` mM
- the lithium row becomes chloride: name `chloride Cl-`, valence `-1`,
  mobility_e9 `-79.1`, p_ka `-2`, `30` mM, role Sample

The app will warn that sodium and chloride exceed 10 % of the BGE. Run
anyway. Chloride migrates toward the inlet and never reaches the
detector, so ignore its row in the results table. The 30 mM sodium peak
will dwarf the K⁺ trace: click **sodium Na+** and **chloride Cl-** in the
electropherogram legend to hide them, and the axis rescales to K⁺.

**Q10. Predict.** Compared with K⁺ at 0.1 mM in Part B (your first
table), will the K⁺ peak in the salty sample be wider, narrower or the
same? Taller or shorter? Give the mechanism in one sentence.

<div class="answer"></div>

**STOP: show your predictions to the instructor before running.**

**Q11. Run it.** Record the K⁺ results. Then, with Overlay on
*Conductivity* and Time slice one step right of zero, read the
conductivity at the center of the sample plug and far from it.

| Quantity | Value |
|---|---|
| K⁺ t (s) | &nbsp; |
| K⁺ FWHM (s) | &nbsp; |
| K⁺ peak height (mM) | &nbsp; |
| κ in the sample plug (S/m) | &nbsp; |
| κ in the BGE (S/m) | &nbsp; |

**Q12. Reconcile.** Compute FWHM(salty) / FWHM(Part B) and
κ_sample / κ_BGE. Compare them using ℓ_zone ≈ ℓ_inj κ_sample / κ_BGE.
What is this effect called? The app's warning names electromigration
dispersion. Is that the same mechanism as Part B? Name one change to the
sample preparation that would fix it.

<div class="answer tall"></div>

---

## Part D: pK_a, pH and migration order (6 min)

Keep the imidazole BGE (12 mM). Set Applied voltage to **1000 V** and
Run time to **30 s**. In the Composition table, keep potassium K+ at
0.1 mM as a marker, and change the other two Sample rows:

| name | valence | mobility_e9 | p_ka | concentration_mM | role |
|---|---|---|---|---|---|
| pyridine | 1 | 30.0 | 5.16 | 0.1 | Sample |
| aniline | 1 | 32.5 | 4.8 | 0.1 | Sample |

Pyridine and aniline are weak bases. Only the protonated form carries a
charge, and the mobilities above are for the fully protonated cations.
The fraction protonated and the effective mobility are

> α = 1 / (1 + 10^(pH − pK_a)), μ_eff = α μ_ep

**Q13. Predict.** When both are fully protonated, which cation is faster?
Now use the background pH you recorded at the start (4.93) to fill in the
table. The field at 1000 V is 33,333 V/m and ℓ = 9 mm.

| Analyte | α at pH 4.93 | μ_eff (×10⁻⁹) | Predicted t (s) |
|---|---|---|---|
| pyridine | &nbsp; | &nbsp; | &nbsp; |
| aniline | &nbsp; | &nbsp; | &nbsp; |

Predicted order of arrival: ________________________________

**STOP: show your predictions to the instructor before running.**

**Q14. Run and reconcile.** Record the migration times and the app's
apparent mobilities. Did the order match your prediction? Explain in
one sentence why a slower ion can arrive first.

| Analyte | t (s) | Apparent mobility (×10⁻⁹) |
|---|---|---|
| pyridine | &nbsp; | &nbsp; |
| aniline | &nbsp; | &nbsp; |

<div class="answer"></div>

**Q15. Extend.** At some pH the two effective mobilities are equal and
the peaks co-migrate. Find that pH by setting α μ_ep equal for the two
bases. The BGE pH follows pH = 4.756 + log[c_im / (20 − c_im)], where
c_im is the imidazole concentration in mM. What imidazole concentration
gives the co-migration pH? Set it (round to the nearest mM), run, and
describe what you see.

<div class="answer tall"></div>

---

## Class checkpoint (2 min)

**Q16.** Each Presenter gives one sentence: of the four effects you
measured today (injection-limited plates, electromigration dispersion,
antistacking, pH-controlled selectivity), which would most change how
you prepare and run a real sample, and why?

<div class="answer"></div>

---

## Homework (individual)

The CE section has no CSV export, so **record the full settings for every
run you report** (voltage, run time, detector position, grid points and
the Composition table). Every number must be traceable to a stated set of
conditions.

**H1.** Return to the Getting started conditions (Tris BGE, 0.1 mM
samples, 500 V). Run the detector at 10, 15, 20 and 25 mm (Run time 20,
20, 30 and 36 s). Plot N for K⁺ against ℓ². From the slope, estimate
σ_inj and compare it with 0.57 mm.

**H2.** K⁺ and NH₄⁺ have nearly identical mobilities (76.2 and 76.1 ×10⁻⁹),
but NH₄⁺ is a weak acid with pK_a 9.25. Edit the five Composition rows to:

| name | valence | mobility_e9 | p_ka | concentration_mM | role |
|---|---|---|---|---|---|
| Tris | 1 | 29.5 | 8.076 | 30 | BGE |
| chloride Cl- | -1 | -79.1 | -2 | 10 | BGE |
| potassium K+ | 1 | 76.2 | 14 | 0.1 | Sample |
| ammonium NH4+ | 1 | 76.1 | 9.25 | 0.1 | Sample |
| sodium Na+ | 1 | 51.9 | 14 | 0.1 | Sample |

Sodium stays in as a marker peak. Predict μ_eff for NH₄⁺ at the pH the
app reports, run at detector 15 mm (Run time 24 s) and 25 mm (Run time
44 s), and compute R_s = 1.18 Δt / (FWHM₁ + FWHM₂) for K⁺ and NH₄⁺.
Repeat with chloride at 2 mM. Which pH separates the pair, and why? Look
at the K⁺ peak shape in the 2 mM chloride BGE and explain what changed.

**H3.** At 1500 V the app reported a Joule heating value. Compare it with
the roughly 1 W/m that an air-cooled capillary can remove, and explain
why no heating broadening appeared in Part A. Which two quantities
would you change to make heating matter, and by what factor does the
power per length grow for each?

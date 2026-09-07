# drylab instructor key — v1 (for exercises revision 3, drylab v0.24.1)

Every number below was **measured against drylab v0.24.1** on 2026-08-18;
where a value depends on conditions, the operating point is stated. Slider
values are exact UI settings, so this key doubles as a self-run script:
follow the *Do* lines top to bottom and the screen should show the *Expect*
values. Small deviations (last digit of Rs, ±1 transfer) are normal; a
disagreement in sign, order, or factor-of-two is not — report it.

Conventions: default HPLC column is the Zorbax SB-C18 preset at
**100 × 4.6 mm, 3 µm** (not the 250 × 5 of the physical product — worth
knowing before checking numbers against intuition). GC default column is
30 m × 0.25 mm, d_f 0.25 µm, He, inlet 250 kPa → ambient outlet.

---

## Exercise 1 — Craig apparatus

**Do:** Craig tab. D_A = 4, D_B = 0.25, both volumes 1.0, tubes ≥ 5.
(The worksheet's advanced section sets tubes to 250 — available from
drylab v0.24.3.)

- n = 2 → **Expect** per-tube fractions (tubes 0,1,2): D = 4 gives
  **0.04 / 0.32 / 0.64**; D = 0.25 mirrors it: **0.64 / 0.32 / 0.04**.
  Hand check:

    $$p = \frac{D\,V_u}{D\,V_u + V_l} \;\overset{V_u = V_l}{=}\; \frac{D}{D+1} = 0.8 \ \mathrm{and}\ 0.2, \qquad (q^2,\; 2pq,\; p^2)$$

- Transfers 5 → 25 → 100: centers at n·p separate linearly; widths grow
  as √(npq). At n = 100 the D = 4 band centers near tube 80, D = 0.25
  near tube 20.

- Normal overlay at n = 100: matches closely; the Gaussian is the
  binomial's limit — each transfer is one equilibration = one plate.

**Quantitative answers:**

- D = 1, equal volumes, n = 50: r_max = n·p = **25**, fraction there
  **0.112**. D = 3 with V_upper = 2·V_lower:

    $$p = \frac{D\,V_u}{D\,V_u + V_l} = \frac{3 \cdot 2}{3 \cdot 2 + 1} = \frac{6}{7} = 0.857 \;\Rightarrow\; r_{max} = 50\,p \approx 43$$

  The trap is using D/(D+1) = 0.75 → tube 37–38; the volume-weighted p is
  the lesson.

- D = 1 vs D = 4 (p = 0.5, 0.8): Rs ≈ 1.5 when

    $$n\,\Delta p \;\geq\; 3\,(\sigma_1 + \sigma_2), \qquad 0.3\,n \;\geq\; 2.7\sqrt{n} \;\Rightarrow\; n \approx 81$$

  the slider search should land in the 75–90 range depending on how the
  student reads "resolved."

**Advanced section (worksheet "Going further", added 2026-08-26;
requires drylab ≥ 0.24.3 for the 250-tube axis):**

- **A1 — scaling law.**

    $$R_s = \frac{n\,|\Delta p|}{2\left(\sqrt{n\,p_A q_A} + \sqrt{n\,p_B q_B}\right)} = \frac{|\Delta p|\,\sqrt{n}}{2\left(\sqrt{p_A q_A} + \sqrt{p_B q_B}\right)} \;\overset{p=0.5,\,0.8}{=}\; \frac{0.3\sqrt{n}}{2\,(0.5+0.4)} = \frac{\sqrt{n}}{6}$$

  Panel readouts: **1.18 (n=50), 1.67 (n=100), 2.36 (n=200)** — exact to
  the displayed digits; each doubling multiplies Rs by **√2 = 1.414**.

- **A2 — placement at fixed selectivity** (D_B/D_A = 4, n = 100):

| (D_A, D_B) | (0.125, 0.5) | (0.25, 1) | (0.5, 2) | (1, 4) | (2, 8) | (4, 16) |
|---|---|---|---|---|---|---|
| Rs | 1.41 | 1.67 | **1.77** | 1.67 | 1.41 | 1.11 |

  The ridge is symmetric with its maximum at **(0.5, 2)** — geometric
  mean of the D's at 1, i.e. the p's straddling ½ (⅓ and ⅔). The trade:
  large D's compress both p's toward 1 (Δp collapses faster than the
  widths shrink); small D's mirror it. This is the Craig-machine form of
  the retention *window* — penalties on both sides — that reappears as
  the k/(1+k) saturation in the HPLC triage exercise.

- **A3 — volume rescue.**

    $$p = \frac{D\,V_u}{D\,V_u + V_l} = \frac{D\,(V_u/V_l)}{D\,(V_u/V_l) + 1}$$

  so the effective distribution ratio is D·(V_u/V_l). Moving (4, 16) onto
  the A2 optimum (0.5, 2) needs **V_u/V_l = 1/8** (set upper 1, lower 8 —
  or 0.125 and 1). Verified: Rs recovers to **1.77** at n = 100, the ridge maximum
  exactly. Column bridge: the volume ratio is the **phase ratio β**
  (k′ = K/β), moved in a real column by film thickness / bore (GC) or
  bonded-phase loading and geometry (LC). Accept any consistent pair of
  volumes with the derivation shown.

---

## Exercise 2A — van Deemter term builder

**Do:** Band shape → Mechanisms. Defaults: d_p 3 µm, λ 1.0, D_m 1.0,
C_s 2 ms, C_m 1 ms.

- **Expect at defaults:** A = 6.0 µm, optimum stamp reads
  **u_opt = 0.063 cm/s, H_min = 9.79 µm**.

- C_s = C_m = 0 → only the flat A line and the falling B/u limb remain;
  stamp reads "no optimum (C = 0)".

- Slider table (one change from defaults each time):

| Change | A (µm) | u_opt (cm/s) | H_min (µm) | Reading |
|---|---|---|---|---|
| defaults | 6.0 | 0.063 | 9.79 | — |
| d_p 3 → 6 | **12.0** | 0.063 | 15.79 | A = 2λd_p; C sliders don't move (they're entered directly — that's the discussion hook) |
| λ 1.0 → 0.5 | **3.0** | 0.063 | 6.79 | better packing buys A only |
| D_m 1 → 2 | 6.0 | **0.089** | 11.37 | B doubles; u_opt scales as √D_m |
| C_s 2 → 4 | 6.0 | **0.049** | 10.90 | steeper fast limb, optimum retreats |
| C_m 1 → 0 | 6.0 | 0.077 | 9.10 | flatter fast side |

**Conceptual answers:** open-tubular columns have no A term because there
is no packing (one flow path). The C expressions students should write:
C_s ∝ d_f²/D_s, C_m ∝ d_p²/D_m; in the HPLC section the particle-size
slider moves C_m (and A), temperature moves D_m and thus B and C_m.
"Same H_min, different shape → run the flatter one fast; the number is
the C sum."

**Quantitative:** from the Term curves CSV: A = the constant column
(6.0 µm); B = (b_um · u) at any row (= 1.2×10⁻⁵ cm²/s → 2γD_m ✓);
C = slope of (cs+cm) vs u (= 3 ms). Then

$$u_{opt} = \sqrt{B/C}, \qquad H_{min} = A + 2\sqrt{B\,C}$$

must reproduce the stamp — exact by construction.

---

## Exercise 2 — van Deemter on the HPLC model

**Do:** HPLC, Default preset. Sweeps tab: flow_rate → hetp.

- **Expect:** minimum at **≈ 1.6 mL/min, h_min ≈ 6.0 µm** (= 2·d_p);
  h ≈ 15.4 µm at 0.2 mL/min, ≈ 8.1 µm at 5.0. Operating point on the
  plot: 100×4.6 mm 3 µm, 50 %B MeCN, 25 °C.

- Temperature probe: at 70 °C the minimum shifts right; at 10 °C left
  (through D_m — B up and C down with T).

- Honest framing for "why not run at optimum": at 3 µm the default
  2.0 mL/min *is* near-optimal; the classic run-fast tradeoff appears at
  6 µm or low T.

**Quantitative (fit of the exported sweep CSV, h in µm, F in mL/min):**

$$h(F) = A + \frac{B}{F} + C\,F, \qquad F_{opt} = \sqrt{B/C}, \qquad h_{min} = A + 2\sqrt{B\,C}$$

- 3 µm: **A = 3.00, B = 2.44, C = 0.922** → F_opt = 1.63, h_min = 6.00 ✓.
- 6 µm: **A = 6.00 (×2), B = 2.44 (unchanged), C = 3.69 (×4)** →
  F_opt = 0.81, h_min = 12.0. Backpressure at 2 mL/min: **173 bar (3 µm)
  vs 43 bar (6 µm)** — the ΔP ∝ 1/d_p² sentence writes itself.

- (If students fit in velocity units instead of flow, coefficients rescale
  but F_opt·(conversion) and h_min must agree — either is acceptable if
  they say which they did.)

---

## Exercise 3 — Resolution triage

**Do:** HPLC preset **Ex 3** (`?hplc=ex3`). Results tab.

- **Expect on open:** acetophenone then p-chlorophenol,
  **Rs = 0.65, α = 1.031**, N ≈ 16 500, k′₂ = 2.08, backpressure 173 bar,
  tR₂ ≈ 98 s.

- Team outcomes (one lever at a time from the preset):

| Team | Move | Expect |
|---|---|---|
| k | 50 → 44 %B | **Rs 2.58** (α also rises to 1.115 — say so up front) |
| α | MeOH, 65 %B | **Rs 7.79, α 1.57** — chemistry wins |
| N | 300 mm | Rs 1.14, 520 bar, tR₂ 295 s |
| N | 300 mm **and** 1.5 µm | **Rs 1.56 at 2082 bar** — technically fixed, physically absurd |

**Quantitative answers:** fundamental equation with the table's N, α, k′₂:

$$R_s = \frac{\sqrt{N}}{4}\cdot\frac{\alpha - 1}{\alpha}\cdot\frac{k'_2}{1 + k'_2} = \frac{\sqrt{16521}}{4}\cdot\frac{0.031}{1.031}\cdot\frac{2.082}{3.082} = \mathbf{0.654}$$

which matches the table's Rs to three figures at this preset (both widths are the model's, and
extra-column terms are small here; if a student's numbers disagree, the
usual cause is using k′₁ or unsorted rows). Length prediction: 0.65·√3 =
1.13 vs measured **1.14** ✓, at 3× time and 3× pressure — tripling the
column is the right *first* move approximately never.

---

## Exercise 4 — General elution problem

**LC leg. Do:** preset **Ex 4** (`?hplc=ex4`, all 22 compounds, 30 %B).

- **Expect:** k′ spans **1.28 → 352**, last peak ≈ **188 min**. At 70 %B:
  k′ 0.22 → 5, everything inside **3 min**, early crowd. The student
  gradient should land every k′ in roughly 1–10; the Band-tracks view
  shows each k′ collapsing as the front arrives.

- Dwell forensics: defaults 200 + 200 µL at 2 mL/min → expected delay

    $$t_{dwell} = \frac{V_{dwell}}{F} = \frac{400\ \mu L}{2\ \mathrm{mL/min}} = 12\ \mathrm{s}$$

  visible as the offset between
  the programmed and delivered profiles in the Solvent-profile view.

**GC leg. Do:** preset **Ex 4** (`?gc=ex4`, C7–C15 on SLB-5ms), 120 °C;
then Programmed tab with the default program (40 °C, 1 min hold, →300 °C
by 27 min); Compare tab.

- **Expect isothermal:** 9 peaks, 87 s → 1047 s (17.4 min), early alkanes
  crowded, C15 flat.

- **Expect programmed:** peaks 139 s → 869 s with near-constant widths
  (mean τ ≈ 0.5 s).

- Peak capacity from the exported results:

    $$n_c^{iso} = 1 + \frac{\sqrt{\bar{N}}}{4}\,\ln\frac{t_{last}}{t_{first}} \approx \mathbf{259}, \qquad n_c^{prog} = 1 + \frac{t_{last} - t_{first}}{4\,\bar{\tau}} \approx \mathbf{381}$$

  → ratio ≈ **1.5×**, and the
  qualitative win (late peaks sharp, run 3 min shorter) is bigger than
  the ratio alone suggests. Accept ±10 % — the formulas are estimates and
  students may average N differently.

---

## Exercise 5 — GC retention: polarity and thermodynamics

**Do:** presets ex5a → ex5b → (phase to Wax) → ex5c.

- **Ladder (ex5a):** Octane < Decane < Dodecane at 120 °C; k roughly
  multiplies per 2 CH₂ (read k from the table).

- **Polarity trio (ex5b):** on SLB-5ms **2-Octanone < Decane < 1-Octanol**;
  switch phase to Wax → **Decane < 2-Octanone < 1-Octanol**. The alkane
  vaults to first; the alcohol anchors last on both.

- **Golay coda** (Decane, SLB-5ms, 120 °C, ambient outlet): **H_min is the
  same for all three gases, 0.137 mm** — the Golay minimum depends on
  geometry and k, not the carrier; the *carrier* sets where and how
  forgiving it is: u_opt ≈ **20 (N₂), 48 (He), 69 (H₂) cm/s**, and at the
  pressure ceiling H ≈ 0.86 (N₂) vs 0.25 (He) vs 0.42 mm (H₂, at
  210 cm/s). "Which to buy": H₂ runs 3× faster than N₂ at equal H.

**Quantitative (Wax, 4 points at 100/120/140/160 °C, k from the table):**

| Solute | k @ 100/120/140/160 °C | slope (K) | −ΔH° (kJ/mol) |
|---|---|---|---|
| Decane | 0.339 / 0.202 / 0.130 / 0.088 | 3623 | **30.1** |
| 1-Octanol | 8.055 / 3.451 / 1.652 / 0.869 | 6001 | **49.9** |
| Tridecane | 1.868 / 0.932 / 0.511 / 0.303 | 4901 | 40.8 |
| 2-Octanone | 1.862 / 0.963 / 0.542 / 0.328 | 4680 | 38.9 |

The fit model and its reading:

$$\ln k = -\frac{\Delta H^{\circ}}{R}\cdot\frac{1}{T} + \mathrm{const} \;\Rightarrow\; \Delta H^{\circ} = -R \times \mathrm{slope}$$

ΔH ranking (alcohol ≫ alkane on Wax) matches the Round-2 order argument.
**Co-elution (ex5c):** intersection of the two 4-point fits predicts
**≈ 101 °C** (exact model crossing ≈ 102 °C; the fit is over a curved
line, so ±2 °C is success). Walking the oven slider down from 120 °C, the
pair merges near 100–105 °C and inverts below.

---

## Exercise 6 — CE

**Do:** CE tab, defaults (30 mm, 500 V, detector 15 mm, run 20 s,
K⁺/Na⁺/Li⁺ over acetate/Tris). Press Run.

- **EOF = 0, expect peaks at ≈ 8.3 s (K⁺), 11.7 s (Na⁺), 14.7 s (Li⁺)** —
  crystal-radius order inverted by hydration. Mobility arithmetic: the
  plug is centered at **6 mm**, so use 9 mm to the detector:

    $$t = \frac{L_{det}}{\mu_{app}\,E}, \qquad \mu_{app} = \mu_{ep} + \mu_{EOF}, \qquad E = \frac{500\ \mathrm{V}}{30\ \mathrm{mm}} = 16.7\ \mathrm{kV/m}$$

  giving 7.1 / 10.4 / 13.5 s for the 9 mm path — order and
  ratios right, simulated times ~15 % longer because effective mobilities
  in the real electrolyte are below the infinite-dilution table values.
  A student who reconciles order + ratio + the systematic has fully
  succeeded.

- Acetate: **in the default composition acetate is BGE — it fills the
  capillary and shows no peak.** The first (intended) stumble is
  realizing this and switching its role to Sample in the composition
  editor. Then, with the plug at 6 mm (9 mm to the detector): at EOF 60,
  μ_app = +17.6 → **≈ 31 s — outside the 20 s default run**; within 20 s
  needs μ_app ≥ 27, i.e. **EOF ≥ ≈ 70**; within a 60 s run needs only
  μ_app ≥ 9, i.e. **EOF ≥ ≈ 52** (bracket at 50–55 on the slider). Any
  consistent pair of (EOF, run time) with the arithmetic shown is full
  credit. Expect simulated arrivals ~10–15 % later than the arithmetic,
  as with the cations.

- N vs V: run 500/1000/1500 V and compute, from the on-screen migration
  time and FWHM,

    $$N = 5.54\,\left(\frac{t}{w_{1/2}}\right)^{2}$$ Expect roughly linear growth until the Joule
  report's ΔT becomes non-trivial at the top of the range; the break
  point depends on the composition, so grade the *method* (linear check +
  correlation with the Joule number), not a specific voltage.

---

## Exercise 7 — Overload and asymmetry

**Do:** Band shape → Peak shape, defaults (N = 100, k = 2, curvature 0,
load 1).

- **Baseline: t_max = 297, As = 1.18 for BOTH curves, N_app = 150** vs
  built-in 100 (the moment-based N of a negative binomial exceeds the
  plate number — a good early "what does this number assume?" moment).
  N = 1000: As_ideal falls to **1.05**.

- Curvature/tau grid (N = 100, k = 2, load 1 unless stated):

| Setting | t_max | As | N_app | Reading |
|---|---|---|---|---|
| linear | 297 | 1.18 | 150 | baseline |
| χ = +1 | 291 | 1.29 | 147 | tailing begins, max walks early |
| χ = +2 | 285 | 1.43 | 143 | |
| χ = +5 | **267** | **1.99** | 126 | strong Langmuir |
| χ = −0.4 | 300 | 1.11 | 151 | fronting: As *below* baseline, max late |
| χ = −0.85 | 303 | **1.06** | 151 | clamp limit; announced in a callout |
| τ = 15, χ = 0 | **310** | 1.26 | **120** | kinetic tailing: max moves LATE |
| curv 0.5 × load 4 | 285 | 1.43 | 143 | ≡ χ = 2 — curvature×load is the coupling |
| curv 0.5 × load 10 | 267 | 1.99 | 126 | ≡ χ = 5 |

- Diagnostic answer: cut the load — overload As collapses toward 1.18,
  kinetic As doesn't; and overload moves t_max *early* while slow-site τ
  moves it *late*. Two observables, fully separating the mechanisms.

- QC design answer: the load ladder drops N_app 150 → 126 (−16 %) on an
  unchanged column; at slightly higher load the −20 % flag fires. The
  saving readouts: As rose and t_max moved *earlier* — a degraded column
  (kinetic tailing) shows As rising with t_max moving *later* and no load
  dependence.

- CSV answers (χ = +2): As from the exported points ≈ 1.43 ✓; the
  Langmuir tail decays toward the linear-isotherm retention (n ≈ 300)
  because the most dilute part of the band travels at the linear
  velocity — the tail *points at* the analytical tR; the front carries
  the isotherm (shock position moves with load).

---

## If a number disagrees

Check, in order: (1) the preset actually loaded (the URL param spelling);
(2) a control drifted from the stated operating point — every exported
CSV carries its operating-point stamp for exactly this comparison;
(3) the version (this key: v0.24.1). If all three check out, the
disagreement is real and worth reporting — several numbers in this key
exist because writing it caught errors in the exercises.

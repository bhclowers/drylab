# classroom/ — the POGIL exercise program

Everything needed to continue developing the classroom materials lives in
this folder: the design logic, the current masters, the rendering
pipelines, the QA gates, and the work remaining. This folder is part of
the DEVELOPMENT tree only — the publication builder's explicit include
list does not carry it, so nothing here can reach the public repo.

## Source materials (required, not shipped here)

Authoring sessions need Wenzel's Separation Science POGIL unit, which
lives in Brian's Claude project (not duplicated into this repo — third-
party course materials): SeparationSciLearningObjectives.pdf, the
In-Class and Out-of-Class Problems, the Instructor's Manual, and the
Text. The exercises are mapped against these; every "Wenzel linkage"
line in the exercises document points into them.

## The design logic (what makes these POGIL, not "play with the sim")

1. **Predict → Simulate → Reconcile → Extend.** Every question commits a
   written prediction BEFORE a control moves; the simulator adjudicates,
   never replaces, the reasoning. The grading contract is stated to
   students: a wrong prediction honestly reconciled earns full credit; a
   correct answer with no prediction does not.
2. **Presets state the problem, never the solution.** Classroom presets
   (URL: `?hplc=ex3`, `?gc=ex5a`… — see the table in the exercises doc)
   seed chemistry only (analytes, phase, T, %B, solvent); geometry and
   pneumatics stay default.
3. **Measurement before delivery.** Every number in a deliverable was
   generated against a stated drylab version with its operating point.
   Writing the instructor key IS the acceptance test for the exercises —
   the key pass has caught classroom-breaking defects three separate
   times (slider-unreachable answers, a BGE ion asked for as a peak, a
   sim-vs-arithmetic systematic). Never ship a scenario the key hasn't
   reproduced.
4. **Traceability.** Homework requires the exported CSVs, which carry
   operating-point stamps; "attach your CSV" is also "state your
   conditions."
5. **Instructor-note facts become student discovery questions.** E.g.
   α moving with %B is the triage worksheet's Q6, not a stated caveat;
   the negative binomial's intrinsic right-skew is the overload
   exercise's baseline-literacy opener.

## Current state (all against drylab v0.24.6; key values cite v0.24.1+,
   still valid — nothing the exercises touch changed since)

| Deliverable | Master | Rendered | Status |
|---|---|---|---|
| Exercises rev. 3 (9 exercises: 1, 2A, 2, 3, 4, 5, 6, 7 + coverage map) | masters/drylab_pogil_exercises_v3.md | rendered/…v3.pdf | CURRENT (v1/v2 superseded; do not extend them) |
| Instructor key v1 (self-run format, 13 typeset equations) | masters/drylab_instructor_key_v1.md | rendered/…key_v1.pdf | CURRENT; incl. Craig advanced answers |
| Worksheet Ex 1 (Craig, + advanced A1–A3) | masters/student_ws_ex1.md | rendered/… ex1_craig.pdf + .docx | BUILT |
| Worksheet Ex 3 (triage) | masters/student_ws_ex3.md | rendered/…ex3_SAMPLE.pdf | BUILT (template exemplar) |
| Worksheet + key 2A rev 2 (trends design, Wenzel-anchored, needs v0.24.7 app) | masters/student_ws_ex2a.md + masters/key_ex2a.md | rendered/…ex2a.pdf | CURRENT (rev 1 superseded same session; anchors measured at v0.24.7) |
| Worksheets 2, 4, 5, 6, 7 | — | — | REMAINING (Ex 5 one-sheet-vs-two undecided) |
| Worksheet + key 8 (CE lab after the CE lectures: injection-limited N, EMD with imidazole co-ion, antistacking; 45 min) | masters/student_ws_ex8.md + masters/key_ex8.md | rendered/…ex8_ce.pdf + …key_ex8.pdf | CURRENT (measured at v0.24.7, validation/ex8/; students read conductivity at time slice 1, see issues.md) |

## Worksheet template rules (derived from the two exemplars)

Strip from the exercises doc: instructor keys/notes, measured expected
values, Wenzel-linkage rationale, coverage map. Add: team roles
(Manager/Recorder/Presenter/Reflector), the grading contract in student
terms, record-the-starting-point tables, Predict tables physically
BEFORE Run tables with a bolded **STOP** checkpoint, class-checkpoint
tables, bordered answer boxes (`<div class="answer">` /
`class="answer tall"`), homework requiring the stamped CSV. Advanced
sections ("Going further") are derivation-first with the simulator as
arbiter.

## Rendering pipelines (tools/)

- `render_worksheet.py master.md out.pdf` — worksheet stylesheet
  (header, boxes, tables).
- `render_key.py key.md out.pdf` — key stylesheet + OFFLINE typeset math:
  `$$…$$` blocks → matplotlib mathtext → vector SVG, pre-flight-parsed.
  mathtext dialect: `\geq` not `\ge`, `\overset` not `\xrightarrow`,
  no `\!`.
- `build_worksheet_docx_ex1.js` — the Ex 1 Word build (docx npm);
  answer boxes as single-cell tables, real header/footer. Use as the
  pattern for further docx versions.
- Markdown traps (hit and fixed; details in ../.context/memory/
  learnings.md 2026-08-26): equations inside bullets need 4-space
  indentation; a `- ` item after indented content needs a preceding
  blank line; lists after a bold lead line need a blank line.

## QA gates — run ALL of these on every rendered deliverable

1. **No-leakage** (worksheets only): whitespace-normalize extracted PDF
   text, assert the instructor key's answer values for that exercise are
   ABSENT (line wraps false-negative naive probes).
2. **UI-reference presence**: control labels and readout names quoted in
   the sheet must exist in the shipped notebook (grep drylab_nb.py).
3. **Raster inspection**: rasterize at least one dense page and look at
   it — text extraction misses layout defects (collapsed lists), and
   layout inspection misses text defects; both are required.
4. **Version stamp**: the key states the drylab version its numbers were
   measured against; re-measure on any model-touching release.

## Key measured anchors the exercises depend on (operating points in the
   key; re-verify if the model changes)

Ex 3 preset opens Rs 0.65 (acetophenone/p-chlorophenol, 50 %B, default
100×4.6 mm 3 µm column); triage levers 2.58 / 7.79 / 1.56@2082 bar.
Ex 4 LC: k′ 1.28–352 at 30 %B. GC peak capacity 259→381. Ex 5 polarity
orders flip SLB-5ms↔Wax; co-elution Tridecane/2-Octanone on Wax ≈102 °C.
Golay H_min = 0.137 mm for ALL carriers (gas-independent), u_opt
20/48/69 cm/s N₂/He/H₂. CE: plug at 6 mm (9 mm path), sim ~10–15 % slower
than infinite-dilution arithmetic, acetate must be switched to Sample.
Craig advanced: Rs = √n/6; A2 ridge peaks (0.5, 2) at 1.77; volume
ratio 1/8 rescues (4, 16). Overload grid χ +1/+2/+5 → As 1.29/1.43/1.99.

## Remaining work and open sub-decisions

1. Worksheets 2A, 2, 4, 5, 6, 7 in the template (7 with its curvature/
   τ diagnostic pair; 2A one-mechanism-at-a-time). **Sub-decision for
   Brian: Ex 5 (three presets) as one sheet or two.**
2. Word versions of further worksheets as requested (pattern exists).
3. Keep the key in lockstep: every new worksheet's numbers enter the key
   in the same self-run Do/Expect format, measured first.
4. Parked (issues.md): `?tab=` deep links — do NOT wire worksheet
   "Getting started" lines to tab links until that issue is resolved;
   preset links (`?hplc=`, `?gc=`) are safe and already in the docs.

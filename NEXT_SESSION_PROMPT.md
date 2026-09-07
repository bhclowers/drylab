# Next session — state as of 2026-08-27 (v0.24.7)

**Shipped this session:** v0.24.7 — "The equations" accordions on Craig,
GC, and both Band shape tabs (statics-only content rule, decisions.md);
"Log velocity axis" checkbox on the van Deemter builder (default on,
positivity-guarded); Peak-shape N_app readout guarded at sigma = 0. Dist
artifact: dist/drylab_wasm_nb_v0_24_7.py (old one retired). Bandshape
validation suite PASS; full notebook executed headlessly via
`asyncio.run(app.embed())` (see learnings.md — this is the new standard
post-edit gate).

**Classroom:** Exercise 2A rev 2 delivered (worksheet + key, masters and
rendered in classroom/; requires the v0.24.7 app). Trends design:
equations published in accordions, questions interrogate behaviour
(crossover, symmetric miss, eddy controversy per Wenzel's A·v^(1/3),
N_app trend with the k=0 edge, Wenzel Homework 1 Q1 tie-in). All three
QA gates clean; anchors measured at v0.24.7.

**Brian must still:** deploy v0.24.7 (content-sync + rebuild publish repo
via tools/build_publish_repo.py) and run the three-click live test; the
worksheet assumes the deployed app shows the accordions and log axis.

**Open docket:** worksheets 2, 4, 5, 6, 7 (Ex 5 one-sheet-vs-two
undecided); HPLC + CE equations blocks (issues.md); ?tab= remains PARKED
(do not reattempt without same-session live-site click testing); Craig
Ex 1 launch-link and per-tube-table defects in Brian's revised sheet
(flagged 2026-08-27, his master to fix); fold H = q derivation into the
Craig key (Q6/Q8 extension) — worked material exists in
craig_worked_solutions_rev.md.

"""Measures every value the Exercise 8 key quotes, against the installed drylab, using the
app's own readout logic (harness.run). Results merge into key_values.json.

Run in sections, each under a minute at 257 grid points:
    python3 measure_ex8.py A      # Part A: voltage and detector-position runs
    python3 measure_ex8.py BC     # Parts B and C: imidazole co-ion, salty sample
    python3 measure_ex8.py kappa  # conductivities at time slice 1, and j
    python3 measure_ex8.py H2     # homework H2: K+/NH4+ in Tris/chloride at two pH values

Conductivities are read at time slice 1 (t ~ 0.03 s), not slice 0: drylab v0.24.7 saves
the hydronium STARTING GUESS (pH 7) as slice 0, so pH and conductivity at slice 0 are
wrong (see .context/memory/issues.md). The march itself is unaffected.
"""
import copy
import json
import os
import sys

import numpy as np

from harness import DEFAULT, run, with_conc

sys.path.insert(0, "/home/claude/bhclowers/drylab")
import drylab  # noqa: E402
from drylab.ce import CEConditions, CESpecies, grid_positions, simulate_cze  # noqa: E402

P = 257
OUT = "key_values.json"

BASE = with_conc(DEFAULT, 0.1)                         # Tris BGE, 0.1 mM samples
IMID = copy.deepcopy(BASE)
IMID[1] = ["imidazole", 1, 52.0, 7.05, 12.0, "BGE"]    # co-ion swap for Parts B and C


def salty(nacl_mm):
    """Part C: trace K+ in NaCl, imidazole BGE (the Li+ row becomes chloride)."""
    return [IMID[0], IMID[1], ["potassium K+", 1, 76.2, 14.0, 0.1, "Sample"],
            ["sodium Na+", 1, 51.9, 14.0, nacl_mm, "Sample"],
            ["chloride Cl-", -1, -79.1, -2.0, nacl_mm, "Sample"]]


def h2(cl_mm):
    """Homework H2 as worded on the worksheet: Tris/chloride BGE, Na+ kept as a marker."""
    return [["Tris", 1, 29.5, 8.076, 30.0, "BGE"], ["chloride Cl-", -1, -79.1, -2.0, cl_mm, "BGE"],
            ["potassium K+", 1, 76.2, 14.0, 0.1, "Sample"],
            ["ammonium NH4+", 1, 76.1, 9.25, 0.1, "Sample"],
            ["sodium Na+", 1, 51.9, 14.0, 0.1, "Sample"]]


def kappa_at_slice1(rows):
    cond = CEConditions(length_m=0.03, voltage_v=500, n_points=P, t_final_s=20.0, save_every=3)
    sp = [CESpecies(r[0], (r[1],), (r[2] * 1e-9,), (r[3],)) for r in rows]
    x = grid_positions(cond)
    c = np.zeros((len(rows), P))
    for i, r in enumerate(rows):
        c[i] = r[4] if r[5] == "BGE" else r[4] * np.exp(-((x - 0.006) / 0.0008) ** 2)
    f = simulate_cze(sp, c, cond)
    k1 = f.conductivity[:, 1]
    return {"plug_S_per_m": round(float(k1.max()), 4), "bge_S_per_m": round(float(k1[-1]), 4),
            "j_A_per_m2": round(float(f.current_density), 1),
            "E_V_per_m": round(cond.field_v_per_m, 1), "slice1_t_s": round(float(f.times_s[1]), 3),
            "slice0_bge_S_per_m_DEFECT": round(float(np.median(f.conductivity[:, 0])), 4)}


SECTIONS = {
    "A": lambda: {
        "A_start_500V_det15": run(BASE, pts=P),
        "A_1000V": run(BASE, V=1000, t_s=12, pts=P),
        "A_1500V": run(BASE, V=1500, t_s=8, pts=P),
        "A_det10": run(BASE, t_s=20, det_mm=10, pts=P),
        "A_det20": run(BASE, t_s=30, det_mm=20, pts=P),
        "A_det25": run(BASE, t_s=36, det_mm=25, pts=P),
    },
    "BC": lambda: {
        "B_imid_0p1": run(IMID, pts=P),
        "B_imid_2": run(with_conc(IMID, 2.0), pts=P),
        "C_nacl_10": run(salty(10.0), pts=P),
        "C_nacl_30": run(salty(30.0), pts=P),
    },
    "kappa": lambda: {
        "kappa_tris_0p1": kappa_at_slice1(BASE),
        "kappa_imid_0p1": kappa_at_slice1(IMID),
        "kappa_nacl_10": kappa_at_slice1(salty(10.0)),
        "kappa_nacl_30": kappa_at_slice1(salty(30.0)),
    },
    "H2": lambda: {
        f"H2_Cl{cl:g}_det{det}": run(h2(cl), pts=P, det_mm=det, t_s=t)
        for cl in (10.0, 2.0) for det, t in ((15, 24), (25, 44))
    },
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in SECTIONS:
        raise SystemExit(f"usage: python3 measure_ex8.py {{{'|'.join(SECTIONS)}}}")
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    res.update({"drylab_version": drylab.__version__, "grid_points": P,
                "operating_point": "L 30 mm, 500 V unless stated, plug 1/e half-width 0.8 mm "
                                   "centered at 0.2 L (6 mm), EOF 0, save_every 3"})
    res.update(SECTIONS[sys.argv[1]]())
    json.dump(res, open(OUT, "w"), indent=1)
    print("section", sys.argv[1], "written to", OUT)

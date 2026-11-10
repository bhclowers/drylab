"""Exercise 8 key figures: what students see on screen, drawn with the app's own plot classes
(CEElectropherogramPlot, CEProfilePlot) and the arguments drylab_nb.py passes them, in the
default "Studio (default)" theme with legends on. BGE traces start hidden, as in the app.

Static export needs kaleido plus a Chromium:
    BROWSER_PATH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome python3 figures_ex8.py SECTION
Sections (each under a minute at 257 points): A, B, C, D, H
Output: classroom/masters/fig_ex8/*.png (referenced by key_ex8.md).
The one non-app figure, H1 (N against l^2), is the plot students are asked to make by hand.
"""
import copy
import json
import os
import sys
from dataclasses import replace

import numpy as np

from harness import DEFAULT, simulate, with_conc
from measure_ex8 import BASE, IMID, h2, salty, weak_bases

sys.path.insert(0, "/home/claude/bhclowers/drylab")
from drylab.plotting.ce import CEElectropherogramPlot, CEProfilePlot  # noqa: E402
from drylab.plotting.config import PlotConfig  # noqa: E402

OUT = "/home/claude/bhclowers/drylab/classroom/masters/fig_ex8"
os.makedirs(OUT, exist_ok=True)
P = 257
CFG = replace(PlotConfig.from_theme("Studio (default)"), show_legend=True)
W, SCALE = 900, 2


def bge_names(rows):
    return {r[0] for r in rows if r[5] == "BGE"}


def epg(name, rows, det_mm=15.0, also_hide=(), field=None, **kw):
    """Electropherogram exactly as the app draws it (whole run at the detector node).
    also_hide reproduces a student clicking a trace off in the legend."""
    f = field if field is not None else simulate(rows, pts=P, **kw)[0]
    node, traces = f.detector_trace(det_mm)
    fig = CEElectropherogramPlot(
        f.times_s, traces, f.species_names, hidden=bge_names(rows) | set(also_hide),
        detector_position_mm=float(f.position_mm[node]),
        current_density=f.current_density, config=CFG, title=None).figure()
    fig.write_image(f"{OUT}/{name}.png", width=W, height=CFG.height, scale=SCALE)
    return f


def profile(name, f, rows, k, overlay="conductivity"):
    """Spatial profile at time slice k with the conductivity overlay, as the app draws it."""
    fig = CEProfilePlot(
        f.position_mm, f.concentrations[:, :, k], f.species_names,
        overlay_values=f.conductivity[:, k], overlay=overlay, hidden=bge_names(rows),
        current_density=f.current_density, capillary_length_mm=float(f.position_mm.max()),
        config=CFG, title=None).figure()
    fig.write_image(f"{OUT}/{name}.png", width=W, height=CFG.height, scale=SCALE)


def section_a():
    f = epg("a1_start_500V", BASE)
    profile("a2_start_profile_slice1", f, BASE, k=1)
    epg("a3_1000V", BASE, V=1000, t_s=12)
    epg("a4_1500V", BASE, V=1500, t_s=8)
    epg("a5_det25", BASE, det_mm=25.0, t_s=36)


def section_b():
    epg("b1_imid_0p1", IMID)
    epg("b2_imid_2", with_conc(IMID, 2.0))


def section_c():
    rows = salty(30.0)
    f = epg("c1_salty_30", rows)
    # what students see after clicking sodium Na+ and chloride Cl- off in the legend (the sheet says to)
    epg("c1b_salty_30_Na_hidden", rows, also_hide=("sodium Na+", "chloride Cl-"), field=f)
    profile("c2_salty_profile_slice1", f, rows, k=1)


def section_h():
    # H1: the plot students make by hand, from the measured (displayed) values
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = json.load(open("key_values.json"))
    keys = [("A_det10", 4), ("A_start_500V_det15", 9), ("A_det20", 14), ("A_det25", 19)]
    l2 = np.array([l * l for _, l in keys], float)
    n = np.array([5.54 * (d[k]["potassium K+"]["t_mig_s"] / d[k]["potassium K+"]["fwhm_s"]) ** 2
                  for k, _ in keys])
    slope = float(l2 @ n / (l2 @ l2))
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    xx = np.linspace(0, 400, 50)
    ax.plot(xx, slope * xx, color="#6E6E6E", ls="--", lw=1.6,
            label=f"fit through origin, slope {slope:.2f} mm$^{{-2}}$")
    ax.plot(l2, n, "o", color="#1F4E79", ms=8, label="K$^+$, measured")
    ax.set_xlabel(r"$\ell^2$ (mm$^2$)"); ax.set_ylabel("N for K$^+$")
    ax.set_xlim(0, 400); ax.set_ylim(0, 1150)
    ax.legend(loc="upper left", frameon=False, fontsize=11.5)
    fig.tight_layout(); fig.savefig(f"{OUT}/h1_N_vs_l2.png", dpi=200); plt.close(fig)
    epg("h2a_pH838_det25", h2(10.0), det_mm=25.0, t_s=44)
    epg("h2b_pH922_det25", h2(2.0), det_mm=25.0, t_s=44)


def section_d():
    epg("d1_weak_bases_pH493", weak_bases(12.0), V=1000, t_s=30)
    epg("d2_weak_bases_pH402", weak_bases(3.0), V=1000, t_s=30)


SECTIONS = {"A": section_a, "B": section_b, "C": section_c, "D": section_d, "H": section_h}
if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in SECTIONS:
        raise SystemExit(f"usage: figures_ex8.py {{{'|'.join(SECTIONS)}}}")
    SECTIONS[sys.argv[1]]()
    print("section", sys.argv[1], "figures written to", OUT)

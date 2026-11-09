"""Exercise 8 measurement harness: reproduces the drylab_nb.py CE cell logic exactly
(plug at 0.2 L with 1/e half-width 0.8 mm, detector_trace, FWHM from saved times,
apparent mobility from plug center to detector node) so key values match the app."""
import sys, time, json
import numpy as np
sys.path.insert(0, "/home/claude/bhclowers/drylab")
from drylab.ce import CEConditions, CESpecies, grid_positions, simulate_cze, joule_report
import drylab

def run(rows, L_mm=30, V=500, t_s=20, pts=129, det_mm=15.0, eof=0.0):
    cond = CEConditions(length_m=L_mm / 1000, voltage_v=float(V), n_points=pts,
                        t_final_s=float(t_s), eof_mobility=eof * 1e-9, save_every=3)
    sp = [CESpecies(r[0], (r[1],), (r[2] * 1e-9,), (r[3],)) for r in rows]
    x = grid_positions(cond); c = np.zeros((len(rows), pts))
    mu_app = [r[2] * 1e-9 + cond.eof_mobility for r in rows if r[5] == "Sample"]
    cen = (0.2 if sum(mu_app) >= 0 else 0.8) * cond.length_m
    for i, r in enumerate(rows):
        c[i] = r[4] if r[5] == "BGE" else r[4] * np.exp(-((x - cen) / 0.0008) ** 2)
    t0 = time.time(); f = simulate_cze(sp, c, cond); wall = time.time() - t0
    node, tr = f.detector_trace(det_mm)
    out = {"wall_s": round(wall, 1), "det_node_mm": round(float(f.position_mm[node]), 2)}
    k = f.times_s.size - 1
    P, dT, warn = joule_report(float(np.median(f.conductivity[:, k])), cond.field_v_per_m, cond.diameter_m)
    out["joule_W_per_m"] = round(P, 3); out["dT_K"] = round(dT, 3); out["joule_warn"] = bool(warn)
    out["pH"] = round(float(np.median(-np.log10(f.hydronium[:, k] / 1000.0))), 2)
    out["dt_save_s"] = round(float(np.median(np.diff(f.times_s))), 4)
    for i, r in enumerate(rows):
        if r[5] == "BGE": continue
        s = tr[i]
        if s.max() <= 1e-9: out[r[0]] = "did not elute"; continue
        j = int(np.argmax(s)); half = s.max() / 2; ab = np.where(s >= half)[0]
        w = float(f.times_s[ab[-1]] - f.times_s[ab[0]]) if ab.size > 1 else 0.0
        dist = (float(f.position_mm[node]) - float(f.position_mm[np.argmax(f.concentrations[i, :, 0])])) / 1000
        t = float(f.times_s[j])
        # asymmetry at 10 % height (rear/front half-widths), plus mean-time moments
        a10 = np.where(s >= 0.1 * s.max())[0]
        front = t - float(f.times_s[a10[0]]); rear = float(f.times_s[a10[-1]]) - t
        out[r[0]] = {"t_mig_s": round(t, 2), "mu_app": round(dist / (t * cond.field_v_per_m) * 1e9, 1),
                     "fwhm_s": round(w, 2), "height_mM": round(float(s.max()), 3),
                     "N_5.54": round(5.54 * (t / w) ** 2) if w > 0 else None,
                     "As10_rear_over_front": round(rear / front, 2) if front > 0 else None,
                     "trace_still_rising_at_end": bool(s[-1] > 0.5 * s.max())}
    return out

DEFAULT = [["acetate", -1, -42.4, 4.756, 20.0, "BGE"], ["Tris", 1, 29.5, 8.076, 12.0, "BGE"],
           ["potassium K+", 1, 76.2, 14.0, 1.0, "Sample"], ["sodium Na+", 1, 51.9, 14.0, 1.0, "Sample"],
           ["lithium Li+", 1, 40.1, 14.0, 1.0, "Sample"]]
def with_conc(rows, c):
    return [r[:4] + [c if r[5] == "Sample" else r[4], r[5]] for r in rows]
if __name__ == "__main__":
    print("drylab", drylab.__version__)
    for pts in (129, 257):
        print(pts, json.dumps(run(with_conc(DEFAULT, 0.1), pts=pts)))

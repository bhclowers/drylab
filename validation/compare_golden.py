"""Compare the Python port against the JS reference golden dump.

Chartered validation run (decision 2026-08-03: keep permanently). Reads
``golden.json`` (produced by ``node dump_golden.js``), recomputes every case
with ``drylab.compute``, and reports the maximum relative error per output.

Exit status: 0 if every value agrees within RTOL, 1 otherwise, with every
failing (case, quantity) named — no silent aggregation of failures.

Usage:
    cd validation && node dump_golden.js > golden.json
    python compare_golden.py [golden.json]
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

# Make the package importable when run from validation/ without installation.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from drylab import SimulationInputs, compound_signal, compute

RTOL = 1e-12  # double precision, same formulae -> agreement should be to ulps
SERIES_RTOL = 1e-9  # exp() of large negatives; slightly looser

SOLVENT_KEY = {"acetonitrile": "Acetonitrile", "methanol": "Methanol"}

# golden name -> attribute on Results
SCALAR_MAP = {
    "voidTime": "void_time",
    "openTubeFlowVelocity": "open_tube_flow_velocity",
    "chromatographicFlowVelocity": "chromatographic_flow_velocity",
    "interstitialFlowVelocity": "interstitial_flow_velocity",
    "eluentViscosity": "eluent_viscosity",
    "diffusionCoefficient": "diffusion_coefficient",
    "reducedFlowVelocity": "reduced_flow_velocity",
    "reducedPlateHeight": "reduced_plate_height",
    "backpressure": "backpressure",
    "hetp": "hetp",
    "theoreticalPlates": "theoretical_plates",
    "dwellVolume": "dwell_volume",
    "dwellTime": "dwell_time",
    "finalTime": "final_time",
    "postTubingVolume": "post_tubing_volume",
}
COLUMN_MAP = {
    "columnArea": "area",
    "columnVolume": "volume",
    "columnTotalPorosity": "total_porosity",
    "columnVoidVolume": "void_volume",
}
COMPOUND_MAP = {"kPrime": "k_prime", "tR": "t_r", "sigma": "sigma", "w": "w"}


def rel_err(ref: float, got: float) -> float:
    if ref == got:
        return 0.0
    denom = max(abs(ref), abs(got), 1e-300)
    return abs(ref - got) / denom


def main(path: str) -> int:
    golden = json.loads(Path(path).read_text())
    failures: list[str] = []
    worst: dict[str, float] = {}
    n_values = 0

    for idx, case in enumerate(golden["cases"]):
        gin = case["inputs"]
        inputs = SimulationInputs(
            flow_rate=gin["flowRate"],
            solvent_percent=gin["solventPercent"],
            temperature=gin["temperature"],
            secondary_solvent=SOLVENT_KEY[gin["solvent"]],
        )
        res = compute(inputs)
        label = (
            f"case {idx} ({gin['solvent']}, {gin['flowRate']} mL/min, "
            f"{gin['solventPercent']}%, {gin['temperature']}C)"
        )

        def check(name: str, ref: float, got: float, rtol: float = RTOL) -> None:
            nonlocal n_values
            n_values += 1
            if ref is None or (isinstance(ref, float) and math.isnan(ref)):
                failures.append(f"{label}: {name}: reference value is null/NaN")
                return
            e = rel_err(float(ref), float(got))
            worst[name] = max(worst.get(name, 0.0), e)
            if e > rtol:
                failures.append(
                    f"{label}: {name}: ref={ref!r} got={got!r} rel_err={e:.3e}"
                )

        for gname, attr in SCALAR_MAP.items():
            check(gname, case["outputs"][gname], getattr(res, attr))
        for gname, attr in COLUMN_MAP.items():
            check(gname, case["outputs"][gname], getattr(res.column, attr))

        if len(case["compounds"]) != len(res.compounds):
            failures.append(
                f"{label}: compound count ref={len(case['compounds'])} "
                f"got={len(res.compounds)}"
            )
            continue
        for gcomp, pcomp in zip(case["compounds"], res.compounds):
            if gcomp["name"] != pcomp.name:
                failures.append(
                    f"{label}: compound order ref={gcomp['name']!r} got={pcomp.name!r}"
                )
                continue
            for gname, attr in COMPOUND_MAP.items():
                check(
                    f"compound.{gname}", gcomp[gname], getattr(pcomp, attr)
                )

        series = case.get("phenolSeriesIntegerSeconds")
        if series is not None:
            t = np.arange(inputs.initial_time, res.final_time, 1.0)
            if len(t) != len(series):
                failures.append(
                    f"{label}: series length ref={len(series)} got={len(t)}"
                )
            else:
                got = compound_signal(res, res.compounds[0], t)
                errs = np.array(
                    [rel_err(r, g) for r, g in zip(series, got)]
                )
                n_values += len(series)
                worst["phenolSeries"] = max(
                    worst.get("phenolSeries", 0.0), float(errs.max())
                )
                bad = np.nonzero(errs > SERIES_RTOL)[0]
                if bad.size:
                    j = int(bad[0])
                    failures.append(
                        f"{label}: series diverges at t={t[j]}s "
                        f"ref={series[j]!r} got={got[j]!r} rel_err={errs[j]:.3e} "
                        f"({bad.size} points beyond tolerance)"
                    )

    print(f"Compared {n_values} values across {len(golden['cases'])} cases.")
    print("Worst relative error per quantity:")
    for name in sorted(worst):
        print(f"  {name:32s} {worst[name]:.3e}")
    if failures:
        print(f"\nFAIL: {len(failures)} disagreement(s):")
        for msg in failures:
            print("  " + msg)
        return 1
    print("\nPASS: Python port agrees with JS reference within tolerance.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "golden.json"))

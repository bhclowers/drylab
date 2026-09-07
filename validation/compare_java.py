"""Compare the Python port against the Java harness oracle.

Chartered validation run (decision 2026-08-04). The Java harness
(``HplcHarness.java``) lifts the compute logic out of the original applet;
it is a validation oracle only — the shipped product is pure Python and has
no Java dependency at runtime.

Trust protocol: ``--trust-check`` first verifies the harness reproduces the
JS-validated isocratic goldens (``golden.json``). Gradient numbers are only
meaningful if that passes.

Usage:
    javac -d /tmp/harness HplcHarness.java
    java -cp /tmp/harness HplcHarness > golden_java.json
    python compare_java.py            # full comparison
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drylab import ElutionMode, SimulationInputs, compute
from drylab.gradient import GradientProgram

# Same formulae, same doubles: agreement should be at ulp level. The gradient
# march is a long sequential accumulation, so error compounds slightly more.
RTOL_SCALAR = 1e-12
RTOL_GRADIENT = 1e-9

SOLVENTS = {0: "Acetonitrile", 1: "Methanol"}

SCALAR_MAP = {
    "voidTime": "void_time",
    "openTubeVelocity": "open_tube_flow_velocity",
    "interstitialVelocity": "interstitial_flow_velocity",
    "chromatographicVelocity": "chromatographic_flow_velocity",
    "eluentViscosity": "eluent_viscosity",
    "backpressure": "backpressure",
    "diffusionCoefficient": "diffusion_coefficient",
    "reducedFlowVelocity": "reduced_flow_velocity",
    "reducedPlateHeight": "reduced_plate_height",
    "hetp": "hetp",
    "theoreticalPlates": "theoretical_plates",
    "tubingTimeBroadening": "tubing_time_broadening",
    "endTime": "final_time",
}


def rel_err(ref: float, got: float) -> float:
    if ref == got:
        return 0.0
    return abs(ref - got) / max(abs(ref), abs(got), 1e-300)


def build_inputs(gin: dict) -> SimulationInputs:
    mix = tuple(zip(gin["compounds"], gin["concentrations"]))
    kwargs = dict(
        flow_rate=gin["flowRate"],
        solvent_percent=gin["solventBFraction"] * 100.0,
        temperature=gin["temperature"],
        secondary_solvent=SOLVENTS[gin["solventB"]],
        injection_volume=gin["injectionVolume"],
        time_constant=gin["timeConstant"],
        post_tubing_length=gin["tubingLength"],
        # Harness emits mils, the core's storage unit (UI presents mm).
        post_tubing_diameter=gin["tubingDiameter"],
        sample_mix=mix,
        column_overrides=(
            ("length", gin["columnLength"]),
            ("particle_size", gin["particleSize"]),
        ),
    )
    if gin["gradientMode"]:
        kwargs["elution_mode"] = ElutionMode.GRADIENT
        # The interactive step budget is a UI policy, not physics. Disable it
        # here so the port reproduces the reference on every case, including
        # the deliberately pathological ones (decision 2026-08-04).
        kwargs["march_step_budget"] = None
        kwargs["gradient_program"] = GradientProgram.from_rows(
            [(t, p) for t, p in gin["gradientProgram"]],
            mixing_volume=gin["mixingVolume"],
            non_mixing_volume=gin["nonMixingVolume"],
        )
    else:
        kwargs["mixing_volume"] = gin["mixingVolume"]
        kwargs["non_mixing_volume"] = gin["nonMixingVolume"]
    return SimulationInputs(**kwargs)


def trust_check(golden_js: Path, golden_java: Path) -> int:
    """Verify the Java harness reproduces the JS-validated isocratic goldens."""
    js = json.loads(golden_js.read_text())["cases"]
    jv = [
        c
        for c in json.loads(golden_java.read_text())["cases"]
        if c["label"] == "isocratic" and c["inputs"]["tubingLength"] == 0
    ]
    index = {
        (
            c["inputs"]["solventB"],
            c["inputs"]["flowRate"],
            round(c["inputs"]["solventBFraction"], 6),
            c["inputs"]["temperature"],
        ): c
        for c in jv
    }
    solv = {"acetonitrile": 0, "methanol": 1}
    pairs = [
        ("voidTime", "voidTime"),
        ("eluentViscosity", "eluentViscosity"),
        ("backpressure", "backpressure"),
        ("theoreticalPlates", "theoreticalPlates"),
        ("diffusionCoefficient", "diffusionCoefficient"),
    ]
    worst = 0.0
    failures = []
    for c in js:
        i = c["inputs"]
        key = (
            solv[i["solvent"]],
            i["flowRate"],
            round(i["solventPercent"] / 100.0, 6),
            i["temperature"],
        )
        jc = index.get(key)
        if jc is None:
            failures.append(f"no Java counterpart for {key}")
            continue
        for a, b in pairs:
            e = rel_err(c["outputs"][a], jc["outputs"][b])
            worst = max(worst, e)
            if e > RTOL_SCALAR:
                failures.append(f"{key} {a}: rel_err={e:.3e}")
        for idx, comp in enumerate(c["compounds"]):
            for a, b in (("kPrime", "kPrime"), ("tR", "tR"), ("sigma", "sigma")):
                e = rel_err(comp[a], jc["outputs"][b][idx])
                worst = max(worst, e)
                if e > RTOL_SCALAR:
                    failures.append(f"{key} {comp['name']} {a}: rel_err={e:.3e}")
    print(f"[trust check] Java harness vs JS goldens: worst rel_err {worst:.3e}")
    if failures:
        print(f"[trust check] FAIL ({len(failures)} disagreements):")
        for m in failures[:10]:
            print("  " + m)
        return 1
    print("[trust check] PASS - harness is a trustworthy oracle")
    return 0


def main() -> int:
    here = Path(__file__).resolve().parent
    golden_java = here / "golden_java.json"
    golden_js = here / "golden.json"
    if not golden_java.is_file():
        raise FileNotFoundError(
            f"{golden_java} missing; run: javac -d /tmp/harness HplcHarness.java "
            "&& java -cp /tmp/harness HplcHarness > golden_java.json"
        )

    status = 0
    if golden_js.is_file():
        status |= trust_check(golden_js, golden_java)
    else:
        print("[trust check] SKIPPED - golden.json absent (run dump_golden.js)")

    cases = json.loads(golden_java.read_text())["cases"]
    worst: dict[str, float] = {}
    failures: list[str] = []
    n_values = 0
    n_iso = n_grad = 0

    for idx, case in enumerate(cases):
        gin = case["inputs"]
        gout = case["outputs"]
        is_grad = gin["gradientMode"]
        rtol = RTOL_GRADIENT if is_grad else RTOL_SCALAR
        label = f"case {idx} ({case['label']})"

        java_tr = gout["tR"]
        if any(v is None for v in java_tr):
            # The harness marks non-elution as null; the Python port raises.
            # Confirm it refuses rather than returning a wrong number.
            try:
                compute(build_inputs(gin))
            except Exception as e:
                if type(e).__name__ != "NonElutingCompoundError":
                    failures.append(
                        f"{label}: expected NonElutingCompoundError, got "
                        f"{type(e).__name__}: {e}"
                    )
                else:
                    print(f"{label}: non-eluting case correctly refused")
            else:
                failures.append(
                    f"{label}: Java reports non-elution but Python returned a result"
                )
            continue

        res = compute(build_inputs(gin))
        if is_grad:
            n_grad += 1
        else:
            n_iso += 1

        def check(name: str, ref, got) -> None:
            nonlocal n_values
            n_values += 1
            if ref is None or (isinstance(ref, float) and math.isnan(ref)):
                failures.append(f"{label}: {name}: reference null/NaN")
                return
            e = rel_err(float(ref), float(got))
            key = ("gradient." if is_grad else "isocratic.") + name
            worst[key] = max(worst.get(key, 0.0), e)
            if e > rtol:
                failures.append(
                    f"{label}: {name}: java={ref!r} py={got!r} rel_err={e:.3e}"
                )

        for jname, attr in SCALAR_MAP.items():
            check(jname, gout[jname], getattr(res, attr))
        check("totalPorosity", gout["totalPorosity"], res.column.total_porosity)
        check("voidVolume", gout["voidVolume"], res.column.void_volume)
        check("tubingVolume", gout["tubingVolume"], res.post_tubing_volume)

        for i, cr in enumerate(res.compounds):
            check(f"kPrime[{cr.name}]", gout["kPrime"][i], cr.k_prime)
            check(f"tR[{cr.name}]", gout["tR"][i], cr.t_r)
            check(f"sigma[{cr.name}]", gout["sigma"][i], cr.sigma)
            check(f"w[{cr.name}]", gout["w"][i], cr.w)

        if is_grad and "gradientProfile" in gout:
            prof = res.gradient_profile
            jprof = gout["gradientProfile"]
            if len(jprof) != len(prof):
                failures.append(
                    f"{label}: profile length java={len(jprof)} py={len(prof)}"
                )
            else:
                errs = [rel_err(j[1], float(p[1])) for j, p in zip(jprof, prof)]
                n_values += len(errs)
                worst["gradient.profile"] = max(
                    worst.get("gradient.profile", 0.0), max(errs)
                )
                bad = [k for k, e in enumerate(errs) if e > rtol]
                if bad:
                    k = bad[0]
                    failures.append(
                        f"{label}: gradient profile diverges at point {k} "
                        f"(t={jprof[k][0]:.4f} min): java={jprof[k][1]!r} "
                        f"py={float(prof[k][1])!r} rel_err={errs[k]:.3e} "
                        f"({len(bad)} points beyond tolerance)"
                    )

    print(
        f"\nCompared {n_values} values across {n_iso} isocratic and "
        f"{n_grad} gradient cases."
    )
    print("Worst relative error per quantity family:")
    families: dict[str, float] = {}
    for k, v in worst.items():
        fam = k.split("[")[0]
        families[fam] = max(families.get(fam, 0.0), v)
    for k in sorted(families):
        print(f"  {k:40s} {families[k]:.3e}")

    if failures:
        print(f"\nFAIL: {len(failures)} disagreement(s):")
        for m in failures[:25]:
            print("  " + m)
        return 1
    print("\nPASS: Python port agrees with the Java oracle within tolerance.")
    return status


if __name__ == "__main__":
    sys.exit(main())

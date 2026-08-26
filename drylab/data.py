"""Reference data tables for the HPLC simulator.

Ported from the JavaScript reference (mlibby/hplc_simulator):
``hplc_globals.js`` (solvents, viscosity fit parameters) and the column
preset embedded in ``hplc_column.js``. The compound table (22 analytes) is
extracted programmatically from the ORIGINAL Java applet's ``Globals.java``
(HPLC Simulator v1.1.3, Boswell/Carr/Stoll; vendored under
``validation/reference_java/``) — the JS port carried only 5 of these, and
those 5 are byte-identical between the two sources (verified 2026-08-04).

Provenance of the numbers, per the reference source comments:

* Eluent-viscosity fit parameters — acetonitrile/water: Chen & Horvath,
  Analytical Methods and Instrumentation 1993, 1, 213-222; methanol/water:
  fit of 1-bar data in J. Chromatogr. A 1210 (2008) 30-44.
* Compound retention coefficients follow the parameterization
  ``log10(k'_w) = km*T + kb`` and ``S = -(sm*T + sb)`` with T in Celsius.

This module is data only: no computation, no side effects on import.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class ViscosityParameters:
    """Coefficients of the binary-mixture viscosity fit (see formulae.eluent_viscosity)."""

    a: float
    b: float
    c: float
    d: float
    e: float
    f: float


@dataclass(frozen=True)
class Solvent:
    """An organic modifier (solvent B). ``molecular_weight`` in g/mol."""

    name: str
    molecular_weight: float
    viscosity: ViscosityParameters


@dataclass(frozen=True)
class RetentionCoefficients:
    """Per-compound, per-solvent LSS-style coefficients (T in Celsius)."""

    km: float
    kb: float
    sm: float
    sb: float


@dataclass(frozen=True)
class CompoundRecord:
    """Static properties of an analyte. ``molar_volume`` in cm^3/mol."""

    name: str
    molar_volume: float
    retention: Mapping[str, RetentionCoefficients]  # keyed by solvent name


@dataclass(frozen=True)
class ColumnPreset:
    """Column geometry and packing. length/diameter mm, particle_size um."""

    name: str
    length: float
    diameter: float
    particle_size: float
    interparticle_porosity: float
    intraparticle_porosity: float
    van_deemter_a: float
    van_deemter_b: float
    van_deemter_c: float


PRIMARY_SOLVENTS: tuple[str, ...] = ("Water",)

SECONDARY_SOLVENTS: Mapping[str, Solvent] = MappingProxyType(
    {
        "Acetonitrile": Solvent(
            name="Acetonitrile",
            molecular_weight=41.0,
            viscosity=ViscosityParameters(
                a=-3.476, b=726.0, c=-5.414, d=1566.0, e=-1.762, f=929.0
            ),
        ),
        "Methanol": Solvent(
            name="Methanol",
            molecular_weight=32.0,
            viscosity=ViscosityParameters(
                a=-4.597, b=1211.0, c=-5.961, d=1736.0, e=-6.215, f=2809.0
            ),
        ),
    }
)

COMPOUNDS: Mapping[str, CompoundRecord] = MappingProxyType(
    {
        "n-benzyl formamide": CompoundRecord(
            name="n-benzyl formamide",
            molar_volume=156.1,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.003731062, kb=0.769127502, sm=0.001962312, sb=-1.950157208
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.00893, kb=1.54084, sm=0.007655, sb=-2.693812
                    ),
                }
            ),
        ),
        "benzylalcohol": CompoundRecord(
            name="benzylalcohol",
            molar_volume=125.6,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.00364158, kb=0.870975072, sm=0.001538701, sb=-1.801193074
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.008879, kb=1.643379, sm=0.00751, sb=-2.603915
                    ),
                }
            ),
        ),
        "phenol": CompoundRecord(
            name="phenol",
            molar_volume=103.4,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.007051397, kb=1.222652803, sm=0.004948239, sb=-2.157819856
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.010465, kb=1.714002, sm=0.00904, sb=-2.66885
                    ),
                }
            ),
        ),
        "3-phenyl propanol": CompoundRecord(
            name="3-phenyl propanol",
            molar_volume=170.0,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.005175387, kb=1.617423196, sm=0.004245094, sb=-2.711627278
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.012422, kb=2.682599, sm=0.010667, sb=-3.544294
                    ),
                }
            ),
        ),
        "acetophenone": CompoundRecord(
            name="acetophenone",
            molar_volume=140.4,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.006113393, kb=1.615282733, sm=0.004190421, sb=-2.419171414
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.009257, kb=2.098172, sm=0.008684, sb=-2.981032
                    ),
                }
            ),
        ),
        "benzonitrile": CompoundRecord(
            name="benzonitrile",
            molar_volume=122.7,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.008118482, kb=1.759520682, sm=0.006344149, sb=-2.581132813
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.009409, kb=1.995681, sm=0.009057, sb=-2.971312
                    ),
                }
            ),
        ),
        "p-chlorophenol": CompoundRecord(
            name="p-chlorophenol",
            molar_volume=124.3,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.009910541, kb=2.006666967, sm=0.009176534, sb=-3.110178571
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.015142, kb=2.752714, sm=0.013319, sb=-3.575982
                    ),
                }
            ),
        ),
        "nitrobenzene": CompoundRecord(
            name="nitrobenzene",
            molar_volume=122.7,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.009433757, kb=2.074051745, sm=0.008291834, sb=-2.909075892
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.010864, kb=2.277843, sm=0.009471, sb=-2.982885
                    ),
                }
            ),
        ),
        "methyl benzoate": CompoundRecord(
            name="methyl benzoate",
            molar_volume=151.2,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.0077323, kb=2.116364506, sm=0.006053077, sb=-2.911497882
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.011888, kb=2.754816, sm=0.010739, sb=-3.478031
                    ),
                }
            ),
        ),
        "anisole": CompoundRecord(
            name="anisole",
            molar_volume=128.1,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.008804318, kb=2.2070705, sm=0.007554149, sb=-2.941605639
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.011362, kb=2.587045, sm=0.009682, sb=-3.103432
                    ),
                }
            ),
        ),
        "benzene": CompoundRecord(
            name="benzene",
            molar_volume=96.0,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.008529343, kb=2.208069224, sm=0.007114051, sb=-2.82653686
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.010915, kb=2.5743, sm=0.009507, sb=-3.003558
                    ),
                }
            ),
        ),
        "p-nitrotoluene": CompoundRecord(
            name="p-nitrotoluene",
            molar_volume=144.9,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.010705359, kb=2.565390235, sm=0.009864271, sb=-3.433694873
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.012887, kb=2.900254, sm=0.011005, sb=-3.522154
                    ),
                }
            ),
        ),
        "p-nitrobenzyl chloride": CompoundRecord(
            name="p-nitrobenzyl chloride",
            molar_volume=165.8,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.012956701, kb=2.804538425, sm=0.012986999, sb=-3.866695802
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.014804, kb=3.063453, sm=0.013295, sb=-3.802081
                    ),
                }
            ),
        ),
        "toluene": CompoundRecord(
            name="toluene",
            molar_volume=118.2,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.010041886, kb=2.738254098, sm=0.009005662, sb=-3.393491059
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.0131, kb=3.230992, sm=0.010959, sb=-3.547073
                    ),
                }
            ),
        ),
        "benzophenone": CompoundRecord(
            name="benzophenone",
            molar_volume=206.8,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.011069419, kb=3.087847385, sm=0.010362441, sb=-4.064139779
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.01561, kb=3.814708, sm=0.01448, sb=-4.572059
                    ),
                }
            ),
        ),
        "bromobenzene": CompoundRecord(
            name="bromobenzene",
            molar_volume=119.3,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.011273051, kb=2.941762836, sm=0.010618543, sb=-3.651869929
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.015204, kb=3.539528, sm=0.013731, sb=-3.937992
                    ),
                }
            ),
        ),
        "naphthalene": CompoundRecord(
            name="naphthalene",
            molar_volume=147.6,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.012795634, kb=3.296888486, sm=0.012596045, sb=-4.112896456
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.017658, kb=3.996277, sm=0.015853, sb=-4.364601
                    ),
                }
            ),
        ),
        "ethylbenzene": CompoundRecord(
            name="ethylbenzene",
            molar_volume=140.4,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.011878845, kb=3.278713293, sm=0.01150122, sb=-4.00434081
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.016026, kb=3.915079, sm=0.014007, sb=-4.212582
                    ),
                }
            ),
        ),
        "p-xylene": CompoundRecord(
            name="p-xylene",
            molar_volume=140.4,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.011333502, kb=3.257874421, sm=0.01022372, sb=-3.911260542
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.015301, kb=3.89882, sm=0.012295, sb=-4.091578
                    ),
                }
            ),
        ),
        "p-dichlorobenzene": CompoundRecord(
            name="p-dichlorobenzene",
            molar_volume=137.8,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.01247399, kb=3.351026587, sm=0.011894773, sb=-4.06721018
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.016725, kb=4.042718, sm=0.014898, sb=-4.384667
                    ),
                }
            ),
        ),
        "propylbenzene": CompoundRecord(
            name="propylbenzene",
            molar_volume=162.6,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.012995521, kb=3.811104371, sm=0.012122284, sb=-4.521888293
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.017711, kb=4.572339, sm=0.014763, sb=-4.776607
                    ),
                }
            ),
        ),
        "n-butylbenzene": CompoundRecord(
            name="n-butylbenzene",
            molar_volume=184.8,
            retention=MappingProxyType(
                {
                    "Acetonitrile": RetentionCoefficients(
                        km=-0.013247488, kb=4.268938682, sm=0.011228978, sb=-4.916062651
                    ),
                    "Methanol": RetentionCoefficients(
                        km=-0.019604, kb=5.195287, sm=0.015945, sb=-5.293528
                    ),
                }
            ),
        ),
    }
)

COLUMN_PRESETS: Mapping[str, ColumnPreset] = MappingProxyType(
    {
        "Agilent Zorbax SB-C18": ColumnPreset(
            name="Agilent Zorbax SB-C18",
            length=100.0,
            diameter=4.6,
            particle_size=3.0,
            interparticle_porosity=0.4,
            intraparticle_porosity=0.4,
            van_deemter_a=1.0,
            van_deemter_b=5.0,
            van_deemter_c=0.05,
        ),
    }
)

# The default sample mix shipped with the reference simulator:
# (name, concentration in MICROMOLAR).
#
# Unit provenance: the Java applet's Concentration field is labelled uM
# (ChemicalDialog.java) and its chromatogram y-axis is "Signal, moles/liter"
# with automatic SI prefixing. Injected amount w = (injection_volume uL -> L)
# x concentration (umol/L) = umol; signal = w / (sqrt(2 pi) sigma F) with
# sigma in s and F in L/s, giving umol/L. So both the stored concentrations
# and the plotted signal are in umol/L (= uM).
DEFAULT_SAMPLE_MIX: tuple[tuple[str, float], ...] = (
    ("phenol", 5.0),
    ("3-phenyl propanol", 25.0),
    ("acetophenone", 40.0),
    ("p-chlorophenol", 15.0),
    ("p-nitrotoluene", 10.0),
)

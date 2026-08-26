"""drylab - Python port of the mlibby/hplc_simulator core (isocratic HPLC).

Derived from the JavaScript conversion by Michael C. Libby of the HPLC
Simulator by Paul Boswell, Peter Carr, and Dwight Stoll (hplcsimulator.org).
License: CC BY-NC-SA 3.0 US, inherited from the reference.
"""

__version__ = "0.24.1"

from .data import (
    COLUMN_PRESETS,
    COMPOUNDS,
    DEFAULT_SAMPLE_MIX,
    PRIMARY_SOLVENTS,
    SECONDARY_SOLVENTS,
)
from .craig import Analyte, CraigResult, simulate as craig_simulate
from .gc import (
    CARRIER_GASES,
    GC_SOLUTES,
    STATIONARY_PHASES,
    GCColumn,
    GCConditions,
    GCPeak,
    GCRun,
    GCSolute,
    NonElutingSoluteError,
    StationaryPhase,
    average_linear_velocity as gc_average_linear_velocity,
    chromatogram as gc_chromatogram,
    holdup_time as gc_holdup_time,
    simulate as gc_simulate,
    solutes_for_phase,
    volumetric_flow as gc_volumetric_flow,
)
from .gc_program import (
    GCProgram,
    simulate_program as gc_simulate_program,
    simulate_solute_program as gc_simulate_solute_program,
)
from .diagnostics import DiagnosticRecord, DiagnosticsLog
from .gradient import (
    GradientProgram,
    GradientStop,
    NonElutingCompoundError,
)
from .model import (
    Column,
    CompoundResult,
    PairMetrics,
    ElutionMode,
    Results,
    SampleCompound,
    SimulationInputs,
    chromatogram,
    compound_signal,
    compute,
    time_grid,
)

__all__ = [
    "COLUMN_PRESETS",
    "COMPOUNDS",
    "DEFAULT_SAMPLE_MIX",
    "PRIMARY_SOLVENTS",
    "SECONDARY_SOLVENTS",
    "Analyte",
    "CraigResult",
    "craig_simulate",
    "CARRIER_GASES",
    "GC_SOLUTES",
    "STATIONARY_PHASES",
    "StationaryPhase",
    "GCColumn",
    "GCConditions",
    "GCPeak",
    "GCProgram",
    "GCRun",
    "GCSolute",
    "NonElutingSoluteError",
    "gc_chromatogram",
    "gc_average_linear_velocity",
    "gc_holdup_time",
    "gc_simulate",
    "gc_simulate_program",
    "gc_simulate_solute_program",
    "gc_volumetric_flow",
    "solutes_for_phase",
    "DiagnosticRecord",
    "DiagnosticsLog",
    "GradientProgram",
    "GradientStop",
    "NonElutingCompoundError",
    "Column",
    "CompoundResult",
    "PairMetrics",
    "ElutionMode",
    "Results",
    "SampleCompound",
    "SimulationInputs",
    "chromatogram",
    "compound_signal",
    "compute",
    "time_grid",
    "__version__",
]

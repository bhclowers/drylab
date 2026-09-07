# GC oracle harness: drives GasChromatographySimulator.jl (MIT) at tight
# tolerances over 162 isothermal cases and writes golden_gc.json next to
# this script, plus one Measurements.jl uncertainty case to stderr.
#
# Usage:  julia dump_golden_gc.jl [path-to-upstream-clone]
# Substance parameters are read from the UPSTREAM clone's MIT-licensed
# test/data/Database_test.csv (default clone path /tmp/gcsim) — deliberately
# NOT from hplc_sim.gc's vendored table, so compare_gc.py catches
# transcription errors in the vendored data as well as physics errors.
CLONE = length(ARGS) >= 1 ? ARGS[1] : "/tmp/gcsim"

# Solver tolerances for the PROGRAMMED cases, overridable from the command
# line so the oracle can be re-dumped at several tolerances and compared
# with itself. That self-comparison is not optional bookkeeping: under a
# temperature program BOTH sides of the validation are numerical, so the
# agreement the Python port can achieve is floored by the oracle's own
# error. Measuring that floor is what lets compare_gc_program.py state a
# tolerance instead of guessing one.
#   julia dump_golden_gc.jl <clone> --prog-only 1e-12 1e-10 golden_gc_program_tight.json
ISO_ONLY   = "--iso-only" in ARGS   # skip the programmed grid entirely
# Part B (Measurements.jl uncertainty propagation) is OPT-IN. It writes
# nothing to any golden file — it prints one reference number to stderr,
# already recorded in .context/memory — but solving with Measurement{Float64}
# forces Julia to JIT-specialise the entire ODE stack for a second element
# type, costing minutes on EVERY invocation. Default off so routine
# regenerations are not held hostage to a one-off measurement.
UNCERTAINTY = "--with-uncertainty" in ARGS
PROG_ONLY  = "--prog-only" in ARGS
_ai        = findfirst(==("--prog-only"), ARGS)
PROG_ABS   = PROG_ONLY && length(ARGS) >= _ai + 1 ? parse(Float64, ARGS[_ai + 1]) : 1e-10
PROG_REL   = PROG_ONLY && length(ARGS) >= _ai + 2 ? parse(Float64, ARGS[_ai + 2]) : 1e-8
PROG_OUT   = PROG_ONLY && length(ARGS) >= _ai + 3 ? ARGS[_ai + 3] : "golden_gc_program.json"
# Optional inclusive case-id range, so a slow high-tolerance dump can be
# built in chunks that each fit inside one tool call and be merged after.
_ri        = findfirst(==("--prog-range"), ARGS)
# Isothermal chunking, same rationale as --prog-range: the extended grid
# reaches combinations (0.53 mm bore, 1.0 um film, N2, vacuum outlet, cold)
# that cost the oracle ~13 s per case against ~0.04 s typical, so the run
# no longer fits one invocation.
_ii        = findfirst(==("--iso-range"), ARGS)
ISO_LO     = _ii === nothing ? 0 : parse(Int, ARGS[_ii + 1])
ISO_HI     = _ii === nothing ? typemax(Int) : parse(Int, ARGS[_ii + 2])
ISO_OUT    = _ii === nothing ? "golden_gc.json" : ARGS[_ii + 3]
_it        = findfirst(==("--iso-tol"), ARGS)
ISO_ABS    = _it === nothing ? 1e-12 : parse(Float64, ARGS[_it + 1])
ISO_REL    = _it === nothing ? 1e-10 : parse(Float64, ARGS[_it + 2])
PROG_LO    = _ri === nothing ? 0 : parse(Int, ARGS[_ri + 1])
PROG_HI    = _ri === nothing ? typemax(Int) : parse(Int, ARGS[_ri + 2])
OUT = "--prog-only" in ARGS ? tempname() * ".json" : joinpath(@__DIR__, ISO_OUT)
using GasChromatographySimulator
const GCS = GasChromatographySimulator
using Measurements
using OrdinaryDiffEq: Vern9

# ---- substances: from the package's own MIT-licensed test DB (Blumberg2017),
# read from the CSV, constructed literally -> no ChemicalIdentifiers/network.
using CSV, DataFrames
db = CSV.read(joinpath(CLONE, "test", "data", "Database_test.csv"), DataFrame)

atoms = Dict(  # formula atom counts + molar mass for Fuller Cag
    "Heptane"=>(100.21,7,16,0), "Octane"=>(114.23,8,18,0),
    "Nonane"=>(128.26,9,20,0), "Decane"=>(142.29,10,22,0),
    "Undecane"=>(156.31,11,24,0), "Dodecane"=>(170.34,12,26,0),
    "Tridecane"=>(184.36,13,28,0), "Tetradecane"=>(198.39,14,30,0),
    "Pentadecane"=>(212.42,15,32,0),
    "2-Octanone"=>(128.21,8,16,1), "2-Decanone"=>(156.27,10,20,1),
    "2-Octanol"=>(130.23,8,18,1), "1-Octanol"=>(130.23,8,18,1),
    "5-Nonanol"=>(144.25,9,20,1), "2-Nonanol"=>(144.25,9,20,1),
    "1-Nonanol"=>(144.25,9,20,1), "5-Decanol"=>(158.28,10,22,1),
)

function make_sub(name, phase, gas)
    row = db[(db.Name .== name) .& (db.Phase .== phase), :][1, :]
    M, Cn, Hn, On = atoms[name]
    Cag = GCS.diffusivity(M, Cn, Hn, On, 0, 0, gas)
    GCS.Substance(name, string(row.CAS), row.Tchar + 273.15, row.thetachar,
                  row.DeltaCp, row.phi0, "Blumberg2017", Cag, 0.0, 0.0)
end

# ---- case grid (isothermal): vary column, gas, T, pin, pout, phase
cases = []
id = 0
# Existing combinations are PRESERVED and enumerated first, so the previous
# 162 cases remain a strict subset whose values must reproduce exactly.
for (L, d) in [(30.0, 0.25e-3), (15.0, 0.25e-3), (30.0, 0.32e-3),
               (30.0, 0.10e-3), (30.0, 0.53e-3)]
    for gas in ["He", "H2", "N2"]
        for T in [80.0, 120.0, 160.0]
            for (pin, pout) in [(250e3, 101300.0), (150e3, 101300.0), (200e3, 0.0)]
                for phase in ["SLB5ms", "SPB50", "Wax"]
                    for df in [0.25e-6, 1.0e-6]
                        global id += 1
                        push!(cases, (id=id, L=L, d=d, df=df, gas=gas, T=T,
                                      pin=pin, pout=pout, phase=phase))
                    end
                end
            end
        end
    end
end

names_by_phase = Dict(
    "SLB5ms" => ["Heptane","Octane","Nonane","2-Octanone","Decane","1-Octanol","Dodecane","Tetradecane"],
    "SPB50"  => ["Heptane","Octane","Nonane","Decane","2-Octanol","Undecane","1-Octanol","Dodecane"],
    # Wax was UI-selectable with ZERO oracle cases until 2026-08-05.
    "Wax"    => ["Heptane","Octane","Nonane","Decane","2-Octanone","2-Octanol","1-Octanol","Dodecane"],
)

# Isothermal solver tolerances, overridable. Raised from the original
# 1e-10/1e-8 after the grid was extended: case 809 (0.53 mm bore, N2,
# vacuum outlet, Wax) showed the oracle itself was under-converged there,
# disagreeing with the Python CLOSED FORM by 1.1e-08 and converging onto
# it as the tolerance tightened. The reference was wrong, not the port.
opt = GCS.Options(alg=Vern9(), abstol=ISO_ABS, reltol=ISO_REL, ng=true,
                  vis="Blumberg", control="Pressure", odesys=true)
println(stderr, "ISO_TOLERANCES: abstol=", ISO_ABS, " reltol=", ISO_REL)

results = []
for c in filter(c -> !PROG_ONLY && ISO_LO <= c.id <= ISO_HI, cases)
    local col = GCS.Column(c.L, c.d, c.df, c.phase, c.gas)
    prog = GCS.Program([0.0, 1e6], [c.T, c.T], [c.pin, c.pin], [c.pout, c.pout], c.L)
    subs = [make_sub(n, c.phase, c.gas) for n in names_by_phase[c.phase]]
    par = GCS.Parameters(col, prog, subs, opt)
    pl, sol = GCS.simulate(par)
    tM = GCS.holdup_time(c.T + 273.15, c.pin, c.pout, c.L, c.d, c.gas;
                         vis="Blumberg", control="Pressure")
    push!(results, (case=c, tM=tM,
                    peaks=[(name=pl.Name[i], tR=pl.tR[i], tauR=pl.τR[i])
                           for i in eachindex(pl.Name)]))
end

# manual JSON (no extra dependency)
esc(s) = replace(s, "\\" => "\\\\", "\"" => "\\\"")
open(OUT, "w") do io
    print(io, "[")
    for (i, r) in enumerate(results)
        c = r.case
        i > 1 && print(io, ",")
        print(io, "{\"id\":", c.id, ",\"L\":", c.L, ",\"d\":", c.d,
              ",\"df\":", c.df, ",\"gas\":\"", c.gas, "\",\"T\":", c.T,
              ",\"pin\":", c.pin, ",\"pout\":", c.pout,
              ",\"phase\":\"", c.phase, "\",\"tM\":", r.tM, ",\"peaks\":[")
        for (j, p) in enumerate(r.peaks)
            j > 1 && print(io, ",")
            print(io, "{\"name\":\"", esc(p.name), "\",\"tR\":", p.tR,
                  ",\"tauR\":", p.tauR, "}")
        end
        print(io, "]}")
    end
    print(io, "]")
end
println(stderr, "CASES: ", length(results))

# ---- Part B: Measurements.jl propagation on one reference case
# Skipped under --prog-only. This block solves with Measurement{Float64}
# element types, which forces Julia to JIT-specialise the WHOLE ODE solver
# stack for a second element type — minutes of compilation on every
# invocation, and nothing to do with the programmed dump. Leaving it
# unguarded made short convergence chunks look like they were hanging.
if UNCERTAINTY
u_sub = GCS.Substance("Octane", "111-65-9",
                      (67.346 ± 0.5) + 273.15,   # Tchar ± 0.5 K
                      26.779 ± 0.3,              # θchar ± 0.3
                      66.363 ± 5.0,              # ΔCp ± 5 J/mol/K
                      0.001, "Blumberg2017 ± illustrative",
                      GCS.diffusivity(114.23, 8, 18, 0, 0, 0, "He"), 0.0 ± 0.0, 0.0 ± 0.0)
col = GCS.Column(30.0, 0.25e-3, 0.25e-6, "SLB5ms", "He")
prog = GCS.Program([0.0, 1e6], [120.0, 120.0], [250e3, 250e3], [101300.0, 101300.0], 30.0)
par_u = GCS.Parameters(col, prog, [u_sub], GCS.Options(ng=true, vis="Blumberg", control="Pressure"))
pl_u, _ = GCS.simulate(par_u)
println(stderr, "MEASUREMENTS CASE (Octane, SLB5ms, He, 120 C, 250/101.3 kPa, 30 m x 0.25 mm x 0.25 um):")
println(stderr, "  inputs: Tchar ± 0.5 K, thetachar ± 0.3, dCp ± 5 J/mol/K")
println(stderr, "  tR   = ", pl_u.tR[1])
println(stderr, "  tauR = ", pl_u.τR[1])
println(stderr, "MEASUREMENTS_DONE")
end  # !PROG_ONLY

# ---- Part C: TEMPERATURE-PROGRAMMED cases -> golden_gc_program.json
#
# Written to a SEPARATE file on purpose. golden_gc.json and its 2,754
# validated isothermal values keep their provenance untouched, so adding
# programmed coverage cannot perturb a suite that already passes. A schema
# change there would also have broken compare_gc.py, which reads a flat
# list of isothermal case records.
#
# Case grid deliberately includes VACUUM OUTLET (pout = 0). That is the
# known trap for the Python port: the singularity at p -> 0 cancels in the
# isothermal closed forms but does NOT cancel under a program, so these are
# the cases that will actually exercise the integrator's handling of it.
#
# Programs are (durations, values) per GCS.Program, NOT absolute times:
# [0.0, 60.0, 1560.0] means "start, hold 60 s, then ramp over 1560 s".
# 1560 s at 10 K/min covers 40 -> 300 C.
PROGRAMS = [
    (name="ramp10",      dt=[0.0, 60.0, 1560.0],               T=[40.0, 40.0, 300.0]),
    (name="ramp20",      dt=[0.0, 60.0, 780.0],                T=[40.0, 40.0, 300.0]),
    (name="ramp5",       dt=[0.0, 60.0, 3120.0],               T=[40.0, 40.0, 300.0]),
    (name="two_ramp",    dt=[0.0, 60.0, 840.0, 120.0, 360.0],  T=[40.0, 40.0, 180.0, 180.0, 300.0]),
]

prog_cases = []
pid = 0
# New bores are APPENDED, never inserted: this loop is outermost, so the
# first three columns still generate ids 1..432 in the same order and the
# existing programmed goldens remain valid for that range (verified by
# re-running a slice and diffing). Only 433.. needs generating.
for (L, d) in [(30.0, 0.25e-3), (15.0, 0.25e-3), (30.0, 0.32e-3),
               (30.0, 0.10e-3), (30.0, 0.53e-3)]
    for gas in ["He", "H2", "N2"]
        for pr in PROGRAMS
            for (pin, pout) in [(250e3, 101300.0), (200e3, 0.0)]
                for phase in ["SLB5ms", "SPB50", "Wax"]
                    for df in [0.25e-6, 1.0e-6]
                        global pid += 1
                        push!(prog_cases, (id=pid, L=L, d=d, df=df, gas=gas,
                                           prog=pr, pin=pin, pout=pout, phase=phase))
                    end
                end
            end
        end
    end
end

prog_opt = GCS.Options(alg=Vern9(), abstol=PROG_ABS, reltol=PROG_REL, ng=true,
                       vis="Blumberg", control="Pressure", odesys=true)
println(stderr, "PROG_TOLERANCES: abstol=", PROG_ABS, " reltol=", PROG_REL,
        " -> ", PROG_OUT)

prog_results = []
for c in filter(c -> !ISO_ONLY && PROG_LO <= c.id <= PROG_HI, prog_cases)
    local col = GCS.Column(c.L, c.d, c.df, c.phase, c.gas)
    npt = length(c.prog.dt)
    local prog = GCS.Program(c.prog.dt, c.prog.T,
                       fill(c.pin, npt), fill(c.pout, npt), c.L)
    subs = [make_sub(n, c.phase, c.gas) for n in names_by_phase[c.phase]]
    par = GCS.Parameters(col, prog, subs, prog_opt)
    pl, sol = GCS.simulate(par)
    push!(prog_results, (case=c,
                         peaks=[(name=pl.Name[i], tR=pl.tR[i], tauR=pl.τR[i])
                                for i in eachindex(pl.Name)]))
end

jarr(v) = string("[", join(v, ","), "]")
open(ISO_ONLY ? tempname() * ".json" : joinpath(@__DIR__, PROG_OUT), "w") do io
    print(io, "[")
    for (i, r) in enumerate(prog_results)
        c = r.case
        i > 1 && print(io, ",")
        print(io, "{\"id\":", c.id, ",\"L\":", c.L, ",\"d\":", c.d,
              ",\"df\":", c.df, ",\"gas\":\"", c.gas, "\",\"program\":\"",
              c.prog.name, "\",\"time_steps\":", jarr(c.prog.dt),
              ",\"temp_steps\":", jarr(c.prog.T),
              ",\"pin\":", c.pin, ",\"pout\":", c.pout,
              ",\"phase\":\"", c.phase, "\",\"peaks\":[")
        for (j, p) in enumerate(r.peaks)
            j > 1 && print(io, ",")
            print(io, "{\"name\":\"", esc(p.name), "\",\"tR\":", p.tR,
                  ",\"tauR\":", p.tauR, "}")
        end
        print(io, "]}")
    end
    print(io, "]")
end
println(stderr, "PROGRAM_CASES: ", length(prog_results))
println(stderr, "HARNESS_DONE")

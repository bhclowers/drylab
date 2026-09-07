'use strict';
/*
 * Golden-value dump from the vendored JS reference (mlibby/hplc_simulator).
 * Runs the shipped Simulator across a grid of inputs and writes JSON to
 * stdout. This is the ground-truth artifact the Python port is measured
 * against (charter: when sources conflict, the shipped artifact adjudicates).
 *
 * Usage: node dump_golden.js > golden.json
 */

var Simulator = require('./reference_js/hplc_simulator.js').Simulator;
var HPLC = require('./reference_js/hplc_globals.js').globals;

var grid = [];
var flowRates = [0.5, 1.0, 2.0, 3.5];
var percents = [30, 50, 70];
var temperatures = [15, 25, 40];
var solvents = ['acetonitrile', 'methanol'];

for (var s = 0; s < solvents.length; s++) {
  for (var fl = 0; fl < flowRates.length; fl++) {
    for (var p = 0; p < percents.length; p++) {
      for (var t = 0; t < temperatures.length; t++) {
        grid.push({
          solvent: solvents[s],
          flowRate: flowRates[fl],
          solventPercent: percents[p],
          temperature: temperatures[t]
        });
      }
    }
  }
}

var cases = [];
for (var i = 0; i < grid.length; i++) {
  var g = grid[i];
  var sim = new Simulator();
  sim.secondarySolvent = HPLC.secondarySolvents[g.solvent];
  // Changing solvent must also re-resolve compound coefficients; the
  // reference constructs compounds once with the initial solvent, so rebuild
  // per-compound coefficients the way the reference Compound does:
  var Compound = require('./reference_js/hplc_compound.js').Compound;
  var names = ['phenol', '3-phenyl propanol', 'acetophenone', 'p-chlorophenol', 'p-nitrotoluene'];
  var concs = [5, 25, 40, 15, 10];
  for (var c = 0; c < sim.compounds.length; c++) {
    var fresh = new Compound(names[c], sim.secondarySolvent.name, concs[c]);
    sim.compounds[c].km = fresh.km;
    sim.compounds[c].kb = fresh.kb;
    sim.compounds[c].sm = fresh.sm;
    sim.compounds[c].sb = fresh.sb;
  }
  sim.flowRate = g.flowRate;
  sim.solventPercent = g.solventPercent;
  sim.temperature = g.temperature; // last assignment triggers final update()

  var compounds = [];
  for (var c = 0; c < sim.compounds.length; c++) {
    var cp = sim.compounds[c];
    compounds.push({
      name: cp.name,
      kPrime: cp.kPrime,
      tR: cp.tR,
      sigma: cp.sigma,
      w: cp.w
    });
  }

  // Signal series at integer seconds for the first case of each solvent
  // (bulky; a spot check, not the whole grid).
  var series = null;
  if (g.flowRate === 2.0 && g.solventPercent === 50 && g.temperature === 25) {
    series = sim.getCompoundSeries(sim.compounds[0]);
  }

  cases.push({
    inputs: g,
    outputs: {
      voidTime: sim.voidTime,
      openTubeFlowVelocity: sim.openTubeFlowVelocity,
      chromatographicFlowVelocity: sim.chromatographicFlowVelocity,
      interstitialFlowVelocity: sim.interstitialFlowVelocity,
      eluentViscosity: sim.eluentViscosity,
      diffusionCoefficient: sim.diffusionCoefficient,
      reducedFlowVelocity: sim.reducedFlowVelocity,
      reducedPlateHeight: sim.reducedPlateHeight,
      backpressure: sim.backpressure,
      hetp: sim.hetp,
      theoreticalPlates: sim.theoreticalPlates,
      dwellVolume: sim.dwellVolume,
      dwellTime: sim.dwellTime,
      finalTime: sim.finalTime,
      postTubingVolume: sim.postTubingVolume,
      columnArea: sim.column.area,
      columnVolume: sim.column.volume,
      columnTotalPorosity: sim.column.totalPorosity,
      columnVoidVolume: sim.column.voidVolume
    },
    compounds: compounds,
    phenolSeriesIntegerSeconds: series
  });
}

process.stdout.write(JSON.stringify({generated: new Date().toISOString(), cases: cases}, null, 1));

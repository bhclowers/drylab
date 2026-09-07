/*
 * Standalone validation harness for the HPLC Simulator.
 *
 * The compute logic is lifted verbatim from HPLCSimulatorApplet.java
 * (HPLC Simulator v1.1.3, Boswell/Carr/Stoll) with all Swing/UI code
 * removed. It is a VALIDATION ORACLE ONLY — the shipped product is the
 * pure-Python hplc_sim package. Java is not a runtime dependency of the
 * project (decision 2026-08-04).
 *
 * Trust protocol: this harness first reproduces the ISOCRATIC golden values
 * already validated against the JS reference. Only if that passes are its
 * gradient outputs used as ground truth.
 *
 * Build/run:
 *   javac -d /tmp/harness HplcHarness.java
 *   java -cp /tmp/harness HplcHarness > golden_java.json
 */

import java.util.ArrayList;
import java.util.List;

public class HplcHarness {

    /* ---- Compound database (Globals.java, verbatim) ---- */
    static final String[] NAMES = {
        "n-benzyl formamide", "benzylalcohol", "phenol", "3-phenyl propanol",
        "acetophenone", "benzonitrile", "p-chlorophenol", "nitrobenzene",
        "methyl benzoate", "anisole", "benzene", "p-nitrotoluene",
        "p-nitrobenzyl chloride", "toluene", "benzophenone", "bromobenzene",
        "naphthalene", "ethylbenzene", "p-xylene", "p-dichlorobenzene",
        "propylbenzene", "n-butylbenzene"
    };
    static final double[][][] LSST = {
        {{-0.003731062, 0.769127502, 0.001962312, -1.950157208}, {-0.008930, 1.540840, 0.007655, -2.693812}},
        {{-0.00364158,  0.870975072, 0.001538701, -1.801193074}, {-0.008879, 1.643379, 0.007510, -2.603915}},
        {{-0.007051397, 1.222652803, 0.004948239, -2.157819856}, {-0.010465, 1.714002, 0.009040, -2.668850}},
        {{-0.005175387, 1.617423196, 0.004245094, -2.711627278}, {-0.012422, 2.682599, 0.010667, -3.544294}},
        {{-0.006113393, 1.615282733, 0.004190421, -2.419171414}, {-0.009257, 2.098172, 0.008684, -2.981032}},
        {{-0.008118482, 1.759520682, 0.006344149, -2.581132813}, {-0.009409, 1.995681, 0.009057, -2.971312}},
        {{-0.009910541, 2.006666967, 0.009176534, -3.110178571}, {-0.015142, 2.752714, 0.013319, -3.575982}},
        {{-0.009433757, 2.074051745, 0.008291834, -2.909075892}, {-0.010864, 2.277843, 0.009471, -2.982885}},
        {{-0.0077323,   2.116364506, 0.006053077, -2.911497882}, {-0.011888, 2.754816, 0.010739, -3.478031}},
        {{-0.008804318, 2.2070705,   0.007554149, -2.941605639}, {-0.011362, 2.587045, 0.009682, -3.103432}},
        {{-0.008529343, 2.208069224, 0.007114051, -2.82653686},  {-0.010915, 2.574300, 0.009507, -3.003558}},
        {{-0.010705359, 2.565390235, 0.009864271, -3.433694873}, {-0.012887, 2.900254, 0.011005, -3.522154}},
        {{-0.012956701, 2.804538425, 0.012986999, -3.866695802}, {-0.014804, 3.063453, 0.013295, -3.802081}},
        {{-0.010041886, 2.738254098, 0.009005662, -3.393491059}, {-0.013100, 3.230992, 0.010959, -3.547073}},
        {{-0.011069419, 3.087847385, 0.010362441, -4.064139779}, {-0.015610, 3.814708, 0.014480, -4.572059}},
        {{-0.011273051, 2.941762836, 0.010618543, -3.651869929}, {-0.015204, 3.539528, 0.013731, -3.937992}},
        {{-0.012795634, 3.296888486, 0.012596045, -4.112896456}, {-0.017658, 3.996277, 0.015853, -4.364601}},
        {{-0.011878845, 3.278713293, 0.01150122,  -4.00434081},  {-0.016026, 3.915079, 0.014007, -4.212582}},
        {{-0.011333502, 3.257874421, 0.01022372,  -3.911260542}, {-0.015301, 3.898820, 0.012295, -4.091578}},
        {{-0.01247399,  3.351026587, 0.011894773, -4.06721018},  {-0.016725, 4.042718, 0.014898, -4.384667}},
        {{-0.012995521, 3.811104371, 0.012122284, -4.521888293}, {-0.017711, 4.572339, 0.014763, -4.776607}},
        {{-0.013247488, 4.268938682, 0.011228978, -4.916062651}, {-0.019604, 5.195287, 0.015945, -5.293528}}
    };
    static final double[] MOLAR_VOLUME = {
        156.1, 125.6, 103.4, 170, 140.4, 122.7, 124.3, 122.7, 151.2, 128.1,
        96, 144.9, 165.8, 118.2, 206.8, 119.3, 147.6, 140.4, 140.4, 137.8,
        162.6, 184.8
    };

    static int indexOf(String name) {
        for (int i = 0; i < NAMES.length; i++) if (NAMES[i].equals(name)) return i;
        throw new IllegalArgumentException("unknown compound: " + name);
    }

    /* ---- LinearInterpolationFunction (verbatim behavior) ---- */
    static class Lif {
        double[][] d;
        Lif(double[][] pts) { d = pts; }  // already time-ordered by construction
        double getAt(double x) {
            if (x < d[0][0]) {
                double s = (d[1][1] - d[0][1]) / (d[1][0] - d[0][0]);
                return s * x + (d[0][1] - s * d[0][0]);
            }
            int n = d.length;
            if (x > d[n - 1][0]) {
                double s = (d[n - 1][1] - d[n - 2][1]) / (d[n - 1][0] - d[n - 2][0]);
                return s * x + (d[n - 1][1] - s * d[n - 1][0]);
            }
            int i = 0;
            while (x > d[i][0]) { i++; if (i >= n) break; }
            if (i >= n) return d[n - 1][1];
            if (i == 0) return d[0][1];
            double pos = (x - d[i - 1][0]) / (d[i][0] - d[i - 1][0]);
            return pos * (d[i][1] - d[i - 1][1]) + d[i - 1][1];
        }
    }

    /* ---- Inputs ---- */
    static class In {
        boolean gradientMode = false;
        double flowRate = 2.0;
        double solventBFraction = 0.5;      // isocratic only
        double temperature = 25.0;
        int solventB = 0;                   // 0 = ACN, 1 = MeOH
        double injectionVolume = 5.0;
        double timeConstant = 0.1;
        double columnLength = 100.0;        // mm
        double columnDiameter = 4.6;        // mm
        double particleSize = 3.0;          // um
        double interparticlePorosity = 0.4;
        double intraparticlePorosity = 0.4;
        double aTerm = 1.0, bTerm = 5.0, cTerm = 0.05;
        double tubingLength = 0.0;          // cm
        double tubingDiameter = 5.0;        // mils
        double mixingVolume = 200.0;        // uL
        double nonMixingVolume = 200.0;     // uL
        double[][] gradientProgram = {{0.0, 5.0}, {10.0, 95.0}};  // {min, %B}
        String[] compounds = {"phenol", "3-phenyl propanol", "acetophenone",
                              "p-chlorophenol", "p-nitrotoluene"};
        double[] concentrations = {5, 25, 40, 15, 10};
    }

    static class Out {
        double totalPorosity, voidVolume, voidTime, openTubeVelocity;
        double interstitialVelocity, chromatographicVelocity, eluentViscosity;
        double backpressure, diffusionCoefficient, reducedFlowVelocity;
        double reducedPlateHeight, hetp, theoreticalPlates, tubingVolume;
        double tubingTimeBroadening, endTime;
        double[] kPrime, tR, sigma, w;
        double[][] gradientProfile;  // {min, %B} sampled, gradient mode only
    }

    static Out run(In in) {
        Out o = new Out();
        int n = in.compounds.length;
        o.kPrime = new double[n]; o.tR = new double[n];
        o.sigma = new double[n]; o.w = new double[n];

        o.totalPorosity = in.interparticlePorosity
            + in.intraparticlePorosity * (1 - in.interparticlePorosity);
        o.voidVolume = Math.PI * Math.pow(((in.columnDiameter / 10) / 2), 2)
            * (in.columnLength / 10) * o.totalPorosity;
        o.voidTime = (o.voidVolume / in.flowRate) * 60;
        o.openTubeVelocity = (in.flowRate / 60)
            / (Math.PI * Math.pow(((in.columnDiameter / 10) / 2), 2));
        o.interstitialVelocity = o.openTubeVelocity / in.interparticlePorosity;
        o.chromatographicVelocity = o.openTubeVelocity / o.totalPorosity;

        double tk = in.temperature + 273.15;
        if (in.solventB == 0) {
            o.eluentViscosity = Math.exp(
                (in.solventBFraction * (-3.476 + (726 / tk)))
                + ((1 - in.solventBFraction) * (-5.414 + (1566 / tk)))
                + (in.solventBFraction * (1 - in.solventBFraction) * (-1.762 + (929 / tk))));
        } else {
            o.eluentViscosity = Math.exp(
                (in.solventBFraction * (-4.597 + (1211 / tk)))
                + ((1 - in.solventBFraction) * (-5.961 + (1736 / tk)))
                + (in.solventBFraction * (1 - in.solventBFraction) * (-6.215 + (2809 / tk))));
        }

        o.backpressure = ((o.openTubeVelocity / 100.0) * (in.columnLength / 1000.0)
            * (o.eluentViscosity / 1000.0) * 180.0
            * Math.pow(1 - in.interparticlePorosity, 2))
            / (Math.pow(in.interparticlePorosity, 3)
               * Math.pow(in.particleSize / 1000000, 2));

        double assoc = ((1 - in.solventBFraction) * 0.7) + 1.9;
        double solventMW = in.solventB == 0 ? 41.0 : 32.0;
        double mixMW = (in.solventBFraction * (solventMW - 18)) + 18;
        double avgMolarVolume = 0;
        for (String c : in.compounds) avgMolarVolume += MOLAR_VOLUME[indexOf(c)];
        avgMolarVolume /= n;
        o.diffusionCoefficient = 0.000000074 * (Math.pow(assoc * mixMW, 0.5) * tk)
            / (o.eluentViscosity * Math.pow(avgMolarVolume, 0.6));

        o.reducedFlowVelocity = ((in.particleSize / 10000) * o.interstitialVelocity)
            / o.diffusionCoefficient;
        o.reducedPlateHeight = in.aTerm + (in.bTerm / o.reducedFlowVelocity)
            + (in.cTerm * o.reducedFlowVelocity);
        o.hetp = (in.particleSize / 10000) * o.reducedPlateHeight;
        o.theoreticalPlates = (in.columnLength / 10) / o.hetp;

        o.tubingVolume = (in.tubingLength / 100)
            * (Math.PI * Math.pow((in.tubingDiameter * 0.0000254) / 2, 2) * 1000000000);
        double tubingRadius = (in.tubingDiameter * 0.00254) / 2;
        double tubingOpenTubeVelocity = (in.flowRate / 60)
            / (Math.PI * Math.pow(tubingRadius, 2));
        double zBroad = (2 * o.diffusionCoefficient * in.tubingLength / tubingOpenTubeVelocity)
            + ((Math.pow(tubingRadius, 2) * in.tubingLength * tubingOpenTubeVelocity)
               / (24 * o.diffusionCoefficient));
        double volBroad = Math.pow(Math.sqrt(zBroad) * Math.PI * Math.pow(tubingRadius, 2), 2);
        o.tubingTimeBroadening = Math.pow((Math.sqrt(volBroad) / in.flowRate) * 60, 2);

        if (in.gradientMode) {
            int last = in.gradientProgram.length - 1;
            o.endTime = in.gradientProgram[last][0] * 60;
            o.endTime += (((in.mixingVolume * 3 + in.nonMixingVolume) / 1000) / in.flowRate) * 60;

            Lif lif = calculateGradient(in, o.endTime);
            o.gradientProfile = lif.d;

            double dtstep = (o.endTime - 0) / 1000;
            for (int ic = 0; ic < n; ic++) {
                int ci = indexOf(in.compounds[ic]);
                double logkw1 = LSST[ci][in.solventB][0] * in.temperature + LSST[ci][in.solventB][1];
                double s1 = -1 * ((LSST[ci][in.solventB][2] * in.temperature) + LSST[ci][in.solventB][3]);

                double integral = 0, tRFinal = 0, dD = 0, totalTime = 0, totalDeadTime = 0;
                double xPos = 0, xMove;
                double[] lastX = {0, 0}, lastKo = {0, 0};
                boolean eluted = false;
                double kprime = 1;
                // Bounded: the applet's loop is unbounded and hangs on
                // non-eluting compounds. 2,000,000 steps >> 1000-step scale.
                long guard = 0, GUARD_MAX = 2000000L;
                while (!eluted) {
                    if (++guard > GUARD_MAX) { tRFinal = Double.NaN; break; }
                    double phiC = lif.getAt((totalTime - integral) / 60) / 100;
                    kprime = Math.pow(10, logkw1 - (s1 * phiC));
                    double curVal = dtstep / kprime;
                    double t0 = o.voidTime;
                    xMove = curVal / t0;
                    if (xPos >= 1) {
                        dD = ((1 - lastX[0]) / (xPos - lastX[0])) * (totalDeadTime - lastX[1]) + lastX[1];
                    } else { lastX[0] = xPos; lastX[1] = totalDeadTime; }
                    totalDeadTime += xMove * t0;
                    if (xPos >= 1) {
                        tRFinal = ((dD - lastKo[0]) / (integral - lastKo[0])) * (totalTime - lastKo[1]) + lastKo[1];
                    } else { lastKo[0] = integral; lastKo[1] = totalTime; }
                    totalTime += dtstep + curVal;
                    integral += curVal;
                    if (xPos > 1) { eluted = true; break; }
                    xPos += xMove;
                }
                o.kPrime[ic] = kprime;
                o.tR[ic] = tRFinal;
                // Java gradient sigma: final k', NO injection-volume term.
                o.sigma[ic] = Math.sqrt(
                    Math.pow((o.voidTime * (1 + kprime)) / Math.sqrt(o.theoreticalPlates), 2)
                    + Math.pow(in.timeConstant, 2) + o.tubingTimeBroadening);
                o.w[ic] = (in.injectionVolume / 1000000) * in.concentrations[ic];
            }
        } else {
            double longest = 0;
            for (int i = 0; i < n; i++) {
                int ci = indexOf(in.compounds[i]);
                double logkw1 = LSST[ci][in.solventB][0] * in.temperature + LSST[ci][in.solventB][1];
                double s1 = -1 * ((LSST[ci][in.solventB][2] * in.temperature) + LSST[ci][in.solventB][3]);
                double kprime = Math.pow(10, logkw1 - (s1 * in.solventBFraction));
                double rt = o.voidTime * (1 + kprime);
                o.kPrime[i] = kprime;
                o.tR[i] = rt;
                o.sigma[i] = Math.sqrt(
                    Math.pow(rt / Math.sqrt(o.theoreticalPlates), 2)
                    + Math.pow(in.timeConstant, 2)
                    + (1.0 / 12.0) * Math.pow((in.injectionVolume / 1000.0) / (in.flowRate / 60.0), 2)
                    + o.tubingTimeBroadening);
                o.w[i] = (in.injectionVolume / 1000000) * in.concentrations[i];
                if (rt > longest) longest = rt;
            }
            o.endTime = longest * 1.1;
        }
        return o;
    }

    static Lif calculateGradient(In in, double endTimeSeconds) {
        int iNumPoints = 1000;
        double[][] arr = new double[iNumPoints][2];
        int tableLen = in.gradientProgram.length;
        double mixerComposition = in.gradientProgram[0][1];
        double finalTime = endTimeSeconds / 60;
        double timeStep = finalTime / (iNumPoints - 1);
        double time;
        for (int i = 0; i < iNumPoints; i++) {
            time = i * timeStep;
            arr[i][0] = time;
            arr[i][1] = mixerComposition;
            double solventBInMixer = mixerComposition * in.mixingVolume;
            solventBInMixer -= ((in.flowRate * 1000) * timeStep) * mixerComposition;
            double incoming = 0;
            if (time < (in.nonMixingVolume / 1000) / in.flowRate) {
                incoming = in.gradientProgram[0][1];
            } else {
                int rowBefore = 0;
                for (int j = 0; j < tableLen; j++) {
                    double rowTime = in.gradientProgram[j][0];
                    if (rowTime <= (time - ((in.nonMixingVolume / 1000) / in.flowRate))) rowBefore = j;
                    else break;
                }
                double rowBeforeTime = in.gradientProgram[rowBefore][0];
                if (rowBefore <= tableLen - 2) {
                    double rowAfterTime = in.gradientProgram[rowBefore + 1][0];
                    double posBetween = ((time - ((in.nonMixingVolume / 1000) / in.flowRate)) - rowBeforeTime)
                        / (rowAfterTime - rowBeforeTime);
                    double cBefore = in.gradientProgram[rowBefore][1];
                    double cAfter = in.gradientProgram[rowBefore + 1][1];
                    incoming = (posBetween * (cAfter - cBefore)) + cBefore;
                } else {
                    incoming = in.gradientProgram[rowBefore][1];
                }
            }
            solventBInMixer += ((in.flowRate * 1000) * timeStep) * incoming;
            if (((in.flowRate * 1000) * timeStep) < in.mixingVolume)
                mixerComposition = solventBInMixer / in.mixingVolume;
            else
                mixerComposition = incoming;
        }
        return new Lif(arr);
    }

    /* ---- JSON emission (no external deps) ---- */
    static String num(double v) {
        if (Double.isNaN(v)) return "null";
        if (Double.isInfinite(v)) return "null";
        return Double.toString(v);
    }

    static String arr(double[] a) {
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < a.length; i++) {
            if (i > 0) sb.append(",");
            sb.append(num(a[i]));
        }
        return sb.append("]").toString();
    }

    static void emit(StringBuilder sb, In in, Out o, String label) {
        sb.append("{\"label\":\"").append(label).append("\",");
        sb.append("\"inputs\":{");
        sb.append("\"gradientMode\":").append(in.gradientMode);
        sb.append(",\"flowRate\":").append(num(in.flowRate));
        sb.append(",\"solventBFraction\":").append(num(in.solventBFraction));
        sb.append(",\"temperature\":").append(num(in.temperature));
        sb.append(",\"solventB\":").append(in.solventB);
        sb.append(",\"injectionVolume\":").append(num(in.injectionVolume));
        sb.append(",\"timeConstant\":").append(num(in.timeConstant));
        sb.append(",\"columnLength\":").append(num(in.columnLength));
        sb.append(",\"particleSize\":").append(num(in.particleSize));
        sb.append(",\"tubingLength\":").append(num(in.tubingLength));
        sb.append(",\"tubingDiameter\":").append(num(in.tubingDiameter));
        sb.append(",\"mixingVolume\":").append(num(in.mixingVolume));
        sb.append(",\"nonMixingVolume\":").append(num(in.nonMixingVolume));
        sb.append(",\"compounds\":[");
        for (int i = 0; i < in.compounds.length; i++) {
            if (i > 0) sb.append(",");
            sb.append("\"").append(in.compounds[i]).append("\"");
        }
        sb.append("],\"concentrations\":").append(arr(in.concentrations));
        sb.append(",\"gradientProgram\":[");
        for (int i = 0; i < in.gradientProgram.length; i++) {
            if (i > 0) sb.append(",");
            sb.append("[").append(num(in.gradientProgram[i][0])).append(",")
              .append(num(in.gradientProgram[i][1])).append("]");
        }
        sb.append("]},\"outputs\":{");
        sb.append("\"totalPorosity\":").append(num(o.totalPorosity));
        sb.append(",\"voidVolume\":").append(num(o.voidVolume));
        sb.append(",\"voidTime\":").append(num(o.voidTime));
        sb.append(",\"openTubeVelocity\":").append(num(o.openTubeVelocity));
        sb.append(",\"interstitialVelocity\":").append(num(o.interstitialVelocity));
        sb.append(",\"chromatographicVelocity\":").append(num(o.chromatographicVelocity));
        sb.append(",\"eluentViscosity\":").append(num(o.eluentViscosity));
        sb.append(",\"backpressure\":").append(num(o.backpressure));
        sb.append(",\"diffusionCoefficient\":").append(num(o.diffusionCoefficient));
        sb.append(",\"reducedFlowVelocity\":").append(num(o.reducedFlowVelocity));
        sb.append(",\"reducedPlateHeight\":").append(num(o.reducedPlateHeight));
        sb.append(",\"hetp\":").append(num(o.hetp));
        sb.append(",\"theoreticalPlates\":").append(num(o.theoreticalPlates));
        sb.append(",\"tubingVolume\":").append(num(o.tubingVolume));
        sb.append(",\"tubingTimeBroadening\":").append(num(o.tubingTimeBroadening));
        sb.append(",\"endTime\":").append(num(o.endTime));
        sb.append(",\"kPrime\":").append(arr(o.kPrime));
        sb.append(",\"tR\":").append(arr(o.tR));
        sb.append(",\"sigma\":").append(arr(o.sigma));
        sb.append(",\"w\":").append(arr(o.w));
        if (o.gradientProfile != null) {
            sb.append(",\"gradientProfile\":[");
            for (int i = 0; i < o.gradientProfile.length; i++) {
                if (i > 0) sb.append(",");
                sb.append("[").append(num(o.gradientProfile[i][0])).append(",")
                  .append(num(o.gradientProfile[i][1])).append("]");
            }
            sb.append("]");
        }
        sb.append("}}");
    }

    public static void main(String[] args) {
        List<In> cases = new ArrayList<>();

        // --- Isocratic trust cases: must match the existing JS-validated goldens ---
        double[] flows = {0.5, 1.0, 2.0, 3.5};
        int[] solvents = {0, 1};
        double[] percents = {30, 50, 70};
        double[] temps = {15, 25, 40};
        for (int s : solvents) for (double fl : flows)
            for (double p : percents) for (double t : temps) {
                In in = new In();
                in.solventB = s; in.flowRate = fl;
                in.solventBFraction = p / 100.0; in.temperature = t;
                cases.add(in);
            }
        // Isocratic with tubing (JS diverges here; Java is the reference)
        for (double len : new double[]{10.0, 50.0}) {
            In in = new In(); in.tubingLength = len; cases.add(in);
        }

        // --- Gradient cases ---
        double[][][] programs = {
            {{0.0, 5.0}, {10.0, 95.0}},
            {{0.0, 20.0}, {5.0, 60.0}, {15.0, 90.0}},
            {{0.0, 40.0}, {8.0, 40.0}},          // isocratic-shaped gradient (hold)
            {{0.0, 10.0}, {20.0, 80.0}}
        };
        for (double[][] prog : programs)
            for (double fl : new double[]{1.0, 2.0})
                for (int s : solvents) {
                    In in = new In();
                    in.gradientMode = true; in.gradientProgram = prog;
                    in.flowRate = fl; in.solventB = s;
                    cases.add(in);
                }
        // Gradient with varied dwell volumes and tubing
        for (double mv : new double[]{0.0, 500.0})
            for (double nmv : new double[]{0.0, 400.0}) {
                In in = new In();
                in.gradientMode = true; in.mixingVolume = mv; in.nonMixingVolume = nmv;
                cases.add(in);
            }
        {
            In in = new In(); in.gradientMode = true; in.tubingLength = 30.0; cases.add(in);
        }
        // Gradient with the full 22-compound set
        {
            In in = new In(); in.gradientMode = true;
            in.compounds = NAMES.clone();
            in.concentrations = new double[NAMES.length];
            for (int i = 0; i < NAMES.length; i++) in.concentrations[i] = 10.0;
            cases.add(in);
        }
        // Non-eluting case: weak gradient, strongly retained compound
        {
            In in = new In(); in.gradientMode = true;
            in.gradientProgram = new double[][]{{0.0, 1.0}, {2.0, 2.0}};
            in.compounds = new String[]{"n-butylbenzene"};
            in.concentrations = new double[]{10.0};
            cases.add(in);
        }

        StringBuilder sb = new StringBuilder("{\"cases\":[");
        for (int i = 0; i < cases.size(); i++) {
            if (i > 0) sb.append(",\n");
            In in = cases.get(i);
            emit(sb, in, run(in), in.gradientMode ? "gradient" : "isocratic");
        }
        sb.append("]}");
        System.out.println(sb);
    }
}

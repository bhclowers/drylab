// Craig worksheet as a .docx — mirrors the PDF: name/group header, POGIL
// structure, record tables, and bordered write-in boxes (rendered as
// single-cell tables so they survive Word editing).
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, HeadingLevel, AlignmentType, BorderStyle, ShadingType,
  Header, PageNumber, Footer,
} = require("docx");

const ACCENT = "2C5F7C";
const BORDER = { style: BorderStyle.SINGLE, size: 6, color: "8FADBD" };
const CELL_BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const PAGE = { size: { width: 12240, height: 15840 },
               margin: { top: 1134, bottom: 1247, left: 1247, right: 1247 } };
const TABLE_W = 12240 - 1247 * 2; // content width in DXA

const P = (text, opts = {}) => new Paragraph({
  spacing: { after: 140, line: 276 },
  children: runs(text), ...opts,
});
// minimal **bold** / *italic* inline markup
function runs(text) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun(text.slice(last, m.index)));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(new TextRun({ text: tok.slice(2, -2), bold: true }));
    else out.push(new TextRun({ text: tok.slice(1, -1), italics: true }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new TextRun(text.slice(last)));
  return out;
}
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { after: 200 },
  children: [new TextRun({ text: t, color: ACCENT })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 160 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "C9DBE4" } },
  children: [new TextRun({ text: t, color: ACCENT })] });
const RULE = () => new Paragraph({ spacing: { before: 160, after: 160 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "C9DBE4" } }, children: [] });

function grid(headers, rows, colW) {
  const widths = colW.map((f) => Math.round(TABLE_W * f));
  const cell = (t, head, w) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders: CELL_BORDERS,
    shading: head ? { type: ShadingType.CLEAR, fill: "E8F0F4" } : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [new Paragraph({ spacing: { after: 0 },
      children: [new TextRun({ text: t, bold: head, size: 19 })] })],
  });
  return new Table({
    width: { size: TABLE_W, type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ children: headers.map((h, i) => cell(h, true, widths[i])) }),
      ...rows.map((r) => new TableRow({
        children: r.map((c, i) => cell(c, false, widths[i])) })),
    ],
  });
}
// Write-in box: a one-cell table with empty lines inside (survives editing,
// visibly bordered in Word).
function answerBox(lines = 4) {
  return new Table({
    width: { size: TABLE_W, type: WidthType.DXA }, columnWidths: [TABLE_W],
    rows: [new TableRow({ children: [new TableCell({
      width: { size: TABLE_W, type: WidthType.DXA }, borders: CELL_BORDERS,
      margins: { top: 80, bottom: 80, left: 100, right: 100 },
      children: Array.from({ length: lines }, () =>
        new Paragraph({ spacing: { after: 160 }, children: [] })),
    })] })],
  });
}
const GAP = () => new Paragraph({ spacing: { after: 120 }, children: [] });

const empty5 = ["", "", "", "", ""];
const doc = new Document({
  styles: { default: { document: { run: { font: "Calibri", size: 21 } } } },
  sections: [{
    properties: { page: PAGE },
    headers: { default: new Header({ children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Name: ____________________   Group: ______", size: 18, color: "555555" })],
    })] }) },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT, " / ", PageNumber.TOTAL_PAGES], size: 17, color: "666666" })],
    })] }) },
    children: [
      H1("From Separatory Funnel to Column — The Craig Apparatus"),
      P("**Team roles for today** (rotate from last session): Manager keeps the group on the current question — no running ahead to the simulator. Recorder writes the group's predictions and reconciliations on this sheet. Presenter reports at the checkpoints. Reflector notes where the group's thinking changed."),
      P("**How this is graded:** full credit requires, for every numbered question, your **written prediction before touching any control**, the **observed result**, and — where they disagree — a sentence on **what changed in your thinking**. A wrong prediction honestly reconciled earns full credit; a correct answer with no prediction does not."),
      RULE(),
      H2("Getting started"),
      P("Open drylab → **Craig apparatus** tab. Set the controls to:"),
      grid(["Control", "Setting"], [
        ["D for analyte A", "4.0"], ["D for analyte B", "0.25"],
        ["Upper (mobile) volume", "1.0"], ["Lower (stationary) volume", "1.0"],
        ["Number of tubes", "20"], ["Transfers (n)", "leave at 0 for now"],
      ], [0.5, 0.5]),
      GAP(),
      P("You did extractions like this by hand in a separatory funnel. This machine does the same equilibrate-and-transfer step over and over: each transfer moves every tube's **upper (mobile) phase** one tube to the right, then every tube re-equilibrates."),
      P("**Q1 — By hand first (no simulator).** For analyte A (D = 4, equal volumes): what fraction of the analyte sits in the mobile phase of a tube after equilibration? Write the expression in terms of D and the volumes, then the number."),
      answerBox(3),
      GAP(),
      P("**Q2 — Predict n = 2.** Starting with everything in tube 0, work out on paper where analyte A is after **two** transfers. Fill in your predicted fractions (they must sum to 1):"),
      grid(["", "Tube 0", "Tube 1", "Tube 2"], [
        ["Predicted fraction of A", "", "", ""],
        ["Predicted fraction of B", "", "", ""],
      ], [0.34, 0.22, 0.22, 0.22]),
      GAP(),
      P("*Hint you may use: each transfer either advances the mobile fraction p or leaves the stationary fraction behind — what family of distribution is \u201Ck advances in n tries\u201D?*"),
      P("**STOP — show your table to the instructor before running.**"),
      P("**Q3 — Run n = 2 and reconcile.** Set Transfers to 2 and read the per-tube table. Record the simulator's fractions next to yours above (use a different pen/color). Where they differ, what step of your hand calculation was wrong?"),
      answerBox(3),
      RULE(),
      H2("Why columns beat funnels"),
      P("**Q4 — Predict before moving the slider.** As n grows from 5 to 100, two things happen to each band: its **center moves** and its **width grows**. Circle one prediction for each and give a reason:"),
      grid(["Quantity", "grows like n / like \u221An / stays fixed", "Why"], [
        ["Position of band center", "", ""],
        ["Width of the band", "", ""],
        ["Gap between the A and B centers", "", ""],
      ], [0.34, 0.33, 0.33]),
      GAP(),
      P("**Q5 — Run it.** Set **Number of tubes to 100**, then step Transfers through the values below. For each, record the center tube of each band (tube of maximum, from the per-tube table), and estimate each band's width by counting tubes at roughly half the peak height:"),
      grid(["n", "Center of B", "Center of A", "Gap (tubes)", "Width of A (tubes)", "Gap \u00F7 Width"], [
        ["5", "", "", "", "", ""], ["25", "", "", "", "", ""], ["100", "", "", "", "", ""],
      ], [0.1, 0.18, 0.18, 0.18, 0.2, 0.16]),
      GAP(),
      P("**Q6 — The whole argument in one ratio.** Look at your Gap \u00F7 Width column, and at the panel's **\u201CResolution on the tube axis\u201D** readout at each n. Both improve with n even though the bands keep getting wider. Reconcile this with your Q4 predictions: which grows faster, and by what factor does the ratio improve when n goes up 4\u00D7 (25 \u2192 100)?"),
      answerBox(5),
      GAP(),
      P("**Q7 — Where did the Gaussian come from?** At n = 100, switch on the **normal approximation** overlay. The match is close — yet nothing in this machine \u201Cknows\u201D about Gaussians; it only equilibrates and transfers. What theorem connects your Q2 distribution to the overlaid curve, and what has to be large for it to apply?"),
      answerBox(3),
      GAP(),
      P("**Q8 — The bridge to chromatography** (whole-class checkpoint). In a packed column there are no tubes and no discrete transfers — yet we describe columns with a \u201Cnumber of theoretical plates.\u201D State the mapping in two sentences: what plays the role of one tube, and what plays the role of one transfer, in a real column?"),
      answerBox(3),
      RULE(),
      H2("Going further — for the ambitious (advanced undergrad / graduate)"),
      P("These use the same apparatus, pushed harder. Show derivations; the simulator is the arbiter, not the argument. (Set **Number of tubes to 250** for this section so nothing runs off the axis.)"),
      P("**A1 — Own the scaling law.** The panel's readout defines Rs = |\u03BC_B \u2212 \u03BC_A| / [2(\u03C3_A + \u03C3_B)]. For two analytes with mobile fractions p_A and p_B, write Rs as an explicit function of n (means and variances of the binomial do all the work), and reduce it for the D = 1 vs D = 4 pair to the cleanest closed form you can. Then test it: record the panel's Rs at n = 50, 100, and 200 and compare with your formula at each n. What single number should the ratio of successive readings give, and does it?"),
      answerBox(5),
      GAP(),
      P("**A2 — Where should the chemistry sit?** Selectivity is fixed by the chemistry: suppose D_B/D_A = 4 always. But *where* the pair sits on the D axis is a choice. Before running: using your A1 expression, argue where on the axis Rs should be largest — what is being traded as both D's grow together? Then scan at n = 100, recording the panel's Rs for each pair:"),
      grid(["(D_A, D_B)", "(0.125, 0.5)", "(0.25, 1)", "(0.5, 2)", "(1, 4)", "(2, 8)", "(4, 16)"], [
        ["Rs", "", "", "", "", "", ""],
      ], [0.16, 0.14, 0.14, 0.14, 0.14, 0.14, 0.14]),
      GAP(),
      P("State where the maximum sits, in terms of the p's rather than the D's — and connect it to the chromatographer's rule you will meet again in the HPLC exercises: why is there a *useful window* of retention, with penalties on both sides?"),
      answerBox(5),
      GAP(),
      P("**A3 — When you can't change the chemistry, change the instrument.** The pair (D_A, D_B) = (4, 16) sits badly on the axis — your A2 scan says so. The D's are thermodynamics; you cannot vote on them. But the *phase volumes* are yours. Derive how the mobile fraction p depends on D **and** the volume ratio V_upper/V_lower, solve for the volume ratio that moves this pair onto your A2 optimum, and verify with the simulator at n = 100 (report the Rs you recover). Close with the bridge: in a real column, what plays the role of the volume ratio, and which instrument parameters move it? (You will meet this quantity as the phase ratio \u03B2, with k\u2032 = K/\u03B2.)"),
      answerBox(6),
      RULE(),
      H2("Homework (individual)"),
      P("Bring numbers, not adjectives — the Craig panel's CSV exports carry the operating point so every value you report is traceable."),
      P("**H1.** For D = 1 and equal volumes, derive the tube of maximum amount after n transfers, r_max, in terms of n and the mobile-phase fraction p. Verify with the simulator at n = 50 (also record the fraction in that tube). Then predict r_max for **D = 3 with the upper volume set to 2.0 and the lower to 1.0**, and verify. If your prediction missed, identify the exact quantity you computed wrong — this one has a famous trap."),
      P("**H2.** Two analytes, D = 1 and D = 4, equal volumes. Using your Q4/Q6 scaling (centers separate \u221D n, widths grow \u221D \u221An), estimate the smallest n at which the pair reaches Rs \u2248 1.5. Show the inequality you solved. Then find the answer empirically with the Transfers slider (report the \u201CResolution on the tube axis\u201D readout at your n). Reconcile estimate vs. observation."),
      P("**H3.** In two sentences: using the H2 result, explain why nobody separates mixtures with 80 sequential funnel extractions — and why a column, which does effectively thousands of \u201Ctransfers,\u201D is not merely 80 funnels' worth of work for free. What is the cost that \u221An growth imposes?"),
    ],
  }],
});
Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync("/mnt/user-data/outputs/drylab_student_worksheet_ex1_craig.docx", b);
  console.log("docx written");
});

// Worksheet master (.md) -> .docx, following the Ex 1 Word build's look:
// name/group header, page-number footer, shaded-header tables, and write-in
// boxes as single-cell tables (they survive editing in Word).
//
// Usage: node build_worksheet_docx.js masters/student_ws_exN.md rendered/out.docx
//
// Understands the subset of Markdown the worksheet masters use: # and ##
// headings, paragraphs (wrapped lines joined), "- " bullets (2-space
// continuation), pipe tables, "> " callouts, "---" rules,
// <div class="answer"></div> and <div class="answer tall"></div>, and inline
// **bold**, *italic*, `code`, &nbsp;. Anything else is refused with the line
// number rather than silently dropped.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
  HeadingLevel, AlignmentType, BorderStyle, ShadingType, Header, Footer,
  PageNumber, LevelFormat,
} = require("docx");

const [, , SRC, OUT] = process.argv;
if (!SRC || !OUT) { console.error("usage: node build_worksheet_docx.js in.md out.docx"); process.exit(2); }

const ACCENT = "2C5F7C";
const FONT = "Calibri";
const BORDER = { style: BorderStyle.SINGLE, size: 6, color: "8FADBD" };
const CELL_BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
const MARGIN = 1247;
const PAGE = { size: { width: 12240, height: 15840 },
               margin: { top: 1134, bottom: 1247, left: MARGIN, right: MARGIN } };
const TABLE_W = 12240 - MARGIN * 2;

function runs(text, base = {}) {
  text = text.replace(/&nbsp;/g, "").replace(/\\\*/g, "\u0000");
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0, m;
  const plain = (s) => s && out.push(new TextRun({ text: s.replace(/\u0000/g, "*"), ...base }));
  while ((m = re.exec(text)) !== null) {
    plain(text.slice(last, m.index));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else if (t.startsWith("`")) out.push(new TextRun({ text: t.slice(1, -1), font: "Consolas", ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    last = m.index + t.length;
  }
  plain(text.slice(last));
  return out;
}

const para = (text, keepNext = false) => new Paragraph({ spacing: { after: 140, line: 276 }, keepNext, children: runs(text) });
const gap = () => new Paragraph({ spacing: { after: 120 }, children: [] });
const rule = () => new Paragraph({ spacing: { before: 160, after: 160 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "C9DBE4" } }, children: [] });

function table(rowsText) {
  const split = (l) => l.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
  const head = split(rowsText[0]);
  const body = rowsText.slice(2).map(split);
  const n = head.length;
  // column widths from the longest text in each column, with a floor
  // capped at 26 characters so one long header cannot squeeze a short column to a letter per line
  const len = head.map((h, i) => Math.min(26, Math.max(h.length, ...body.map((r) => (r[i] || "").replace(/&nbsp;/g, "").length), 9)));
  const tot = len.reduce((a, b) => a + b, 0);
  const widths = len.map((l) => Math.round(TABLE_W * l / tot));
  widths[n - 1] += TABLE_W - widths.reduce((a, b) => a + b, 0);
  // short tables stay on one page: keep-with-next on every row but the last
  const keep = body.length <= 8;
  const cell = (t, isHead, w, last) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders: CELL_BORDERS,
    shading: isHead ? { type: ShadingType.CLEAR, fill: "E8F0F4" } : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [new Paragraph({ spacing: { after: 0 }, keepNext: keep && !last,
      children: runs(t, { bold: isHead || undefined, size: 19 }) })],
  });
  return new Table({
    width: { size: TABLE_W, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: head.map((h, i) => cell(h, true, widths[i], false)) }),
      ...body.map((r, j) => new TableRow({ cantSplit: true,
        children: head.map((_, i) => cell(r[i] || "", false, widths[i], j === body.length - 1)) }))],
  });
}

function answerBox(lines) {
  return new Table({
    width: { size: TABLE_W, type: WidthType.DXA }, columnWidths: [TABLE_W],
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({
      width: { size: TABLE_W, type: WidthType.DXA }, borders: CELL_BORDERS,
      margins: { top: 80, bottom: 80, left: 100, right: 100 },
      children: Array.from({ length: lines }, () => new Paragraph({ spacing: { after: 160 }, children: [] })),
    })] })],
  });
}

function callout(text) {
  return new Paragraph({
    spacing: { before: 80, after: 160 }, indent: { left: 360 },
    shading: { type: ShadingType.CLEAR, fill: "F2F6F8" },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: ACCENT, space: 8 } },
    children: runs(text),
  });
}

// ------------------------------------------------------------------ parse
const lines = fs.readFileSync(SRC, "utf8").split("\n");
const body = [];
let i = 0;
const isBlank = (l) => l.trim() === "";
while (i < lines.length) {
  const l = lines[i];
  if (isBlank(l)) { i++; continue; }
  if (l.startsWith("# ")) {
    body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: l.slice(2), color: ACCENT })] }));
    i++; continue;
  }
  if (l.startsWith("## ")) {
    body.push(new Paragraph({ heading: HeadingLevel.HEADING_2,
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "C9DBE4" } },
      children: [new TextRun({ text: l.slice(3), color: ACCENT })] }));
    i++; continue;
  }
  if (l.trim() === "---") { body.push(rule()); i++; continue; }
  const box = l.match(/^<div class="answer( tall)?"><\/div>$/);
  if (box) { body.push(answerBox(box[1] ? 8 : 4)); body.push(gap()); i++; continue; }
  if (l.startsWith("|")) {
    const t = [];
    while (i < lines.length && lines[i].startsWith("|")) t.push(lines[i++]);
    if (t.length < 2 || !/^\|[\s:|-]+\|$/.test(t[1].trim())) throw new Error(`${SRC}:${i}: malformed table`);
    body.push(table(t)); body.push(gap()); continue;
  }
  if (l.startsWith("> ")) {
    const t = [];
    while (i < lines.length && lines[i].startsWith(">")) t.push(lines[i++].replace(/^>\s?/, ""));
    body.push(callout(t.join(" "))); continue;
  }
  if (l.startsWith("- ")) {
    while (i < lines.length && lines[i].startsWith("- ")) {
      let t = lines[i++].slice(2);
      while (i < lines.length && /^ {2}\S/.test(lines[i])) t += " " + lines[i++].trim();
      body.push(new Paragraph({ numbering: { reference: "bullets", level: 0 },
        spacing: { after: 80, line: 276 }, children: runs(t) }));
    }
    body.push(gap()); continue;
  }
  if (l.startsWith("<")) throw new Error(`${SRC}:${i + 1}: unhandled HTML: ${l}`);
  const t = [];
  while (i < lines.length && !isBlank(lines[i]) && !/^(#|\||> |- |---|<)/.test(lines[i])) t.push(lines[i++].trim());
  const next = lines.slice(i).find((x) => !isBlank(x)) || "";
  body.push(para(t.join(" "), next.startsWith("|") || next.startsWith("<div class=\"answer")));
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 34, bold: true },
        paragraph: { spacing: { before: 0, after: 200 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 26, bold: true },
        paragraph: { spacing: { before: 280, after: 160 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: PAGE },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Name: ____________________   Group: ______", size: 18, color: "555555" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT, " / ", PageNumber.TOTAL_PAGES], size: 17, color: "666666" })] })] }) },
    children: body,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log(`wrote ${OUT} (${body.length} blocks)`); });

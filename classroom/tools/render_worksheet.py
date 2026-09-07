#!/usr/bin/env python3
"""Render a student-worksheet markdown master to its print PDF.

The worksheet stylesheet (name/group header, answer boxes, POGIL tables)
lives here so every worksheet renders identically. Answer boxes are
<div class="answer"></div> / <div class="answer tall"></div> blocks in
the master (md_in_html passes them through).

QA after rendering (see classroom/README.md, "QA gates"): whitespace-
normalized no-leakage check against the instructor key's answer values,
real-UI-reference presence check, and raster inspection of at least one
dense page. This script does the rendering; the checks are per-worksheet
because the leakage list is per-exercise.

Usage: python render_worksheet.py <master.md> <out.pdf>
"""
import sys
import markdown
from weasyprint import HTML

CSS = """
@page { size: letter; margin: 2cm 2.2cm 2.4cm 2.2cm;
        @top-right { content: "Name: ____________________  Group: ______";
                     font-size: 8.5pt; color: #555; }
        @bottom-center { content: counter(page) " / " counter(pages);
                         font-size: 8.5pt; color: #666; } }
body { font-family: "DejaVu Sans", sans-serif; font-size: 10pt;
       line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 15pt; color: #2c5f7c; border-bottom: 2px solid #2c5f7c;
     padding-bottom: 4px; }
h2 { font-size: 12pt; color: #2c5f7c; margin-top: 1.3em;
     border-bottom: 1px solid #c9dbe4; padding-bottom: 2px; }
table { border-collapse: collapse; margin: 0.6em 0; width: 100%;
        font-size: 9.2pt; break-inside: avoid; }
tr { break-inside: avoid; }
th, td { border: 0.7pt solid #8fadbd; padding: 6px 7px; text-align: left; }
th { background: #e8f0f4; }
blockquote { border-left: 3px solid #2c5f7c; margin-left: 0;
             padding: 4px 12px; background: #f2f7fa; font-size: 10.5pt; }
.answer { border: 0.8pt solid #8fadbd; border-radius: 3px;
          min-height: 5.5em; margin: 0.5em 0 1em 0; background: #fcfdfe; }
.answer.tall { min-height: 9em; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 9pt;
       background: #f2f5f7; padding: 0 2px; }
hr { border: none; border-top: 1px solid #c9dbe4; margin: 1.1em 0; }
strong { color: #000; }
"""

def main(src, out):
    body = markdown.markdown(open(src).read(),
                             extensions=["tables", "smarty", "md_in_html"])
    HTML(string=f"<html><head><meta charset='utf-8'><style>{CSS}</style>"
                f"</head><body>{body}</body></html>").write_pdf(out)
    print(f"wrote {out}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

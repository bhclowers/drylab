#!/usr/bin/env python3
r"""Render instructor-key markdown ($$...$$ display, $...$ inline) to PDF.

Equations are typeset OFFLINE via matplotlib mathtext to vector SVG and
embedded as data URIs — MathJax-quality output without a JS engine, which
the weasyprint print pipeline does not have. Pre-flight parses every block
(display AND inline) so all TeX errors surface at once.

INLINE MATH (added 2026-08-27) is baseline-aligned exactly: mathtext's
parser reports the box height and depth, and math_to_image emits an SVG of
precisely that box, so `height`/`vertical-align` follow from the metrics
rather than from a fudge factor. Inline math is rendered at BODY_PT so it
matches the surrounding text.

DELIMITER CONTRACT: a `$` means math. A literal dollar sign in the source
must be written `\$`, or it will be swallowed as an inline delimiter.

mathtext dialect notes (verified against matplotlib in this environment,
2026-08-27): \geq not \ge; \overset not \xrightarrow; NO \boxed and NO
\tfrac (use \frac). \text{}, \! and \checkmark DO parse here despite the
earlier note — but a markdown TABLE cell cannot contain a literal `|`, so
absolute values inside table cells must be written \mid…\mid, never
|…| or \left|…\right|.

Usage: python render_key.py <key.md> <out.pdf>
"""
import base64, html, io, re, sys
import matplotlib; matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import MathTextParser, math_to_image
import markdown
from weasyprint import HTML

#: Body text size. The CSS below reads this via the __BODY_PT__ token so the
#: stylesheet and the inline-math rendering cannot disagree about it.
BODY_PT = 9.6

CSS = """
@page { size: letter; margin: 2.2cm 2.2cm 2.4cm 2.2cm;
        @bottom-center { content: counter(page) " / " counter(pages); font-size: 8.5pt; color: #666; } }
body { font-family: "DejaVu Sans", sans-serif; font-size: __BODY_PT__pt; line-height: 1.42; color: #1a1a1a; }
h1 { font-size: 16pt; border-bottom: 2px solid #2c5f7c; padding-bottom: 4px; color: #2c5f7c; }
h2 { font-size: 12.5pt; color: #2c5f7c; margin-top: 1.4em; border-bottom: 1px solid #c9dbe4; padding-bottom: 2px; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.6pt; background: #f2f5f7; padding: 0 2px; border-radius: 2px; }
table { border-collapse: collapse; margin: 0.7em 0; font-size: 8.8pt; width: 100%; }
th, td { border: 0.6pt solid #9db8c6; padding: 3.5px 6px; text-align: left; vertical-align: top; }
th { background: #e8f0f4; }
li { margin: 0.25em 0; }
hr { border: none; border-top: 1px solid #c9dbe4; margin: 1.2em 0; }
strong { color: #000; }
.eq { text-align: center; margin: 0.55em 0 0.65em 0; }
.eq img { max-width: 100%; height: auto; }
img.imath { display: inline-block; }
"""

def tex_to_svg(tex, fontsize=11.5):
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${tex}$", fontsize=fontsize)
    buf = io.BytesIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.02,
                transparent=True)
    plt.close(fig)
    return buf.getvalue()

def tex_to_inline_html(tex, parser):
    """One inline expression as a baseline-aligned <img>.

    The parser reports (width, height, depth) of the math box and
    math_to_image emits an SVG of exactly that box, so the CSS height and
    vertical-align are the measured metrics, not a tuned offset.
    """
    prop = FontProperties(size=BODY_PT)
    _w, h, d, _g, _r = parser.parse(f"${tex}$", dpi=72, prop=prop)
    buf = io.BytesIO()
    math_to_image(f"${tex}$", buf, prop=prop, dpi=72, format="svg")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (
        f'<img class="imath" src="data:image/svg+xml;base64,{b64}" '
        f'alt="{html.escape(tex, quote=True)}" '
        f'style="height:{h:.2f}pt;vertical-align:-{d:.2f}pt"/>'
    )


def main(src_path, out_path):
    src = open(src_path).read()
    parser = MathTextParser("path")

    # Display math first, so inline extraction cannot see inside a $$ block.
    blocks = re.findall(r"\$\$(.+?)\$\$", src, re.S)
    cnt = iter(range(len(blocks)))
    proc = re.sub(r"\$\$(.+?)\$\$",
                  lambda m: f"EQPLACEHOLDER{next(cnt)}ENDEQ", src, flags=re.S)
    for a, b in [(r"\(u_{opt} = \sqrt{B/C}\)", "u_opt = √(B/C)"),
                 (r"\(H_{min} = A + 2\sqrt{BC}\)", "H_min = A + 2√(BC)"),
                 (r"\(\sqrt{B/C}\)", "√(B/C)"),
                 (r"\(A + 2\sqrt{BC}\)", "A + 2√(BC)")]:
        proc = proc.replace(a, b)

    # Escaped dollars are literal text; park them so they cannot open math.
    proc = proc.replace(r"\$", "ESCAPEDDOLLARTOKEN")
    inline = re.findall(r"\$([^$\n]+?)\$", proc)

    # Pre-flight BOTH classes before rendering anything, so every TeX error
    # in the document surfaces in one run rather than one per invocation.
    body_prop = FontProperties(size=BODY_PT)
    bad = []
    for i, t in enumerate(blocks):
        try:
            parser.parse("$" + " ".join(t.split()) + "$", dpi=72)
        except Exception as e:
            bad.append(("display", i, t[:60], str(e).splitlines()[-1][:100]))
    for i, t in enumerate(inline):
        try:
            parser.parse("$" + t + "$", dpi=72, prop=body_prop)
        except Exception as e:
            bad.append(("inline", i, t[:60], str(e).splitlines()[-1][:100]))
    if bad:
        for kind, i, t, msg in bad:
            print(f"{kind} TeX {i} ({t!r}): {msg}", file=sys.stderr)
        return 1

    imgs = {i: ('<div class="eq"><img src="data:image/svg+xml;base64,'
                + base64.b64encode(tex_to_svg(" ".join(t.split()))).decode()
                + '" alt="equation"/></div>') for i, t in enumerate(blocks)}
    iimgs = {i: tex_to_inline_html(t, parser) for i, t in enumerate(inline)}
    icnt = iter(range(len(inline)))
    proc = re.sub(r"\$([^$\n]+?)\$",
                  lambda m: f"IMATHPLACEHOLDER{next(icnt)}ENDIMATH", proc)

    body = markdown.markdown(proc, extensions=["tables", "smarty"])
    for i, h in imgs.items():
        body = body.replace(f"EQPLACEHOLDER{i}ENDEQ", h)
    for i, h in iimgs.items():
        body = body.replace(f"IMATHPLACEHOLDER{i}ENDIMATH", h)
    body = body.replace("ESCAPEDDOLLARTOKEN", "$")
    assert "EQPLACEHOLDER" not in body
    assert "IMATHPLACEHOLDER" not in body
    HTML(string=f"<html><head><meta charset='utf-8'>"
                f"<style>{CSS.replace('__BODY_PT__', str(BODY_PT))}</style>"
                f"</head><body>{body}</body></html>").write_pdf(out_path)
    print(f"wrote {out_path} ({len(blocks)} display, {len(inline)} inline "
          f"typeset equations)")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

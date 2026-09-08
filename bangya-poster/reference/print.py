#!/usr/bin/env python3
"""Wrap poster.html for print: bleed + crop marks, page = trim + 2*(bleed+marklen)."""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(HERE, "poster.html")
OUT  = os.path.join(HERE, "poster_print.html")

TRIM_W, TRIM_H = 1400, 1000
BLEED   = 5      # mm of bleed on every side
MARKLEN = 10     # mm length of each crop mark
T       = 0.25   # mm mark stroke
M       = BLEED + MARKLEN          # page margin outside the trim box
PW, PH  = TRIM_W + 2*M, TRIM_H + 2*M

CSS = f"""
@page{{size:{PW}mm {PH}mm;margin:0}}
html,body{{margin:0;padding:0;width:{PW}mm;height:{PH}mm;background:#fff;overflow:hidden}}
*{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
/* the sheet is authored at 1 CSS px = 1 mm; scale it into real millimetres */
#pg{{position:relative;width:{PW}px;height:{PH}px;background:#fff;
  transform:scale({96/25.4:.10f});transform-origin:0 0}}
.poster{{position:absolute;left:{M}px;top:{M}px}}
.cm{{position:absolute;background:#000}}
"""

def marks():
    """Two marks per corner, offset from the trim edge by the bleed."""
    L, R = M, M + TRIM_W          # trim left / right in page coords
    Tp, B = M, M + TRIM_H         # trim top / bottom
    d = []
    for x in (L, R):              # verticals, above and below the trim box
        for y0 in (0, B + BLEED):
            d.append(f'<div class="cm" style="left:{x-T/2}px;top:{y0}px;'
                     f'width:{T}px;height:{MARKLEN}px"></div>')
    for y in (Tp, B):             # horizontals, left and right of the trim box
        for x0 in (0, R + BLEED):
            d.append(f'<div class="cm" style="left:{x0}px;top:{y-T/2}px;'
                     f'width:{MARKLEN}px;height:{T}px"></div>')
    return "".join(d)

s = open(SRC, encoding="utf-8").read()
s = s.replace("</style></head>", "</style><style>" + CSS + "</style></head>", 1)
s = s.replace("<body>", '<body><div id="pg">', 1)
s = s.replace("</body>", marks() + "</div></body>", 1)
open(OUT, "w", encoding="utf-8").write(s)
print(f"{OUT}  page {PW}x{PH} mm  trim {TRIM_W}x{TRIM_H}  bleed {BLEED}  marks {MARKLEN}")

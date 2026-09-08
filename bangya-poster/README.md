# bangya-poster

A Claude Code skill for a conference poster built as one HTML sheet at 1 CSS px = 1 mm:
styleboard · ranked layout candidates · figures rendered by script from the paper's data ·
`feedback_N.md` rounds verified by render and overflow probe · Chrome → Ghostscript export to a
CMYK, bled, crop-marked, font-outlined print PDF.

Distilled from the ECCV 2026 ByteLOOM poster (140 × 100 cm, ~17 hours, six feedback rounds).
`TRAJECTORY.md` is the record; `SKILL.md` is the reusable process.

## The parts that carry their weight

**1 CSS px = 1 mm.** The sheet is a 1400 × 1000 px div. Every size discussed is a millimetre;
print is one `transform: scale(96/25.4)`; nothing is re-laid out for export.

**Choose from rendered candidates.** Six styles as the same real fragment, then ranked
layout wireframes. The user picks and prunes; nothing about style or structure is assumed.

**`PLACEHOLDERS.md` is the canvas.** Status, section map, rules, verified facts (with the
measurement), block inventory, a decisions log with revert cost. It survived two context
compactions and is what "continue" means.

**Figures from data, by script, sources measured first.** Baselines did not share
resolution or frame count; sampling by absolute index produced a wrong figure once. Sample by
normalised position, crop by fraction of frame, record the alignment.

**Look before saying done.** A geometry probe (`check.py`) catches overflow; only a rendered
look caught the sheet printing at 26 % in a corner. Sixty percent of feedback is geometry, and
the items that recur are alignments visible in the render.

**Export verified from the bytes.** TrimBox exact to the micron, zero embedded fonts, zero
DeviceRGB, an OutputIntent — then rasterised corners for crop marks and real glyphs.

## Files

```
SKILL.md                      the procedure, conventions, gotchas
TRAJECTORY.md                 the record: sessions, phases, the 43 feedback items, what hurt
bangya-poster-pipeline.html   one-page picture
reference/
  print.py        wrap the sheet in trim + bleed + crop marks, scale px → mm
  prologue.ps     pdfmark: TrimBox / BleedBox / ArtBox + OutputIntent
  export_pdf.sh   Chrome → Ghostscript: CMYK via ICC, fonts outlined, boxes stamped
  check.py        headless overflow probe by real geometry
  qr.py           vector QR codes (segno)
```

The `reference/` scripts carry the ECCV sheet's constants (1400 × 1000, Fogra 39, the ICC
path); change those, keep the pipeline.

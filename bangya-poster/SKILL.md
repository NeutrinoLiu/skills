---
name: bangya-poster
description: Bangya's pipeline for an academic conference poster built as one HTML sheet at 1 CSS px = 1 mm — a rendered styleboard and ranked layout candidates to choose from, a hand-maintained PLACEHOLDERS.md canvas, every figure rendered by script from the paper's own data, numbered feedback_N.md rounds verified by headless render and a DOM overflow probe, then a Chrome → Ghostscript export to a CMYK, bled, crop-marked, font-outlined print PDF plus the PNG and thumbnail a submission site asks for. Use when the user wants to design, build, revise, or export a conference or academic poster, or mentions bangya-poster.
---

# bangya-poster

Build a conference poster the way Bangya likes to work. Distilled from a real build (ECCV
2026, 140 × 100 cm landscape, ~17 hours over two days, six feedback rounds); the record is in
[TRAJECTORY.md](TRAJECTORY.md), the one-page picture is
[bangya-poster-pipeline.html](bangya-poster-pipeline.html), and `reference/` holds the scripts
that carried over unchanged.

## Conventions (hold through every phase)

- **The sheet is one HTML file, authored at 1 CSS px = 1 mm.** A 140 × 100 cm poster is a
  1400 × 1000 px `.poster`. Every size in the conversation is then a millimetre, print is a
  single `transform: scale(96/25.4)`, and nothing is re-laid out for export. Asset paths stay
  relative so the file stays small and editable; `--embed` inlines base64 only to publish a
  self-contained copy.
- **`PLACEHOLDERS.md` is the working canvas**, hand-maintained, never regenerated: status
  table, section map, the rules that hold the sheet together, verified facts (measured, with
  the measurement), a block inventory by id (`V` figure · `T` table · `X` words · `L` logo ·
  `Q` QR), a decisions log with a *revert cost* column, and a next list. When the user says
  "continue", this file is the state.
- **Style is chosen, never assumed.** A styleboard of ~6 candidates, each rendering the *same*
  real content so they compare fairly; more if asked. Layout the same way: ranked
  space-allocation candidates the user picks from and prunes.
- **Every figure is rendered by script from the paper's own data** — frame grids from the
  result videos and the dataset, the real mesh beside its real coordinate map, a real curation
  chain rather than a redrawn diagram. Tiles go out *unlabelled*: labels stay live HTML text so
  they are vector in the PDF.
- **Words are rationed and type never shrinks.** Problem statement ≤ 25 words, contributions
  three bullets ≤ 12 words each. If a block will not fit, cut the block, not the type size. Tile
  size is set by the container (`min(box_w/cols, box_h/rows)`); under ~55 mm nothing reads at
  1.5 m. Never raise a row or column count without re-measuring.
- **Feedback arrives as `feedback_N.md`** — numbered bullets, terse, sometimes misspelled.
  Implement every item, render, *look*, then reply. About 60 % of items are pure geometry
  ("larger", "centralize", "no gaps between cols"), and the ones that recur across rounds are
  alignments you could have seen in the render.
- **Illustrations that cannot be rendered from data are generated** with the user's image
  endpoint (`image_gen_api.json`: `base`, `key`, `model` — never copy it anywhere). Write a
  long prompt, show the result, expect semantic corrections ("don't mirror the mesh", "the
  second step colours vertices, the last the whole mesh") and regenerate.
- **Temp files in `_claude_tmp/`** inside the project, never `/tmp`.

## Pipeline

### 1. Brief — read the paper and the print spec
Read the paper source (`main.tex`, `sec/*.tex`, `images/`), the venue's print spec (sheet
size, colour profile, bleed, crop marks, fonts, filename pattern), and the project links (page,
dataset). Fix the sheet size and the 1 px = 1 mm rule before drawing anything.
**Done when:** sheet size, orientation, print requirements and the exact filename sit at the
top of `PLACEHOLDERS.md`.

### 2. Styleboard
Render ~6 candidate identities as the same poster fragment each (title block + one real
section) on one page the user can compare. Expect "more styles" and a correction of register
("it's an academic poster — multi-column, clean fonts, not superficial"). Converge to one:
type pair, ink, accent, band and rule colours.
**Done when:** the user names a candidate and its tokens are in `PLACEHOLDERS.md`.

### 3. Layout candidates
Propose space allocations as rendered wireframes with dotted placeholder blocks, ranked
"preferred to less preferred" with the reason. The user picks one and prunes: which sections
get a solid bar (usually only the evidence band), which blocks to drop or fuse, what is a
section versus a sub-result.
**Done when:** one layout file is the base and the section map lists every block id with its
column or band.

### 4. Content and assets
`build/content.py` holds every word and table; `build/assets.py` renders every tile;
`build/qr.py` makes vector QR codes (segno, ECC M, 4-module quiet zone); logos as true vector
where possible. **Measure the sources before sampling** — resolutions and frame counts differ
across methods, so sample by normalised position and crop by fraction of frame, and record the
alignment you find under *verified facts*. Decide early which paper figure to reuse and which
to redraw.
**Done when:** every block in the inventory is ✅ or has an owner, and `build/poster.py`
assembles `poster.html` from real files only.

### 5. Wire-up and the global size pass
Replace every placeholder, then measure: `reference/check.py` loads the sheet headless and
reports any container whose descendants spill outside it, by real geometry (`scrollHeight`
lies for overflowing flex children). Fix by cutting content or re-allocating columns.
**Done when:** `check.py` prints *no overflow* and you have looked at a full render.

### 6. Feedback rounds — until the user stops
`feedback_N.md` per round, plus short chat lines late in a round. For each item: change,
render, look, tick. Typical rounds: section purpose ("tell people what the task is"), space
("framework takes two columns, fill the full width"), evidence layout ("A and B aligned, ours
last, no gaps between sequences"), attribution and wording ("07 title should be *Mani4D
curation*", "remove the big numbers"), identity ("logos as large as possible, floating so they
never wrap the title"). Log decisions and their revert cost.
**Done when:** the latest `feedback_N.md` is fully addressed and `check.py` is still clean.

### 7. Export
`reference/export_pdf.sh` is the whole pipeline: `print.py` wraps the sheet in a page of
trim + bleed + crop marks and scales it into millimetres; Chrome prints it; Ghostscript
converts to CMYK through the venue's ICC profile, outlines every font, and stamps TrimBox /
BleedBox / ArtBox and an OutputIntent from `prologue.ps`. Then **verify from the bytes**: box
sizes in mm, `/BaseFont` count 0, `/DeviceRGB` count 0, and a rasterised look at each corner
for crop marks and real glyphs. For a submission site's PNG: Chrome screenshot with
`--force-device-scale-factor` chosen to hit the pixel cap; the thumbnail letterboxed on the
paper colour to the exact size asked.
**Done when:** the file named per the spec passes the numeric checks and the corner crops, and
its size is under the cap.

## Gotchas that cost real time

- Chrome prints 1 CSS px = 1/96 in, so a 1 px = 1 mm sheet prints at 26 % in a corner unless
  scaled by 96/25.4. Only a rendered look catches this; every number passes.
- Chrome rounds the page up by ~0.19 mm; `gs -dFIXEDMEDIA -dPDFFitPage` with exact point sizes
  pulls the TrimBox back to 1400.000 × 1000.000.
- `gs -dSAFER` refuses to read the ICC profile ("Permission denied" inside `--runpdf--`); use
  `-dNOSAFER` with a local copy of the profile.
- The ICC stream in `pdfmark` ends with `/CLOSE`, not `/PUT`; a stray `/PUT` collapses the
  output to 100 KB with a `rangecheck`.
- `mix-blend-mode: multiply` survives as live transparency, so the result is a CMYK PDF 1.4
  with an OutputIntent, not a PDF/X claim. Say so.
- Chrome's updater keeps the headless process alive for minutes after the screenshot lands;
  run it with the crashpad and update flags off and a hard timeout.
- JPEG logos print as white boxes on some RIPs; get vector or transparent PNG ≥ 300 dpi.
- Effective resolution = pixels / mm × 25.4; report the weakest raster on the sheet.

## After the build

When geometry feedback starts repeating, the fix is a channel, not more prose: a
direct-manipulation extension over the local HTML for moves and resizes, comments pinned to
the element for semantics. The project's `_design_survey/` is the survey that reached that
conclusion.

# Trajectory: ByteLOOM poster, ECCV 2026

The record behind `bangya-poster`, reconstructed from the session log of
`~/Desktop/2026summer/submissions/ECCV26` (project `107a3716`, plus one side session). Times
are UTC as logged.

## The sessions

| Session | Role | Span | Scale |
|---|---|---|---|
| Main (`107a3716`, first half) | style → layout → content → six feedback rounds → print export | Aug 23 07:29 – Aug 24 00:50 | ~50 user turns; the same session later built the video |
| Side (`dea945b7`) | "stop typing feedback": survey of direct-manipulation design tooling | Aug 24 05:54 – 07:18 | 7 user turns, published as `_design_survey/` |

## Phase 1 — style (07:29 – 08:30)

- Brief: "help me design the academic poster for my eccv submission. first lets settle on the
  visual style. give me 6 visual candidates in html, then let me choose from." Six candidates,
  each the same title block and section.
- "more styles" → a second set. Then the register correction that shaped everything after:
  "its an academic poster and they should be of multi column layout and clean font styles. not
  make it so superficial."
- Chosen: **F** — Newsreader over Karla, slate ink `#2B3440`, ochre accent `#A9760F`.
- Two reference posters pasted as screenshots set the target density.

## Phase 2 — structure (08:43 – 10:52)

- Structural rulings came before any layout: "unseen human should not be a stand alone
  section, it is just one of the sub results"; "check eccv_supp/webpage/videos, there are
  other sub tasks our framework can do, take them in".
- "how you recommend the space allocation? rank by preferred to less preferred" → three layout
  candidates as dotted wireframes. "lets work on C3, yet we dont need a solid bar for section
  10. only section 9 needs a bar." Then "we dont really need the row of V1, X1, X3 — eliminate
  or fuse them."
- C3: five method columns over one full-width evidence band.

## Phase 3 — content and assets (11:11 – 20:22)

- "then lets start working on the content, clean up the useless drafts. feel free to adjust
  the sizing of each section." `PLACEHOLDERS.md` became the canvas: status, section map,
  rules, verified facts, block inventory, decisions log.
- `build/assets.py` rendered 36 frame grids. The measurement that mattered: UniAnimate-DiT is
  720 × 1280 / 81 frames while everything else is 576 × 1024 / 97, so sampling by absolute
  index had produced a figure where UniAnimate "had no object". Evalset ↔ video alignment
  found by RMSE match: `evalset_frame = 241 + 2 × video_frame`. Rendered and RCM verified to
  share the GT camera by compositing one over the other.
- Decisions with revert cost: no teaser (11 % of the sheet), V9 four rows not five (59 mm vs
  43 mm tiles), four cache views drawn where nine are cached, the paper's system figure reused
  rather than redrawn, stage I shown as its annotation type because the data is proprietary.
- 20:22 a screenshot and "go do all the rest" → tables typeset, words written, QR codes,
  vector logos, global size pass with `build/check.py`.

## Phase 4 — feedback rounds (23:10 – 00:46, then six files)

- 23:10 a 9036 × 1337 strip of the rendered header: "why there is STILL a contention between
  the logo space and the title space??? why my affiliation is of two lines" — the first of
  fourteen chat items in an hour ("human in the second line", "keep all the grey explanation
  words the same font size", "'proprietary studio video' → large scale video", "add a formula
  for the rcm cache", "meter not o(n2), remove o(n2)").
- Then `feedback_1.md` … `feedback_6.md`, 43 bullets:
  1. purpose of sections 01/02; framework across two columns; curation pipeline redrawn in our
     style; no big numbers; explain MEt3R and T-SSIM; drop 09.B; 4 rows × 12 cols with three
     sequences; vertical labels.
  2. section 01 public-facing, none of our own vis; RCM illustration via the image endpoint;
     curriculum clearer across two columns; A/B grids aligned; crops moved down to hands and
     object.
  3. larger task image; shorter text; RCM explainer regenerated ("the cube in the coord does
     not make any sense"); curriculum diversity; ours last row; smaller labels; A and B *still*
     not aligned.
  4. wider first column; framework full width; RCM text right ("you should not mirror flip the
     mesh"); 06/07/08 resized; ours last column; no gaps between rows; "07 title should be
     mani4d curation".
  5. icons and QR as large as possible; task illustration redrawn via API; pipeline in four
     rows; remove "Nine views are cached; four shown"; "there are still pixel gap in 09.A".
  6. logos floating and centred; body text small grey; curriculum tag placement; pipeline
     image centred without border; spare height into 09's crops.
- Classified afterwards in `_design_survey/07-recommendation.md`: ~26 of 43 geometry, ~17
  semantic; "A/B not aligned, gaps between cols" recurs in rounds 2, 4 and 5.

## Phase 5 — print export (00:50 →)

- After a context compaction: "lets call it a day, export the pdf." Spec: 1400 × 1000 mm,
  CMYK Fogra 39, 5–10 mm bleed, crop marks, fonts outlined, `5222_Liu_1400x1000mm.pdf`.
- Built `build/print.py` (page = trim + bleed + marks, `transform: scale(96/25.4)`),
  `build/prologue.ps` (pdfmark boxes + OutputIntent), `build/export_pdf.sh` (Chrome →
  Ghostscript). Errors in order: `-dSAFER` blocked the ICC; a stray `/PUT` where `/CLOSE`
  belonged; TrimBox off by 0.19 mm until the FitPage scale was folded in; the sheet rendering
  at 26 % in a corner — caught only by rasterising and looking.
- Verified from the bytes: TrimBox 1400.000 × 1000.000, BleedBox 1410 × 1010, MediaBox
  1430 × 1030, 0 embedded fonts, 0 DeviceRGB, OutputIntent Coated FOGRA39; corner crops at
  150 dpi; ink coverage; a resolution audit (weakest raster 94 dpi, the framework figure).
- Later, for the submission site: PNG at 4032 × 2880 (6.98 MB, under 5120 × 2880 / 10 MB) via
  Chrome at device scale 2.88 with the kill-timeout recipe, and a 320 × 256 thumbnail
  letterboxed on the paper colour. "why it take so long time" — Chrome without the timeout.

## The side session — stop typing feedback (Aug 24 05:54 – 07:18)

- "get our session under this dir, typically is a back and forth design detail polishment
  between you and me. so i think using language to instruct you to update some details is
  inefficient" → a survey of five architectures for direct manipulation with a coding agent, a
  two-axis taxonomy (where the canvas lives; whether the hand-edit is the source of truth or a
  message to the agent), and a recommendation for this poster: a Design-Mode-style extension
  over the local HTML for geometry, Artifact comments for semantics, an Excalidraw canvas for
  diagrams. Written up in Chinese on request and published as an artifact.

## What made it work

1. **1 CSS px = 1 mm.** Every conversation about size was in millimetres; print was a scale.
2. **Choosing from rendered candidates** — style and layout — instead of describing them.
3. **`PLACEHOLDERS.md` as the canvas**, with verified facts and a decisions log that survived
   two context compactions.
4. **Figures from data, by script**, with the sources measured first.
5. **A geometry probe plus a rendered look** before every "done".
6. **Export verified from the PDF bytes**, then by looking at rasterised corners.

## What hurt

- Geometry feedback in prose: the same alignment took three rounds. The side session exists
  because of it.
- Saying "fits" from numbers alone — the 26 % print bug passed every check that was not a look.
- Chrome's lingering process, twice (export, then PNG) — always run it with a timeout.
- Attribution left open: stage I frames from another paper's results, dataset tiles that need
  their citations. Flagged, not resolved.

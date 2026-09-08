---
name: bangya-video
description: Bangya's pipeline for a five-minute paper presentation video built from an HTML deck — cuts planned in markdown, a deck.html checkpoint showing every cut with its hold time and script for the user to approve, assets rendered by script (Chrome slide frames, Blender turntables, condition streams cut from the dataset), edge-tts narration measured to set the timings, and ffmpeg assembly with a reserved one-line caption strip. Use when the user wants a paper video, a narrated talk or presentation video, a conference supplementary video, or mentions bangya-video.
---

# bangya-video

Build a narrated presentation video the way Bangya likes to work. Distilled from a real build
(ECCV 2026 paper video, 16 cuts, 4:58, first delivery in one evening, then a revision day);
the record is in [TRAJECTORY.md](TRAJECTORY.md), the one-page picture is
[bangya-video-pipeline.html](bangya-video-pipeline.html), and `reference/` holds the scripts
that carried over.

## The contract

Bangya set the shape of the work in the first message, and it held:

1. **Design the cuts** in a markdown scratch book.
2. **Implement an HTML deck** showing every cut with its expected hold time and its script.
   **This is the checkpoint — bring the user in here.**
3. **Render the assets** each cut needs, and generate the narration with TTS meanwhile.
4. **Assemble** everything into the video.

Then feedback rounds against the finished file.

## Conventions (hold through every phase)

- **One source file.** `build/cutdata.py` holds each cut as `{n, title, dur, script, body}`.
  `deck.html` is generated from it and is *both* the review checkpoint and the render source,
  so the frames the user approves are the frames that render. Everything else is derived.
- **Design for 480p.** The video is watched small and often at low bitrate. Type floor 32 px
  on the 1920-wide frame (14 px at 854 × 480); at most ~30 words to read per cut, counted by
  the build; one idea and at most two regions per cut; short words; **video panels do the
  arguing**. A paper's system figure is unreadable here — redraw it as four boxes.
- **Correspondence is not optional.** Where a cut shows an input beside an output, both come
  from the same sequence, and the streams are synced by shared frame index, not by eye. Use
  different sequences across cuts; the one that carries the argument stays where the
  narration names it.
- **Don't crop assets unless necessary.** Lock panels to the media's aspect; use `contain`.
- **Rotate what is 3D, not what is cached.** A mesh or a coordinate map gets a seamless
  turntable (a still cannot show the back). A cache of views *is* a set of stills — show them
  as stills, the same angles wherever else they appear.
- **Title verbatim from the paper**, even its typos; flag the typo, do not fix it.
- **Captions live in a reserved strip** — not overlaid on the slide, not a black matte around
  a shrunken slide. The deck lays out at 1920 × 1000 and the bottom 80 px belong to the
  script, white on black, **one line always**: a long block is split into consecutive blocks,
  never wrapped. No `.srt` sidecar beside the file — VLC and IINA auto-load it and it looks
  burned in.
- **Narration ~130 wpm, measured.** Hold = lead + the engine's real duration + tail. Loudness
  normalised two-pass to −16 LUFS.
- **Verify by measurement and by looking.** DOM probe for overflow; a frame at each cut's
  midpoint against its slide PNG; speech onset by `silencedetect`; every cut downsampled to
  480p and read; then a real watch-through. The bug that scales a sheet to 26 % passes every
  number.
- **Temp files in `_claude_tmp/`**; per-cut MP4s in `cuts/`, disposable.

## Pipeline

### 1. Plan the cuts — `cuts.md`
Movements (setup / method / results / close), then a cut sheet: number, title, target hold,
what is on screen, and the narration for each. Failures before the fix, so the viewer wants
the method cut. Budget ≤ 5:00, 600–650 words.
**Done when:** every cut has a title, a visual and a script, and the holds sum under the cap.

### 2. The checkpoint — `deck.html`
`build/deck.py` renders every cut as a 1920 × 1000 frame with its hold and script beside it,
plus a 480p toggle. Show it and take the decisions here: TTS engine and voice, captions, any
cut to rebuild. Video panels are `<div class="vp" data-clip data-fit>` sized off one CSS
variable (`--vh`), never `aspect-ratio + flex` — with the aspect locked, an auto-width panel
takes its width from its caption and silently overflows its neighbours.
**Done when:** the user has reviewed the deck and every open decision is answered.

### 3. Assets and narration — in parallel
- `reference/shots.py`: Chrome screenshots each cut with the `<video>` elements removed and
  probes every panel's box out of the DOM into `boxes.json`, so ffmpeg overlay coordinates
  are never hand-computed. It also reports any element outside its frame.
- `reference/orbit.py` + `orbits.py`: Blender turntables — `tex`, `rcm` (the *Generated*
  texture coordinate rendered raw is exactly position-in-bounding-box), `white`; transparent
  film, panel colour composited after. Still sheets of N evenly spaced angles from the same
  frames.
- `reference/conds.py`: condition streams cut from the dataset by shared index, spread across
  the whole take to match the result's frame count; depth colourised on one range held across
  the clip.
- `reference/tts.py`: `edge-tts` per cut → mp3 + word-boundary srt → `timing.json`.
**Done when:** every clip a cut references exists, plays under `ffprobe`, and looks right in a
sampled frame; `timing.json` is written from measured durations.

### 4. Assemble — `reference/assemble.py`
Per cut: loop the PNG, overlay each looped clip into its probed box (`cover` = scale with
`force_original_aspect_ratio=increase` + crop; `contain` = decrease + pad), burn the captions
from an ASS built off the cut's srt, encode. Concat, two-pass `loudnorm`, mux. Two encoders
in parallel, not four — wide inputs get the run OOM-killed.
**Done when:** the file plays, its duration matches the plan, and the verification list above
passes.

### 5. Feedback rounds
`video_feedbacks/feedback_N.md`, terse bullets. Expect: correspondence ("make sure your video
and your input correspond", "not a random combination"), cropping, stills versus rotation,
tool names and attributions in the pipeline cut, title wording. Fix in `cutdata.py`, re-run
only the stages the edit touches (script → `tts.py` + `assemble.py`; slide → `deck.py` +
`shots.py` + `assemble.py`), sample frames from the *final* file, look.
**Done when:** the latest feedback file is fully addressed and the watch-through is clean.

## Gotchas that cost real time

- Chrome writes the screenshot in seconds, then its updater keeps the process alive for
  ~3 minutes; without a kill timeout sixteen cuts took 55 minutes.
- A looping `<video>` keeps Chrome's virtual clock from going quiescent, so `--screenshot`
  never fires — strip them in render mode.
- `magick -trim` with `%@` re-measures *inside* the trimmed image and always reports `+0+0`;
  use `%w %h %X %Y` for a shared crop box, or it anchors to the canvas corner.
- libx264 rejects odd dimensions under yuv420p; pad cells to even.
- The system Python may lack numpy and refuse `pip install` (PEP 668) — make a venv in
  `_claude_tmp/` and point the one script that needs it there.
- A `.npy` can be a zip around `data.npy`; check the magic bytes before guessing the format.
- Exit 137 from ffmpeg is the OOM killer, not a codec error.

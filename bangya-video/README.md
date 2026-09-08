# bangya-video

A Claude Code skill for a narrated paper presentation video built from an HTML deck:
cuts planned in markdown · a `deck.html` checkpoint with hold time and script per cut ·
assets rendered by script (Chrome frames, Blender turntables, dataset condition streams) ·
`edge-tts` narration measured to set the timings · ffmpeg assembly with a reserved one-line
caption strip.

Distilled from the ECCV 2026 ByteLOOM video (16 cuts, 4:58, delivered in one evening, then a
revision day). `TRAJECTORY.md` is the record; `SKILL.md` is the reusable process.

## The parts that carry their weight

**A four-step contract with a named checkpoint.** Cuts in markdown → HTML deck with time and
script per cut, *user reviews here* → assets and TTS in parallel → assemble. The user set this
shape in the first message and it never needed changing.

**One source, one file.** `cutdata.py` holds every cut's slide HTML and narration;
`deck.html` is both what the user approves and what the renderer screenshots.

**Design for 480p.** Type floor 32 px on 1920, ~30 words per cut, one idea, short words,
video panels do the arguing. Written down before the first slide.

**Geometry from the DOM.** Panel boxes are probed with `getBoundingClientRect()` and handed to
ffmpeg; overlay coordinates are never typed. The same probe reports overflow.

**Correspondence built, not assumed.** Condition and result from the same sequence, streams
synced by shared frame index, nothing cropped, different sequences across cuts. Turntables for
what is 3D; stills for what is a cache of stills.

**Captions in a reserved strip.** Not overlaid, not a matte: the deck lays out at 1920 × 1000
and the bottom 80 px carry one line of script, split into blocks rather than wrapped. Took
three rounds to arrive at; now a convention.

## Files

```
SKILL.md                     the contract, conventions, procedure, gotchas
TRAJECTORY.md                the record: two days, the feedback items, what hurt
bangya-video-pipeline.html   one-page picture
reference/
  deck.py        cutdata → deck.html (review mode, 480p toggle, ?cut=N render mode)
  deck.css       the frame stylesheet: 32 px floor, --vh panel sizing, --fh caption reserve
  shots.py       Chrome screenshots + DOM probe → boxes.json, with the kill timeout
  tts.py         edge-tts per cut → mp3 + word-boundary srt → timing.json
  assemble.py    overlay clips into probed boxes, ASS captions, concat, loudnorm, mux
  orbit.py       Blender turntable (tex / rcm / white), run inside Blender
  orbits.py      drives orbit.py per clip, muxes frames, builds still sheets
  conds.py       condition streams cut from a dataset by shared frame index; depth colourised
```

The `reference/` scripts carry the ByteLOOM deck's names and paths; change those, keep the
pipeline. `conds.py` and `orbit.py` assume that project's dataset layout and meshes.

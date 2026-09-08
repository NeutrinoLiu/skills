# -*- coding: utf-8 -*-
"""Narrate each cut with edge-tts, measure it, and derive the real slide timings.

    python3 build/tts.py            # all cuts
    python3 build/tts.py 3 7        # just those (timings.json is still rebuilt from all)

Writes audio/cutNN.mp3, audio/cutNN.srt (word-boundary timings straight from the engine),
and audio/timing.json — the authoritative per-cut hold times the assembler works from.

Hold = LEAD + measured speech + TAIL, so narration never starts flush on the cut and each
slide is still up for a beat after the sentence lands.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cutdata import CUTS                                              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
AUD = os.path.join(ROOT, "audio")
EDGE = os.path.expanduser("~/Library/Python/3.9/bin/edge-tts")

VOICE = "en-US-AndrewMultilingualNeural"
RATE = "-4%"        # a touch under default: the slides are sparse and want reading time
LEAD = 0.25         # silence before the first word of a cut
TAIL = 0.85         # silence after the last word, before the cut changes
TAIL_LAST = 2.60    # the closing card holds longer

# Extra dwell, where the visual needs longer than the sentence does: 06 and 07 carry the core
# idea on static images, 12 and 15 ask the viewer to actually watch four clips.
EXTRA = {6: 1.0, 7: 1.0, 12: 0.6, 15: 0.4}


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def speak(c):
    mp3 = os.path.join(AUD, f"cut{c['n']:02d}.mp3")
    srt = os.path.join(AUD, f"cut{c['n']:02d}.srt")
    r = subprocess.run([EDGE, "--voice", VOICE, f"--rate={RATE}", "--text", c["script"],
                        "--write-media", mp3, "--write-subtitles", srt],
                       capture_output=True, text=True, check=False)
    if not os.path.exists(mp3) or os.path.getsize(mp3) < 2000:
        return c["n"], None, (r.stderr or "")[-400:]
    return c["n"], dur(mp3), None


def main():
    want = [int(a) for a in sys.argv[1:]] or [c["n"] for c in CUTS]
    os.makedirs(AUD, exist_ok=True)
    todo = [c for c in CUTS if c["n"] in want]

    with ThreadPoolExecutor(max_workers=4) as ex:
        got = {n: (d, e) for n, d, e in ex.map(speak, todo)}

    for n, (d, e) in sorted(got.items()):
        if e:
            print(f"cut{n:02d}  FAILED  {e}")
            return 1

    cuts, t = [], 0.0
    for c in CUTS:
        mp3 = os.path.join(AUD, f"cut{c['n']:02d}.mp3")
        if not os.path.exists(mp3):
            print(f"cut{c['n']:02d}  no audio yet — run without arguments once")
            return 1
        sp = dur(mp3)
        tail = TAIL_LAST if c["n"] == len(CUTS) else TAIL
        hold = round(LEAD + sp + tail + EXTRA.get(c["n"], 0.0), 2)
        cuts.append(dict(n=c["n"], title=c["title"], start=round(t, 2), hold=hold,
                         speech=round(sp, 2), lead=LEAD, target=c["dur"]))
        t += hold

    out = dict(voice=VOICE, rate=RATE, lead=LEAD, tail=TAIL, total=round(t, 2), cuts=cuts)
    with open(os.path.join(AUD, "timing.json"), "w") as f:
        json.dump(out, f, indent=1)

    print(f"{'cut':>4} {'speech':>7} {'hold':>7} {'target':>7} {'drift':>7}  title")
    for c in cuts:
        print(f"{c['n']:>4} {c['speech']:>6.1f}s {c['hold']:>6.1f}s {c['target']:>6}s "
              f"{c['hold'] - c['target']:>+6.1f}s  {c['title']}")
    print(f"\ntotal {t:.1f}s = {int(t) // 60}:{t % 60:04.1f}   "
          f"(target 300.0s, {t - 300:+.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

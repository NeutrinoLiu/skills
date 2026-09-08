# -*- coding: utf-8 -*-
"""Assemble the finished video from the slide PNGs, the probed panel boxes, and the narration.

    python3 build/assemble.py            # video with the burned-in script
    python3 build/assemble.py --nocap    # reserve the strip but leave it empty
    python3 build/assemble.py --cuts     # per-cut MP4s only, skip the final concat
    python3 build/assemble.py --srt      # also write the subtitle sidecar

Inputs
    slides/cutNN.png          the slide chrome, 1920x1000, video panels left empty
    _claude_tmp/boxes.json    each panel's pixel box, read out of the DOM by build/shots.py
    audio/cutNN.mp3           narration
    audio/cutNN.srt           narration timed to the engine's own word boundaries
    audio/timing.json         per-cut hold times, derived from the measured narration

Output
    5222_Liu_ByteLOOM_5min.mp4   H.264 + AAC, 1920x1080, 30 fps

The narration is burned in as white Karla on a black strip across the foot of the frame. The
strip is reserved rather than overlaid or matted: the deck lays every slide out at 1920x1000
(--fh in deck.css), and the bottom 80 px of the 1080-line frame belongs to the script. So the
slide keeps its full width and nothing of it is covered or scaled down.

The strip carries exactly one line. A block too long for one line is split into consecutive
blocks — two shorter captions rather than one tall one — recursively, breaking after
punctuation, so the strip never has to grow to hold a second row of text.

A sidecar .srt is off by default and now redundant: VLC and IINA auto-load a same-basename
.srt beside the video, so it would double up on the burned-in band. --srt still writes one.

Each source clip is looped and composited into its own box. `cover` is
scale(force_original_aspect_ratio=increase) + crop, which is exactly what CSS object-fit:cover
does, so the finished frame matches the deck.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PROJ = os.path.abspath(os.path.join(ROOT, ".."))
SLIDES = os.path.join(ROOT, "slides")
AUD = os.path.join(ROOT, "audio")
TMP = os.path.join(ROOT, "_claude_tmp")
CUTDIR = os.path.join(ROOT, "cuts")
NAME = "5222_Liu_ByteLOOM_5min"
FPS = 30
LUFS = -16      # EBU R128 target for web/speech
TP = -1.5       # true-peak ceiling, dBTP

# The script strip. SLIDE_H is the height the deck renders at and must match --fh in
# deck.css and FRAME_H in shots.py; the rest of the 1080-line frame is the strip.
SLIDE_H = 1000
CAP_H = 1080 - SLIDE_H                  # 80 px reserved for the script
CAP_FS = 38                             # well over the deck's 32 px type floor
CAP_COLS = 78                           # one line only — longer blocks are split, never wrapped
FONTS = os.path.join(ROOT, "assets", "fonts")   # Karla, so the band matches the deck

ASS_HEAD = ("[Script Info]\n"
            "ScriptType: v4.00+\n"
            "PlayResX: 1920\n"
            "PlayResY: 1080\n"
            "WrapStyle: 2\n"                    # only break where we put a \N
            "ScaledBorderAndShadow: yes\n"
            "YCbCr Matrix: TV.709\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
            "Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, "
            "MarginV, Encoding\n"
            "Style: cap,Karla,%d,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,"
            "0,0,0,0,100,100,0.6,0,1,0,0,5,60,60,0,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, "
            "Text\n") % CAP_FS


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=False, **kw)
    if r.returncode:
        raise RuntimeError(f"{cmd[0]} failed\n{' '.join(cmd[:14])}\n{r.stderr[-1600:]}")
    return r


def clip_path(rel):
    """Panel clips are stored relative to video/deck.html."""
    return os.path.normpath(os.path.join(ROOT, rel))


def ass_time(t):
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


BREAKS = (",", ";", ":", ".", "!", "?", "\u2014", "\u2013")
GLUE = {"a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "for", "with", "that",
        "than", "from", "as", "by", "so", "but", "into", "over", "is", "are", "we", "you"}


def split_at(words, ok=None):
    """Halve a caption as evenly as the sentence allows: break after punctuation where
    there is any, and never orphan an article or preposition at the end of a line."""
    target = len(" ".join(words)) / 2
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if ok and not ok(a, b):
            continue
        d = abs(len(a) - target)
        if not words[i - 1].endswith(BREAKS):
            d += 45
        if words[i - 1].lower().strip(".,;:") in GLUE:
            d += 200
        if best is None or d < best[0]:
            best = (d, a, b)
    return best


def split_long(blocks):
    """Recursively halve any block too long for the single line the strip allows."""
    out = []
    for a, z, txt in blocks:
        if len(txt) <= CAP_COLS or len(txt.split()) < 4:
            out.append((a, z, txt))
            continue
        _, p_, q = split_at(txt.split())
        mid = a + (z - a) * len(p_) / (len(p_) + len(q))   # split the time by character count
        out += split_long([(a, mid, p_), (mid, z, q)])
    return out


def build_ass(n, lead):
    """The cut's own narration timings, shifted by its lead-in, as one ASS file."""
    src = os.path.join(AUD, f"cut{n:02d}.srt")
    if not os.path.exists(src):
        return None
    pos = "{\\pos(960,%d)}" % (SLIDE_H + CAP_H // 2)         # centred in the strip
    rows = [f"Dialogue: 0,{ass_time(a + lead)},{ass_time(z + lead)},cap,,0,0,0,,"
            f"{pos}{txt}" for a, z, txt in split_long(parse_srt(src))]
    out = os.path.join(TMP, f"cap{n:02d}.ass")
    with open(out, "w", encoding="utf-8") as f:
        f.write(ASS_HEAD + "\n".join(rows) + "\n")
    return out


def build_cut(cut, boxes, ass):
    n, hold = cut["n"], cut["hold"]
    png = os.path.join(SLIDES, f"cut{n:02d}.png")
    out = os.path.join(CUTDIR, f"cut{n:02d}.mp4")

    cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", png]
    for b in boxes:
        cmd += ["-stream_loop", "-1", "-i", clip_path(b["clip"])]

    parts, last = [], "0:v"
    for i, b in enumerate(boxes, start=1):
        # yuv420p cannot carry an odd dimension, and a DOM box lands on one often enough;
        # the pixel that is dropped falls on the panel's own background colour.
        w, h = b["w"] - b["w"] % 2, b["h"] - b["h"] % 2
        if b["fit"] == "contain":
            fit = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                   f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0xF1EFEA")
        else:                                        # cover — matches CSS object-fit:cover
            fit = (f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                   f"crop={w}:{h}")
        parts.append(f"[{i}:v]{fit},fps={FPS},setsar=1[p{i}]")
        parts.append(f"[{last}][p{i}]overlay={b['x']}:{b['y']}:shortest=0[b{i}]")
        last = f"b{i}"

    # the slide is already 1920xSLIDE_H, so the strip is pure padding — no rescaling
    tail = ["pad=1920:1080:0:0:black"]
    if ass:
        tail.append(f"ass=filename={ass}:fontsdir={FONTS}")
    tail.append("format=yuv420p")

    if parts:
        parts.append(f"[{last}]" + ",".join(tail) + "[v]")
        cmd += ["-filter_complex", ";".join(parts), "-map", "[v]"]
    else:
        cmd += ["-vf", f"fps={FPS}," + ",".join(tail), "-map", "0:v"]

    cmd += ["-t", f"{hold:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p", out]
    sh(cmd)
    return n, out


def build_audio(timing):
    """One track: LEAD of silence, the narration, then silence out to the cut's hold."""
    segs = []
    for c in timing["cuts"]:
        mp3 = os.path.join(AUD, f"cut{c['n']:02d}.mp3")
        wav = os.path.join(TMP, f"a{c['n']:02d}.wav")
        pad = c["hold"] - c["lead"]
        sh(["ffmpeg", "-y", "-i", mp3,
            "-af", f"adelay={int(c['lead'] * 1000)}:all=1,"
                   f"apad=whole_dur={pad + c['lead']:.3f},"
                   f"atrim=0:{c['hold']:.3f},aresample=48000",
            "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", wav])
        segs.append(wav)

    lst = os.path.join(TMP, "audio.txt")
    with open(lst, "w") as f:
        for s_ in segs:
            f.write(f"file '{s_}'\n")
    raw = os.path.join(TMP, "narration_raw.wav")
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", raw])

    # Two-pass EBU R128 to -16 LUFS. The engine's own output sits around -24 dB mean, which
    # is noticeably quiet against anything else a viewer will have open; single-pass loudnorm
    # pumps on speech, so measure first and feed the numbers back.
    r = sh(["ffmpeg", "-hide_banner", "-i", raw, "-af",
            f"loudnorm=I={LUFS}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"])
    stats = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    out = os.path.join(TMP, "narration.wav")
    sh(["ffmpeg", "-y", "-i", raw, "-af",
        f"loudnorm=I={LUFS}:TP={TP}:LRA=11"
        f":measured_I={stats['input_i']}:measured_TP={stats['input_tp']}"
        f":measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}"
        f":offset={stats['target_offset']}:linear=true,aresample=48000",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", out])
    print(f"loudness  {stats['input_i']} LUFS -> {LUFS} LUFS  "
          f"(true peak {stats['input_tp']} -> max {TP} dBTP)")
    return out


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt(path):
    blocks, cur = [], []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(line)
    if cur:
        blocks.append(cur)
    out = []
    for b in blocks:
        if len(b) < 3 or "-->" not in b[1]:
            continue
        a, z = [x.strip() for x in b[1].split("-->")]

        def sec(x):
            hh, mm, rest = x.split(":")
            ss, mss = rest.split(",")
            return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(mss) / 1000
        out.append((sec(a), sec(z), " ".join(b[2:])))
    return out


def build_srt(timing):
    lines, i = [], 1
    for c in timing["cuts"]:
        p = os.path.join(AUD, f"cut{c['n']:02d}.srt")
        if not os.path.exists(p):
            continue
        off = c["start"] + c["lead"]
        for a, z, txt in parse_srt(p):
            lines.append(f"{i}\n{srt_time(a + off)} --> {srt_time(z + off)}\n{txt}\n")
            i += 1
    out = os.path.join(PROJ, f"{NAME}.srt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out, i - 1


def main():
    only_cuts = "--cuts" in sys.argv
    want_srt = "--srt" in sys.argv
    nocap = "--nocap" in sys.argv
    timing = json.load(open(os.path.join(AUD, "timing.json")))
    boxes = json.load(open(os.path.join(TMP, "boxes.json")))
    os.makedirs(CUTDIR, exist_ok=True)

    caps = {} if nocap else {c["n"]: build_ass(c["n"], c["lead"]) for c in timing["cuts"]}
    h = {sh(["ffprobe", "-v", "error", "-show_entries", "stream=height", "-of", "csv=p=0",
             os.path.join(SLIDES, f"cut{c['n']:02d}.png")]).stdout.strip()
         for c in timing["cuts"]}
    if h != {str(SLIDE_H)}:
        raise SystemExit(f"slides are {sorted(h)} px tall, expected {SLIDE_H} — "
                         f"re-run build/shots.py after changing --fh")
    what = "reserved, empty" if nocap else f"{sum(1 for v in caps.values() if v)} cuts"
    print(f"script    {what}, {CAP_H}px strip under a 1920x{SLIDE_H} slide")

    # two at a time: the tiled orbit strips are 3906 px wide, and four concurrent
    # encoders holding those frames is enough to get the run OOM-killed
    with ThreadPoolExecutor(max_workers=2) as ex:
        made = dict(ex.map(lambda c: build_cut(c, boxes.get(str(c["n"]), []),
                                               caps.get(c["n"])), timing["cuts"]))

    for c in timing["cuts"]:
        f = made[c["n"]]
        d = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", f]).stdout.strip())
        nb = len(boxes.get(str(c["n"]), []))
        print(f"cut{c['n']:02d}  {d:6.2f}s  want {c['hold']:6.2f}s  "
              f"{nb} panel(s)  {os.path.getsize(f) / 1e6:5.1f} MB")
    if only_cuts:
        return

    lst = os.path.join(TMP, "cuts.txt")
    with open(lst, "w") as f:
        for c in timing["cuts"]:
            f.write(f"file '{made[c['n']]}'\n")
    silent = os.path.join(TMP, "silent.mp4")
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])

    wav = build_audio(timing)
    out = os.path.join(PROJ, f"{NAME}.mp4")
    sh(["ffmpeg", "-y", "-i", silent, "-i", wav,
        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", "-shortest", out])

    d = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                  "-of", "csv=p=0", out]).stdout.strip())
    print(f"\n{os.path.basename(out)}  {d:.2f}s = {int(d) // 60}:{d % 60:05.2f}  "
          f"{os.path.getsize(out) / 1e6:.1f} MB"
          f"{'' if nocap else '  (captions burned in)'}")
    if want_srt:
        srt, nsub = build_srt(timing)
        print(f"{os.path.basename(srt)}  {nsub} subtitle blocks")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Render the turntables the deck needs, and the nine-view cache grid built from one.

    python3 build/orbits.py            # everything below
    python3 build/orbits.py 4.07       # only clips whose sequence matches
    python3 build/orbits.py --sheets   # only the still sheets, from frames already on disk

Each entry is (sequence, mode) — see build/orbit.py for the modes. Blender writes a PNG
sequence into _claude_tmp, ffmpeg muxes it to assets/orbit/<seq>_<mode>.mp4, and the deck
plays it in a video panel like any other clip.
"""
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
EVAL = os.path.abspath(os.path.join(ROOT, "..", "Mani4D_test", "evalset"))
OUT = os.path.join(ROOT, "assets", "orbit")
TMP = os.path.join(ROOT, "_claude_tmp", "orbit")
BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
FPS = 30
RES = 640            # must match build/orbit.py
BG = "0xF1EFEA"      # --band; the renders are alpha, this is composited under them

CLIPS = [
    ("forest_small.forest_small_4.07", "tex"),    # 06 the floral teapot, and its map
    ("forest_small.forest_small_4.07", "rcm"),
    ("forest_mid.forest_mid_3.00", "tex"),        # 07 the SUV, sampled into the cache grid
    ("forest_mid.forest_mid_3.00", "rcm"),
    ("forest_mid.forest_mid_2.09", "white"),      # 10 the shell recovered by SAM 2 + recon
    ("forest_mid.forest_mid_2.09", "rcm"),
    ("forest_mid.forest_mid_2.09", "tex"),        # 08 the cache behind 2.09's own result
    ("forest_mid.forest_mid_7.10", "tex"),        # 05/07 the compartment box, nine cached views
    ("forest_mid.forest_mid_7.10", "rcm"),
    ("forest_mid.forest_mid_2.07", "tex"),        # 02 the sprayer you hand it
    ("forest_mid.forest_mid_7.06", "tex"),        # 10 the textured mesh recovered from video
]

# Cached views are stills — that is what a cache is — so these are sheets, not loops. The
# angles are shared: cut 05's nine supplied views and cut 07's nine cached pairs are the same
# nine angles of the same object, which is the point the two cuts make together.
SHEETS = [("forest_mid.forest_mid_7.10", 3, 3, "refs9", ("tex",)),         # 05 views supplied
          ("forest_mid.forest_mid_7.10", 9, 2, "cache9", ("tex", "rcm")),  # 07 the cache
          ("forest_mid.forest_mid_2.09", 3, 2, "mini", ("tex", "rcm"))]    # 08 the same, small
FRAMES = 120
CELL_H = 260         # one cell's height; the width follows the object's crop box


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode:
        raise RuntimeError(f"{cmd[0]} failed\n{r.stderr[-1500:]}")
    return r


def short(seq):
    return seq.split(".", 1)[1]


def one(job):
    seq, mode = job
    d = os.path.join(TMP, f"{short(seq)}_{mode}")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    sh([BLENDER, "-b", "-P", os.path.join(HERE, "orbit.py"), "--",
        os.path.join(EVAL, seq), mode, d + os.sep])
    mp4 = os.path.join(OUT, f"{short(seq)}_{mode}.mp4")
    sh(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(d, "%04d.png"),
        "-filter_complex", f"color=c={BG}:s={RES}x{RES}[b];[b][0:v]overlay=shortest=1,"
                           f"format=yuv420p",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-movflags", "+faststart", mp4])
    return f"{os.path.basename(mp4)}  {os.path.getsize(mp4) / 1e6:.1f} MB"


def trim_box(paths, pad=14):
    """One crop box for every cell, so the object keeps a constant size as it turns."""
    lo_x = lo_y = 10 ** 6
    hi_x = hi_y = 0
    for p_ in paths:
        # after -trim, %w %h are the ink size and %X %Y its offset in the original canvas.
        # (%@ is *not* the same thing here: it re-measures inside the trimmed image, so it
        # always reads +0+0 and the box ends up anchored to the canvas corner.)
        w, h, x, y = map(int, sh(["magick", p_, "-trim", "-format", "%w %h %X %Y", "info:"]
                                 ).stdout.replace("+", " ").split())
        lo_x, lo_y = min(lo_x, x), min(lo_y, y)
        hi_x, hi_y = max(hi_x, x + w), max(hi_y, y + h)
    return (hi_x - lo_x + 2 * pad, hi_y - lo_y + 2 * pad, lo_x - pad, lo_y - pad)


def precrop(seq, mode, box):
    """Every frame cropped to the shared box and flattened onto the panel colour, once.

    The cell is padded out to an even width: cells are appended into one strip, and libx264
    refuses an odd-width frame under yuv420p."""
    w, h, x, y = box
    cw = round(w * CELL_H / h)
    cw += cw & 1
    src = os.path.join(TMP, f"{short(seq)}_{mode}")
    dst = os.path.join(TMP, f"crop_{short(seq)}_{mode}")
    os.makedirs(dst, exist_ok=True)
    out = []
    for i in range(1, FRAMES + 1):
        p_ = os.path.join(dst, f"{i:04d}.png")
        sh(["magick", os.path.join(src, f"{i:04d}.png"), "-crop", f"{w}x{h}+{x}+{y}",
            "+repage", "-resize", f"x{CELL_H}", "-background", BG.replace("0x", "#"),
            "-layers", "flatten", "-gravity", "center",
            "-extent", f"{cw}x{CELL_H}", p_])
        out.append(p_)
    return out


def sheet(seq, cols, rows, name, modes):
    """One still. Two modes means the rows are the modes — colour over coordinates, so a pair
    reads down a column, both rows at the same angle. One mode fills the grid row-major.
    Either way the angles are evenly spaced all the way around the object."""
    box = trim_box([os.path.join(TMP, f"{short(seq)}_tex", f"{i:04d}.png")
                    for i in range(1, FRAMES + 1)])
    cells = {m: precrop(seq, m, box) for m in modes}
    paired = len(modes) == rows
    n = cols if paired else cols * rows
    args = []
    for r in range(rows):
        mode = modes[r] if paired else modes[0]
        picks = [cells[mode][round((c if paired else r * cols + c) * FRAMES / n) % FRAMES]
                 for c in range(cols)]
        args += ["("] + picks + ["+append", ")"]
    out = os.path.join(ROOT, "assets", f"{name}_{short(seq)}.png")
    sh(["magick"] + args + (["-append"] if rows > 1 else []) + [out])
    return (f"{os.path.basename(out):32s} {cols}x{rows} views  "
            f"{os.path.getsize(out) / 1e6:.1f} MB")


def main():
    pick = sys.argv[1] if len(sys.argv) > 1 else ""
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    if pick != "--sheets":                     # --sheets rebuilds them from frames on disk
        jobs = [j for j in CLIPS if pick in j[0]] or CLIPS
        with ThreadPoolExecutor(max_workers=3) as ex:
            for line in ex.map(one, jobs):
                print(line)
    for t in SHEETS:
        print(sheet(*t))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Build the condition clips a cut needs, straight from the evalset.

    python3 build/conds.py             # everything in NEED
    python3 build/conds.py 7.06        # only sequences whose name matches

The depth stream needs numpy, which the system python does not have:

    ../_claude_tmp/venv/bin/python build/conds.py

Every stream of a sequence is one frame directory with a shared index, so sampling the same
indices from each gives clips that are synced to each other by construction. The generated
results are 97 frames at 15 fps covering the whole take, so the sample is spread across the
whole take too — condition and result then run the same motion over the same seconds.

Nothing is cropped. The conditions are 1080x1920 and the results 576x1024, both 9:16, so the
only change is a scale down to the results' size.

`depth` is the odd one out: MoGe2 writes float32 metres, zipped, masked to the object (about
93% of the frame is zero). It is colourised here rather than shipped raw — near in ochre, far
in slate, background white, on one range held across the whole clip so the colour means the
same thing in every frame.
"""
import io
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
EVAL = os.path.abspath(os.path.join(ROOT, "..", "Mani4D_test", "evalset"))
OUT = os.path.join(ROOT, "assets", "cond")
TMP = os.path.join(ROOT, "_claude_tmp", "cond")
W, H = 576, 1024      # the generated results' size
FPS = 15              # the generated results' rate
N = 97                # the generated results' length

# sequence -> the streams that some cut asks for
NEED = {
    "forest_mid.forest_mid_2.07": ["pose"],                          # 02 the task
    "forest_mid.forest_mid_2.09": ["pose", "rcm"],                   # 08 what goes in
    "forest_mid.forest_mid_7.06": ["gt", "pose", "depth", "rendered", "rcm"],  # 10 curation
}

NEAR = (0xA9, 0x76, 0x0F)      # --ochre
FAR = (0x2B, 0x34, 0x40)       # --ink


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode:
        raise RuntimeError(f"{cmd[0]} failed\n{r.stderr[-1500:]}")
    return r


def short(seq):
    return seq.split(".", 1)[1]


def load_depth(path):
    """MoGe2's .npy is really a zip around one float32 array."""
    import numpy as np
    import zipfile
    with zipfile.ZipFile(path) as z:
        return np.load(io.BytesIO(z.read("data.npy")))


def depth_clip(seq, picks, mp4):
    """Colourise the depth maps and pipe them straight into ffmpeg as raw RGB."""
    import numpy as np
    near = np.array(NEAR, np.float32)
    far = np.array(FAR, np.float32)

    # one range for the whole clip, from a sample, so the colour is stable frame to frame
    lo_hi = [np.percentile(a[a > 0], [2, 98]) for a in
             (load_depth(p_) for p_ in picks[::8])]
    lo, hi = np.mean(lo_hi, axis=0)

    h, w = load_depth(picks[0]).shape
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
         "-framerate", str(FPS), "-i", "-",
         "-vf", f"scale={W}:{H},format=yuv420p", "-c:v", "libx264", "-preset", "slow",
         "-crf", "18", "-movflags", "+faststart", mp4],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for path in picks:
        a = load_depth(path)
        t = np.clip((a - lo) / (hi - lo), 0, 1)[..., None]
        rgb = (near * (1 - t) + far * t).astype(np.uint8)
        rgb[a <= 0] = 255                      # unmeasured: leave the panel white
        p.stdin.write(rgb.tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg failed\n" + p.stderr.read().decode("utf-8", "replace"))
    return lo, hi


def one(job):
    seq, stream = job
    src = os.path.join(EVAL, seq, stream)
    files = sorted(f for f in os.listdir(src) if f.split(".")[-1] in ("jpg", "png", "npy"))
    ext = files[0].split(".")[-1]

    mp4 = os.path.join(OUT, f"{short(seq)}_{stream}.mp4")
    idx = [round(i * (len(files) - 1) / (N - 1)) for i in range(N)]

    if stream == "depth":
        lo, hi = depth_clip(seq, [os.path.join(src, files[j]) for j in idx], mp4)
        return (f"{os.path.basename(mp4):32s} {len(files):4d} frames -> {N}  "
                f"{lo:.2f}-{hi:.2f} m  {os.path.getsize(mp4) / 1e6:.1f} MB")

    work = os.path.join(TMP, f"{short(seq)}_{stream}")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    for i, j in enumerate(idx):
        os.symlink(os.path.join(src, files[j]), os.path.join(work, f"{i + 1:04d}.{ext}"))

    sh(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(work, f"%04d.{ext}"),
        "-vf", f"scale={W}:{H},format=yuv420p", "-c:v", "libx264", "-preset", "slow",
        "-crf", "18", "-movflags", "+faststart", mp4])
    return (f"{os.path.basename(mp4):32s} {len(files):4d} frames -> {N}  "
            f"{os.path.getsize(mp4) / 1e6:.1f} MB")


def main():
    pick = sys.argv[1] if len(sys.argv) > 1 else ""
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    jobs = [(s, st) for s, streams in NEED.items() if pick in s for st in streams]
    with ThreadPoolExecutor(max_workers=3) as ex:
        for line in ex.map(one, jobs):
            print(line)


if __name__ == "__main__":
    main()

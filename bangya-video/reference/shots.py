# -*- coding: utf-8 -*-
"""Render every cut and report anything that overflows its 1920x1000 frame.

    python3 build/shots.py              # screenshot + probe all cuts
    python3 build/shots.py 3 7          # just those
    python3 build/shots.py --probe      # probe only, no screenshots

The frame is 1000 px tall, not 1080: the video reserves the bottom 80 px for the
burned-in script. FRAME_H here and --fh in deck.css must agree.

Writes slides/cutNN.png and _claude_tmp/boxes.json. The JSON carries every video panel's
pixel box, straight out of the DOM, so ffmpeg overlay coordinates are never hand-computed.
"""
import json
from concurrent.futures import ThreadPoolExecutor
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cutdata import CUTS                                              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DECK = os.path.join(ROOT, "deck.html")
SLIDES = os.path.join(ROOT, "slides")
TMP = os.path.join(ROOT, "_claude_tmp")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FRAME_H = 1000          # must match --fh in deck.css

BASE = [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
        "--force-device-scale-factor=1", f"--window-size=1920,{FRAME_H}",
        "--virtual-time-budget=5000", "--run-all-compositor-stages-before-draw",
        "--autoplay-policy=no-user-gesture-required", "--mute-audio",
        # Chrome does its work in seconds but its updater/crashpad keeps the process
        # alive for minutes afterwards, so shut all of that off and cap the wait below.
        "--no-first-run", "--no-default-browser-check", "--disable-crash-reporter",
        "--disable-component-update", "--disable-background-networking",
        "--disable-domain-reliability", "--metrics-recording-only"]
# Chrome never exits on its own here, so WAIT is the normal exit path, not an error path:
# every call runs the full WAIT seconds. Keep it just long enough for the render to land.
# JOBS above 3 starves each instance and screenshots start coming back empty.
WAIT = 25
JOBS = 3


def chrome(n, extra, url):
    """One profile per cut, so the cuts can render in parallel."""
    cmd = BASE + [f"--user-data-dir={TMP}/chrome{n:02d}"] + extra + [url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                           check=False, timeout=WAIT)
        return r.stdout or ""
    except subprocess.TimeoutExpired as e:
        # the render already landed; only the lingering process was killed
        return (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) \
            else (e.stdout or "")


def one(n, shot=True):
    png = os.path.join(SLIDES, f"cut{n:02d}.png")
    if shot:
        if os.path.exists(png):
            os.remove(png)
        chrome(n, [f"--screenshot={png}"], f"file://{DECK}?cut={n}")
    dom = chrome(n, ["--dump-dom"], f"file://{DECK}?cut={n}&probe=1")
    m = re.search(r'<pre id="probe"[^>]*>(.*?)</pre>', dom, re.S)
    if not m:
        return n, None
    txt = m.group(1).replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<")
    return n, json.loads(txt)


def main():
    args = list(sys.argv[1:])
    shot = "--probe" not in args
    want = [int(a) for a in args if a.isdigit()] or [c["n"] for c in CUTS]
    os.makedirs(SLIDES, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)

    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        res = dict(ex.map(lambda n: one(n, shot), want))

    # a partial run must not clobber the boxes of the cuts it did not probe
    bpath = os.path.join(TMP, "boxes.json")
    allboxes = json.load(open(bpath)) if os.path.exists(bpath) else {}
    bad, thin = 0, []
    for n in want:
        d = res.get(n)
        if d is None:
            print(f"cut{n:02d}  PROBE FAILED")
            continue
        allboxes[str(n)] = d["boxes"]
        png = os.path.join(SLIDES, f"cut{n:02d}.png")
        sz = os.path.getsize(png) / 1024 if os.path.exists(png) else 0
        print(f"cut{n:02d}  {sz:6.0f} KB  {len(d['boxes'])} panel(s)", end="")
        if d["over"]:
            bad += len(d["over"])
            print("   ** OVERFLOW **")
            for o in d["over"][:6]:
                print(f"          {o['over']:6.1f} px  {o['w']}x{o['h']}  {o['sel'][:70]}")
        else:
            print("   fits")
        for im in d["imgs"]:
            if im["nw"] and im["w"] > 40:
                r = im["nw"] / im["w"]
                if r < 0.85:
                    thin.append((n, os.path.basename(im["src"]), im["nw"], im["w"], r))

    with open(bpath, "w") as f:
        json.dump(allboxes, f, indent=2, sort_keys=True)

    print(f"\n{'OVERFLOWS: ' + str(bad) if bad else 'no overflow'}")
    if thin:
        print("\nupscaled images (native px / displayed px < 0.85):")
        for n, f_, nw, w, r in sorted(thin, key=lambda x: x[4]):
            print(f"  cut{n:02d}  {r:.2f}x  {f_}  {nw}px native -> {w}px shown")


if __name__ == "__main__":
    main()

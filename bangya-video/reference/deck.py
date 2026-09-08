# -*- coding: utf-8 -*-
"""Build video/deck.html — the review checkpoint and the render source in one file.

    python3 build/deck.py

Review mode is the default, with a 480p toggle so legibility can be checked at the size the
video is actually watched. `deck.html?cut=7` shows cut 7 alone as a bare 1920x1000 frame,
which is what the screenshot pass loads.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cutdata import CUTS, MOVEMENT                                     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "deck.html")

FONTS = ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Karla:wght@400;500;600;700;800&'
         'family=Newsreader:opsz,ital,wght@6..72,0,400;6..72,0,500;6..72,0,600;6..72,0,700;'
         '6..72,1,500&display=swap">')

TOTAL = sum(c["dur"] for c in CUTS)
WPM = 150.0          # the rate the target durations are budgeted against


def words(s):
    return len(re.findall(r"[A-Za-z0-9][\w'’.-]*", s))


def mmss(t):
    return f"{int(t)//60}:{int(round(t))%60:02d}"


def onslide(body):
    """Rough count of words the viewer has to read, for the 480p budget."""
    txt = re.sub(r"<[^>]+>", " ", body)
    txt = re.sub(r"&[a-z]+;|&#\d+;", " ", txt)
    return len(re.findall(r"[A-Za-z][A-Za-z'’-]+", txt))


def assets(body):
    out = []
    for p in re.findall(r'data-clip="([^"]+)"', body):
        out.append(("clip", p))
    for p in re.findall(r'src="([^"]+)"', body):
        if not p.endswith(".mp4"):
            out.append(("img", p))
    return out


def frame(c, start):
    """One 1920x1000 slide. Title and close cuts drop the header bar."""
    bare = c["kind"] in ("title", "close")
    top = "" if bare else (
        f'<div class="top"><h2>{c["title"]}</h2>'
        f'<span class="mv">{MOVEMENT[c["kind"]]}</span></div>')
    bot = (f'<div class="bot"><div class="rail">'
           f'<i style="width:{(start + c["dur"]) / TOTAL * 100:.3f}%"></i></div></div>')
    return (f'<div class="frame{" bare" if bare else ""}">{top}'
            f'<div class="stage">{c["body"]}</div>{bot}</div>')


def notes(c):
    a = "".join(f'<li><span class="k">{k}</span> <code>{p.split("/")[-1]}</code></li>'
                for k, p in assets(c["body"]))
    w = words(c["script"])
    osw = onslide(c["body"])
    spoken = w / WPM * 60
    fit = "ok" if spoken <= c["dur"] + 0.5 else "tight"
    return (f'<div class="notes">'
            f'<h4>narration</h4><p class="script">{c["script"]}</p>'
            f'<p class="wc">{w} words &rarr; <b>{spoken:.0f} s</b> spoken at {WPM:.0f} wpm '
            f'&middot; hold <b>{c["dur"]} s</b> <span class="{fit}">{fit}</span><br>'
            f'<b>{osw}</b> words to read on the slide</p>'
            f'<h4>assets</h4><ul class="al">{a}</ul></div>')


def main():
    parts, t = [], 0.0
    for c in CUTS:
        parts.append(
            f'<section class="cut" id="c{c["n"]}" data-cut="{c["n"]}" data-dur="{c["dur"]}">'
            f'<div class="cut-hd"><span class="n">CUT {c["n"]:02d}</span><h2>{c["title"]}</h2>'
            f'<span class="tc"><span>in <b>{mmss(t)}</b></span>'
            f'<span>out <b>{mmss(t + c["dur"])}</b></span>'
            f'<span>hold <b>{c["dur"]}s</b></span></span></div>'
            f'<div class="cut-bd"><div class="shot">{frame(c, t)}</div>{notes(c)}</div></section>')
        t += c["dur"]

    tw = sum(words(c["script"]) for c in CUTS)
    mx = max(CUTS, key=lambda c: onslide(c["body"]))
    head = f"""<div class="rv-hd">
  <h1>ByteLOOM &mdash; 5-minute talk, cut sheet</h1>
  <p>{len(CUTS)} cuts. Each frame below is the <b>real 1920&times;1000 slide</b>, so what you see is
     what renders &mdash; and the video panels are live, they play in place. The video is
     1920&times;1080; the bottom 80&nbsp;px is reserved for the spoken script, burned in as white
     Karla on black, and is not shown here. Built to the 480p rule:
     nothing on a frame is under 32&nbsp;px, one idea per cut, and the wordiest slide is
     {onslide(mx["body"])} words (cut&nbsp;{mx["n"]:02d}). <b>Hit &ldquo;view at 480p&rdquo; and read
     every slide</b> &mdash; if anything is a strain there, it changes.</p>
  <div class="meta">
    <div><b>{len(CUTS)}</b>cuts</div>
    <div><b>{mmss(TOTAL)}</b>runtime</div>
    <div><b>{tw}</b>words spoken</div>
    <div><b>{tw / (TOTAL / 60):.0f}</b>words / minute</div>
    <div><b>{TOTAL / len(CUTS):.0f} s</b>mean cut</div>
    <div><b>1920&times;1080</b>30 fps &middot; H.264</div>
    <div><b>1000 + 80</b>slide + script strip</div>
  </div>
</div>
<div class="rv-note">
  <p><b>Two things need your go-ahead before I render.</b></p>
  <p><b>1 &middot; TTS is an external service.</b> The narration text goes to Microsoft's
     <code>edge-tts</code> endpoint. The words come from your already-public paper and project page,
     but it does leave this machine. The offline fallback is the macOS voice, which sounds
     noticeably worse.</p>
  <p><b>2 &middot; Voice.</b> My pick is <code>en-US-AndrewMultilingualNeural</code> &mdash; warm,
     confident, male. Alternatives: <code>en-US-BrianMultilingualNeural</code> (casual),
     <code>en-US-EmmaMultilingualNeural</code> (clear, female),
     <code>en-GB-RyanNeural</code> (British).</p>
  <p><b>Also worth a decision:</b> burned-in captions? Cheap to add, and they help anyone
     watching muted &mdash; but they cost the bottom sixth of every frame.</p>
</div>"""

    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<title>ByteLOOM &mdash; 5-minute cut sheet</title>{FONTS}'
            f'<link rel="stylesheet" href="build/deck.css">'
            f'<style>{TOOLBAR_CSS}</style></head><body class="review">'
            f'{TOOLBAR}{head}{"".join(parts)}'
            f'<script>{JS}</script></body></html>')
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"deck.html  {len(html) / 1024:.0f} KB  {len(CUTS)} cuts  {mmss(TOTAL)}  {tw} words  "
          f"{tw / (TOTAL / 60):.0f} wpm  worst slide {onslide(mx['body'])} words (cut {mx['n']})")


TOOLBAR = ('<div class="tb"><button id="t480">view at 480p</button>'
           '<button id="tplay">pause all video</button>'
           '<span class="tbi">the 480p view is the legibility test</span></div>')

TOOLBAR_CSS = """
.tb{position:sticky;top:0;z-index:9;display:flex;align-items:center;gap:14px;
  background:#2B3440;color:#fff;padding:12px 56px;font-size:15px}
.tb button{font:inherit;font-weight:700;background:#fff;color:#2B3440;border:0;
  padding:8px 16px;cursor:pointer}
.tb button.on{background:#A9760F;color:#fff}
.tb .tbi{color:#A6AEB8;font-size:14px}
.notes .wc .ok{color:#2F6B3A;font-weight:700}
.notes .wc .tight{color:#A9760F;font-weight:700}
.notes .al{list-style:none;padding:0}
.notes .al .k{display:inline-block;width:34px;font-size:11px;font-weight:800;
  letter-spacing:.1em;text-transform:uppercase;color:#A9760F}
body.p480 .cut-bd{grid-template-columns:854px 1fr}
body.p480 .shot{width:854px;height:calc(var(--fh) * .4447917)}
body.p480 .shot .frame{transform:scale(.4447917)}
body.render .tb{display:none}
"""

JS = """
// ?cut=N -> render mode: that one frame, bare, at native 1920x1080.
// ?probe=1 additionally writes layout measurements into <pre id=probe> for --dump-dom to read.
(function(){
  var q = new URLSearchParams(location.search), n = q.get('cut');

  if(n){
    document.body.className = 'render';
    document.querySelectorAll('.cut').forEach(function(s){
      if(s.dataset.cut !== n) s.classList.add('off');
    });
    // Drop the <video> elements entirely. The slide PNG carries only the chrome — ffmpeg
    // overlays the real clip into each .vp box afterwards — and a looping video keeps
    // Chrome's virtual clock from ever going quiescent, so --screenshot never fires.
    // Panel geometry is set by CSS aspect-ratio, so removing the media changes no layout.
    if(q.get('still') !== '0') document.querySelectorAll('.frame video').forEach(function(v){
      v.parentNode.removeChild(v);
    });
    if(!q.get('probe')) return;

    var measure = function(){
      var f = document.querySelector('.cut:not(.off) .frame');
      var fb = f.getBoundingClientRect(), over = [], boxes = [], imgs = [];
      f.querySelectorAll('*').forEach(function(e){
        var r = e.getBoundingClientRect();
        if(!r.width && !r.height) return;
        var o = Math.max(0, r.right-fb.right, fb.left-r.left, r.bottom-fb.bottom, fb.top-r.top);
        if(o > 1) over.push({sel:e.tagName.toLowerCase()+'.'+(e.className||'-'),
                             over:+o.toFixed(1), w:Math.round(r.width), h:Math.round(r.height)});
        if(e.dataset.clip) boxes.push({clip:e.dataset.clip, fit:e.dataset.fit||'cover',
          x:Math.round(r.left-fb.left), y:Math.round(r.top-fb.top),
          w:Math.round(r.width), h:Math.round(r.height)});
        if(e.tagName === 'IMG' && r.width > 2) imgs.push({src:e.getAttribute('src'),
          nw:e.naturalWidth, nh:e.naturalHeight, w:Math.round(r.width), h:Math.round(r.height)});
      });
      // Collision. Comparing only the stage's direct children misses the common case: a
      // caption that overflows its own panel and lands under the next block. So check every
      // descendant of stage child i against the box of stage child i+1.
      var kids = [].slice.call(f.querySelectorAll('.stage > *'));
      kids.forEach(function(kid, i){
        var next = kids[i+1]; if(!next) return;
        var nb = next.getBoundingClientRect();
        if(nb.height < 1) return;
        [].slice.call(kid.querySelectorAll('*')).concat([kid]).forEach(function(e){
          if(!e.textContent.trim() && e.tagName !== 'IMG') return;
          var r = e.getBoundingClientRect();
          if(r.height < 1 || r.width < 1) return;
          var ov = Math.min(r.bottom, nb.bottom) - Math.max(r.top, nb.top);
          var oh = Math.min(r.right, nb.right) - Math.max(r.left, nb.left);
          if(ov > 1 && oh > 1)
            over.push({sel:'COLLIDES ' + e.tagName.toLowerCase()+'.'+(e.className||'-')
                            + ' into ' + next.tagName.toLowerCase()+'.'+(next.className||'-'),
                       over:+ov.toFixed(1), w:Math.round(r.width), h:Math.round(r.height)});
        });
      });
      var pre = document.createElement('pre');
      pre.id = 'probe'; pre.style.display = 'none';
      pre.textContent = JSON.stringify({cut:+n, over:over, boxes:boxes, imgs:imgs});
      document.body.appendChild(pre);
    };
    if(document.readyState === 'complete') setTimeout(measure, 500);
    else window.addEventListener('load', function(){ setTimeout(measure, 500); });
    return;
  }

  // ---- review page -------------------------------------------------------
  var b480 = document.getElementById('t480'), bply = document.getElementById('tplay');
  b480.onclick = function(){
    document.body.classList.toggle('p480');
    b480.classList.toggle('on');
    b480.textContent = document.body.classList.contains('p480')
      ? 'back to full size' : 'view at 480p';
  };
  var paused = false;
  bply.onclick = function(){
    paused = !paused; bply.classList.toggle('on');
    bply.textContent = paused ? 'play video' : 'pause all video';
    document.querySelectorAll('video').forEach(function(v){ paused ? v.pause() : v.play(); });
  };

  // 40-odd looping videos will choke a tab, so only the ones on screen actually run
  var io = new IntersectionObserver(function(es){
    es.forEach(function(e){
      var v = e.target;
      if(e.isIntersecting && !paused) v.play().catch(function(){});
      else v.pause();
    });
  }, {rootMargin: '200px'});
  document.querySelectorAll('video').forEach(function(v){ io.observe(v); });
})();
"""

if __name__ == "__main__":
    main()

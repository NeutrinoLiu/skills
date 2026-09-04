# Explainer page

A page that explains the paper and carries the verdict. Load `artifact-design` before writing it, and `dataviz` before any chart.

## Structure

Follow the referee's reasoning as a numbered sequence, because that is what the reader needs in order: the problem, the insight and what it rests on, the method as a numbered pipeline, the evidence, whether the evaluation justifies the claim, what would change the verdict. A rating card sits under the masthead.

Give the paper's voice and your own different typography. Body prose reports what the paper says; a bordered, tinted aside labelled `Reviewer note` carries what you found. A reader must never have to guess which is which. This is the page's whole information design.

Use the paper's real cropped figures and transcribe its real tables. Charts earn their place by showing something a table cannot: an effect against the spread that swamps it, where a gain is concentrated, a decomposition of what is capacity and what is method.

## Series identity

Reviewing several papers gives one visual system with a per-paper accent, so they read as one set. Keep the type and layout fixed; vary two accent colours. Draw the accent from the paper's own subject where you can.

Validate every accent pair in both themes before use:

```bash
node <dataviz>/scripts/validate_palette.js "#hex,#hex" --mode light
node <dataviz>/scripts/validate_palette.js "#hex,#hex" --mode dark
```

The dark band is tighter than the light one, so a colour that passes light routinely fails dark on lightness. Iterate until both pass rather than shipping a warning.

Define every colour as a token in all three theme states: bare `:root`, `@media (prefers-color-scheme: dark)` guarded by `:root:not([data-theme="light"])`, and `:root[data-theme="dark"]`. A colour defined only inside a media block renders one theme's text on the other theme's ground.

## Build

Keep the page as `<name>.src.html` with `{{CSS}}` and `{{FIG:name}}` tokens, a shared stylesheet, and a script that inlines both. Editing a source file beats regenerating a megabyte of base64.

```python
import base64, re, sys, pathlib
site = pathlib.Path(__file__).parent
src, figdir, out = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3]
html = (site/src).read_text().replace("{{CSS}}", (site/"_shared.css").read_text())
missing = []
def sub(m):
    p = figdir/"figs"/f"{m.group(1)}.png"
    if not p.exists():
        missing.append(m.group(1)); return m.group(0)
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
html = re.sub(r"\{\{FIG:([a-z0-9_]+)\}\}", sub, html)
(site/out).write_text(html)
print("wrote", out, len(html)//1024, "KB", "MISSING:", missing or "none",
      "UNRESOLVED:", set(re.findall(r"\{\{[^}]+\}\}", html)) or "none")
```

## Render it and look at it

Reading the source does not find layout bugs. Render and read the image back:

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless --disable-gpu --hide-scrollbars --virtual-time-budget=8000 \
  --window-size=1200,22000 --screenshot=shot.png "file://$PWD/page.html"
magick shot.png -trim +repage shot.png
magick shot.png -crop 1056x1200+0+<y> +repage -resize 800x slice.png
```

A sharp jump in page height between builds means a layout collapse. Force dark mode by prepending `<script>document.documentElement.setAttribute("data-theme","dark")</script>` to a copy.

Defects that only appear on render:

- A CSS grid row whose children outnumber its columns wraps the overflow into column one, and a text block lands in a 30px gutter one word per line.
- Direct labels past the right edge of an SVG `viewBox` are silently clipped, truncating the values they carry.
- Labels stacked at even spacing beside tightly clustered points imply values those points do not have. Bracket the cluster instead.
- An entity beside a literal high character inside SVG `<text>` can render as mojibake.
- Bars for all-positive data drawn from a centre line imply a diverging scale.
- A series colour that contradicts its own legend.
- White text on a light accent passes in light mode and fails in dark.

Re-derive every hard-coded chart coordinate from the source values before publishing. Disagreements under a quarter of a percentage point are sub-pixel; anything larger is a bug.

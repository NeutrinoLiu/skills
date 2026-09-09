---
name: mac-app-icon-recolor
description: Recolor a macOS app's Dock/Finder icon (hue shift or palette swap) without touching the signed bundle, by attaching a Finder custom icon. Use when the user wants an app's icon a different color, wants to tell two look-alike apps apart (Feishu vs Lark, Slack workspaces, two Chrome builds), or asks to re-apply or revert a custom app icon.
---

# mac-app-icon-recolor

Apps have no palette setting; the icon is the lever. Editing `Contents/Resources/*.icns`
breaks the code signature, so attach the recolored icon as a **Finder custom icon**
(an `Icon\r` resource file plus a FinderInfo flag). The signed contents stay untouched,
updates keep working, and one call reverts it.

Work in `~/_claude_tmp/icons/<App>/` so the built `.icns` survives for re-application.
Tools: `sips`, `iconutil` (macOS), `magick` (ImageMagick, `brew install imagemagick`).

## 1. Find the real bundle

Folder names lie. Check `CFBundleName` on every candidate — Feishu ships as
`/Applications/Lark.app` (name "Feishu") while Lark is `/Applications/LarkSuite.app`.

```zsh
for a in /Applications/*.app ~/Applications/*.app; do
  n=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleName' "$a/Contents/Info.plist" 2>/dev/null)
  echo "$n	$a"
done | grep -i "<name>"
APP=/Applications/<Found>.app
ICNS="$APP/Contents/Resources/$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIconFile' "$APP/Contents/Info.plist" | sed 's/\.icns$//').icns"
```

If two apps must be told apart, `ls -la` both `.icns` files; identical size means identical
icon and confirms the job.

## 2. Render candidates and choose

Extract at full size, generate hue shifts, and **look at the contact sheet** before choosing.
`-modulate 100,105,H` rotates hue by `(H-100)*1.8°`; `200` is the complement, which
contrasts most at Dock size.

```zsh
D=~/_claude_tmp/icons/<App>; mkdir -p $D; cd $D
sips -s format png "$ICNS" --out orig.png >/dev/null
for h in 133 166 200 233; do magick orig.png -modulate 100,105,$h cand_$h.png; done
magick orig.png cand_*.png +append -resize 1280x sheet.png
```

Read `sheet.png`. Pick the one furthest from the app it must differ from, or the hue the
user named. For a specific palette instead of a hue shift, use `-fill <color> -opaque
<orig>` per color with `-fuzz 10%`, and still check the sheet.

## 3. Build the icns and attach it

```zsh
magick orig.png -modulate 100,105,<H> new.png
mkdir -p new.iconset
for s in 16 32 128 256 512; do
  sips -z $s $s new.png --out new.iconset/icon_${s}x${s}.png >/dev/null
  sips -z $((s*2)) $((s*2)) new.png --out new.iconset/icon_${s}x${s}@2x.png >/dev/null
done
iconutil -c icns new.iconset -o new.icns

cat > apply.sh <<EOS
#!/bin/zsh
osascript -l JavaScript -e 'ObjC.import("AppKit"); var img=\$.NSImage.alloc.initWithContentsOfFile("$D/new.icns"); \$.NSWorkspace.sharedWorkspace.setIconForFileOptions(img,"$APP",0)'
touch "$APP"; killall Dock Finder
EOS
cat > revert.sh <<EOS
#!/bin/zsh
osascript -l JavaScript -e 'ObjC.import("AppKit"); \$.NSWorkspace.sharedWorkspace.setIconForFileOptions(\$(), "$APP", 0)'
touch "$APP"; killall Dock Finder
EOS
chmod +x apply.sh revert.sh
./apply.sh
```

`setIconForFileOptions` prints `true` on success. **Run it unsandboxed**: the tool sandbox
blocks writes under `/Applications`.

If it prints `false` and `touch "$APP/.t"` says `Operation not permitted` even unsandboxed,
macOS App Management is blocking the terminal. Open the pane and ask the user to toggle
on the terminal app (find it by walking `ps -o ppid=` up from `$$`), then re-run `apply.sh`:

```zsh
open "x-apple.systempreferences:com.apple.preference.security?Privacy_AppBundles"
```

**App Management is a standing grant, not a one-shot prompt.** While it is on, every
process launched from that terminal, not just this session, can rewrite any installed app
in `/Applications`: swap binaries, inject into Electron bundles, tamper with signed code.
Say this to the user when asking for it, and treat the grant as temporary:

1. Ask for it only after the unsandboxed `touch` test fails, never pre-emptively.
2. Run `apply.sh` and step 4 immediately, while the user is present.
3. As soon as verification passes, tell the user to **turn it off again** in the same pane.
   The custom icon persists without it; macOS needs no permission to read it. Only a
   re-apply after an app update, or a revert, needs it switched on again briefly.

The turn-off reminder is part of done, not an optional footnote.

Fallback with no permission: the user selects the app in Finder, Cmd+I, drags `new.png`
onto the small icon at the top-left of Get Info.

## 4. Verify what macOS actually resolves

Done means a side-by-side render of the resolved icons shows the new color:

```zsh
osascript -l JavaScript -e '
ObjC.import("AppKit");
function dump(p,o){var i=$.NSWorkspace.sharedWorkspace.iconForFile(p); i.size=$.NSMakeSize(256,256);
var r=$.NSBitmapImageRep.alloc.initWithCGImage(i.CGImageForProposedRectContextHints($(),$(),$()));
$.NSData.dataWithData(r.representationUsingTypeProperties($.NSBitmapImageFileTypePNG,$())).writeToFileAtomically(o,true);}
dump("'$APP'","'$D'/now.png"); dump("/Applications/<OtherApp>.app","'$D'/other.png");'
magick now.png other.png +append verify.png
```

Read `verify.png`. Also check `ls "$APP/Icon"$'\r'` exists and
`xattr -px com.apple.FinderInfo "$APP"` has `04` in byte 9 (custom-icon flag).

## Afterwards

- A running app's Dock tile updates on next launch.
- An update that replaces the whole bundle drops the icon; re-run `apply.sh`.
- Revert: `revert.sh`, or select the icon in Get Info and press Delete.
- Both need App Management on for the terminal; ask for it, do the write, remind the user to
  turn it off.
- Tell the user the paths of `apply.sh` and `revert.sh`, and close with the App Management
  turn-off reminder if it was granted this session.

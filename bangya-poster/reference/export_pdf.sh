#!/bin/sh
# Print export: poster.html -> 5222_Liu_1400x1000mm.pdf
#   trim 1400x1000 mm, 5 mm bleed, 10 mm crop marks, CMYK Coated FOGRA39, fonts outlined.
set -e
cd "$(dirname "$0")/.."
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ICC=/usr/local/texlive/2025/texmf-dist/tex/generic/colorprofiles/FOGRA39L_coated.icc
TMP=_claude_tmp; mkdir -p $TMP; cp "$ICC" $TMP/

python3 build/print.py                       # wraps poster.html -> poster_print.html

"$CHROME" --headless --disable-gpu --no-sandbox --virtual-time-budget=60000 \
  --run-all-compositor-stages-before-draw --no-pdf-header-footer \
  --print-to-pdf=$TMP/poster_rgb.pdf "file://$PWD/poster_print.html"

# Chrome rounds the media box up by 0.19 mm; PDFFitPage pulls it back so the
# trim box lands on exactly 1400.000 x 1000.000 mm.
cd $TMP; cp ../build/prologue.ps .
gs -dNOPAUSE -dBATCH -dNOSAFER -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
   -sColorConversionStrategy=CMYK -dProcessColorModel=/DeviceCMYK \
   -sOutputICCProfile=FOGRA39L_coated.icc -dNoOutputFonts \
   -dDEVICEWIDTHPOINTS=4053.5433 -dDEVICEHEIGHTPOINTS=2919.6850 -dFIXEDMEDIA -dPDFFitPage \
   -dDownsampleColorImages=false -dDownsampleGrayImages=false \
   -dAutoFilterColorImages=false -dAutoFilterGrayImages=false \
   -dColorImageFilter=/FlateEncode -dGrayImageFilter=/FlateEncode \
   -sOutputFile=poster_cmyk.pdf prologue.ps poster_rgb.pdf
cd ..
cp $TMP/poster_cmyk.pdf ../5222_Liu_1400x1000mm.pdf

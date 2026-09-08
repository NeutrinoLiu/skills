#!/usr/bin/env python3
"""Vector QR codes for the poster. Error correction M, 4-module quiet zone."""
import segno, os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

CODES = {
    "Q1": "https://neutrinoliu.github.io/byteloom/",
    "Q2": "https://huggingface.co/datasets/byteloom-HOI/Mani4D_test",
}

for key, url in CODES.items():
    q = segno.make(url, error="m")
    path = f"{OUT}/{key}.svg"
    q.save(path, scale=10, border=4, dark="#2B3440", light=None, svgclass=None, xmldecl=False)
    print(f"{key}: version {q.version}, {q.symbol_size(border=4)[0]} modules  <- {url}")

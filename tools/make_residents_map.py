#!/usr/bin/env python3
"""Residents map: plots Resident (green, R) and Building (orange, B), everything else pale.
Usage: python3 tools/make_residents_map.py OUT.jpg   (uses the same label placement as make_map_pdf.py)"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_map_pdf as M
from PIL import Image, ImageDraw
COL = {"Resident": (46, 139, 87), "Building": (240, 165, 0)}
cls, n = {}, {"Resident": 0, "Building": 0}
for k, u in M.D["U"].items():
    st = u[1]
    if st in COL:
        for p in k.split("-"):
            cls[p] = st; n[st] += 1
base = M.base.convert("RGBA"); over = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(over)
for p, st in cls.items():
    d.polygon([tuple(q) for q in M.POLY[p]], fill=COL[st] + (235,), outline=(60, 30, 25, 255), width=2)
img = Image.alpha_composite(base, over); d = ImageDraw.Draw(img)
for p, st in cls.items():
    M.draw_label(d, M.POLY[p], p, st[0], (255, 255, 255))
d.rectangle([1240, 2185, 2255, 2515], fill=(255, 255, 255, 255))   # hide the co-ordinates note
img = img.convert("RGB").resize((1613, 1800), Image.LANCZOS)
img.save(sys.argv[1], quality=93); print(n)

#!/usr/bin/env python3
"""Map of ONE month's service charge: green = that month is paid, red = not yet paid.
Only Resident/Building units (or any unit that has paid) are coloured; unit months not due are skipped.
Usage: python3 tools/make_month_map.py OUT.jpg [month_index]   (month_index 0 = May 2025 ... 18 = Nov 2026)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_map_pdf as M
from PIL import Image, ImageDraw
mi = int(sys.argv[2]) if len(sys.argv) > 2 else 18
GREEN, RED = (30, 132, 73), (192, 57, 43)
cls, n = {}, {"paid": 0, "unpaid": 0}
for k, v in M.D["V"].items():
    st = M.D["U"][k][1]; nd = v.get("nd", 0)
    paid_ever = any(v["cov"][i] for i in range(nd, 19)) or v["credit"] > 0 or any(v["rec"])
    if (st not in ("Resident", "Building") and not paid_ever) or mi < nd:
        continue
    ok = bool(v["cov"][mi]); n["paid" if ok else "unpaid"] += 1
    for p in k.split("-"): cls[p] = ok
base = M.base.convert("RGBA"); over = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(over)
for p, ok in cls.items():
    d.polygon([tuple(q) for q in M.POLY[p]], fill=(GREEN if ok else RED) + (235,), outline=(60, 30, 25, 255), width=2)
img = Image.alpha_composite(base, over); d = ImageDraw.Draw(img)
for p in cls: M.draw_label(d, M.POLY[p], p, "", (255, 255, 255))
d.rectangle([1240, 2185, 2255, 2515], fill=(255, 255, 255, 255))
img.convert("RGB").resize((1613, 1800), Image.LANCZOS).save(sys.argv[1], quality=93); print(n)

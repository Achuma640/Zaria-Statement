#!/usr/bin/env python3
"""Draw the Service charge payment map (PNG + PDF) from the statement data in index.html.
Usage: python3 tools/make_map_pdf.py OUT_DIR
Colours: purple = living/building but never paid; red = 5+ months unpaid; yellow = 1-4 unpaid;
green = up to date (all due months to the current month covered). Plots with no payment and no
Resident/Building status are left uncoloured. Needs receipts-r5m8xw/nav.jpg + navp.json (public base map)."""
import datetime as dt, json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
D = json.loads(re.search(r"const D=(\{.*?\});\s*\n", open(os.path.join(ROOT, "index.html")).read(), re.S).group(1))
POLY = json.load(open(os.path.join(ROOT, "receipts-r5m8xw", "navp.json")))
base = Image.open(os.path.join(ROOT, "receipts-r5m8xw", "nav.jpg")).convert("RGB")
COL = {"never": (74, 20, 140), "red": (192, 57, 43), "yellow": (241, 196, 15), "green": (30, 132, 73)}
MN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def classify():
    out, counts = {}, dict.fromkeys(COL, 0)
    for k, v in D["V"].items():
        st = D["U"][k][1]; nd = v.get("nd", 0)
        paid = any(v["cov"][i] for i in range(nd, 19)) or v["credit"] > 0 or any(v["rec"])
        if st not in ("Resident", "Building") and not paid:
            continue
        un = sum(1 for i in range(nd, 19) if not v["cov"][i])
        c = "never" if not paid else "red" if un >= 5 else "yellow" if un >= 1 else "green"
        for p in k.split("-"):
            out[p] = (c, {"Resident": "R", "Building": "B"}.get(st, ""))
            counts[c] += 1
    return out, counts

def font(sz): return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", sz)

def main(outdir):
    cls, counts = classify()
    last = dt.datetime.strptime(max(p[0] for p in D["P"]), "%Y-%m-%d")
    over = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(over)
    for p, (c, letter) in cls.items():
        d.polygon([tuple(q) for q in POLY[p]], fill=COL[c] + (235,), outline=(60, 30, 25, 255), width=2)
    img = Image.alpha_composite(base.convert("RGBA"), over); d = ImageDraw.Draw(img)
    for p, (c, letter) in cls.items():
        xs, ys = [q[0] for q in POLY[p]], [q[1] for q in POLY[p]]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        fg = (0, 0, 0) if c == "yellow" else (255, 255, 255)
        d.text((cx, cy - (11 if letter else 0)), p, font=font(25), fill=fg, anchor="mm")
        if letter: d.text((cx, cy + 13), letter, font=font(21), fill=fg, anchor="mm")
    # hide the "CO-ORDINATES" note and draw the legend there
    d.rectangle([1240, 2185, 2255, 2515], outline=(0, 0, 0), width=3, fill=(255, 255, 255, 255))
    lab = [("never", "Living or building, never paid: %d plots"), ("red", "5 or more months unpaid: %d plots"),
           ("yellow", "1 to 4 months unpaid: %d plots"),
           ("green", "Up to date (paid to %s'%s): %%d plots" % (MN[last.month - 1], str(last.year)[2:]))]
    y = 2215
    for c, t in lab:
        d.rectangle([1270, y, 1320, y + 48], fill=COL[c], outline=(0, 0, 0), width=2)
        d.text((1350, y + 24), t % counts[c], font=font(36), fill=(0, 0, 0), anchor="lm"); y += 66
    d.text((1270, y + 8), "R = residence   B = building", font=font(28), fill=(0, 0, 0), anchor="lm")
    head = Image.new("RGBA", (img.width, 190), (255, 255, 255, 255)); h = ImageDraw.Draw(head)
    h.text((60, 80), "Zaria Village: Service charge payment map", font=font(74), fill=(0, 0, 0), anchor="lm")
    h.text((60, 148), "May 2025 to %s %d, position at %d %s %d" % (MN[last.month - 1], last.year, last.day, MN[last.month - 1], last.year),
           font=font(36), fill=(80, 80, 80), anchor="lm")
    final = Image.new("RGB", (img.width, img.height + 190), "white")
    final.paste(head.convert("RGB"), (0, 0)); final.paste(img.convert("RGB"), (0, 190))
    os.makedirs(outdir, exist_ok=True)
    name = "Zaria_Payment_Map_%d%s%d" % (last.day, MN[last.month - 1], last.year)
    final.save(os.path.join(outdir, name + ".png"))
    final.save(os.path.join(outdir, name + ".pdf"), resolution=200)
    print(name, counts)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")

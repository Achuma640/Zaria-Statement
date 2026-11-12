#!/usr/bin/env python3
"""Rebuild the PIN-locked payment-map page (map-pm3x9c/index.html) from the statement data.
Usage: ZARIA_PIN=... python3 tools/make_map_page.py
The map shows which plots have not paid, so it is encrypted like the committee reports.
Writes the page only when the map changed (compares the PNG hash stored in the page title attr)."""
import base64, hashlib, io, json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_map_pdf, zcrypto
from PIL import Image

pin = os.environ.get("ZARIA_PIN") or sys.exit("set ZARIA_PIN")
PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "map-pm3x9c", "index.html")
with tempfile.TemporaryDirectory() as t:
    make_map_pdf.main(t)
    name = [f[:-4] for f in os.listdir(t) if f.endswith(".png")][0]
    png = Image.open(os.path.join(t, name + ".png")).convert("RGB")
    pdf = open(os.path.join(t, name + ".pdf"), "rb").read()
buf = io.BytesIO(); png.save(buf, "JPEG", quality=88, optimize=True); jpg = buf.getvalue()
digest = hashlib.sha256(jpg + pdf[:0]).hexdigest()[:16]
html, m, cur = zcrypto.load(PAGE, pin) if os.path.getsize(PAGE) and "ENC={\"s\"" in open(PAGE).read() else (open(PAGE).read(), None, None)
if cur and cur.get("h") == digest:
    print("map unchanged"); sys.exit(0)
payload = {"name": name, "h": digest, "jpg": base64.b64encode(jpg).decode(), "pdf": base64.b64encode(pdf).decode()}
if m is None:   # first build: template has an empty "var ENC={};" - give zcrypto a regex match to replace
    import re
    m = zcrypto.PAT.search(html.replace("var ENC={};", 'var ENC={"s":"AAAAAAAAAAAAAAAAAAAAAA==","i":"AAAAAAAAAAAA","c":"AA==","n":600000};'))
    html = html.replace("var ENC={};", 'var ENC={"s":"AAAAAAAAAAAAAAAAAAAAAA==","i":"AAAAAAAAAAAA","c":"AA==","n":600000};')
zcrypto.save(PAGE, html, m, payload, pin)
print("map page written:", name, "%.1f MB" % (os.path.getsize(PAGE) / 1e6))

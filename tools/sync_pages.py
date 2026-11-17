#!/usr/bin/env python3
"""Make the treasurer and receipts pages mirror the committee page (the master payload).
Usage: ZARIA_PIN=... python3 tools/sync_pages.py [--write]   (dry-run unless --write)
treasurer: d = payments, b = {open, days}, rf = {ref: [[tag, link]]} (optional receipts);  receipts: d = receipts, b = full b block."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import zcrypto
pin = os.environ.get("ZARIA_PIN") or sys.exit("set ZARIA_PIN")
C = zcrypto.load("committee-q4n7vd/index.html", pin)[2]
def receipt_map():
    """{M-Pesa ref: [[tag, Drive link], ...]} from the Sheet's 'Receipt Files' tab export (optional)."""
    if "--rf" not in sys.argv: return None
    try: rows = json.load(open(sys.argv[sys.argv.index("--rf") + 1]))["values"][1:]
    except OSError: return None
    m = {}
    for r in rows:
        r = r + [""] * (9 - len(r))
        if r[1] and r[6]: m.setdefault(r[1], []).append([r[2], r[6]])
    return m
RF = receipt_map()
want = {"treasurer-zv7k2q": {"d": C["p"], "b": {"open": C["b"]["open"], "days": C["b"]["days"]}},
        "receipts-r5m8xw": {"d": C["r"], "b": C["b"]}}
for name, payload in want.items():
    path = name + "/index.html"
    html, m, cur = zcrypto.load(path, pin)
    if name == "treasurer-zv7k2q":      # expenditure report: optional receipt links
        rf = RF if RF is not None else cur.get("rf", {})
        if rf: payload["rf"] = rf
    same = cur == payload
    print(name, "up to date" if same else "DIFFERS")
    if not same and "--write" in sys.argv:
        zcrypto.save(path, html, m, payload, pin); print("  written")

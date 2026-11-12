#!/usr/bin/env python3
"""Make the treasurer and receipts pages mirror the committee page (the master payload).
Usage: ZARIA_PIN=... python3 tools/sync_pages.py [--write]   (dry-run unless --write)
treasurer: d = payments, b = {open, days};  receipts: d = receipts, b = full b block."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import zcrypto
pin = os.environ.get("ZARIA_PIN") or sys.exit("set ZARIA_PIN")
C = zcrypto.load("committee-q4n7vd/index.html", pin)[2]
want = {"treasurer-zv7k2q": {"d": C["p"], "b": {"open": C["b"]["open"], "days": C["b"]["days"]}},
        "receipts-r5m8xw": {"d": C["r"], "b": C["b"]}}
for name, payload in want.items():
    path = name + "/index.html"
    html, m, cur = zcrypto.load(path, pin)
    same = cur == payload
    print(name, "up to date" if same else "DIFFERS")
    if not same and "--write" in sys.argv:
        zcrypto.save(path, html, m, payload, pin); print("  written")

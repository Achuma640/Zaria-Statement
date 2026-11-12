#!/usr/bin/env python3
"""Compare Sheet exports against the published committee page.

Usage: ZARIA_PIN=... python3 tools/check_sync.py transactions.json
`transactions.json` is the output of reading Transactions!A1:P1000 from the Sheet
(a dict with a "values" list). Reports refs or amounts that differ.
"""
import base64, json, os, re, sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

pin = os.environ.get("ZARIA_PIN")
if not pin:
    sys.exit("set ZARIA_PIN")
html = open("committee-q4n7vd/index.html").read()
E = json.loads(re.search(r"var ENC=(\{.*?\});", html).group(1))
d = base64.b64decode
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=d(E["s"]), iterations=E["n"]).derive(pin.encode())
C = json.loads(AESGCM(key).decrypt(d(E["i"]), d(E["c"]), None))

rows = json.load(open(sys.argv[1]))["values"][1:]
rows = [r + [""] * (16 - len(r)) for r in rows]
num = lambda s: float(str(s).replace(",", "") or 0)
rec = {r[1]: r for r in rows if r[2] == "Receipt"}
pay = {r[1]: r for r in rows if r[2] == "Payment"}
pr = {r[2]: r for r in C["r"]}
pp = {p[2]: p for p in C["p"]}
# Splits (_1 suffixes) and July float top-ups live only in the page data.
print("receipts in Sheet not on page:", sorted(set(rec) - set(pr)))
print("payments in Sheet not on page:", sorted(set(pay) - set(pp)))
print("payments on page not in Sheet:", sorted(set(pp) - set(pay)))
bad = [k for k in pay if k in pp and abs(num(pay[k][3]) - pp[k][3]) > 0.01]
print("payment amount differences:", bad)

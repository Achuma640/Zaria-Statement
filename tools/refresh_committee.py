#!/usr/bin/env python3
"""Add NEW Sheet transactions to the committee page's p (payments) / r (receipts) lists.

Usage: ZARIA_PIN=... python3 tools/refresh_committee.py transactions.json [--write]
Only refs not already on the page are added (page data holds curated names and
splits that the Sheet does not, so a full regeneration would lose them).
Dry-run by default. NOTE: does not yet recompute the 'b' block (daily balance,
map, units) - that still needs the balance rebuild step.
"""
import datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import zcrypto

CATS = {"General": "Service charge / general"}
num = lambda s: float(str(s).replace(",", "") or 0)

def rec(r):
    d = dt.datetime.strptime(r[0], "%d-%b-%Y %H:%M")
    base = [d.strftime("%Y-%m-%d"), d.strftime("%H:%M"), r[1], num(r[3]), num(r[4])]
    if r[2] == "Payment":
        return base + [r[5], r[6], r[9]]
    plot = "Plot " + r[7] + (" & " + r[8] if r[8] else "") if r[7] else "Plot not recorded"
    return base + [r[6].title(), plot, CATS.get(r[9], r[9])]

def main():
    pin = os.environ.get("ZARIA_PIN") or sys.exit("set ZARIA_PIN")
    path = "committee-q4n7vd/index.html"
    html, m, C = zcrypto.load(path, pin)
    rows = [r + [""] * (18 - len(r)) for r in json.load(open(sys.argv[1]))["values"][1:]]
    have = {x[2].split("_")[0] for x in C["p"] + C["r"]}
    new = {"Payment": [], "Receipt": []}
    for r in rows:
        if r[2] in new and r[1] not in have:
            new[r[2]].append(rec(r))
    print("new payments:", len(new["Payment"]), "new receipts:", len(new["Receipt"]))
    for k in new.values():
        for x in k: print(" ", x)
    if "--write" in sys.argv and (new["Payment"] or new["Receipt"]):
        C["p"] = sorted(C["p"] + new["Payment"], key=lambda x: (x[0], x[1]), reverse=True)
        C["r"] = sorted(C["r"] + new["Receipt"], key=lambda x: (x[0], x[1]), reverse=True)
        zcrypto.save(path, html, m, C, pin)
        print("written")

if __name__ == "__main__":
    main()

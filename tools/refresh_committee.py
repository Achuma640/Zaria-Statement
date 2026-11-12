#!/usr/bin/env python3
"""Add NEW Sheet transactions to the committee page's p (payments) / r (receipts) lists.

Usage: ZARIA_PIN=... python3 tools/refresh_committee.py transactions.json [--sc service_charge.json] [--write]
Only refs not already on the page are added (page data holds curated names and
splits that the Sheet does not, so a full regeneration would lose them).
Dry-run by default. Also rebuilds b.days (daily balance) from the Sheet. b.units/map not yet.
"""
import datetime as dt, json, os, re, sys
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

def days(rows):
    """Per-date [date, money in, money out, last time] from the Sheet (matches the page, except the
    KES 60 'Charge on payment' of 20 Jun 2026, which the old page put on 21 Mar; closing is unchanged)."""
    A = {}
    for r in rows:
        if not r[0] or r[2] not in ("Payment", "Receipt", "Float top-up", "Charge on payment"):
            continue
        d = dt.datetime.strptime(r[0], "%d-%b-%Y %H:%M"); a, c = num(r[3]), num(r[4])
        i, o = (0, a + c) if r[2] == "Payment" else (a, c)
        e = A.setdefault(d.strftime("%Y-%m-%d"), [0.0, 0.0, "00:00"])
        e[0] += i; e[1] += o; e[2] = max(e[2], d.strftime("%H:%M"))
    return [[k, round(e[0], 2), round(e[1], 2), e[2]] for k, e in sorted(A.items())]

def _f(x):
    x = str(x).replace(",", "")
    return float(x) if x.replace(".", "").lstrip("-").isdigit() else 0.0

def units(U, sc):
    """Refresh coverage c (18 months May25-Oct26), credit cr and not-due nd from the Service Charge export
    ('Service Charge'!A7:BU80). Names n, status s and notes t are kept. Returns the changed unit keys."""
    changed = []
    for r in sc:
        r = r + [""] * (73 - len(r))
        u = U.get(str(r[0]))
        if not u:
            print("unit not on page:", r[0]); continue
        nd = int(_f(r[71]) or 1) - 1
        c = [1 if str(x).upper() == "TRUE" and i >= nd else 0 for i, x in enumerate(r[50:68])]
        cr = _f(r[22])
        if (u["c"], u["nd"], u["cr"]) != (c, nd, cr):
            u["c"], u["nd"], u["cr"] = c, nd, cr; changed.append(r[0])
    return changed

def main():
    pin = os.environ.get("ZARIA_PIN") or sys.exit("set ZARIA_PIN")
    path = "committee-q4n7vd/index.html"
    html, m, C = zcrypto.load(path, pin)
    before = json.dumps(C, sort_keys=True)
    rows = [r + [""] * (18 - len(r)) for r in json.load(open(sys.argv[1]))["values"][1:]]
    bad = [r[1] for r in rows if not re.match(r"^\d{2}-\w{3}-\d{4} \d{2}:\d{2}$", r[0]) and r[1]]
    if bad: print("SKIPPED rows with unreadable dates (fix in the Sheet):", bad)
    rows = [r for r in rows if re.match(r"^\d{2}-\w{3}-\d{4} \d{2}:\d{2}$", r[0])]
    have = {x[2].split("_")[0] for x in C["p"] + C["r"]}
    new = {"Payment": [], "Receipt": []}
    for r in rows:
        if r[2] in new and r[1] not in have:
            new[r[2]].append(rec(r))
    print("new payments:", len(new["Payment"]), "new receipts:", len(new["Receipt"]))
    for k in new.values():
        for x in k: print(" ", x)
    nd = days(rows)
    close = lambda dd: round(C["b"]["open"] + sum(x[1] - x[2] for x in dd), 2)
    print("closing balance: page %.2f -> sheet %.2f" % (close(C["b"]["days"]), close(nd)))
    if "--sc" in sys.argv:
        ch = units(C["b"]["units"], json.load(open(sys.argv[sys.argv.index("--sc") + 1]))["values"])
        print("units changed:", ch)
    if "--write" in sys.argv:
        C["b"]["days"] = nd
        C["p"] = sorted(C["p"] + new["Payment"], key=lambda x: (x[0], x[1]), reverse=True)
        C["r"] = sorted(C["r"] + new["Receipt"], key=lambda x: (x[0], x[1]), reverse=True)
        if json.dumps(C, sort_keys=True) == before:
            print("no change; page left as is")
        else:
            zcrypto.save(path, html, m, C, pin)
            print("written")

if __name__ == "__main__":
    main()

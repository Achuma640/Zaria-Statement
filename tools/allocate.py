#!/usr/bin/env python3
"""Apply NEW service-charge receipts to the oldest unpaid month first.

Reads two Sheet exports (JSON from the Sheets values API: {"values": [...]}):
  --tx  Transactions!A1:R<last>   column R ("Applied") is blank for rows not yet applied
  --sc  'Service Charge'!A7:BU<last>
Writes a JSON plan (--out) of cell updates for the Sheet and prints a summary.
It never writes to the Sheet itself, so either treasurer's Claude can review and apply it.

Rules (see HANDOFF.md): General receipts only; oldest unpaid due month first; monthly rate
5,000 (5,500 where the plot has paid 5,500 before); remainder carries to the next receipt
(column BU of the Service Charge tab); months before the plot's "due from" (BT) are skipped;
only Resident/Building units are charged.
"""
import argparse, json
from datetime import datetime

MONTHS = ["May 25","Jun 25","Jul 25","Aug 25","Sep 25","Oct 25","Nov 25","Dec 25","Jan 26",
          "Feb 26","Mar 26","Apr 26","May 26","Jun 26","Jul 26","Aug 26","Sep 26","Oct 26","Nov 26"]
FLAG0, RCVD0 = 50, 30          # 0-based column index of AY (May 25 flag) and AE (May 25 received)
NOT_CHARGED = {"106", "148", "156"}   # plots that are never charged service charge
COL_BT, COL_BU = 71, 72        # 0-based index of BT (first month due) and BU (carry)


def col(n):                    # 0-based index -> A1 letters
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def num(s):
    s = str(s).replace(",", "").strip()
    return 0.0 if s in ("", "-") else float(s)


def truth(v):
    return str(v).upper() in ("TRUE", "1")


def plan(tx_rows, sc_rows, first_sc_row=7, tx_first_row=2):
    units = {}
    for i, r in enumerate(sc_rows):
        r = r + [""] * (75 - len(r))
        if not r[0] or r[0] == "TOTAL":
            continue
        rcvd = [num(x) for x in r[RCVD0:RCVD0 + 19]]
        rate = 5500 if any(abs(x - 5500) < 1 for x in rcvd) else 5000
        units[r[0]] = dict(
            row=first_sc_row + i, status=r[2], rate=rate,
            nd=max(int(num(r[COL_BT]) or 1) - 1, 0),
            flags=[truth(x) for x in r[FLAG0:FLAG0 + 19]],
            carry=num(r[COL_BU]), notes=[], carry0=num(r[COL_BU]), flags0=None)
    for u in units.values():
        u["flags0"] = list(u["flags"])
    plot_to_unit = {}
    for k in units:
        for p in k.split("-"):
            plot_to_unit[p] = k
    writes, applied = [], []
    todo = []
    for i, r in enumerate(tx_rows):
        r = r + [""] * (18 - len(r))
        if r[2] == "Receipt" and r[9] == "General" and not r[17]:
            todo.append((datetime.strptime(r[0], "%d-%b-%Y %H:%M"), tx_first_row + i, r))
    todo.sort(key=lambda t: t[0])
    for _, rowno, r in todo:
        if not str(r[7]).strip():       # no plot yet (row still being typed): retry next run
            applied.append((rowno, r[1], "skipped: no plot"))
            continue
        key = plot_to_unit.get(str(r[7]).strip()) or (r[16] if r[16] in units else None)
        if not key and str(r[7]).strip() in NOT_CHARGED:
            writes.append(dict(range="Transactions!R%d" % rowno, values=[["not charged"]]))
            applied.append((rowno, r[1], "plot %s not charged" % r[7]))
            continue
        if not key:                      # unknown plot: leave a visible flag for a person
            lab = "REVIEW: plot %s not on Service Charge tab" % r[7]
            applied.append((rowno, r[1], lab))
            writes.append(dict(range="Transactions!R%d" % rowno, values=[[lab]]))
            continue
        u = units[key]
        if u["status"] not in ("Resident", "Building"):
            writes.append(dict(range="Transactions!R%d" % rowno, values=[["not charged"]]))
            applied.append((rowno, r[1], "unit %s not charged" % key))
            continue
        money = u["carry"] + num(r[3])
        got = []
        while money >= u["rate"]:
            idx = next((m for m in range(u["nd"], 19) if not u["flags"][m]), None)
            if idx is None:
                break
            u["flags"][idx] = True
            got.append(MONTHS[idx])
            money -= u["rate"]
        u["carry"] = money
        label = ("Applied: " + ", ".join(got)) if got else "Held as credit"
        if money and not got:
            label += " (%d)" % money
        writes.append(dict(range="Transactions!R%d" % rowno, values=[[label]]))
        applied.append((rowno, r[1], "%s %s: %s" % (key, r[3], label)))
    for k, u in units.items():
        for m in range(19):
            if u["flags"][m] != u["flags0"][m]:
                writes.append(dict(range="'Service Charge'!%s%d" % (col(FLAG0 + m), u["row"]),
                                   values=[[u["flags"][m]]]))
        if abs(u["carry"] - u["carry0"]) > 0.001:
            writes.append(dict(range="'Service Charge'!%s%d" % (col(COL_BU), u["row"]),
                               values=[[u["carry"]]]))
    return writes, applied


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tx", required=True)
    ap.add_argument("--sc", required=True)
    ap.add_argument("--out", default="allocation_plan.json")
    a = ap.parse_args()
    tx = json.load(open(a.tx))["values"][1:]
    sc = json.load(open(a.sc))["values"]
    w, ap_ = plan(tx, sc)
    json.dump(w, open(a.out, "w"), indent=1)
    for x in ap_:
        print(x[1], x[2])
    print("%d receipts, %d cell updates -> %s" % (len(ap_), len(w), a.out))

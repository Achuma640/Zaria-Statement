#!/usr/bin/env python3
"""Publish committee-approved worker recommendations, with vote counts, into estate.json ("workers").
One vote per plot per worker. Usage: python3 tools/build_workers.py workers.json worker_votes.json"""
import json, sys, re
W = json.load(open(sys.argv[1])).get("values", [])[1:]
V = json.load(open(sys.argv[2])).get("values", [])[1:]
seen = {}
for r in V:
    r = list(r) + [""] * 3
    wid, plot = str(r[1]).strip(), re.sub(r"\s+", "", str(r[2]).lower())
    if wid and plot:
        seen.setdefault(wid, set()).add(plot)
def phone(p):
    """Kenyan numbers: Sheets drops the leading 0 (712280152), so restore it. 254/+254 forms become 0..."""
    d = re.sub(r"\D", "", p)
    if d.startswith("254") and len(d) == 12:
        d = "0" + d[3:]
    elif len(d) == 9 and d[0] in "71":
        d = "0" + d
    return d or p
out = []
for i, r in enumerate(W, start=2):
    r = list(r) + [""] * 8
    ok, trade, name, phone_raw, note, by = [str(x).strip() for x in r[:6]]
    if ok.upper() not in ("TRUE", "YES", "1") or not name or not trade:
        continue
    out.append({"id": str(i), "trade": trade, "name": name, "phone": phone(phone_raw), "note": note,
                "by": by, "votes": len(seen.get(str(i), ()))})
out.sort(key=lambda w: (w["trade"], -w["votes"], w["name"]))
j = json.load(open("estate.json"))
if j.get("workers") != out:
    j["workers"] = out
    json.dump(j, open("estate.json", "w"), indent=1, ensure_ascii=False)
print(len(out), "approved workers")

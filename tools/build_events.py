#!/usr/bin/env python3
"""Publish committee-approved notices from the Sheet's Notices tab into estate.json ("events").
Only rows with Approved ticked and a date today or later are published; the submitter column is never copied.
Usage: python3 tools/build_events.py notices.json"""
import json, sys, datetime
rows = json.load(open(sys.argv[1])).get("values", [])[1:]
today = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).date()
ev = []
for r in rows:
    r = list(r) + [""] * 8
    ok, d, tm, where, title, plot, note = [str(x).strip() for x in r[:7]]
    if ok.upper() not in ("TRUE", "YES", "1") or not title:
        continue
    try:
        dd = datetime.date.fromisoformat(d[:10])
    except ValueError:
        continue
    if dd < today:
        continue
    ev.append({"date": dd.isoformat(), "time": tm, "where": where,
               "title": title + (", plot " + plot if plot and plot not in title else ""), "note": note})
ev.sort(key=lambda e: e["date"])
j = json.load(open("estate.json"))
if j.get("events") != ev:
    j["events"] = ev
    json.dump(j, open("estate.json", "w"), indent=1, ensure_ascii=False)
print(len(ev), "approved upcoming notices")

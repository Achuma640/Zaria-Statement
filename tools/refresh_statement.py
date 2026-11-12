#!/usr/bin/env python3
"""Incrementally update the plot statement page (index.html, `const D={...}`) from the Sheet.

Usage: python3 tools/refresh_statement.py transactions.json service_charge.json [--write]
Adds receipts whose ref is not yet in D.P, marks newly covered months in D.V (cov, disp, ahead,
credit, nd) and adds a note to D.N from the Transactions column R label ("Applied: Jun 26, Jul 26").
Existing display data is never rewritten, only extended. Dry-run unless --write.
"""
import datetime as dt, json, re, sys

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
num = lambda s: float(str(s).replace(",", "").strip() or 0) if str(s).replace(",", "").replace(".", "").lstrip("-").strip().isdigit() else 0.0

def mlabel(s):               # "Jun 26" -> "Jun 2026"
    m, y = s.split(); return "%s 20%s" % (m, y)

def update(D, tx, sc, log=print):
    P, V, N = D["P"], D["V"], D["N"]
    last = max(p[0] for p in P)
    have = {p[1] for p in P}
    new = []
    for r in tx:
        r = r + [""] * (18 - len(r))
        if r[2] != "Receipt" or r[1].split("_")[0] in have or not r[0]:
            continue
        d = dt.datetime.strptime(r[0], "%d-%b-%Y %H:%M")
        if d.strftime("%Y-%m-%d") >= last and str(r[7]).strip():   # older gaps are historic, not new
            new.append((d, r))
    new.sort(key=lambda t: t[0])
    for d, r in new:
        P.append([d.strftime("%Y-%m-%d"), r[1], num(r[3]) if num(r[3]) % 1 else int(num(r[3])), r[5], r[6],
                  str(r[7]), "", r[9], d.strftime("%H:%M")])
        label = r[17]
        if label.startswith("Applied:"):
            ms = [mlabel(x.strip()) for x in label[8:].split(",")]
            N.append([str(r[7]), "%s %d" % (MONTHS[d.month - 1], d.year),
                      "Received KES %s on %d %s %d (ref %s); applied to %s (earlier unpaid months were cleared first)."
                      % ("{:,}".format(int(num(r[3]))), d.day, MONTHS[d.month - 1], d.year, r[1], ", ".join(ms))])
        log("new receipt", r[1], r[3], "plot", r[7], label)
    for row in sc:
        row = row + [""] * (73 - len(row))
        v = V.get(row[0])
        if not v:
            log("unit not on statement page:", row[0]); continue
        nd = int(num(row[71]) or 1) - 1
        rcvd = [num(x) for x in row[30:49]]
        rate = 5500 if any(abs(x - 5500) < 1 for x in rcvd) else 5000
        v["credit"] = num(row[22])
        if nd:
            v["nd"] = nd
        for i in range(19):
            if str(row[50 + i]).upper() == "TRUE" and i >= nd and not v["cov"][i]:
                v["cov"][i] = 1
                if i < 18: v["disp"][i] = rate
                else: v["ahead"][i - 18] = rate
                log("plot", row[0], "month", i, "newly covered")
    for d, r in new:                       # receipt arrived in a month but was applied to older months
        mi = (d.year - 2025) * 12 + d.month - 5
        v = V.get(str(r[7]))
        if v and r[9] == "General" and 14 <= mi < 18 and not v["cov"][mi] and v["disp"][mi] == 0:
            v["disp"][mi] = -1
    return D

if __name__ == "__main__":
    html = open("index.html").read()
    m = re.search(r"const D=(\{.*?\});\s*\n", html, re.S)
    D = json.loads(m.group(1))
    tx = [r for r in json.load(open(sys.argv[1]))["values"][1:] if r and re.match(r"^\d{2}-\w{3}-\d{4} \d{2}:\d{2}$", r[0])]
    update(D, tx, json.load(open(sys.argv[2]))["values"])
    out = html[:m.start(1)] + json.dumps(D, separators=(",", ":"), ensure_ascii=False) + html[m.end(1):]
    last = max(dt.datetime.strptime(r[0], "%d-%b-%Y %H:%M") for r in tx if r and r[0])
    out = re.sub(r"(10 Feb 2025 – )\d+ \w+ \d{4}", lambda x: x.group(1) + "%d %s %d" % (last.day, MONTHS[last.month - 1], last.year), out)
    if out == html:
        print("no change")
    elif "--write" in sys.argv:
        open("index.html", "w").write(out); print("written")
    else:
        print("changes pending (use --write)")

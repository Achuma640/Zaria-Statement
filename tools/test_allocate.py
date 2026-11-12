import sys; sys.path.insert(0, "tools")
from allocate import plan, MONTHS

def sc_row(unit, status, flags, nd=0, carry=0, rcvd=None):
    r = [""] * 75
    r[0], r[2] = unit, status
    for i in range(19):
        r[50 + i] = "TRUE" if flags[i] else "FALSE"
        r[30 + i] = (rcvd or [0] * 19)[i]
    r[71], r[72] = nd + 1, carry
    return r

def tx(ref, amt, plot, date="05-Nov-2026 10:00"):
    r = [""] * 18
    r[0], r[1], r[2], r[3], r[7], r[9] = date, ref, "Receipt", "{:,.2f}".format(amt), plot, "General"
    return r

# 1. plot 61 style: unpaid since May 25, 5,000 -> May 2025 first
f = [False] * 19
w, a = plan([tx("A1", 5000, "61")], [sc_row("61", "Building", f)])
assert any(x["range"].startswith("'Service Charge'!AY") and x["values"] == [[True]] for x in w), w
# 2. 10,000 clears the two oldest unpaid months, skipping paid ones
f = [True, True, False, True, False] + [True] * 14
w, a = plan([tx("A2", 10000, "87")], [sc_row("87", "Resident", f)])
cells = sorted(x["range"] for x in w if x["range"].startswith("'Service Charge'!"))
assert cells == ["'Service Charge'!BA7", "'Service Charge'!BC7"], cells
# 3. not-due months (nd) are never filled
f = [True] * 14 + [False] * 5
w, a = plan([tx("A3", 5000, "65")], [sc_row("65", "Building", f, nd=14)])
assert any(x["range"] == "'Service Charge'!BM7" for x in w), w
# 4. partial payments carry: 3,000 then 2,000 = one month
f = [False] * 19
w, a = plan([tx("A4", 3000, "9", "01-Nov-2026 09:00"), tx("A5", 2000, "9", "02-Nov-2026 09:00")], [sc_row("9", "Resident", f)])
assert any(x["range"] == "'Service Charge'!AY7" for x in w) and not any(x["range"].endswith("AZ7") for x in w)
# 5. fully paid unit: money stays as carry, nothing flagged
f = [True] * 19
w, a = plan([tx("A6", 15000, "13")], [sc_row("13", "Resident", f)])
assert [x for x in w if x["range"].startswith("'Service Charge'!B")][0]["values"] == [[15000.0]]
# 6. already-applied receipts are ignored; non-charged plots are marked
r = tx("A7", 5000, "106"); w, a = plan([r], [sc_row("13", "Resident", [True] * 19)])
assert w[0]["values"] == [["not charged"]]
r = tx("A8", 5000, "13"); r[17] = "legacy"; w, a = plan([r], [sc_row("13", "Resident", [False] * 19)])
assert w == []
print("all allocator tests passed")

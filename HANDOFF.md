# Zaria Village treasurer pipeline: handoff notes

Paybill 820820, account `1136#plot`. Two treasurers may work on this, each with their own Claude.
Keep this file current. Do not put the report PIN or residents' phone numbers in the repo.

## Single source of truth
The Google Sheet **Zaria Village Receipts and Payments** (ID `1E9q6ot6hEpbIsJujR72FJ24i1eZcH5SWNAk930pMRfY`).
Everything else (GitHub pages, Excel files, payment-map PDFs, residents deck, flyer) is **generated** from it. Never edit a generated output by hand; fix the Sheet and rebuild.

| Tab | Role |
|---|---|
| Transactions | Every receipt and payment (one row per M-Pesa ref). Columns A..O are inputs. **Column P (Period) is an ARRAYFORMULA starting at P2 and Q (Unit) is a formula. Never write into P or Q.** |
| Tendepay Import / To Add | Paste a Tendepay CSV here; To Add categorises new rows using Category Rules. |
| Category Rules | Keyword rules for payment categories, road threshold (15,000 from 1 Jul 2026), AGM exact amount (1,000 from 1 Jun 2026). |
| Master / Plot Register | Names, status (Resident/Building/blank), phones. Register records when a plot was bought or started building. Service charge is due only from that month. |
| Service Charge | Per-unit monthly coverage. `AY:BQ` hold the covered flags (May 25 = AY ... Nov 26 = BQ), `W` the credit brought forward, `BT` the first month due (1 = May 2025). Months before BT show `n/a` and their flag is TRUE. |
| Monthly Summary / Month Summary | Receipts, payments, balances by month (Feb 25 ... Nov 26, Total in X). |
| Comments | Notes shown on the statement page and Excel files. |

## Standing rules
- A Tendepay CSV sent with no text means "update all": add only NEW transactions everywhere, then resend the Excel files and payment-map PDFs.
- Payments apply to the **oldest unpaid month first**.
- Receipts of 15,000 and above are service charge from 1 Oct 2026 unless marked road.
- Service charge is due from the 5th and active from the 6th.
- Plots 106, 148 and 156 are not charged. A plot's charge is due only from its "Due from" month.
- Arrears counts only Resident and Building units. 159-160 is one Building unit; 224-225 is one unit.
- Plot 65: the KES 20,000 of 24 Oct 2026 (UJOOI029VY) is **service charge** (decided 12 Nov 2026).
- Plot 221: the 20 Jul 2026 KES 5,000 (UGKSG3P3WM) is one receipt, not also a float top-up.
- Closing balance should agree with the Tendepay statement within a few shillings (Tendepay rounds charges; 11 Nov 2026 difference was KES 3).

## Published outputs (GitHub Pages, repo `Achuma640/zaria-statement`)
- `index.html` public statement page: `const D={P,C,U,M,V,N}` in plain JSON.
- `committee-q4n7vd/`, `treasurer-zv7k2q/`, `receipts-r5m8xw/`: locked pages holding `var ENC={s,i,c,n}`, AES-GCM with a PBKDF2-SHA256 key (600000 iterations; fresh 16-byte salt, 12-byte IV, base64). Decrypted payloads: committee `{p,r,b}`, treasurer `{d,b}`, receipts `{d,b}`. The PIN is held by the treasurers, not in this repo.
- `nov-committee-zv/`, `nov-update-zv/`: November pages (last built 6 Nov).
- Record layouts: receipt `[date,time,ref,amount,charge,who,'Plot N',category]`; payment `[date,time,ref,amount,charge,payee,description,category]`; `b.days` = `[date,in,out,time]`, balance = 446378 + sum(in - out).

## What a rebuild needs (the gap)
The coverage flags in the Sheet are *stored results*, not live formulas: after new receipts arrive, someone must apply them oldest-unpaid-first and write the flags and credit. The allocator script was lost with an earlier workspace reset and is not yet rebuilt. `tools/check_sync.py` verifies the Sheet against the published pages so drift is caught.

## Open items (12 Nov 2026)
- Allocator and page builders to be rebuilt as scripts in `tools/` (so any Claude or a GitHub Action can run them).
- November pages (`nov-*`), names-map PDF, interactive map artifacts, and committee members PDF are not regenerated.
- Plot 236 phone numbers; plots 77, 269, 276 names (no payments yet); plot 262 owner.
- Transactions!Q2 shows #REF! (first data row only).

## Gotchas learned
- Update the user's own Excel files in place; do not rebuild them from scratch.
- Local `python3 -m http.server 8765` dies; restart it before screenshots.

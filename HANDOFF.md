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

## Applying new receipts (the allocator)
`tools/allocate.py` applies NEW General receipts to the oldest unpaid month first and prints a plan of Sheet cell updates (it never writes to the Sheet itself). Tests: `python3 tools/test_allocate.py`.
- Transactions column R ("Applied") is blank for rows not yet applied; every row up to 11 Nov 2026 is marked `legacy`. After applying, write the plan's `Applied: ...` text into R so a receipt is never applied twice.
- Service Charge column BU ("Carry (KES)") holds a partial remainder (e.g. 2,500 toward the next month). Flags are `AY:BQ`.
- Steps for "update all": (1) paste the Tendepay CSV into Tendepay Import / To Add and move the new rows to Transactions (never touch P or Q); (2) export `Transactions!A1:R1000` and `'Service Charge'!A7:BU90`; (3) run `allocate.py` and write its updates; (4) rebuild the outputs.

## Automatic rebuild (GitHub Action "Rebuild reports from the Sheet", every 3 h or manual)
fetch Sheet (service account, secret GOOGLE_SA_KEY) -> `allocate.py` -> `apply_plan.py` (writes R / flags / BU; refuses >40 receipts) -> re-fetch -> `refresh_committee.py --write` -> `sync_pages.py --write` -> commit if changed. Receipts with no plot are retried next run; a plot missing from the Service Charge tab gets `REVIEW: ...` in column R for a person to fix. `refresh_statement.py` then extends the plot statement page (new receipts, newly covered months, notes from column R, header date). Tested by replaying 9 Nov -> 11 Nov: reproduced the published page exactly. Not automated in the Action (they hold phones/names and the repo is public): Excel files - `tools/update_lookup_xlsx.py PREVIOUS.xlsx OUT.xlsx` rebuilds the Plot Statement Lookup workbook; the Receipts and Payments workbook is rebuilt by Claude from the Sheet. Payment map: `python3 tools/make_map_pdf.py OUT_DIR` (needs Pillow; uses receipts-r5m8xw/nav.jpg + navp.json) writes the PNG and PDF; classes: purple never paid, red 5+ unpaid, yellow 1-4, green up to date. Names map, committee members PDF and interactive maps are not scripted yet. Monthly chore: a new month needs a new column in the Sheet (and a 20th flag/received column) before the allocator can fill it.

## Page tools
- `tools/sync_pages.py [--write]` copies the committee payload into the treasurer and receipts pages (run after refresh_committee --write).
- `tools/zcrypto.py` decrypts/re-encrypts the locked pages (PIN via `ZARIA_PIN`, never stored).
- `tools/refresh_committee.py transactions.json [--sc service_charge.json] [--write]` adds only NEW refs to the committee page lists, rebuilds the daily balance and (with --sc) refreshes unit coverage/credit/not-due. Dry-run by default; 0 differences today. It does not yet rebuild the `b` block (balances/map/units), the treasurer and receipts pages, statement `D`, Excel or PDFs.

## Open items (12 Nov 2026)
- Page builders (statement, locked reports, Excel, map) still to be rebuilt as scripts in `tools/`; the allocator is done.
- November pages (`nov-*`), names-map PDF, interactive map artifacts, and committee members PDF are not regenerated.
- Plot 236 phone numbers; plots 77, 269, 276 names (no payments yet); plot 262 owner.
- Transactions!Q2 shows #REF! (first data row only).

## Gotchas learned
- Update the user's own Excel files in place; do not rebuild them from scratch.
- Local `python3 -m http.server 8765` dies; restart it before screenshots.

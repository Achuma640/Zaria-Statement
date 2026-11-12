#!/usr/bin/env python3
"""Download the two Sheet ranges the rebuild needs, as {"values": [...]} JSON.
Needs GOOGLE_SA_KEY (service-account JSON, as text) in the environment.
Usage: python3 tools/fetch_sheet.py OUT_DIR   -> OUT_DIR/transactions.json, OUT_DIR/service_charge.json"""
import json, os, sys
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

SHEET = "1E9q6ot6hEpbIsJujR72FJ24i1eZcH5SWNAk930pMRfY"
RANGES = {"transactions.json": "Transactions!A1:R3007", "service_charge.json": "'Service Charge'!A7:BU80"}
creds = service_account.Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_SA_KEY"]), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
s = AuthorizedSession(creds)
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for fn, rng in RANGES.items():
    r = s.get("https://sheets.googleapis.com/v4/spreadsheets/%s/values/%s" % (SHEET, rng))
    r.raise_for_status()
    vals = r.json().get("values", [])
    # drop empty trailing rows
    while vals and not any(vals[-1]):
        vals.pop()
    json.dump({"values": vals}, open(os.path.join(out, fn), "w"))
    print(fn, len(vals), "rows")

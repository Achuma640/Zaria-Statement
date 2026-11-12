#!/usr/bin/env python3
"""Write an allocation plan (from allocate.py) to the Sheet. Needs GOOGLE_SA_KEY (Editor access).
Usage: python3 tools/apply_plan.py allocation_plan.json [--max-receipts 40]
Refuses to write if the plan touches more Transactions rows than --max-receipts (likely a mistake)."""
import json, os, sys
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
SHEET = "1E9q6ot6hEpbIsJujR72FJ24i1eZcH5SWNAk930pMRfY"
plan = json.load(open(sys.argv[1]))
cap = int(sys.argv[sys.argv.index("--max-receipts") + 1]) if "--max-receipts" in sys.argv else 40
rows = sum(1 for w in plan if w["range"].startswith("Transactions!R"))
if not plan:
    print("nothing to apply"); sys.exit(0)
if rows > cap:
    sys.exit("plan marks %d receipts (> %d): refusing, needs a person" % (rows, cap))
creds = service_account.Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_SA_KEY"]), scopes=["https://www.googleapis.com/auth/spreadsheets"])
r = AuthorizedSession(creds).post(
    "https://sheets.googleapis.com/v4/spreadsheets/%s/values:batchUpdate" % SHEET,
    json={"valueInputOption": "USER_ENTERED", "data": plan})
r.raise_for_status()
print("applied %d cell updates (%d receipts)" % (len(plan), rows))

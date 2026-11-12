#!/usr/bin/env python3
"""Decide whether this scheduled tick should run the rebuild (Nairobi time, UTC+3).
Window 08:00-22:30 every day. Weekdays: hourly. Weekends: every 3 hours (08,11,14,17,20).
First 5 and last 5 days of a month: every 30 minutes, any day. Manual runs always go (handled in the workflow).
Usage: python3 tools/should_run.py [ISO-UTC-time]   -> prints true/false; with GITHUB_OUTPUT set, writes run=..."""
import calendar, datetime as dt, os, sys

def should_run(now_utc):
    t = now_utc + dt.timedelta(hours=3)
    h, m = t.hour, t.minute
    if h < 8 or h > 22 or (h == 22 and m >= 30):
        return False
    edge = t.day <= 5 or t.day > calendar.monthrange(t.year, t.month)[1] - 5
    if edge:
        return True
    hourly = m < 30
    if t.weekday() < 5:
        return hourly
    return hourly and (h - 8) % 3 == 0

if __name__ == "__main__":
    now = dt.datetime.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.utcnow()
    r = str(should_run(now)).lower()
    print(r)
    if os.environ.get("GITHUB_OUTPUT"):
        open(os.environ["GITHUB_OUTPUT"], "a").write("run=%s\n" % r)

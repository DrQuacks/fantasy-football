# peek_json.py
import json, sys

path = sys.argv[1] if len(sys.argv) > 1 else "snap_mMatchupScore_w7.json"
with open(path) as f:
    data = json.load(f)

def head_keys(label, obj, n=40):
    if isinstance(obj, dict):
        print(f"\n== {label} (dict, {len(obj)} keys) ==")
        print(list(obj.keys())[:n])
    elif isinstance(obj, list):
        print(f"\n== {label} (list, len={len(obj)}) ==")
        if obj and isinstance(obj[0], dict):
            print(" [0] keys:", list(obj[0].keys())[:n])
        else:
            print(" [0]:", obj[0] if obj else None)

# top level
head_keys("root", data)

# schedule
sched = data.get("schedule", [])
head_keys("schedule", sched)
if not sched:
    raise SystemExit("No schedule in this view/file")

m0 = sched[0]  # first matchup in that week
head_keys("schedule[0]", m0)

for side in ("home", "away"):
    team = m0.get(side, {})
    head_keys(f"schedule[0].{side}", team)

    rfsp = team.get("rosterForCurrentScoringPeriod", {})
    head_keys(f"{side}.rosterForCurrentScoringPeriod", rfsp)

    entries = rfsp.get("entries", [])
    head_keys(f"{side}.entries", entries)

    if entries:
        e0 = entries[0]
        head_keys(f"{side}.entries[0]", e0)

        ppe = e0.get("playerPoolEntry", {})
        head_keys(f"{side}.entries[0].playerPoolEntry", ppe)

        player = ppe.get("player", {})
        head_keys(f"{side}.entries[0].playerPoolEntry.player", player)

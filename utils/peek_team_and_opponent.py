# peek_team_and_opponent.py
import json, sys

path = sys.argv[1] if len(sys.argv) > 1 else "snap_mMatchupScore_w7.json"
with open(path) as f:
    data = json.load(f)

def safe_get(d, *keys):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return None
    return d

rows = []
for m in data.get("schedule", []):
    for side in ("home", "away"):
        team = m.get(side) or {}
        rfsp = team.get("rosterForCurrentScoringPeriod") or {}
        for e in rfsp.get("entries", []):
            ppe = e.get("playerPoolEntry") or {}
            player = ppe.get("player") or {}

            rows.append({
                "fantasyTeam": safe_get(team, "teamId"),
                "slot": e.get("lineupSlotId"),
                "playerId": player.get("id"),
                "name": player.get("fullName") or player.get("name"),
                "pro_team": player.get("proTeamAbbreviation") or player.get("proTeam"),
                "pro_opponent": e.get("opponentProTeamAbbreviation") or e.get("proOpponent") or e.get("opponent"),
                "gameDate": e.get("gameDate") or player.get("gameDate"),
                "onBye": e.get("onBye") or player.get("onBye"),
                "playedFlag": e.get("gamePlayed") or player.get("gamePlayed"),
                "points_this_week": e.get("appliedStatTotal") or e.get("points") or ppe.get("appliedStatTotal"),
                "projected_points": e.get("appliedProjectedStatTotal") or e.get("projectedPoints"),
            })

print(f"Sample {min(10,len(rows))} rows (of {len(rows)}):")
for r in rows[:10]:
    print(r)
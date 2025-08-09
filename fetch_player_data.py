from espn_api.football import League
import json

LEAGUE_ID = 57220027
YEAR = 2022

# Initialize the league
league = League(league_id=LEAGUE_ID, year=YEAR)

# Collect all players from all teams
all_players = []
for team in league.teams:
    all_players.extend(team.roster)

# Optionally include free agents
# all_players.extend(league.free_agents())

# Find Christian McCaffrey (case-insensitive match)
jj = next(p for p in all_players if "christian mccaffrey" in p.name.lower())

# Save full player object dictionary
with open("christian_mccaffrey_2022.json", "w") as f:
    json.dump(jj.__dict__, f, indent=2, default=str)

print(f"✅ Saved Christian McCaffrey's 2022 player object with keys: {list(jj.__dict__.keys())}")

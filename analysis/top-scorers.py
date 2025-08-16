from espn_api.football import League
from rich.console import Console
from rich.table import Table
from pprint import pprint

# === CONFIG ===
LEAGUE_ID = 57220027       # <-- replace with your league ID
YEAR = 2024               # <-- last season
espn_s2 = 'your_espn_s2_cookie'  # <-- optional: only for private leagues
swid = '{your_swid_cookie}'      # <-- optional: only for private leagues

# === INIT ===
console = Console()
league = League(league_id=LEAGUE_ID, year=YEAR)

# === Get your team (or first team for now) ===
my_team = league.teams[0]  # You can loop through all teams if needed

# === Loop through each player on the team ===
for player in my_team.roster:
    print(f"\n🧍 Player: {player.name}")
    
    # Fetch full player data (including complete .stats)
    full_player = league.player_info(playerId=player.playerId)

    # Print available weeks
    weeks = list(full_player.stats.keys())
    print(f"Available weeks: {weeks}")
    
    # Print stats for each available week
    for week, stats in full_player.stats.items():
        print(f"\n📅 Week {week}")
        for k, v in stats.items():
            print(f"  {k}: {v}")
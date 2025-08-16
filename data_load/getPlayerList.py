from espn_api.football import League
from collections import defaultdict
import os

LEAGUE_ID = 57220027
YEAR = 2024
SWID = os.getenv("ESPN_SWID")
ESPN_S2 = os.getenv("ESPN_S2")

league = League(league_id=LEAGUE_ID, year=YEAR)

player_points = defaultdict(float)

for week in range(1, 18):  # Assuming regular season is 17 weeks
    print(f"Checking week {week}...")
    try:
        box_scores = league.box_scores(week)
    except Exception as e:
        print(f"⚠️ Error in week {week}: {e}")
        continue

    for matchup in box_scores:
        for player in matchup.home_lineup + matchup.away_lineup:
            if player.points and player.points > 0:
                player_points[(player.name, player.playerId)] += player.points

# Sort and print results
sorted_players = sorted(player_points.items(), key=lambda x: -x[1])

print(f"\nPlayers who scored points in {YEAR}:\n")
for (name, player_id), total_points in sorted_players:
    print(f"{name} ({player_id}): {total_points:.2f} points")
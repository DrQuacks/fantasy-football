from espn_api.football import League
from espn_api.football import Player
from pymongo import MongoClient, UpdateOne
from tqdm import tqdm
import time

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["fantasy_football"]
collection = db["player_stats"]

for year in range(2019, 2025):
    print(f"\n📅 Processing year {year}")
    league = League(league_id=57220027, year=year)

    # Collect all unique players from weekly stats
    all_player_ids = set()

    for week in tqdm(range(1, 19), desc=f"Finding all player IDs in {year}"):
        try:
            box_scores = league.box_scores(week)
            for matchup in box_scores:
                for team in [matchup.home_lineup, matchup.away_lineup]:
                    for player in team:
                        all_player_ids.add(player.playerId)
        except Exception as e:
            print(f"⚠️  Failed to get box scores for week {week} in {year}: {e}")
        time.sleep(1)

    # Gather stats and insert into MongoDB
    operations = []

    for player_id in tqdm(all_player_ids, desc=f"Gathering stats in {year}"):
        try:
            player = league.player_info(playerId=player_id)
            name = player.name
            stats = player.stats or {}
            position = getattr(player, "position", None)
            schedule = getattr(player, "schedule", {}) or {}

            season_stats = {
                str(k): v for k, v in stats.items()
                if not str(k).isdigit()
            }

            weekly_stats = {
                str(k): {
                    "points": v.get("points", 0),
                    "avg_points": v.get("avg_points", 0),
                    "projected_points": v.get("projected_points", 0),
                    "breakdown": {
                        str(bk): bv for bk, bv in v.get("breakdown", {}).items()
                        if not str(bk).isdigit()
                    },
                    "projected_breakdown": {
                        str(pbk): pbv for pbk, pbv in v.get("projected_breakdown", {}).items()
                        if not str(pbk).isdigit()
                    },
                    "projected_avg_points": v.get("projected_avg_points", 0)
                }
                for k, v in stats.items()
                if str(k).isdigit() and isinstance(v, dict)
            }

            # Enrich weekly stats with opponent and game datetime information if available
            # Expected schedule structure per week: {"team": "<OPP>", "date": "YYYY-MM-DD HH:MM:SS"}
            for week_key in list(weekly_stats.keys()):
                # schedule keys may be int or str depending on source; check both
                sched_info = schedule.get(week_key, schedule.get(int(week_key)) if isinstance(week_key, str) and week_key.isdigit() else None)
                if not sched_info:
                    continue
                opponent_team = sched_info.get("team")
                game_datetime_str = str(sched_info.get("date")) if sched_info.get("date") is not None else None
                game_date = None
                game_time = None
                if game_datetime_str and " " in game_datetime_str:
                    parts = game_datetime_str.split(" ")
                    if len(parts) >= 2:
                        game_date, game_time = parts[0], parts[1]
                elif game_datetime_str:
                    # If only a date was provided
                    game_date = game_datetime_str

                if opponent_team is not None:
                    weekly_stats[week_key]["team"] = opponent_team
                # Per request: include date and time separately
                if game_date is not None:
                    weekly_stats[week_key]["date"] = game_date
                if game_time is not None:
                    weekly_stats[week_key]["time"] = game_time

            operations.append(
                UpdateOne(
                    {"name": name, "year": year},
                    {
                        "$set": {
                            "name": name,
                            "year": year,
                            "playerId": player_id,
                            "position": position,
                            "season_stats": season_stats,
                            "weekly_stats": weekly_stats
                        }
                    },
                    upsert=True
                )
            )

        except Exception as e:
            print(f"❌ Failed to insert {player_id} in {year}: {e}")

    # Write to DB
    if operations:
        result = collection.bulk_write(operations)
        print(f"✅ MongoDB write complete for {year}")
        print(f"Matched: {result.matched_count}, Modified: {result.modified_count}, Upserts: {len(result.upserted_ids)}")
    else:
        print(f"⚠️  No data written for {year}")

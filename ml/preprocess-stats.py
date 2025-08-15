from pymongo import MongoClient
import pandas as pd
from tqdm import tqdm
import os

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["fantasy_football"]
collection = db["player_stats"]

# Define breakdown keys and full feature list
BREAKDOWN_KEYS = [
    'receivingReceptions',
    'receivingYards',
    'receivingTouchdowns',
    'receivingTargets',
    'receivingYardsAfterCatch',
    'receivingYardsPerReception',
    'receiving100To199YardGame',
    'receiving200PlusYardGame',
    'passingAttempts',
    'passingCompletions',
    'passingIncompletions',
    'passingYards',
    'passingTouchdowns',
    'passingInterceptions',
    'passing40PlusYardTD',
    'passing50PlusYardTD',
    'passing300To399YardGame',
    'passing400PlusYardGame',
    'passing2PtConversions',
    'passingCompletionPercentage',
    'rushingAttempts',
    'rushingYards',
    'rushing40PlusYardTD',
    'rushing50PlusYardTD',
    'rushing100To199YardGame',
    'rushing200PlusYardGame',
    'rushingTouchdowns',
    'rushingYardsPerAttempt',
    'passingTimesSacked',
    'fumbles',
    'lostFumbles',
    'turnovers',
    'madeFieldGoalsFrom50Plus',
    'attemptedFieldGoalsFrom50Plus',
    'madeFieldGoalsFromUnder40',
    'attemptedFieldGoalsFromUnder40',
    'madeFieldGoals',
    'attemptedFieldGoals',
    'madeExtraPoints',
    'attemptedExtraPoints',
    'pointsScored',
]

FEATURE_KEYS = ['points', 'projected_points', 'winLoss', 'week'] + BREAKDOWN_KEYS

# Process data
data_rows = []

cursor = collection.find({})
for doc in tqdm(cursor, desc="Processing player stats"):
    name = doc.get("name")
    year = doc.get("year")
    playerId = doc.get("playerId")
    position = doc.get("position")
    weekly_stats = doc.get("weekly_stats", {})

    for week, stats in weekly_stats.items():
        # Skip season aggregate rows stored under week 0
        try:
            if int(week) == 0:
                continue
        except Exception:
            # If week is non-numeric, skip defensively
            continue
        row = {
            "name": name,
            "year": year,
            "playerId": playerId,
            "week": int(week),
            "points": stats.get("points", 0),
            "projected_points": stats.get("projected_points", 0),
            "winLoss": 1 if stats.get("breakdown", {}).get("teamWin") else 0,
            # Optional enriched fields from schedule augmentation
            "position": position,
            "player_team": stats.get("player_team"),
            "bye_week": bool(stats.get("bye_week", False)),
            "opponent": stats.get("team"),
            "date": stats.get("date"),
            "time": stats.get("time"),
            # Grouping key to identify teammates without knowing explicit team abbrev
            "team_week_key": f"{year}-W{int(week)}-opp:{stats.get('team')}",
            # New fields from ESPN gamelog augmentation
            "nfl_team": stats.get("nfl_team"),
            "nfl_opponent": stats.get("nfl_opponent"),
            "isHome": stats.get("isHome"),
        }

        breakdown = stats.get("breakdown", {})
        for key in BREAKDOWN_KEYS:
            row[key] = breakdown.get(key, 0)

        data_rows.append(row)

# Convert to DataFrame
df = pd.DataFrame(data_rows)

# Save to CSV and Parquet
os.makedirs("data", exist_ok=True)
df.to_csv("data/fantasy_weekly_stats.csv", index=False)
df.to_parquet("data/fantasy_weekly_stats.parquet", index=False)

print("✅ Files saved to 'data/fantasy_weekly_stats.{csv,parquet}'")

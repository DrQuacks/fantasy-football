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
            "position": position,
        }

        breakdown = stats.get("breakdown", {})
        for key in BREAKDOWN_KEYS:
            row[key] = breakdown.get(key, 0)

        data_rows.append(row)

# Create DataFrame and save
df = pd.DataFrame(data_rows)
print(f"✅ Processed {len(df)} rows from {len(df['name'].unique())} unique players")

# Save to CSV and Parquet
df.to_csv("data/fantasy_weekly_stats_clean.csv", index=False)
df.to_parquet("data/fantasy_weekly_stats_clean.parquet", index=False)

print("✅ Files saved to 'data/fantasy_weekly_stats_clean.{csv,parquet}'")


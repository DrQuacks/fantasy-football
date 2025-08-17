#!/usr/bin/env python3
"""
Export existing fantasy_football_complete database to CSV and Parquet files.
This script does NOT rebuild the database - it only exports existing data.
"""

import os
import pandas as pd
from pymongo import MongoClient
from tqdm import tqdm

# Database configuration
DEFAULT_MONGO_URI = "mongodb://localhost:27017/"
DEFAULT_DB_NAME = "fantasy_football_complete"
DEFAULT_COLL_NAME = "player_stats"

def export_to_csv():
    """Export existing database to CSV."""
    
    print("📊 Exporting existing database to CSV...")
    
    # MongoDB connection
    client = MongoClient(DEFAULT_MONGO_URI)
    collection = client[DEFAULT_DB_NAME][DEFAULT_COLL_NAME]
    
    # Check if database exists and has data
    count = collection.count_documents({})
    if count == 0:
        print("❌ No data found in database. Please run build_complete_database.py first.")
        client.close()
        return
    
    print(f"📊 Found {count} player documents in database")
    
    # Define breakdown keys (mapped stat names)
    breakdown_keys = [
        'receivingReceptions', 'receivingYards', 'receivingTouchdowns', 'receivingTargets',
        'receivingYardsAfterCatch', 'receivingYardsPerReception', 'receiving100To199YardGame',
        'receiving200PlusYardGame', 'passingAttempts', 'passingCompletions', 'passingIncompletions',
        'passingYards', 'passingTouchdowns', 'passingInterceptions', 'passing40PlusYardTD',
        'passing50PlusYardTD', 'passing300To399YardGame', 'passing400PlusYardGame',
        'passing2PtConversions', 'passingCompletionPercentage', 'rushingAttempts', 'rushingYards',
        'rushing40PlusYardTD', 'rushing50PlusYardTD', 'rushing100To199YardGame', 'rushing200PlusYardGame',
        'rushingTouchdowns', 'rushingYardsPerAttempt', 'passingTimesSacked', 'fumbles', 'lostFumbles',
        'turnovers', 'madeFieldGoalsFrom50Plus', 'attemptedFieldGoalsFrom50Plus',
        'madeFieldGoalsFromUnder40', 'attemptedFieldGoalsFromUnder40', 'madeFieldGoals',
        'attemptedFieldGoals', 'madeExtraPoints', 'attemptedExtraPoints', 'pointsScored'
    ]
    
    # Process data
    data_rows = []
    cursor = collection.find({})
    
    for doc in tqdm(cursor, desc="Processing player stats"):
        name = doc.get("name")
        year = doc.get("year")
        playerId = doc.get("playerId")
        position = doc.get("position")
        acquisitionType = doc.get("acquisitionType", "unknown")
        weekly_stats = doc.get("weekly_stats", {})

        for week, stats in weekly_stats.items():
            # Skip season aggregate rows stored under week 0
            try:
                if int(week) == 0:
                    continue
            except Exception:
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
                "acquisitionType": acquisitionType,
                "nfl_team": stats.get("nfl_team", ""),
                "nfl_opponent": stats.get("nfl_opponent", ""),
                "isHome": stats.get("isHome", False),
                "date": stats.get("date", ""),
                "time": stats.get("time", "")
            }

            breakdown = stats.get("breakdown", {})
            for key in breakdown_keys:
                row[key] = breakdown.get(key, 0)

            data_rows.append(row)
    
    # Create DataFrame and save
    df = pd.DataFrame(data_rows)
    csv_path = "data/fantasy_weekly_stats_complete.csv"
    parquet_path = "data/fantasy_weekly_stats_complete.parquet"
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    
    print(f"✅ Exported {len(df)} rows to {csv_path} and {parquet_path}")
    print(f"📊 CSV file: {csv_path}")
    print(f"📊 Parquet file: {parquet_path}")
    client.close()

if __name__ == "__main__":
    export_to_csv()

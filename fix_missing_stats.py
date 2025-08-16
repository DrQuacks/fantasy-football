#!/usr/bin/env python3
"""
Fix players missing weekly_stats by fetching their actual stats from ESPN.
"""

from espn_api.football import League
from pymongo import MongoClient, UpdateOne
import time

def fix_missing_stats():
    """Fix players missing weekly_stats."""
    
    # MongoDB connection
    client = MongoClient("mongodb://localhost:27017/")
    db = client["fantasy_football"]
    collection = db["player_stats"]
    
    # Find players missing weekly_stats
    players_to_fix = list(collection.find({"weekly_stats": {"$exists": False}}))
    print(f"Found {len(players_to_fix)} players missing weekly_stats")
    
    if not players_to_fix:
        print("No players to fix")
        return
    
    # Process each player
    for player in players_to_fix:
        name = player["name"]
        year = player["year"]
        player_id = player["playerId"]
        
        print(f"Fixing {name} ({year})...")
        
        try:
            # Get league for the year
            league = League(league_id=57220027, year=year)
            
            # Get player info
            player_info = league.player_info(playerId=player_id)
            
            if player_info and player_info.stats:
                # Extract stats using same pattern as createTable.py
                stats = player_info.stats or {}
                
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
                
                # Update the player
                collection.update_one(
                    {"_id": player["_id"]},
                    {
                        "$set": {
                            "stats": season_stats,
                            "weekly_stats": weekly_stats
                        }
                    }
                )
                print(f"  ✅ Updated {name} with {len(weekly_stats)} weeks of stats")
            else:
                print(f"  ❌ No stats found for {name}")
                
        except Exception as e:
            print(f"  ❌ Error fixing {name}: {e}")
        
        time.sleep(1)  # Rate limiting
    
    client.close()
    print("Done")

if __name__ == "__main__":
    fix_missing_stats()


#!/usr/bin/env python3
"""
rebuild_table_clean.py

Clean rebuild of the entire fantasy football database with all players and their stats.
Includes both rostered players and free agents, excludes problematic columns.
"""

from espn_api.football import League
from pymongo import MongoClient, UpdateOne
from tqdm import tqdm
import time

def rebuild_table():
    """Rebuild the entire table from scratch."""
    
    # MongoDB setup
    client = MongoClient("mongodb://localhost:27017/")
    db = client["fantasy_football"]
    collection = db["player_stats"]
    
    # Clear existing data
    print("Clearing existing data...")
    collection.delete_many({})
    
    # Process each year
    for year in range(2019, 2025):
        print(f"\n📅 Processing year {year}")
        
        # Get all unique players from weekly stats (rostered players)
        league = League(league_id=57220027, year=year)
        all_player_ids = set()
        
        print("  Finding rostered players...")
        for week in tqdm(range(1, 19), desc=f"Finding rostered players in {year}"):
            try:
                box_scores = league.box_scores(week)
                for matchup in box_scores:
                    for team in [matchup.home_lineup, matchup.away_lineup]:
                        for player in team:
                            all_player_ids.add(player.playerId)
            except Exception as e:
                print(f"⚠️  Failed to get box scores for week {week} in {year}: {e}")
            time.sleep(0.5)
        
        # Get free agents for each position
        print("  Finding free agents...")
        positions = ['QB', 'RB', 'WR', 'TE', 'K']
        free_agent_ids = set()
        
        for position in positions:
            try:
                free_agents = league.free_agents(size=500, position=position)
                for player in free_agents:
                    free_agent_ids.add(player.playerId)
            except Exception as e:
                print(f"⚠️  Failed to get {position} free agents in {year}: {e}")
            time.sleep(0.5)
        
        # Combine all player IDs
        all_players = all_player_ids.union(free_agent_ids)
        print(f"  Total unique players found: {len(all_players)}")
        
        # Gather stats for all players
        operations = []
        print("  Gathering stats...")
        
        for player_id in tqdm(all_players, desc=f"Gathering stats in {year}"):
            try:
                player = league.player_info(playerId=player_id)
                name = player.name
                stats = player.stats or {}
                position = getattr(player, "position", None)
                
                # Extract season stats (non-numeric keys)
                season_stats = {
                    str(k): v for k, v in stats.items()
                    if not str(k).isdigit()
                }
                
                # Extract weekly stats (numeric keys)
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
                
                # Only add players with actual weekly stats
                if weekly_stats:
                    operations.append(
                        UpdateOne(
                            {"name": name, "year": year},
                            {
                                "$set": {
                                    "name": name,
                                    "year": year,
                                    "playerId": player_id,
                                    "position": position,
                                    "stats": season_stats,
                                    "weekly_stats": weekly_stats
                                }
                            },
                            upsert=True
                        )
                    )
                
            except Exception as e:
                print(f"⚠️  Failed to get stats for player {player_id} in {year}: {e}")
            
            time.sleep(0.1)  # Rate limiting
        
        # Execute bulk write
        if operations:
            print(f"  Writing {len(operations)} players to database...")
            collection.bulk_write(operations, ordered=False)
            print(f"  ✅ Added {len(operations)} players for {year}")
    
    client.close()
    print("\n🎉 Database rebuild complete!")

if __name__ == "__main__":
    rebuild_table()


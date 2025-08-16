#!/usr/bin/env python3
"""
add_free_agents.py

Fetch free agents from ESPN API for QB, RB, WR, TE, K positions (2019-2024)
and add players who aren't already in the MongoDB database.
"""

import os
import time
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests
from pymongo import MongoClient, UpdateOne
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry



# ESPN API imports
try:
    from espn_api.football import League
except ImportError:
    print("Error: espn_api not found. Please install with: pip install espn-api")
    exit(1)

# ---------- Configuration ----------
DEFAULT_MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DEFAULT_DB_NAME = os.getenv("MONGO_DB", "fantasy_football")
DEFAULT_COLL_NAME = os.getenv("MONGO_COLL", "player_stats")

# ESPN League configuration (using same approach as createTable.py)
LEAGUE_ID = 57220027  # Same league ID as createTable.py

# Position mapping
POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K']
POSITION_IDS = {
    'QB': 0,
    'RB': 2, 
    'WR': 4,
    'TE': 6,
    'K': 16
}

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("free_agents")


def build_session() -> requests.Session:
    """Requests session with retries/backoff."""
    s = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s


def get_league(year: int = 2024) -> Optional[League]:
    """Initialize ESPN league connection."""
    try:
        league = League(league_id=LEAGUE_ID, year=year)
        return league
    except Exception as e:
        log.error(f"Failed to connect to ESPN league for year {year}: {e}")
        return None


def get_existing_player_keys(collection) -> set:
    """Get set of existing player keys (name, year) from MongoDB."""
    cursor = collection.find({}, {"name": 1, "year": 1})
    existing_keys = set()
    for doc in cursor:
        name = doc.get("name")
        year = doc.get("year")
        if name and year:
            existing_keys.add((name, year))
    return existing_keys


def fetch_free_agents_for_position(league: League, position: str, year: int, size: int = 100) -> List[Dict[str, Any]]:
    """Fetch free agents for a specific position and year."""
    try:
        # Get free agents for the position
        position_id = POSITION_IDS.get(position)
        if position_id is None:
            log.warning(f"Unknown position: {position}")
            return []
        
        free_agents = league.free_agents(size=size, position=position)
        
        players = []
        for player in free_agents:
            # Get player stats using the same pattern as rostered players
            stats = player.stats or {}
            
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
            
            # Only add players who have actual weekly stats
            if weekly_stats:
                player_data = {
                    "playerId": player.playerId,
                    "name": player.name,
                    "position": position,
                    "year": year,
                    "team": getattr(player, 'team', None),
                    "proTeam": getattr(player, 'proTeam', None),
                    "injuryStatus": getattr(player, 'injuryStatus', None),
                    "rosterSlots": getattr(player, 'rosterSlots', []),
                    "acquisitionType": "free_agent",
                    "added_date": datetime.now().isoformat(),
                    "stats": season_stats,
                    "weekly_stats": weekly_stats
                }
                players.append(player_data)
        
        return players
    
    except Exception as e:
        log.error(f"Error fetching free agents for {position} in {year}: {e}")
        return []


def add_free_agents_to_mongo():
    """Main function to add free agents to MongoDB."""
    
    # Initialize MongoDB connection
    client = MongoClient(DEFAULT_MONGO_URI)
    collection = client[DEFAULT_DB_NAME][DEFAULT_COLL_NAME]
    
    # Initialize ESPN league
    league = get_league()
    if not league:
        client.close()
        return
    
    # Get existing player keys
    log.info("Getting existing player keys from MongoDB...")
    existing_keys = get_existing_player_keys(collection)
    log.info(f"Found {len(existing_keys)} existing players")
    
    # Process each year and position
    years = range(2019, 2025)  # 2019-2024
    total_added = 0
    total_skipped = 0
    
    for year in years:
        log.info(f"Processing year {year}...")
        
        # Update league year
        league = get_league(year)
        if not league:
            continue
        
        for position in POSITIONS:
            log.info(f"  Fetching {position} free agents for {year}...")
            
            # Fetch free agents
            free_agents = fetch_free_agents_for_position(league, position, year)
            
            # Process all players (new and existing)
            new_players = []
            updated_players = []
            for player in free_agents:
                player_key = (player["name"], player["year"])
                if player_key not in existing_keys:
                    new_players.append(player)
                    existing_keys.add(player_key)  # Add to set to avoid duplicates
                else:
                    # Update existing player with stats
                    updated_players.append(player)
                    total_skipped += 1
            
                        if new_players or updated_players:
                # Prepare bulk operations
                operations = []
                for player in new_players:
                    operations.append(
                        UpdateOne(
                            {"name": player["name"], "year": year},
                            {
                                "$set": {
                                    "name": player["name"],
                                    "year": year,
                                    "playerId": player["playerId"],
                                    "position": player["position"],
                                    "stats": player["stats"],
                                    "weekly_stats": player["weekly_stats"],
                                    "acquisitionType": "free_agent",
                                    "added_date": player["added_date"]
                                }
                            },
                            upsert=True
                        )
                    )
                
                for player in updated_players:
                    operations.append(
                        UpdateOne(
                            {"name": player["name"], "year": year},
                            {
                                "$set": {
                                    "stats": player["stats"],
                                    "weekly_stats": player["weekly_stats"],
                                    "acquisitionType": "free_agent",
                                    "updated_date": player["added_date"]
                                }
                            }
                        )
                    )
                
                # Execute bulk write
                if operations:
                    result = collection.bulk_write(operations, ordered=False)
                    total_added += len(new_players)
                    log.info(f"    Added {len(new_players)} new {position} players for {year}")
                    log.info(f"    Updated {len(updated_players)} existing {position} players for {year}")
            
            # Rate limiting
            time.sleep(1)
    
    client.close()
    
    log.info(f"✅ Complete! Added {total_added} new players, skipped {total_skipped} existing players")
    
    return total_added, total_skipped


def main():
    """Main entry point."""
    log.info("Starting free agent collection...")
    
    added, skipped = add_free_agents_to_mongo()
    
    # Generate summary report
    report_lines = []
    report_lines.append("# Free Agent Collection Report")
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("## Summary")
    report_lines.append("")
    report_lines.append(f"- **New players added**: {added}")
    report_lines.append(f"- **Existing players skipped**: {skipped}")
    report_lines.append(f"- **Years processed**: 2019-2024")
    report_lines.append(f"- **Positions processed**: {', '.join(POSITIONS)}")
    report_lines.append("")
    report_lines.append("## Process")
    report_lines.append("")
    report_lines.append("1. Connected to ESPN fantasy league")
    report_lines.append("2. Retrieved existing player IDs from MongoDB")
    report_lines.append("3. Fetched free agents for each position/year combination")
    report_lines.append("4. Filtered out players already in database")
    report_lines.append("5. Added new players to MongoDB")
    report_lines.append("")
    
    report_path = "free_agent_collection_report.md"
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    log.info(f"📄 Report written to: {report_path}")


if __name__ == "__main__":
    main()

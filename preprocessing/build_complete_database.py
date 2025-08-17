#!/usr/bin/env python3
"""
build_complete_database.py

Comprehensive database builder that combines:
1. build_database.py - Create database with rostered + free agent players
2. augment_weekly_team_opponent.py - Add team/opponent data via ESPN gamelog

This script creates a complete fantasy football database with all players
(rostered + free agents) and enriches weekly stats with team/opponent data.

Includes built-in tests to verify data quality.
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Tuple, Optional, Set
from datetime import datetime
from tqdm import tqdm

import requests
import pandas as pd
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
DEFAULT_DB_NAME = os.getenv("MONGO_DB", "fantasy_football_complete")
DEFAULT_COLL_NAME = os.getenv("MONGO_COLL", "player_stats")

# ESPN League configuration
LEAGUE_ID = 57220027

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
log = logging.getLogger("complete_database")


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
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def get_league(year: int = 2024) -> Optional[League]:
    """Initialize ESPN league connection."""
    try:
        league = League(league_id=LEAGUE_ID, year=year)
        return league
    except Exception as e:
        log.error(f"Failed to connect to ESPN league for year {year}: {e}")
        return None


def fetch_rostered_players(league: League, year: int) -> Set[int]:
    """Fetch all rostered player IDs from ESPN league."""
    all_player_ids = set()
    
    for week in tqdm(range(1, 19), desc=f"Finding rostered players in {year}"):
        try:
            box_scores = league.box_scores(week)
            for matchup in box_scores:
                for team in [matchup.home_lineup, matchup.away_lineup]:
                    for player in team:
                        all_player_ids.add(player.playerId)
        except Exception as e:
            log.warning(f"Failed to get box scores for week {week} in {year}: {e}")
        time.sleep(1)
    
    return all_player_ids


def fetch_free_agents(league: League, year: int) -> Set[int]:
    """Fetch all free agent player IDs from ESPN league."""
    all_player_ids = set()
    
    for position in tqdm(POSITIONS, desc=f"Finding free agents in {year}"):
        try:
            free_agents = league.free_agents(size=100, position=position)
            for player in free_agents:
                all_player_ids.add(player.playerId)
        except Exception as e:
            log.warning(f"Failed to get free agents for {position} in {year}: {e}")
        time.sleep(1)
    
    return all_player_ids


def process_player_stats(stats: Dict[str, Any], schedule: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Process player stats into season and weekly stats."""
    
    # ESPN API stats mapping
    PLAYER_STATS_MAP = {
        # Receiving Stats
        41: 'receivingReceptions',
        42: 'receivingYards', 
        43: 'receivingTouchdowns',
        58: 'receivingTargets',
        59: 'receivingYardsAfterCatch',
        60: 'receivingYardsPerReception',
        56: 'receiving100To199YardGame',
        57: 'receiving200PlusYardGame',
        
        # Rushing Stats
        23: 'rushingAttempts',
        24: 'rushingYards',
        25: 'rushingTouchdowns',
        35: 'rushing40PlusYardTD',
        36: 'rushing50PlusYardTD',
        37: 'rushing100To199YardGame',
        38: 'rushing200PlusYardGame',
        39: 'rushingYardsPerAttempt',
        
        # Passing Stats
        0: 'passingAttempts',
        1: 'passingCompletions',
        3: 'passingYards',
        4: 'passingTouchdowns',
        20: 'passingInterceptions',
        15: 'passing40PlusYardTD',
        16: 'passing50PlusYardTD',
        17: 'passing300To399YardGame',
        18: 'passing400PlusYardGame',
        21: 'passingCompletionPercentage',
        
        # Other Stats
        68: 'fumbles',
        72: 'lostFumbles',
        73: 'turnovers',
        155: 'teamWin',
        158: 'pointsScored'
    }
    
    # Extract season stats (non-numeric keys)
    season_stats = {
        str(k): v for k, v in stats.items()
        if not str(k).isdigit()
    }
    
    # Extract weekly stats (numeric keys) with proper mapping
    weekly_stats = {}
    for k, v in stats.items():
        if str(k).isdigit() and isinstance(v, dict):
            # Map numeric keys to readable names
            mapped_breakdown = {}
            if "breakdown" in v:
                for bk, bv in v["breakdown"].items():
                    if str(bk).isdigit():
                        mapped_name = PLAYER_STATS_MAP.get(int(bk), f"stat_{bk}")
                        mapped_breakdown[mapped_name] = bv
                    else:
                        mapped_breakdown[str(bk)] = bv
            
            mapped_projected_breakdown = {}
            if "projected_breakdown" in v:
                for pbk, pbv in v["projected_breakdown"].items():
                    if str(pbk).isdigit():
                        mapped_name = PLAYER_STATS_MAP.get(int(pbk), f"stat_{pbk}")
                        mapped_projected_breakdown[mapped_name] = pbv
                    else:
                        mapped_projected_breakdown[str(pbk)] = pbv
            
            weekly_stats[str(k)] = {
                "points": v.get("points", 0),
                "avg_points": v.get("avg_points", 0),
                "projected_points": v.get("projected_points", 0),
                "breakdown": mapped_breakdown,
                "projected_breakdown": mapped_projected_breakdown,
                "projected_avg_points": v.get("projected_avg_points", 0)
            }
    
    # Enrich weekly stats with schedule information if available
    for week_key in list(weekly_stats.keys()):
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
            game_date = game_datetime_str

        if opponent_team is not None:
            weekly_stats[week_key]["team"] = opponent_team
        if game_date is not None:
            weekly_stats[week_key]["date"] = game_date
        if game_time is not None:
            weekly_stats[week_key]["time"] = game_time
    
    return season_stats, weekly_stats


# ESPN Gamelog API functions (from augment_weekly_team_opponent.py)
ESPN_GAMES_URL = "https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{athlete_id}/gamelog"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17 Safari/605.1.15"

def fetch_gamelog(session: requests.Session, athlete_id: int, season: int, seasontype: int = 2) -> Optional[Dict[str, Any]]:
    """Fetch ESPN gamelog JSON for a player; return dict or None on failure."""
    url = ESPN_GAMES_URL.format(athlete_id=athlete_id)
    try:
        r = session.get(url, params={"season": season, "seasontype": seasontype}, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning(f"Fetch failed for player {athlete_id} {season}: {e}")
        return None


def iter_events(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize response to a list of event dicts."""
    events = data.get("events")
    if isinstance(events, dict):
        return list(events.values())
    if isinstance(events, list):
        return events
    return []


def extract_week_info(event: Dict[str, Any]) -> Optional[Tuple[int, str, str, bool]]:
    """
    Return (week, nfl_team, nfl_opponent, isHome) or None.
    Skip if 'eventNote' present (playoffs).
    """
    if "eventNote" in event:
        return None

    # Week number
    week = event.get("week")
    try:
        week_int = int(week)
    except (TypeError, ValueError):
        return None

    # NFL team & opponent abbreviations
    team_abbr = (event.get("team") or {}).get("abbreviation") or (event.get("team") or {}).get("shortDisplayName")
    opp_abbr  = (event.get("opponent") or {}).get("abbreviation") or (event.get("opponent") or {}).get("shortDisplayName")
    if not team_abbr or not opp_abbr:
        return None

    # Home/away from atVs ("vs" => home, "@" => away). Default to False if unknown.
    at_vs = event.get("atVs")
    is_home = (isinstance(at_vs, str) and at_vs.strip() != "@")

    return (week_int, str(team_abbr), str(opp_abbr), bool(is_home))


def enrich_with_gamelog_data(session: requests.Session, player_id: int, year: int, weekly_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich weekly stats with team/opponent data from ESPN gamelog."""
    if not isinstance(player_id, int) or player_id <= 0:
        return weekly_stats
    
    data = fetch_gamelog(session, athlete_id=player_id, season=year, seasontype=2)
    if not data:
        return weekly_stats
    
    events = iter_events(data)
    if not events:
        return weekly_stats
    
    enriched_stats = weekly_stats.copy()
    
    for ev in events:
        info = extract_week_info(ev)
        if not info:
            continue
        week_int, team, opp, is_home = info
        wk = str(week_int)
        
        if wk in enriched_stats:
            enriched_stats[wk]["nfl_team"] = team
            enriched_stats[wk]["nfl_opponent"] = opp
            enriched_stats[wk]["isHome"] = is_home
    
    return enriched_stats


def build_complete_database(start_year: int = 2019, end_year: int = 2024, rate_delay: float = 0.5, dry_run: bool = False):
    """Main function to build complete database."""
    
    # Initialize MongoDB connection
    client = MongoClient(DEFAULT_MONGO_URI)
    collection = client[DEFAULT_DB_NAME][DEFAULT_COLL_NAME]
    
    if dry_run:
        log.info("🔍 DRY RUN: Will not write to database")
    else:
        # Clear existing data
        log.info("Clearing existing data...")
        collection.delete_many({})
    
    # Initialize session for gamelog API
    session = build_session()
    
    total_players = 0
    total_rostered = 0
    total_free_agents = 0
    processed_data = []  # Store processed data for dry run testing
    
    for year in range(start_year, end_year + 1):
        log.info(f"\n📅 Processing year {year}")
        
        # Initialize league for this year
        league = get_league(year)
        if not league:
            continue
        
        # Step 1: Fetch all rostered players
        log.info("Step 1: Fetching rostered players...")
        rostered_ids = fetch_rostered_players(league, year)
        log.info(f"Found {len(rostered_ids)} rostered players")
        
        # Step 2: Fetch all free agents
        log.info("Step 2: Fetching free agents...")
        free_agent_ids = fetch_free_agents(league, year)
        log.info(f"Found {len(free_agent_ids)} free agents")
        
        # Combine all player IDs
        all_player_ids = rostered_ids.union(free_agent_ids)
        log.info(f"Total unique players: {len(all_player_ids)}")
        
        # Step 3: Process all players
        log.info("Step 3: Processing all players...")
        operations = []
        
        for player_id in tqdm(all_player_ids, desc=f"Processing players in {year}"):
            try:
                player = league.player_info(playerId=player_id)
                name = player.name
                stats = player.stats or {}
                position = getattr(player, "position", None)
                schedule = getattr(player, "schedule", {}) or {}
                
                # Process stats
                season_stats, weekly_stats = process_player_stats(stats, schedule)
                
                # Enrich with gamelog data
                enriched_weekly_stats = enrich_with_gamelog_data(session, player_id, year, weekly_stats)
                
                # Determine if player was rostered or free agent
                acquisition_type = "rostered" if player_id in rostered_ids else "free_agent"
                
                player_data = {
                    "name": name,
                    "year": year,
                    "playerId": player_id,
                    "position": position,
                    "season_stats": season_stats,
                    "weekly_stats": enriched_weekly_stats,
                    "acquisitionType": acquisition_type,
                    "added_date": datetime.now().isoformat()
                }
                
                operations.append(
                    UpdateOne(
                        {"name": name, "year": year},
                        {"$set": player_data},
                        upsert=True
                    )
                )
                
                # Store for dry run testing
                if dry_run:
                    processed_data.append(player_data)
                
                total_players += 1
                if acquisition_type == "rostered":
                    total_rostered += 1
                else:
                    total_free_agents += 1
                
            except Exception as e:
                log.error(f"Failed to process player {player_id} in {year}: {e}")
            
            # Rate limiting
            time.sleep(rate_delay)
        
        # Step 4: Write to database
        if operations:
            if dry_run:
                log.info(f"🔍 DRY RUN: Would write {len(operations)} players to database...")
                log.info(f"🔍 DRY RUN: Sample players: {[op._filter.get('name', 'Unknown') for op in operations[:3]]}")
            else:
                log.info(f"Writing {len(operations)} players to database...")
                result = collection.bulk_write(operations, ordered=False)
                log.info(f"✅ MongoDB write complete for {year}")
                log.info(f"Matched: {result.matched_count}, Modified: {result.modified_count}, Upserts: {len(result.upserted_ids)}")
        else:
            log.warning(f"⚠️  No data written for {year}")
    
    client.close()
    
    log.info(f"\n🎉 Database build complete!")
    log.info(f"Total players processed: {total_players}")
    log.info(f"Rostered players: {total_rostered}")
    log.info(f"Free agents: {total_free_agents}")
    
    return total_players, total_rostered, total_free_agents, processed_data


def run_tests(processed_data=None):
    """Run built-in tests to verify data quality."""
    log.info("\n🧪 Running data quality tests...")
    
    tests_passed = 0
    total_tests = 4
    client = None
    
    # If we have processed data (from dry run), use that instead of database
    if processed_data:
        log.info("Using processed data from dry run for testing...")
        test_data = processed_data
    else:
        # Otherwise read from database
        client = MongoClient(DEFAULT_MONGO_URI)
        collection = client[DEFAULT_DB_NAME][DEFAULT_COLL_NAME]
        test_data = collection
    
    # Test 1: Check that there is a player named David Moore in 2019 who has weeks with non-zero receiving stats
    log.info("Test 1: David Moore 2019 receiving stats...")
    try:
        if processed_data:
            # Search in processed data
            david_moore = None
            for player in processed_data:
                if player.get("name") == "David Moore" and player.get("year") == 2019:
                    david_moore = player
                    break
        else:
            # Search in database
            david_moore = test_data.find_one({"name": "David Moore", "year": 2019})
        
        if david_moore:
            weekly_stats = david_moore.get("weekly_stats", {})
            has_receiving_stats = False
            for week, stats in weekly_stats.items():
                breakdown = stats.get("breakdown", {})
                if breakdown.get("receivingYards", 0) > 0 or breakdown.get("receivingReceptions", 0) > 0:
                    has_receiving_stats = True
                    break
            
            if has_receiving_stats:
                log.info("✅ Test 1 PASSED: David Moore has non-zero receiving stats in 2019")
                tests_passed += 1
            else:
                log.error("❌ Test 1 FAILED: David Moore has no non-zero receiving stats in 2019")
                # Debug: show what stats we actually have
                log.error(f"DEBUG: David Moore weekly stats keys: {list(weekly_stats.keys())}")
                if weekly_stats:
                    sample_week = list(weekly_stats.keys())[0]
                    sample_breakdown = weekly_stats[sample_week].get("breakdown", {})
                    log.error(f"DEBUG: Sample week {sample_week} breakdown keys: {list(sample_breakdown.keys())}")
        else:
            log.error("❌ Test 1 FAILED: David Moore not found in 2019")
    except Exception as e:
        log.error(f"❌ Test 1 ERROR: {e}")
    
    # Test 2: Check that Greg Olsen is on Carolina in 2019 AND has receiving stats
    log.info("Test 2: Greg Olsen team and receiving stats in 2019...")
    try:
        if processed_data:
            # Search in processed data
            greg_olsen = None
            for player in processed_data:
                if player.get("name") == "Greg Olsen" and player.get("year") == 2019:
                    greg_olsen = player
                    break
        else:
            # Search in database
            greg_olsen = test_data.find_one({"name": "Greg Olsen", "year": 2019})
        
        if greg_olsen:
            weekly_stats = greg_olsen.get("weekly_stats", {})
            on_carolina = False
            has_receiving_stats = False
            
            for week, stats in weekly_stats.items():
                # Check team
                if stats.get("nfl_team") == "CAR":
                    on_carolina = True
                
                # Check receiving stats
                breakdown = stats.get("breakdown", {})
                if breakdown.get("receivingYards", 0) > 0 or breakdown.get("receivingReceptions", 0) > 0:
                    has_receiving_stats = True
            
            if on_carolina and has_receiving_stats:
                log.info("✅ Test 2 PASSED: Greg Olsen is on Carolina and has receiving stats in 2019")
                tests_passed += 1
            elif on_carolina and not has_receiving_stats:
                log.error("❌ Test 2 FAILED: Greg Olsen is on Carolina but has NO receiving stats in 2019")
            elif not on_carolina and has_receiving_stats:
                log.error("❌ Test 2 FAILED: Greg Olsen has receiving stats but is NOT on Carolina in 2019")
            else:
                log.error("❌ Test 2 FAILED: Greg Olsen is not on Carolina and has no receiving stats in 2019")
        else:
            log.error("❌ Test 2 FAILED: Greg Olsen not found in 2019")
    except Exception as e:
        log.error(f"❌ Test 2 ERROR: {e}")
    
    # Test 3: Check that Christian McCaffrey is on Carolina in week 6 of 2022
    log.info("Test 3: Christian McCaffrey team in week 6, 2022...")
    try:
        if processed_data:
            # Search in processed data
            cmc = None
            for player in processed_data:
                if player.get("name") == "Christian McCaffrey" and player.get("year") == 2022:
                    cmc = player
                    break
        else:
            # Search in database
            cmc = test_data.find_one({"name": "Christian McCaffrey", "year": 2022})
        
        if cmc:
            weekly_stats = cmc.get("weekly_stats", {})
            week_6_stats = weekly_stats.get("6", {})
            if week_6_stats.get("nfl_team") == "CAR":
                log.info("✅ Test 3 PASSED: Christian McCaffrey is on Carolina in week 6, 2022")
                tests_passed += 1
            else:
                log.error(f"❌ Test 3 FAILED: Christian McCaffrey team in week 6, 2022 is {week_6_stats.get('nfl_team', 'NOT FOUND')}")
        else:
            log.error("❌ Test 3 FAILED: Christian McCaffrey not found in 2022")
    except Exception as e:
        log.error(f"❌ Test 3 ERROR: {e}")
    
    # Test 4: Check that Christian McCaffrey is on San Francisco in week 7 of 2022
    log.info("Test 4: Christian McCaffrey team in week 7, 2022...")
    try:
        if processed_data:
            # Search in processed data
            cmc = None
            for player in processed_data:
                if player.get("name") == "Christian McCaffrey" and player.get("year") == 2022:
                    cmc = player
                    break
        else:
            # Search in database
            cmc = test_data.find_one({"name": "Christian McCaffrey", "year": 2022})
        
        if cmc:
            weekly_stats = cmc.get("weekly_stats", {})
            week_7_stats = weekly_stats.get("7", {})
            if week_7_stats.get("nfl_team") == "SF":
                log.info("✅ Test 4 PASSED: Christian McCaffrey is on San Francisco in week 7, 2022")
                tests_passed += 1
            else:
                log.error(f"❌ Test 4 FAILED: Christian McCaffrey team in week 7, 2022 is {week_7_stats.get('nfl_team', 'NOT FOUND')}")
        else:
            log.error("❌ Test 4 FAILED: Christian McCaffrey not found in 2022")
    except Exception as e:
        log.error(f"❌ Test 4 ERROR: {e}")
    
    client.close()
    
    log.info(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    if tests_passed == total_tests:
        log.info("🎉 All tests passed!")
    else:
        log.warning(f"⚠️  {total_tests - tests_passed} tests failed")
    
    return tests_passed, total_tests


def run_tests_temp_db(temp_db_name: str):
    """Run tests against a temporary database."""
    log.info(f"\n🧪 Running data quality tests against temporary database: {temp_db_name}")
    
    client = MongoClient(DEFAULT_MONGO_URI)
    collection = client[temp_db_name][DEFAULT_COLL_NAME]
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Check that there is a player named David Moore in 2019 who has weeks with non-zero receiving stats
    log.info("Test 1: David Moore 2019 receiving stats...")
    try:
        david_moore = collection.find_one({"name": "David Moore", "year": 2019})
        if david_moore:
            weekly_stats = david_moore.get("weekly_stats", {})
            has_receiving_stats = False
            for week, stats in weekly_stats.items():
                breakdown = stats.get("breakdown", {})
                if breakdown.get("receiving_yards", 0) > 0 or breakdown.get("receptions", 0) > 0:
                    has_receiving_stats = True
                    break
            
            if has_receiving_stats:
                log.info("✅ Test 1 PASSED: David Moore has non-zero receiving stats in 2019")
                tests_passed += 1
            else:
                log.error("❌ Test 1 FAILED: David Moore has no non-zero receiving stats in 2019")
        else:
            log.error("❌ Test 1 FAILED: David Moore not found in 2019")
    except Exception as e:
        log.error(f"❌ Test 1 ERROR: {e}")
    
    # Test 2: Check that Greg Olsen is on Carolina in 2019
    log.info("Test 2: Greg Olsen team in 2019...")
    try:
        greg_olsen = collection.find_one({"name": "Greg Olsen", "year": 2019})
        if greg_olsen:
            weekly_stats = greg_olsen.get("weekly_stats", {})
            on_carolina = False
            for week, stats in weekly_stats.items():
                if stats.get("nfl_team") == "CAR":
                    on_carolina = True
                    break
            
            if on_carolina:
                log.info("✅ Test 2 PASSED: Greg Olsen is on Carolina in 2019")
                tests_passed += 1
            else:
                log.error("❌ Test 2 FAILED: Greg Olsen is not on Carolina in 2019")
        else:
            log.error("❌ Test 2 FAILED: Greg Olsen not found in 2019")
    except Exception as e:
        log.error(f"❌ Test 2 ERROR: {e}")
    
    # Test 3: Check that Christian McCaffrey is on Carolina in week 6 of 2022
    log.info("Test 3: Christian McCaffrey team in week 6, 2022...")
    try:
        cmc = collection.find_one({"name": "Christian McCaffrey", "year": 2022})
        if cmc:
            weekly_stats = cmc.get("weekly_stats", {})
            week_6_stats = weekly_stats.get("6", {})
            if week_6_stats.get("nfl_team") == "CAR":
                log.info("✅ Test 3 PASSED: Christian McCaffrey is on Carolina in week 6, 2022")
                tests_passed += 1
            else:
                log.error(f"❌ Test 3 FAILED: Christian McCaffrey team in week 6, 2022 is {week_6_stats.get('nfl_team', 'NOT FOUND')}")
        else:
            log.error("❌ Test 3 FAILED: Christian McCaffrey not found in 2022")
    except Exception as e:
        log.error(f"❌ Test 3 ERROR: {e}")
    
    # Test 4: Check that Christian McCaffrey is on San Francisco in week 7 of 2022
    log.info("Test 4: Christian McCaffrey team in week 7, 2022...")
    try:
        cmc = collection.find_one({"name": "Christian McCaffrey", "year": 2022})
        if cmc:
            weekly_stats = cmc.get("weekly_stats", {})
            week_7_stats = weekly_stats.get("7", {})
            if week_7_stats.get("nfl_team") == "SF":
                log.info("✅ Test 4 PASSED: Christian McCaffrey is on San Francisco in week 7, 2022")
                tests_passed += 1
            else:
                log.error(f"❌ Test 4 FAILED: Christian McCaffrey team in week 7, 2022 is {week_7_stats.get('nfl_team', 'NOT FOUND')}")
        else:
            log.error("❌ Test 4 FAILED: Christian McCaffrey not found in 2022")
    except Exception as e:
        log.error(f"❌ Test 4 ERROR: {e}")
    
    client.close()
    
    log.info(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    if tests_passed == total_tests:
        log.info("🎉 All tests passed!")
    else:
        log.warning(f"⚠️  {total_tests - tests_passed} tests failed")
    
    return tests_passed, total_tests


def export_to_csv():
    """Export database to CSV."""
    
    print("\n📊 Exporting to CSV...")
    
    # MongoDB connection
    client = MongoClient(DEFAULT_MONGO_URI)
    collection = client[DEFAULT_DB_NAME][DEFAULT_COLL_NAME]
    
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
    client.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build complete fantasy football database')
    parser.add_argument('--start-year', type=int, default=2019, 
                       help='Start year (default: 2019)')
    parser.add_argument('--end-year', type=int, default=2024, 
                       help='End year (default: 2024)')
    parser.add_argument('--database', default='fantasy_football_complete', 
                       help='MongoDB database name (default: fantasy_football_complete)')
    parser.add_argument('--collection', default='player_stats',
                       help='MongoDB collection name')
    parser.add_argument('--suffix', default=None,
                       help='Optional suffix for database name (e.g., _v2, _test)')
    parser.add_argument('--rate-delay', type=float, default=0.5,
                       help='Delay between API calls in seconds (default: 0.5)')
    parser.add_argument('--skip-tests', action='store_true',
                       help='Skip running data quality tests')
    parser.add_argument('--test-only', action='store_true',
                       help='Only run tests against existing database (no data fetching)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run - don\'t write to database')
    parser.add_argument('--save-dry-run', action='store_true',
                       help='Save dry run data to temporary database for testing')
    
    args = parser.parse_args()
    
    # Set up database name with optional suffix
    db_name = args.database
    if args.suffix:
        db_name = f"{args.database}_{args.suffix}"
    
    # Update global constants
    global DEFAULT_DB_NAME
    DEFAULT_DB_NAME = db_name
    
    if args.test_only:
        log.info(f"🧪 Running tests only against database: {db_name}")
        tests_passed, total_tests = run_tests()
        total_players, total_rostered, total_free_agents = 0, 0, 0
    else:
        log.info(f"🚀 Starting complete database build for database: {db_name}")
        log.info(f"📅 Years: {args.start_year}-{args.end_year}")
        log.info(f"⏱️  Rate delay: {args.rate_delay}s")
        
        if args.dry_run:
            log.info("🔍 DRY RUN MODE - No data will be written to database")
        
        # Build the database
        total_players, total_rostered, total_free_agents, processed_data = build_complete_database(
            start_year=args.start_year, 
            end_year=args.end_year, 
            rate_delay=args.rate_delay,
            dry_run=args.dry_run
        )
        
        # Save dry run data to temporary database if requested
        if args.save_dry_run and args.dry_run and processed_data:
            temp_db_name = f"{db_name}_temp"
            log.info(f"💾 Saving dry run data to temporary database: {temp_db_name}")
            client = MongoClient(DEFAULT_MONGO_URI)
            temp_collection = client[temp_db_name][DEFAULT_COLL_NAME]
            temp_collection.delete_many({})  # Clear any existing temp data
            
            operations = []
            for player_data in processed_data:
                operations.append(
                    UpdateOne(
                        {"name": player_data["name"], "year": player_data["year"]},
                        {"$set": player_data},
                        upsert=True
                    )
                )
            
            if operations:
                result = temp_collection.bulk_write(operations, ordered=False)
                log.info(f"✅ Saved {len(operations)} players to temporary database")
            
            client.close()
        
        # Run tests unless skipped
        tests_passed, total_tests = 0, 4
        if not args.skip_tests:
            if args.save_dry_run and args.dry_run:
                # Run tests against temporary database
                log.info("🧪 Running tests against temporary database...")
                tests_passed, total_tests = run_tests_temp_db(f"{db_name}_temp")
            else:
                tests_passed, total_tests = run_tests(processed_data if args.dry_run else None)
    
    # Generate summary report
    report_lines = []
    report_lines.append("# Complete Database Build Report")
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("## Summary")
    report_lines.append("")
    report_lines.append(f"- **Total players processed**: {total_players}")
    report_lines.append(f"- **Rostered players**: {total_rostered}")
    report_lines.append(f"- **Free agents**: {total_free_agents}")
    report_lines.append(f"- **Years processed**: {args.start_year}-{args.end_year}")
    report_lines.append(f"- **Test results**: {tests_passed}/{total_tests} passed")
    report_lines.append("")
    report_lines.append("## Process")
    report_lines.append("")
    report_lines.append("1. Connected to ESPN fantasy league")
    report_lines.append("2. Fetched all rostered players from league")
    report_lines.append("3. Fetched all free agents for each position")
    report_lines.append("4. Combined unique player IDs")
    report_lines.append("5. Processed player stats and enriched with gamelog data")
    report_lines.append("6. Wrote all data to MongoDB")
    report_lines.append("7. Ran data quality tests")
    report_lines.append("")
    
    report_path = "docs/complete_database_build_report.md"
    os.makedirs("docs", exist_ok=True)
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    log.info(f"📄 Report written to: {report_path}")
    
    # Export to CSV and Parquet
    export_to_csv()


if __name__ == "__main__":
    main()

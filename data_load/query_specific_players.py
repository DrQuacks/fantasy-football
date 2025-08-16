from espn_api.football import League
import time

def query_specific_players():
    """Query ESPN API for specific players using the same approach as createTable.py."""
    
    LEAGUE_ID = 57220027
    YEAR = 2019
    TARGET_NAMES = ["Greg Olsen", "David Moore", "Malik Turner"]
    
    print(f"Querying ESPN API for league {LEAGUE_ID}, year {YEAR}")
    print(f"Looking for: {TARGET_NAMES}")
    
    try:
        league = League(league_id=LEAGUE_ID, year=YEAR)
        print("✅ Connected to ESPN API")
        
        # Collect all unique players from weekly stats (same as createTable.py)
        all_player_ids = set()
        
        print("Collecting player IDs from box scores...")
        for week in range(1, 19):
            try:
                box_scores = league.box_scores(week)
                for matchup in box_scores:
                    for team in [matchup.home_lineup, matchup.away_lineup]:
                        for player in team:
                            all_player_ids.add(player.playerId)
            except Exception as e:
                print(f"⚠️  Failed to get box scores for week {week}: {e}")
            time.sleep(1)
        
        print(f"Found {len(all_player_ids)} total player IDs")
        
        # Search for our target players
        found_players = []
        
        for player_id in all_player_ids:
            try:
                player = league.player_info(playerId=player_id)
                if player and player.name:
                    for target_name in TARGET_NAMES:
                        if target_name.lower() in player.name.lower():
                            print(f"\n🎯 FOUND: {player.name}")
                            print(f"  Player ID: {player_id}")
                            print(f"  Team: {getattr(player, 'proTeam', 'Unknown')}")
                            print(f"  Position: {getattr(player, 'position', 'Unknown')}")
                            
                            # Get stats
                            stats = getattr(player, 'stats', {}) or {}
                            print(f"  Has stats: {bool(stats)}")
                            
                            # Get schedule
                            schedule = getattr(player, 'schedule', {}) or {}
                            print(f"  Has schedule: {bool(schedule)}")
                            
                            # Show week 16 specifically
                            week_16_stats = stats.get('16', {})
                            if week_16_stats:
                                print(f"  Week 16 stats: {week_16_stats}")
                            
                            week_16_schedule = schedule.get('16', {})
                            if week_16_schedule:
                                print(f"  Week 16 schedule: {week_16_schedule}")
                            
                            found_players.append(player)
                            break
                            
            except Exception as e:
                print(f"Error getting player {player_id}: {e}")
            time.sleep(0.5)  # Be nice to the API
        
        print(f"\n📊 Summary: Found {len(found_players)} target players")
        
        if not found_players:
            print("❌ None of the target players were found in the fantasy league data")
            print("This suggests they may not have been on fantasy rosters in 2019")
        
        return found_players
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    players = query_specific_players()




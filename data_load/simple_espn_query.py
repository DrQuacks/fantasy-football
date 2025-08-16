from espn_api.football import League

def query_espn_raw():
    """Query ESPN API for raw player data."""
    
    LEAGUE_ID = 57220027
    YEAR = 2019
    
    print(f"Querying ESPN API for league {LEAGUE_ID}, year {YEAR}")
    
    try:
        # Try to connect to ESPN API
        league = League(league_id=LEAGUE_ID, year=YEAR)
        print("✅ Connected to ESPN API")
        
        # Get all players
        print("Getting all players...")
        all_players = league.player_info()
        print(f"Found {len(all_players)} players")
        
        # Search for specific players
        target_names = ["Greg Olsen", "Malik Turner", "David Moore"]
        
        for target_name in target_names:
            print(f"\nSearching for: {target_name}")
            found = False
            for player in all_players:
                if target_name.lower() in player.name.lower():
                    print(f"FOUND: {player.name}")
                    print(f"  Team: {player.proTeam}")
                    print(f"  Position: {player.position}")
                    print(f"  Player ID: {player.playerId}")
                    found = True
                    break
            if not found:
                print(f"NOT FOUND: {target_name}")
        
        return all_players
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    players = query_espn_raw()




from espn_api.football import League

def explore_espn_api():
    """Explore what data is available from ESPN API."""
    
    LEAGUE_ID = 57220027
    YEAR = 2019
    
    print(f"Exploring ESPN API for league {LEAGUE_ID}, year {YEAR}")
    
    try:
        league = League(league_id=LEAGUE_ID, year=YEAR)
        print("✅ Connected to ESPN API")
        
        # Check what attributes are available
        print("\nLeague object attributes:")
        for attr in dir(league):
            if not attr.startswith('_'):
                print(f"  {attr}")
        
        # Try to get teams
        print(f"\nNumber of teams: {len(league.teams)}")
        
        # Try to get box scores for a specific week
        print("\nTrying to get box scores for week 16...")
        try:
            box_scores = league.box_scores(16)
            print(f"Got {len(box_scores)} box scores")
            
            # Look at first box score
            if box_scores:
                first_matchup = box_scores[0]
                print(f"First matchup: {first_matchup.home_team} vs {first_matchup.away_team}")
                
                # Look at players in first matchup
                home_players = first_matchup.home_lineup
                print(f"Home team has {len(home_players)} players")
                
                # Search for our target players
                target_names = ["Greg Olsen", "Malik Turner", "David Moore"]
                for player in home_players:
                    for target in target_names:
                        if target.lower() in player.name.lower():
                            print(f"FOUND in home lineup: {player.name} - {player.proTeam}")
                
                away_players = first_matchup.away_lineup
                print(f"Away team has {len(away_players)} players")
                for player in away_players:
                    for target in target_names:
                        if target.lower() in player.name.lower():
                            print(f"FOUND in away lineup: {player.name} - {player.proTeam}")
                            
        except Exception as e:
            print(f"Error getting box scores: {e}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    explore_espn_api()




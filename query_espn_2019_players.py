import pandas as pd
from espn_api.football import League
import json
from datetime import datetime

def query_espn_2019_players():
    """Query ESPN API for specific players' 2019 stats using the actual league ID."""
    
    LEAGUE_ID = 57220027
    YEAR = 2019
    
    print("🔍 Querying ESPN API for 2019 Player Data")
    print("=" * 50)
    print(f"League ID: {LEAGUE_ID}")
    print(f"Year: {YEAR}")
    
    try:
        print(f"\n🔗 Connecting to ESPN API...")
        league = League(league_id=LEAGUE_ID, year=YEAR)
        print("✅ Successfully connected to ESPN API")
        
        # Get all players from the league
        print(f"\n📊 Fetching all players from league...")
        all_players = league.player_info()
        print(f"✅ Found {len(all_players)} total players")
        
        # Players to search for
        target_players = [
            "Greg Olsen",
            "Malik Turner", 
            "David Moore"
        ]
        
        print(f"\n🔍 Searching for specific players...")
        found_players = []
        
        for player_name in target_players:
            print(f"\n🔍 Looking for: {player_name}")
            
            # Search through all players
            found = False
            for player in all_players:
                if player_name.lower() in player.name.lower():
                    print(f"   ✅ Found: {player.name}")
                    print(f"      Team: {player.proTeam}")
                    print(f"      Position: {player.position}")
                    if hasattr(player, 'injuryStatus'):
                        print(f"      Status: {player.injuryStatus}")
                    if hasattr(player, 'totalPoints'):
                        print(f"      Total Points: {player.totalPoints}")
                    found_players.append(player)
                    found = True
                    break
            
            if not found:
                print(f"   ❌ Not found: {player_name}")
        
        # Also check for any players with similar names
        print(f"\n🔍 Checking for similar names...")
        similar_players = []
        for player in all_players:
            if any(name.lower() in player.name.lower() for name in ["olsen", "turner", "moore"]):
                print(f"   Found similar: {player.name} ({player.proTeam}, {player.position})")
                similar_players.append(player)
        
        # Check for any Seattle players
        print(f"\n🔍 Checking for Seattle players...")
        seattle_players = []
        for player in all_players:
            if hasattr(player, 'proTeam') and player.proTeam == 'SEA':
                seattle_players.append(player)
                print(f"   Seattle player: {player.name} ({player.position})")
        
        print(f"\n📊 Summary:")
        print(f"   Target players found: {len(found_players)}")
        print(f"   Similar players found: {len(similar_players)}")
        print(f"   Seattle players found: {len(seattle_players)}")
        
        return found_players, similar_players, seattle_players
        
    except Exception as e:
        print(f"❌ Error connecting to ESPN API: {e}")
        print(f"\n💡 This might be because:")
        print(f"   1. The league ID {LEAGUE_ID} doesn't exist or isn't accessible")
        print(f"   2. The year {YEAR} data isn't available")
        print(f"   3. Authentication issues with ESPN API")
        return None, None, None

def analyze_espn_data(found_players, similar_players, seattle_players):
    """Analyze the ESPN API data we retrieved."""
    
    print(f"\n🔍 Analysis of ESPN API Data:")
    print("=" * 40)
    
    if found_players:
        print(f"\n✅ Target Players Found:")
        for player in found_players:
            print(f"   • {player.name} ({player.proTeam}, {player.position})")
    else:
        print(f"\n❌ No target players found in ESPN API")
    
    if similar_players:
        print(f"\n🔍 Similar Players Found:")
        for player in similar_players:
            print(f"   • {player.name} ({player.proTeam}, {player.position})")
    
    if seattle_players:
        print(f"\n🔍 Seattle Players in ESPN API:")
        for player in seattle_players:
            print(f"   • {player.name} ({player.position})")
    
    print(f"\n💡 Comparison with our dataset:")
    print(f"   • Our dataset shows Greg Olsen on SEA in 2019")
    print(f"   • ESPN API should show the correct team assignment")
    print(f"   • This will help us understand the data quality issues")

def main():
    """Main function to query ESPN API."""
    
    print("🏈 ESPN API 2019 Player Data Query")
    print("=" * 50)
    
    # Query ESPN API
    found_players, similar_players, seattle_players = query_espn_2019_players()
    
    # Analyze the results
    if found_players is not None:
        analyze_espn_data(found_players, similar_players, seattle_players)
    else:
        print(f"\n❌ Could not retrieve data from ESPN API")
        print(f"   This prevents us from verifying the correct player data")

if __name__ == "__main__":
    main()




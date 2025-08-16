import pandas as pd
from espn_api.football import League
import json
from datetime import datetime

def query_espn_for_players(league_id=None, year=2019):
    """Query ESPN API for specific players' stats."""
    
    print("🔍 ESPN API Player Query Tool")
    print("=" * 40)
    
    if league_id is None:
        print("❌ No league ID provided. Please provide a valid ESPN league ID.")
        print("   Usage: query_espn_for_players(league_id=YOUR_LEAGUE_ID)")
        return
    
    try:
        print(f"🔗 Connecting to ESPN API for league {league_id}, year {year}...")
        league = League(league_id=league_id, year=year)
        print("✅ Successfully connected to ESPN API")
        
        # Players to search for
        target_players = [
            "Greg Olsen",
            "Malik Turner", 
            "David Moore"
        ]
        
        print(f"\n📊 Searching for {len(target_players)} players...")
        
        # Get all players from the league
        all_players = league.player_info()
        
        found_players = []
        for player_name in target_players:
            print(f"\n🔍 Looking for: {player_name}")
            
            # Search through all players
            for player in all_players:
                if player_name.lower() in player.name.lower():
                    print(f"   ✅ Found: {player.name}")
                    print(f"      Team: {player.proTeam}")
                    print(f"      Position: {player.position}")
                    print(f"      Status: {player.injuryStatus if hasattr(player, 'injuryStatus') else 'Unknown'}")
                    found_players.append(player)
                    break
            else:
                print(f"   ❌ Not found: {player_name}")
        
        # Also check for any players with similar names
        print(f"\n🔍 Checking for similar names...")
        for player in all_players:
            if any(name.lower() in player.name.lower() for name in ["olsen", "turner", "moore"]):
                print(f"   Found similar: {player.name} ({player.proTeam}, {player.position})")
        
        return found_players
        
    except Exception as e:
        print(f"❌ Error connecting to ESPN API: {e}")
        print("\n💡 To use this script:")
        print("   1. Get your ESPN league ID from your league URL")
        print("   2. Call: query_espn_for_players(league_id=YOUR_LEAGUE_ID)")
        return None

def analyze_data_discrepancies():
    """Analyze the discrepancies we found in our data."""
    
    print("\n🔍 Data Quality Issues Found:")
    print("=" * 40)
    
    print("\n❌ ISSUE 1: Greg Olsen Team Assignment")
    print("   • Our data shows: Greg Olsen on SEA (Seattle) in 2019")
    print("   • Reality: Greg Olsen was on CAR (Carolina) in 2019")
    print("   • He joined Seattle in 2020")
    
    print("\n❌ ISSUE 2: Missing Seattle WRs")
    print("   • Our data shows only 12.0 WR receiving yards for Seattle in week 16")
    print("   • Missing players: Malik Turner, David Moore")
    print("   • These players had significant receiving yards in that game")
    
    print("\n❌ ISSUE 3: Data Completeness")
    print("   • Our dataset appears to only include fantasy roster players")
    print("   • Missing players who played but weren't on fantasy rosters")
    print("   • This affects defensive performance calculations")
    
    print("\n💡 Impact on Defense PI Calculations:")
    print("   • Arizona's defense PI is based on incomplete offensive data")
    print("   • The 12.0 yards figure is significantly understated")
    print("   • This makes Arizona's defense appear to perform better than it actually did")
    print("   • The PI calculation is mathematically correct, but based on wrong data")

def main():
    """Main function."""
    
    print("🏈 ESPN Player Data Verification Tool")
    print("=" * 50)
    
    # Analyze the issues we found
    analyze_data_discrepancies()
    
    # Try to query ESPN API (will fail without valid credentials)
    print(f"\n🔗 ESPN API Query:")
    print("   To query ESPN API, call: query_espn_for_players(league_id=YOUR_LEAGUE_ID)")
    print("   Replace YOUR_LEAGUE_ID with your actual ESPN league ID")
    
    print(f"\n📝 Summary of Issues:")
    print("   1. Team assignment errors (Greg Olsen on wrong team)")
    print("   2. Missing players (Malik Turner, David Moore)")
    print("   3. Incomplete data (only fantasy roster players)")
    print("   4. Incorrect defensive performance indices as a result")

if __name__ == "__main__":
    main()




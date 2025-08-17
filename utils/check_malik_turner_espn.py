#!/usr/bin/env python3
"""
Check ESPN API for Malik Turner in 2019.
"""

import requests
import time
from espn_api.football import League

def check_malik_turner_espn():
    """Check if Malik Turner exists in ESPN API data for 2019."""
    
    print("🔍 Checking ESPN API for Malik Turner in 2019")
    print("=" * 50)
    
    # ESPN API configuration
    LEAGUE_ID = 57220027  # Your actual league ID
    YEAR = 2019
    
    try:
        # Try to get league data
        print("📊 Attempting to connect to ESPN Fantasy API...")
        league = League(league_id=LEAGUE_ID, year=YEAR)
        
        # Check rostered players
        print("\n🏈 Checking rostered players...")
        rostered_players = []
        for team in league.teams:
            for player in team.roster:
                if 'malik' in player.name.lower() and 'turner' in player.name.lower():
                    rostered_players.append(f"{player.name} (Team: {team.team_name})")
        
        if rostered_players:
            print("✅ Found Malik Turner in rostered players:")
            for player in rostered_players:
                print(f"   {player}")
        else:
            print("❌ Malik Turner not found in rostered players")
        
        # Check free agents
        print("\n🏈 Checking free agents...")
        free_agents = []
        try:
            for player in league.free_agents(None,800):
                if 'malik' in player.name.lower() and 'turner' in player.name.lower():
                    free_agents.append(player.name)
        except Exception as e:
            print(f"⚠️  Error checking free agents: {e}")
        
        if free_agents:
            print("✅ Found Malik Turner in free agents:")
            for player in free_agents:
                print(f"   {player}")
        else:
            print("❌ Malik Turner not found in free agents")
        
        # Try to search for any player with "Malik" in the name
        print("\n🔍 Searching for any players with 'Malik' in name...")
        malik_players = []
        
        # Check rostered players
        for team in league.teams:
            for player in team.roster:
                if 'malik' in player.name.lower():
                    malik_players.append(f"{player.name} (Rostered - {team.team_name})")
        
        # Check free agents
        try:
            for player in league.free_agents(None, 800):
                if 'malik' in player.name.lower():
                    malik_players.append(f"{player.name} (Free Agent)")
        except:
            pass
        
        if malik_players:
            print("✅ Found players with 'Malik' in name:")
            for player in malik_players:
                print(f"   {player}")
        else:
            print("❌ No players with 'Malik' in name found")
        
    except Exception as e:
        print(f"❌ Error connecting to ESPN API: {e}")
        print("   Note: You may need to set up proper ESPN API credentials")
    
    # Try ESPN Gamelog API directly
    print("\n🌐 Trying ESPN Gamelog API...")
    try:
        # Search for Malik Turner in ESPN's athlete database
        search_url = "https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/search"
        params = {
            'query': 'Malik Turner',
            'limit': 10
        }
        
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            data = response.json()
            print("✅ ESPN search API response received")
            print(f"   Response keys: {list(data.keys())}")
            
            # Look for athletes in the response
            if 'athletes' in data:
                athletes = data['athletes']
                print(f"   Found {len(athletes)} athletes in search results")
                
                for athlete in athletes:
                    name = athlete.get('name', 'Unknown')
                    print(f"   - {name}")
                    
                    # Check if this is Malik Turner
                    if 'malik' in name.lower() and 'turner' in name.lower():
                        print(f"   ✅ Found Malik Turner in ESPN athlete database!")
                        print(f"      ID: {athlete.get('id', 'Unknown')}")
                        print(f"      Team: {athlete.get('team', {}).get('name', 'Unknown')}")
        else:
            print(f"❌ ESPN search API returned status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error with ESPN Gamelog API: {e}")

if __name__ == "__main__":
    check_malik_turner_espn()

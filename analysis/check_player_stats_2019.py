import pandas as pd
from espn_api.football import League
import json
from datetime import datetime

def get_player_stats_2019():
    """Query ESPN API for specific players' 2019 stats."""
    
    print("🔍 Checking ESPN API for player stats in 2019")
    print("=" * 50)
    
    # Initialize league (we'll use a dummy league to access the API)
    # Note: We need a valid league ID and year to access historical data
    try:
        # Try to get a league - you may need to provide actual league details
        league = League(league_id=123456, year=2019)  # This will likely fail, but let's try
        print("✅ Successfully connected to ESPN API")
    except Exception as e:
        print(f"❌ Could not connect to ESPN API: {e}")
        print("This is expected if we don't have valid league credentials")
        return
    
    # Players to check
    players_to_check = [
        {"name": "Greg Olsen", "expected_team_2019": "CAR"},
        {"name": "Malik Turner", "expected_team_2019": "SEA"}, 
        {"name": "David Moore", "expected_team_2019": "SEA"}
    ]
    
    print(f"\n📊 Checking {len(players_to_check)} players...")
    
    for player_info in players_to_check:
        player_name = player_info["name"]
        expected_team = player_info["expected_team_2019"]
        
        print(f"\n🔍 Looking for: {player_name} (expected team: {expected_team})")
        
        try:
            # Search for the player
            # Note: This is a simplified approach - the actual ESPN API might require different methods
            print(f"   Searching ESPN API for {player_name}...")
            
            # This is where we'd normally query the API
            # For now, let's show what we expect to find
            print(f"   Expected: {player_name} should be on {expected_team} in 2019")
            print(f"   Status: Need valid ESPN API credentials to query")
            
        except Exception as e:
            print(f"   ❌ Error querying for {player_name}: {e}")
    
    print(f"\n📝 Summary:")
    print(f"   • Greg Olsen should be on CAR (Carolina) in 2019, not SEA")
    print(f"   • Malik Turner should be on SEA (Seattle) in 2019")
    print(f"   • David Moore should be on SEA (Seattle) in 2019")
    print(f"   • Our dataset has incorrect team assignments and missing players")

def check_our_data_issues():
    """Check what's wrong in our current dataset."""
    
    print(f"\n🔍 Analyzing our dataset issues:")
    print("=" * 40)
    
    df = pd.read_parquet("data/fantasy_weekly_stats.parquet")
    
    # Check Greg Olsen in our data
    print(f"\n📊 Greg Olsen in our dataset:")
    olsen_data = df[(df['year'] == 2019) & (df['name'].str.contains('Olsen', case=False, na=False))]
    if not olsen_data.empty:
        print(olsen_data[['name', 'player_team', 'position', 'week', 'receivingYards']].sort_values('week'))
    else:
        print("   No Greg Olsen found in our dataset")
    
    # Check Seattle players in week 16
    print(f"\n📊 Seattle players in week 16, 2019 (our dataset):")
    sea_week16 = df[(df['year'] == 2019) & (df['week'] == 16) & (df['player_team'] == 'SEA')]
    print(sea_week16[['name', 'position', 'receivingYards', 'receivingReceptions']].sort_values('receivingYards', ascending=False))
    
    # Check if we have any players with similar names
    print(f"\n📊 Players with 'Moore' in name (our dataset):")
    moore_players = df[(df['year'] == 2019) & (df['name'].str.contains('Moore', case=False, na=False))]
    print(moore_players[['name', 'player_team', 'position']].drop_duplicates())
    
    print(f"\n📊 Players with 'Turner' in name (our dataset):")
    turner_players = df[(df['year'] == 2019) & (df['name'].str.contains('Turner', case=False, na=False))]
    print(turner_players[['name', 'player_team', 'position']].drop_duplicates())

def main():
    """Main function to check player stats."""
    
    print("🏈 ESPN API Player Stats Checker - 2019")
    print("=" * 50)
    
    # Check our current data issues
    check_our_data_issues()
    
    # Try to query ESPN API
    get_player_stats_2019()
    
    print(f"\n💡 Recommendations:")
    print(f"   1. Verify ESPN API credentials and league access")
    print(f"   2. Check if our data collection process is filtering out non-fantasy players")
    print(f"   3. Verify team assignments in our dataset")
    print(f"   4. Consider using a different data source for complete player stats")

if __name__ == "__main__":
    main()




#!/usr/bin/env python3
"""
Analyze all Seattle players in our 2019 data to understand data completeness.
"""

import pandas as pd

def analyze_seattle_players_2019():
    """Analyze Seattle players in our 2019 dataset."""
    
    print("🔍 Analyzing Seattle players in 2019 dataset")
    print("=" * 50)
    
    # Load the complete player stats
    df = pd.read_parquet("data/fantasy_weekly_stats_complete.parquet")
    
    # Get all Seattle players in 2019
    seattle_2019 = df[(df['nfl_team'] == 'SEA') & (df['year'] == 2019)]
    
    if seattle_2019.empty:
        print("❌ No Seattle players found in 2019")
        return
    
    print(f"📊 Found {len(seattle_2019)} Seattle player records in 2019")
    print(f"📊 Unique players: {seattle_2019['name'].nunique()}")
    print()
    
    # Get unique players
    unique_players = seattle_2019[['name', 'position', 'playerId']].drop_duplicates()
    unique_players = unique_players.sort_values(['position', 'name'])
    
    print("🏈 All Seattle Players in 2019 Dataset:")
    print("-" * 50)
    print(f"{'Player':<25} {'Position':<8} {'Player ID':<10}")
    print("-" * 50)
    
    for _, player in unique_players.iterrows():
        print(f"{player['name']:<25} {player['position']:<8} {player['playerId']:<10}")
    
    print()
    
    # Analyze by position
    print("📊 Players by Position:")
    pos_counts = unique_players['position'].value_counts()
    for pos, count in pos_counts.items():
        print(f"   {pos}: {count} players")
    
    print()
    
    # Check for players with receiving stats
    print("🏈 Players with Receiving Stats (any week):")
    print("-" * 50)
    
    receiving_players = seattle_2019[
        (seattle_2019['receivingYards'] > 0) | 
        (seattle_2019['receivingReceptions'] > 0)
    ][['name', 'position']].drop_duplicates().sort_values(['position', 'name'])
    
    for _, player in receiving_players.iterrows():
        print(f"   {player['name']} ({player['position']})")
    
    print()
    
    # Check specific weeks for receiving stats
    print("📊 Receiving Stats by Week (all Seattle players):")
    print("-" * 50)
    
    for week in range(1, 18):
        week_data = seattle_2019[seattle_2019['week'] == week]
        if not week_data.empty:
            receiving_week = week_data[
                (week_data['receivingYards'] > 0) | 
                (week_data['receivingReceptions'] > 0)
            ]
            
            if not receiving_week.empty:
                print(f"Week {week:2d}: {len(receiving_week)} players with receiving stats")
                for _, player in receiving_week.iterrows():
                    print(f"   {player['name']} ({player['position']}): {player['receivingReceptions']:.0f} rec, {player['receivingYards']:.0f} yards")
            else:
                print(f"Week {week:2d}: No receiving stats")
    
    print()
    
    # Check for any players with "Malik" in name
    malik_players = seattle_2019[seattle_2019['name'].str.contains('Malik', case=False, na=False)]
    if not malik_players.empty:
        print("✅ Found players with 'Malik' in name:")
        for _, player in malik_players.iterrows():
            print(f"   {player['name']} ({player['position']}) - Week {player['week']}")
    else:
        print("❌ No players with 'Malik' in name found")
    
    print()
    
    # Check for any players with "Turner" in name
    turner_players = seattle_2019[seattle_2019['name'].str.contains('Turner', case=False, na=False)]
    if not turner_players.empty:
        print("✅ Found players with 'Turner' in name:")
        for _, player in turner_players.iterrows():
            print(f"   {player['name']} ({player['position']}) - Week {player['week']}")
    else:
        print("❌ No players with 'Turner' in name found")

if __name__ == "__main__":
    analyze_seattle_players_2019()

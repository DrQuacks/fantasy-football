#!/usr/bin/env python3
"""
Test script to check for Malik Turner in 2019 and 2021 after the improved data collection.
"""

import pandas as pd

def test_malik_turner_complete():
    """Test if Malik Turner is now in our complete dataset."""
    
    print("🔍 Testing Malik Turner data completeness after improved collection")
    print("=" * 60)
    
    # Load the complete player stats
    df = pd.read_parquet("data/fantasy_weekly_stats_complete.parquet")
    
    # Check for Malik Turner in 2019
    print("\n📊 Checking Malik Turner in 2019:")
    malik_2019 = df[(df['name'].str.contains('Malik', case=False, na=False)) & 
                    (df['name'].str.contains('Turner', case=False, na=False)) & 
                    (df['year'] == 2019)]
    
    if not malik_2019.empty:
        print("✅ Found Malik Turner in 2019!")
        print(f"   Total records: {len(malik_2019)}")
        print(f"   Teams: {malik_2019['nfl_team'].unique()}")
        print(f"   Position: {malik_2019['position'].iloc[0]}")
        print(f"   Player ID: {malik_2019['playerId'].iloc[0]}")
        
        # Show his stats
        print("\n   Malik Turner 2019 Stats:")
        for _, record in malik_2019.iterrows():
            print(f"   Week {record['week']:2d} vs {record['nfl_opponent']}: "
                  f"{record['receivingReceptions']:.0f} rec, {record['receivingYards']:.0f} yards, "
                  f"{record['receivingTouchdowns']:.0f} TDs")
    else:
        print("❌ Malik Turner NOT found in 2019")
    
    # Check for Malik Turner in 2021
    print("\n📊 Checking Malik Turner in 2021:")
    malik_2021 = df[(df['name'].str.contains('Malik', case=False, na=False)) & 
                    (df['name'].str.contains('Turner', case=False, na=False)) & 
                    (df['year'] == 2021)]
    
    if not malik_2021.empty:
        print("✅ Found Malik Turner in 2021!")
        print(f"   Total records: {len(malik_2021)}")
        print(f"   Teams: {malik_2021['nfl_team'].unique()}")
        print(f"   Position: {malik_2021['position'].iloc[0]}")
        print(f"   Player ID: {malik_2021['playerId'].iloc[0]}")
        
        # Show his stats
        print("\n   Malik Turner 2021 Stats:")
        for _, record in malik_2021.iterrows():
            print(f"   Week {record['week']:2d} vs {record['nfl_opponent']}: "
                  f"{record['receivingReceptions']:.0f} rec, {record['receivingYards']:.0f} yards, "
                  f"{record['receivingTouchdowns']:.0f} TDs")
    else:
        print("❌ Malik Turner NOT found in 2021")
    
    # Check Seattle Week 16, 2019 specifically
    print("\n📊 Checking Seattle Week 16, 2019 (the original issue):")
    seattle_week16_2019 = df[(df['nfl_team'] == 'SEA') & 
                             (df['year'] == 2019) & 
                             (df['week'] == 16)]
    
    if not seattle_week16_2019.empty:
        print(f"   Found {len(seattle_week16_2019)} Seattle players in Week 16, 2019")
        
        # Check for Malik Turner specifically
        malik_week16 = seattle_week16_2019[
            seattle_week16_2019['name'].str.contains('Malik', case=False, na=False)
        ]
        
        if not malik_week16.empty:
            print("✅ Malik Turner is now in Seattle Week 16, 2019!")
            for _, player in malik_week16.iterrows():
                print(f"   {player['name']}: {player['receivingReceptions']:.0f} rec, {player['receivingYards']:.0f} yards")
        else:
            print("❌ Malik Turner still not found in Seattle Week 16, 2019")
        
        # Show all WR receiving stats for that game
        wr_stats = seattle_week16_2019[seattle_week16_2019['position'] == 'WR']
        if not wr_stats.empty:
            print("\n   All WR receiving stats for Seattle Week 16, 2019:")
            total_wr_yards = 0
            for _, player in wr_stats.iterrows():
                yards = player['receivingYards']
                total_wr_yards += yards
                print(f"   {player['name']}: {player['receivingReceptions']:.0f} rec, {yards:.0f} yards")
            print(f"   Total WR yards: {total_wr_yards:.0f}")
    
    # Overall data completeness check
    print("\n📊 Overall Data Completeness Check:")
    total_players = df['name'].nunique()
    total_records = len(df)
    print(f"   Total unique players: {total_players:,}")
    print(f"   Total player records: {total_records:,}")
    print(f"   Average records per player: {total_records/total_players:.1f}")

if __name__ == "__main__":
    test_malik_turner_complete()

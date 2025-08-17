#!/usr/bin/env python3
"""
Check Seattle's actual receiving stats in Week 16, 2019 against Arizona.
"""

import pandas as pd

def check_seattle_week16():
    """Check Seattle's receiving stats in Week 16, 2019."""
    
    print("🔍 Checking Seattle receiving stats - Week 16, 2019 vs Arizona")
    print("=" * 60)
    
    # Load the complete player stats
    df = pd.read_parquet("data/fantasy_weekly_stats_complete.parquet")
    
    # Find Seattle players in Week 16, 2019
    seattle_week16 = df[(df['nfl_team'] == 'SEA') & 
                        (df['year'] == 2019) & 
                        (df['week'] == 16)]
    
    if seattle_week16.empty:
        print("❌ No Seattle players found for Week 16, 2019")
        return
    
    print(f"📊 Found {len(seattle_week16)} Seattle players in Week 16, 2019")
    print()
    
    # Check for Malik Turner specifically
    malik_turner = seattle_week16[seattle_week16['name'].str.contains('Malik', case=False, na=False)]
    if not malik_turner.empty:
        print("✅ Found Malik Turner in our data:")
        for _, player in malik_turner.iterrows():
            print(f"   {player['name']} ({player['position']}): {player['receivingReceptions']:.0f} rec, {player['receivingYards']:.0f} yards")
    else:
        print("❌ Malik Turner NOT found in our data!")
    
    print()
    
    # Show ALL Seattle players (not just those with receiving stats)
    print("🏈 ALL Seattle Players - Week 16, 2019 vs Arizona:")
    print("-" * 60)
    print(f"{'Player':<20} {'Pos':<4} {'Rec':<4} {'Yards':<6} {'TDs':<4} {'Targets':<7}")
    print("-" * 60)
    
    total_rec = 0
    total_yards = 0
    total_tds = 0
    total_targets = 0
    
    for _, player in seattle_week16.sort_values('receivingYards', ascending=False).iterrows():
        name = player['name']
        pos = player['position']
        rec = player['receivingReceptions']
        yards = player['receivingYards']
        tds = player['receivingTouchdowns']
        targets = player['receivingTargets']
        
        print(f"{name:<20} {pos:<4} {rec:<4.0f} {yards:<6.0f} {tds:<4.0f} {targets:<7.0f}")
        
        total_rec += rec
        total_yards += yards
        total_tds += tds
        total_targets += targets
    
    print("-" * 60)
    print(f"{'TOTAL':<20} {'':<4} {total_rec:<4.0f} {total_yards:<6.0f} {total_tds:<4.0f} {total_targets:<7.0f}")
    print()
    
    # Calculate WR-only totals
    wr_players = seattle_week16[seattle_week16['position'] == 'WR']
    wr_total_rec = wr_players['receivingReceptions'].sum()
    wr_total_yards = wr_players['receivingYards'].sum()
    wr_total_tds = wr_players['receivingTouchdowns'].sum()
    wr_total_targets = wr_players['receivingTargets'].sum()
    
    print("📊 WR-Only Totals:")
    print(f"   WR Receptions: {wr_total_rec:.0f}")
    print(f"   WR Yards: {wr_total_yards:.0f}")
    print(f"   WR TDs: {wr_total_tds:.0f}")
    print(f"   WR Targets: {wr_total_targets:.0f}")
    print()
    
    # Check the defense table value
    print("🔍 Comparing with defense table value:")
    defense_df = pd.read_parquet("data/defense_weekly_stats.parquet")
    
    defense_game = defense_df[(defense_df['defense_team'] == 'ARI') & 
                              (defense_df['offense_team'] == 'SEA') & 
                              (defense_df['year'] == 2019) & 
                              (defense_df['week'] == 16)]
    
    if not defense_game.empty:
        defense_wr_yards = defense_game['receivingYardsWR'].iloc[0]
        print(f"   Defense table shows: {defense_wr_yards:.1f} WR receiving yards")
        print(f"   Our calculation shows: {wr_total_yards:.1f} WR receiving yards")
        print(f"   Difference: {abs(defense_wr_yards - wr_total_yards):.1f} yards")
        
        if abs(defense_wr_yards - wr_total_yards) > 1:
            print("   ⚠️  DISCREPANCY: Defense table value doesn't match player stats!")
        else:
            print("   ✅ Values match!")
    else:
        print("   ❌ Game not found in defense table")

if __name__ == "__main__":
    check_seattle_week16()

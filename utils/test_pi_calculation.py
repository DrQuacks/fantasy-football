#!/usr/bin/env python3
"""
Test script to debug PI calculation for Arizona vs Seattle case.
"""

import pandas as pd
import numpy as np

def test_arizona_seattle_pi():
    """Test the PI calculation for Arizona defense vs Seattle offense in week 16, 2019."""
    
    print("🔍 Testing PI calculation for Arizona vs Seattle - Week 16, 2019")
    print("=" * 70)
    
    # Load the defense weekly stats
    df = pd.read_parquet("data/defense_weekly_stats.parquet")
    
    # Find the specific game
    game = df[(df['defense_team'] == 'ARI') & 
              (df['offense_team'] == 'SEA') & 
              (df['year'] == 2019) & 
              (df['week'] == 16)]
    
    if game.empty:
        print("❌ Game not found!")
        return
    
    print(f"📊 Found game: Arizona defense vs Seattle offense, Week 16, 2019")
    print(f"   Actual receivingYardsWR: {game['receivingYardsWR'].iloc[0]}")
    print(f"   isHome: {game['isHome'].iloc[0]}")
    
    # Calculate Seattle's offensive baseline for 2019 (excluding week 16)
    seattle_offense = df[(df['offense_team'] == 'SEA') & (df['year'] == 2019) & (df['week'] != 16)]
    seattle_avg_excluding_week16 = seattle_offense['receivingYardsWR'].mean()
    
    print(f"\n📈 Seattle offense 2019 receivingYardsWR average (excluding week 16): {seattle_avg_excluding_week16:.2f}")
    
    # Calculate expected PI
    actual = game['receivingYardsWR'].iloc[0]
    expected = seattle_avg_excluding_week16
    pi_manual = (expected - actual) / expected
    
    print(f"\n🧮 Manual PI calculation (leave-one-out):")
    print(f"   Expected (Seattle avg excluding week 16): {expected:.2f}")
    print(f"   Actual (Arizona allowed): {actual:.2f}")
    print(f"   PI = ({expected:.2f} - {actual:.2f}) / {expected:.2f}")
    print(f"   PI = {pi_manual:.6f}")
    
    # Now check what our compute_defense_adjusted_metrics.py produces
    print(f"\n🔍 Checking computed PI values...")
    
    # Load the computed PI data
    pi_df = pd.read_parquet("data/defense_adjusted_pi.parquet")
    
    # Find Arizona 2019
    arizona_pi = pi_df[(pi_df['defense_team'] == 'ARI') & (pi_df['year'] == 2019)]
    
    if not arizona_pi.empty:
        print(f"📊 Arizona 2019 computed PI values:")
        print(f"   pi_last1_receivingYardsWR: {arizona_pi['pi_last1_receivingYardsWR'].iloc[0]:.6f}")
        print(f"   pi_season_receivingYardsWR: {arizona_pi['pi_season_receivingYardsWR'].iloc[0]:.6f}")
        
        print(f"\n❌ DISCREPANCY FOUND!")
        print(f"   Manual calculation (leave-one-out): {pi_manual:.6f}")
        print(f"   Computed last1: {arizona_pi['pi_last1_receivingYardsWR'].iloc[0]:.6f}")
        print(f"   Difference: {abs(pi_manual - arizona_pi['pi_last1_receivingYardsWR'].iloc[0]):.6f}")
    else:
        print("❌ Arizona 2019 not found in PI data!")
    
    # Let's also check what the baseline calculation is doing
    print(f"\n🔍 Debugging baseline calculation...")
    
    # Check if Seattle offense data exists
    seattle_games = df[(df['offense_team'] == 'SEA') & (df['year'] == 2019)]
    print(f"   Seattle offense games found: {len(seattle_games)}")
    
    if not seattle_games.empty:
        print(f"   Seattle receivingYardsWR values:")
        for _, row in seattle_games.sort_values('week').iterrows():
            print(f"     Week {row['week']:2d}: {row['receivingYardsWR']:.1f}")
        
        print(f"   Seattle average (all games): {seattle_games['receivingYardsWR'].mean():.2f}")
        print(f"   Seattle average (excluding week 16): {seattle_avg_excluding_week16:.2f}")
        print(f"   Seattle std dev: {seattle_games['receivingYardsWR'].std():.2f}")

if __name__ == "__main__":
    test_arizona_seattle_pi()

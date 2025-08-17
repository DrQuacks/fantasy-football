#!/usr/bin/env python3
"""
Debug the exact PI calculation that's happening in the computed table.
"""

import pandas as pd
import numpy as np

def debug_computed_pi():
    """Debug the computed PI calculation for Arizona vs Seattle Week 16, 2019."""
    
    print("🔍 Debugging Computed PI Calculation - Arizona vs Seattle Week 16, 2019")
    print("=" * 70)
    
    # Load the defense weekly stats (this is what the PI calculation uses)
    df = pd.read_parquet("data/defense_weekly_stats.parquet")
    
    # Find the Arizona vs Seattle Week 16, 2019 game
    target_game = df[(df['defense_team'] == 'ARI') & 
                     (df['offense_team'] == 'SEA') & 
                     (df['year'] == 2019) & 
                     (df['week'] == 16)]
    
    if target_game.empty:
        print("❌ Target game not found!")
        return
    
    print(f"✅ Found target game:")
    print(f"   Defense: {target_game['defense_team'].iloc[0]}")
    print(f"   Offense: {target_game['offense_team'].iloc[0]}")
    print(f"   Year: {target_game['year'].iloc[0]}")
    print(f"   Week: {target_game['week'].iloc[0]}")
    print(f"   Actual WR receiving yards: {target_game['receivingYardsWR'].iloc[0]:.1f}")
    
    # Now simulate the leave-one-out baseline calculation
    year = 2019
    offense_team = 'SEA'
    week = 16
    
    # Get all Seattle games in 2019 EXCEPT Week 16
    other_games = df[
        (df['year'] == year) & 
        (df['offense_team'] == offense_team) & 
        (df['week'] != week)
    ]
    
    print(f"\n📊 Seattle 2019 games (excluding Week 16):")
    for _, game in other_games.iterrows():
        print(f"   Week {int(game['week']):2d}: {game['receivingYardsWR']:.1f} yards")
    
    # Calculate expected value
    expected = other_games['receivingYardsWR'].mean()
    actual = target_game['receivingYardsWR'].iloc[0]
    
    print(f"\n🧮 Baseline calculation:")
    print(f"   Expected (Seattle avg excluding Week 16): {expected:.2f} yards")
    print(f"   Actual (Week 16): {actual:.1f} yards")
    
    # Calculate PI with EPS
    EPS = 1e-6
    pi = (expected - actual) / (expected + EPS)
    
    print(f"\n📈 PI Calculation:")
    print(f"   PI = (Expected - Actual) / (Expected + EPS)")
    print(f"   PI = ({expected:.2f} - {actual:.1f}) / ({expected:.2f} + {EPS})")
    print(f"   PI = {expected - actual:.2f} / {expected + EPS:.6f}")
    print(f"   PI = {pi:.6f}")
    
    # Check against the actual PI value from our table
    pi_df = pd.read_parquet("data/defense_adjusted_pi.parquet")
    arizona_2019_pi = pi_df[(pi_df['defense_team'] == 'ARI') & (pi_df['year'] == 2019)]['pi_last1_receivingYardsWR'].iloc[0]
    
    print(f"\n✅ Verification:")
    print(f"   Our calculation: {pi:.6f}")
    print(f"   Table value: {arizona_2019_pi:.6f}")
    print(f"   Difference: {abs(pi - arizona_2019_pi):.6f}")
    
    if abs(pi - arizona_2019_pi) < 0.001:
        print("   ✅ Our calculation matches the table!")
    else:
        print("   ❌ Our calculation doesn't match the table")
        print("   🔍 This suggests there's a different baseline being used")

if __name__ == "__main__":
    debug_computed_pi()

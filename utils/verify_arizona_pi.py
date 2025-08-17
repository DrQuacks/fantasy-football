#!/usr/bin/env python3
"""
Verify the actual PI calculation for Arizona vs Seattle Week 16, 2019.
"""

import pandas as pd
import numpy as np

def verify_arizona_pi():
    """Verify the PI calculation for Arizona vs Seattle Week 16, 2019."""
    
    print("🔍 Verifying Arizona PI calculation - Week 16, 2019")
    print("=" * 60)
    
    # Load the complete player stats
    df = pd.read_parquet("data/fantasy_weekly_stats_complete.parquet")
    
    # Get Seattle's WR receiving yards for all games in 2019
    seattle_2019 = df[(df['nfl_team'] == 'SEA') & (df['year'] == 2019) & (df['position'] == 'WR')]
    
    # Group by week and sum WR receiving yards
    seattle_weekly_wr = seattle_2019.groupby('week')['receivingYards'].sum().reset_index()
    seattle_weekly_wr = seattle_weekly_wr.rename(columns={'receivingYards': 'receivingYardsWR'})
    
    print(f"\n📊 Seattle 2019 WR receiving yards by week:")
    for _, row in seattle_weekly_wr.iterrows():
        print(f"   Week {int(row['week']):2d}: {row['receivingYardsWR']:.0f} yards")
    
    # Calculate baseline excluding Week 16 (leave-one-out)
    baseline_excluding_week16 = seattle_weekly_wr[seattle_weekly_wr['week'] != 16]['receivingYardsWR'].mean()
    
    # Actual value for Week 16
    actual_week16 = seattle_weekly_wr[seattle_weekly_wr['week'] == 16]['receivingYardsWR'].iloc[0]
    
    print(f"\n🧮 Leave-one-out baseline calculation:")
    print(f"   Baseline (excluding Week 16): {baseline_excluding_week16:.2f} yards")
    print(f"   Actual Week 16: {actual_week16:.0f} yards")
    
    # Calculate PI
    pi = (baseline_excluding_week16 - actual_week16) / baseline_excluding_week16
    
    print(f"\n📈 PI Calculation:")
    print(f"   PI = (Expected - Actual) / Expected")
    print(f"   PI = ({baseline_excluding_week16:.2f} - {actual_week16:.0f}) / {baseline_excluding_week16:.2f}")
    print(f"   PI = {baseline_excluding_week16 - actual_week16:.2f} / {baseline_excluding_week16:.2f}")
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
    
    # Also check what the season average would be
    season_avg = seattle_weekly_wr['receivingYardsWR'].mean()
    season_pi = (season_avg - actual_week16) / season_avg
    
    print(f"\n📊 For comparison - Season average baseline:")
    print(f"   Season average: {season_avg:.2f} yards")
    print(f"   Season PI: {season_pi:.6f}")

if __name__ == "__main__":
    verify_arizona_pi()

import pandas as pd
import numpy as np

def debug_arizona_calculation():
    """Debug the calculation for Arizona receivingYardsWR in week 16 of 2019."""
    
    print("🔍 Debugging Arizona receivingYardsWR calculation - Week 16, 2019")
    print("=" * 70)
    
    # Load the defense weekly stats
    df = pd.read_parquet("data/defense_weekly_stats.parquet")
    
    # Find the specific game
    ari_game = df[(df['defense_team'] == 'ARI') & (df['year'] == 2019) & (df['week'] == 16)]
    
    if ari_game.empty:
        print("❌ No data found for Arizona defense in week 16, 2019")
        return
    
    print(f"📊 Found Arizona defense data for week 16, 2019")
    print(f"   Offense team: {ari_game['offense_team'].iloc[0]}")
    print(f"   Actual receivingYardsWR: {ari_game['receivingYardsWR'].iloc[0]}")
    
    # Calculate the expected value (Arizona offense average for 2019)
    ari_offense_2019 = df[(df['offense_team'] == 'ARI') & (df['year'] == 2019)]
    expected_receiving_yards = ari_offense_2019['receivingYardsWR'].mean()
    
    print(f"\n📈 Expected value calculation:")
    print(f"   Arizona offense 2019 receivingYardsWR per game: {expected_receiving_yards:.2f}")
    print(f"   This is the average across all 16 games Arizona played as offense")
    
    # Show all Arizona offense games for context
    print(f"\n📋 Arizona offense 2019 - All games receivingYardsWR:")
    ari_offense_games = ari_offense_2019[['week', 'receivingYardsWR']].sort_values('week')
    for _, row in ari_offense_games.iterrows():
        print(f"   Week {int(row['week']):2d}: {row['receivingYardsWR']:6.1f}")
    
    # Calculate the PI
    actual = ari_game['receivingYardsWR'].iloc[0]
    expected = expected_receiving_yards
    
    # PI = (Expected - Actual) / Expected
    pi = (expected - actual) / expected
    
    print(f"\n🧮 Performance Index (PI) calculation:")
    print(f"   Formula: PI = (Expected - Actual) / Expected")
    print(f"   PI = ({expected:.2f} - {actual:.2f}) / {expected:.2f}")
    print(f"   PI = {expected - actual:.2f} / {expected:.2f}")
    print(f"   PI = {pi:.6f}")
    
    # Check if this matches the computed value
    pi_df = pd.read_parquet("data/defense_adjusted_pi.parquet")
    computed_pi = pi_df[(pi_df['defense_team'] == 'ARI') & (pi_df['year'] == 2019)]
    
    if not computed_pi.empty:
        season_pi = computed_pi['pi_season_receivingYardsWR'].iloc[0]
        last1_pi = computed_pi['pi_last1_receivingYardsWR'].iloc[0]
        
        print(f"\n✅ Verification:")
        print(f"   Computed season PI: {season_pi:.6f}")
        print(f"   Computed last1 PI: {last1_pi:.6f}")
        print(f"   Our calculation: {pi:.6f}")
        
        if abs(pi - last1_pi) < 0.0001:
            print(f"   ✅ Our calculation matches the last1 PI!")
        else:
            print(f"   ❌ Our calculation doesn't match the last1 PI")
            print(f"   Difference: {abs(pi - last1_pi):.6f}")
    
    # Interpretation
    print(f"\n📝 Interpretation:")
    if pi > 0:
        print(f"   Positive PI ({pi:.3f}) means Arizona defense performed BETTER than expected")
        print(f"   They held the opponent to {actual:.1f} yards vs expected {expected:.1f} yards")
    else:
        print(f"   Negative PI ({pi:.3f}) means Arizona defense performed WORSE than expected")
        print(f"   They allowed {actual:.1f} yards vs expected {expected:.1f} yards")
    
    print(f"\n🔍 What this means:")
    print(f"   • Arizona's defense faced an offense that typically gets {expected:.1f} WR receiving yards per game")
    print(f"   • In week 16, they allowed {actual:.1f} WR receiving yards")
    print(f"   • The PI of {pi:.3f} indicates how well they defended compared to expectation")

if __name__ == "__main__":
    debug_arizona_calculation()

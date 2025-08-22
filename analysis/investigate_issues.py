import pandas as pd

def investigate_issues():
    """
    Investigate the Week 1 NaN issues and 2019 Week 2 -1.0 issues.
    """
    print("🔍 Investigating issues...")
    
    # Load the PI table
    df = pd.read_parquet("data/defense_adjusted_pi.parquet")
    
    # Check Week 1 NaN values for non-2019 years
    print("📊 Week 1 NaN analysis (non-2019 years):")
    for year in [2020, 2021, 2022, 2023, 2024]:
        week1 = df[(df['year'] == year) & (df['week'] == 1)]
        nan_count = week1.isna().sum().sum()
        print(f"   Year {year} Week 1: {nan_count} NaN values")
    
    # Check 2019 Week 2 values
    print("\n🔍 2019 Week 2 analysis:")
    week2_2019 = df[(df['year'] == 2019) & (df['week'] == 2)]
    print("   Sample 2019 Week 2 values:")
    print(week2_2019[['year', 'defense_team', 'week', 'pi_last1_receivingYardsWR', 'pi_last4_receivingYardsWR', 'pi_season_receivingYardsWR']].head(5))
    
    # Check if -1.0 values are widespread in 2019 Week 2
    pi_cols = [col for col in week2_2019.columns if col.startswith('pi_')]
    minus_one_count = (week2_2019[pi_cols] == -1.0).sum().sum()
    total_pi_cells = len(week2_2019) * len(pi_cols)
    print(f"   -1.0 values in 2019 Week 2: {minus_one_count}/{total_pi_cells}")
    
    # Check source data to understand the expected value calculation
    print("\n🔍 Checking source data for expected values...")
    source_df = pd.read_parquet("data/defense_weekly_stats.parquet")
    
    # Check if 2019 Week 1 data exists for expected values
    week1_2019_source = source_df[(source_df['year'] == 2019) & (source_df['week'] == 1)]
    print(f"   2019 Week 1 source records: {len(week1_2019_source)}")
    
    # Check if 2018 data exists for 2019 Week 1 expected values
    year_2018_source = source_df[source_df['year'] == 2018]
    print(f"   2018 source records: {len(year_2018_source)}")
    
    # Check a specific example: Arizona 2019 Week 1
    print("\n🔍 Arizona 2019 Week 1 example:")
    ari_week1_2019 = week1_2019_source[week1_2019_source['defense_team'] == 'ARI']
    if not ari_week1_2019.empty:
        print("   Arizona 2019 Week 1 games:")
        print(ari_week1_2019[['year', 'week', 'defense_team', 'offense_team', 'receivingYardsWR']])
        
        # Check what the expected value should be
        offense_team = ari_week1_2019.iloc[0]['offense_team']
        print(f"   Offense team: {offense_team}")
        
        # Check if there's 2018 data for this offense team
        offense_2018 = year_2018_source[year_2018_source['offense_team'] == offense_team]
        print(f"   {offense_team} 2018 records: {len(offense_2018)}")
        if not offense_2018.empty:
            print(f"   {offense_team} 2018 receivingYardsWR mean: {offense_2018['receivingYardsWR'].mean()}")
    
    print("\n✅ Investigation complete!")

if __name__ == "__main__":
    investigate_issues()

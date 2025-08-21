#!/usr/bin/env python3
"""
Defense Fantasy Rankings 2024

This script ranks defenses week-by-week for 2024 based on fantasy points allowed
compared to expected fantasy points. Uses leave-one-out baseline calculation
and ranks defenses from stingiest (1st place) to most generous (last place).

Fantasy points are calculated using the scoring rules from SCORING_RULES.md.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
INPUT_PATH = "data/fantasy_weekly_stats_complete.parquet"
OUTPUT_PATH = "data/defense_fantasy_rankings_2024.parquet"
OUTPUT_CSV_PATH = "data/defense_fantasy_rankings_2024.csv"

# Fantasy scoring rules (from SCORING_RULES.md)
FANTASY_SCORING = {
    # Passing
    'passingYards': 0.04,
    'passingTouchdowns': 4,
    'passing40PlusYardTD': 2,
    'passing50PlusYardTD': 3,
    'passingInterceptions': -2,
    'passing2PtConversions': 2,
    'passing300To399YardGame': 2,
    'passing400PlusYardGame': 4,
    
    # Rushing
    'rushingYards': 0.1,
    'rushingTouchdowns': 6,
    'rushing40PlusYardTD': 2,
    'rushing50PlusYardTD': 3,
    'rushing100To199YardGame': 2,
    'rushing200PlusYardGame': 4,
    
    # Receiving
    'receivingYards': 0.1,
    'receivingReceptions': 1,
    'receivingTouchdowns': 6,
    'receiving100To199YardGame': 2,
    'receiving200PlusYardGame': 4,
    
    # Kicking
    'madeExtraPoints': 1,
    'attemptedFieldGoals': -1,  # FG Missed
    'madeFieldGoalsFromUnder40': 3,
    'madeFieldGoalsFrom50Plus': 5,
    
    # Other
    'fumbles': -2,  # Fumbles lost
    'lostFumbles': -2,
}

# Position mapping for fantasy points
POSITION_STATS = {
    'QB': ['passingYards', 'passingTouchdowns', 'passing40PlusYardTD', 'passing50PlusYardTD', 
           'passingInterceptions', 'passing2PtConversions', 'passing300To399YardGame', 
           'passing400PlusYardGame', 'rushingYards', 'rushingTouchdowns', 'rushing40PlusYardTD', 
           'rushing50PlusYardTD', 'rushing100To199YardGame', 'rushing200PlusYardGame', 'fumbles'],
    'RB': ['rushingYards', 'rushingTouchdowns', 'rushing40PlusYardTD', 'rushing50PlusYardTD',
           'rushing100To199YardGame', 'rushing200PlusYardGame', 'receivingYards', 'receivingReceptions',
           'receivingTouchdowns', 'receiving100To199YardGame', 'receiving200PlusYardGame', 'fumbles'],
    'WR': ['receivingYards', 'receivingReceptions', 'receivingTouchdowns', 'receiving100To199YardGame',
           'receiving200PlusYardGame', 'rushingYards', 'rushingTouchdowns', 'rushing40PlusYardTD',
           'rushing50PlusYardTD', 'rushing100To199YardGame', 'rushing200PlusYardGame', 'fumbles'],
    'TE': ['receivingYards', 'receivingReceptions', 'receivingTouchdowns', 'receiving100To199YardGame',
           'receiving200PlusYardGame', 'rushingYards', 'rushingTouchdowns', 'rushing40PlusYardTD',
           'rushing50PlusYardTD', 'rushing100To199YardGame', 'rushing200PlusYardGame', 'fumbles'],
    'K': ['madeExtraPoints', 'attemptedFieldGoals', 'madeFieldGoalsFromUnder40', 'madeFieldGoalsFrom50Plus']
}

def calculate_fantasy_points(row):
    """Calculate fantasy points for a player based on their stats."""
    position = row['position']
    if position not in POSITION_STATS:
        return 0.0
    
    total_points = 0.0
    
    for stat in POSITION_STATS[position]:
        if stat in FANTASY_SCORING and stat in row:
            value = row[stat] or 0
            points = value * FANTASY_SCORING[stat]
            total_points += points
    
    return total_points

def load_and_prepare_data():
    """Load data and calculate fantasy points for each player."""
    print("📊 Loading player stats data...")
    df = pd.read_parquet(INPUT_PATH)
    
    # Filter for 2024 only
    df_2024 = df[df['year'] == 2024].copy()
    print(f"   Found {len(df_2024)} player-week records for 2024")
    
    # Calculate fantasy points for each player
    print("🧮 Calculating fantasy points...")
    df_2024['fantasy_points'] = df_2024.apply(calculate_fantasy_points, axis=1)
    
    # Aggregate fantasy points by defense team and position for each week
    print("📈 Aggregating fantasy points by defense...")
    defense_stats = df_2024.groupby(['year', 'week', 'nfl_opponent', 'position']).agg({
        'fantasy_points': 'sum',
        'nfl_team': 'first'  # Keep offense team for reference
    }).reset_index()
    
    # Rename columns for clarity
    defense_stats = defense_stats.rename(columns={
        'nfl_opponent': 'defense_team',
        'nfl_team': 'offense_team',
        'fantasy_points': 'fantasy_points_allowed'
    })
    
    print(f"   Created {len(defense_stats)} defense-week-position records")
    return defense_stats

def calculate_leave_one_out_baseline(df, stat_col):
    """Calculate leave-one-out baseline for fantasy points allowed."""
    print(f"🔄 Computing leave-one-out baselines for {stat_col}...")
    
    df_copy = df.copy()
    df_copy[f'expected_{stat_col}'] = np.nan
    
    total_games = len(df_copy)
    for idx, row in df_copy.iterrows():
        if idx % 100 == 0:
            print(f"   Processing game {idx+1}/{total_games}")
        
        year = row['year']
        offense_team = row['offense_team']
        week = row['week']
        position = row['position']
        
        # Get all other games for this offense team in this year and position (excluding current game)
        other_games = df_copy[
            (df_copy['year'] == year) & 
            (df_copy['offense_team'] == offense_team) & 
            (df_copy['position'] == position) &
            ~((df_copy['year'] == year) & (df_copy['offense_team'] == offense_team) & 
              (df_copy['position'] == position) & (df_copy['week'] == week))
        ]
        
        if not other_games.empty:
            mean_val = other_games[stat_col].mean()
            df_copy.at[idx, f'expected_{stat_col}'] = mean_val
    
    print("✅ Leave-one-out baselines computed!")
    return df_copy

def calculate_pi_and_rank(df, stat_col):
    """Calculate Fantasy Points Above Expected and rank defenses."""
    print(f"📊 Calculating Fantasy Points Above Expected for {stat_col}...")
    
    # Calculate Fantasy Points Above Expected
    exp_col = f'expected_{stat_col}'
    pi_col = f'fantasy_points_above_expected'  # Raw fantasy points above expected
    
    exp = df[exp_col].astype(float)
    act = df[stat_col].astype(float)
    
    # Fantasy Points Above Expected = Actual - Expected
    # Higher value means defense allowed more points than expected (worse defense = better matchup)
    fpaoe = act - exp
    
    # Handle expected == 0
    zero_mask = (exp.abs() < 1e-6)
    fpaoe = np.where(
        zero_mask,
        act,  # If expected is 0, just use actual points
        fpaoe
    )
    
    df[pi_col] = fpaoe
    
    # Calculate season-to-date FPAOE for each defense team and position
    season_fpaoe = df.groupby(['defense_team', 'position']).agg({
        pi_col: 'mean'
    }).reset_index()
    
    # Rank defenses (higher FPAOE = worse defense = better matchup = higher rank)
    season_fpaoe['rank'] = season_fpaoe.groupby('position')[pi_col].rank(method='min', ascending=False)
    
    return df, season_fpaoe

def main():
    """Main function to generate defense fantasy rankings."""
    print("🏈 Defense Fantasy Rankings 2024")
    print("=" * 50)
    
    # Load and prepare data
    df = load_and_prepare_data()
    
    if df.empty:
        print("❌ No data found for 2024")
        return
    
    # Calculate leave-one-out baselines
    df = calculate_leave_one_out_baseline(df, 'fantasy_points_allowed')
    
    # Calculate PI and rankings for each position
    all_rankings = []
    
    for position in ['QB', 'RB', 'WR', 'TE', 'K']:
        print(f"\n📊 Processing {position} position...")
        pos_data = df[df['position'] == position].copy()
        
        if not pos_data.empty:
            df_with_pi, rankings = calculate_pi_and_rank(pos_data, 'fantasy_points_allowed')
            
            # Add position info
            rankings['position'] = position
            all_rankings.append(rankings)
            
            # Show top 5 worst defenses (best matchups) for this position
            top_5 = rankings.nsmallest(5, 'rank')  # rank 1 is worst defense (best matchup)
            print(f"   Top 5 worst defenses vs {position} (best matchups):")
            for _, row in top_5.iterrows():
                print(f"     {int(row['rank'])}. {row['defense_team']} (+{row['fantasy_points_above_expected']:.1f} pts)")
    
    # Combine all rankings
    if all_rankings:
        final_rankings = pd.concat(all_rankings, ignore_index=True)
        final_rankings = final_rankings.sort_values(['position', 'rank'])
        
        # Save results
        final_rankings.to_parquet(OUTPUT_PATH, index=False)
        final_rankings.to_csv(OUTPUT_CSV_PATH, index=False)
        print(f"\n✅ Saved rankings to:")
        print(f"   {OUTPUT_PATH}")
        print(f"   {OUTPUT_CSV_PATH}")
        
        # Show overall summary
        print(f"\n📊 Overall Rankings Summary:")
        for position in ['QB', 'RB', 'WR', 'TE', 'K']:
            pos_rankings = final_rankings[final_rankings['position'] == position]
            if not pos_rankings.empty:
                worst_defense = pos_rankings.loc[pos_rankings['rank'].idxmin()]
                print(f"   Worst vs {position} (best matchup): {worst_defense['defense_team']} (+{worst_defense['fantasy_points_above_expected']:.1f} pts)")
    
    else:
        print("❌ No rankings generated")

if __name__ == "__main__":
    main()

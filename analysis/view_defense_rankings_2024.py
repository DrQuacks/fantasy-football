#!/usr/bin/env python3
"""
View Defense Fantasy Rankings 2024

This script displays the defense fantasy rankings for 2024 in various formats:
- Complete rankings by position
- Week-by-week progression
- Top/bottom defenses
"""

import pandas as pd
import numpy as np

def load_rankings():
    """Load the defense fantasy rankings."""
    try:
        rankings = pd.read_parquet("data/defense_fantasy_rankings_2024.parquet")
        return rankings
    except FileNotFoundError:
        print("❌ Rankings file not found. Please run defense_fantasy_rankings_2024.py first.")
        return None

def show_complete_rankings(rankings):
    """Show complete rankings for each position."""
    print("🏈 Complete Defense Fantasy Rankings 2024")
    print("=" * 60)
    
    for position in ['QB', 'RB', 'WR', 'TE', 'K']:
        print(f"\n📊 {position} Position Rankings:")
        print("-" * 40)
        
        pos_rankings = rankings[rankings['position'] == position].copy()
        pos_rankings = pos_rankings.sort_values('rank')
        
        if not pos_rankings.empty:
            # Filter out empty team names
            pos_rankings = pos_rankings[pos_rankings['defense_team'].str.strip() != '']
            
            print(f"{'Rank':<4} {'Team':<4} {'PI':<8} {'Description'}")
            print("-" * 40)
            
            for _, row in pos_rankings.iterrows():
                pi = row['pi_fantasy_points_allowed']
                rank = int(row['rank'])
                team = row['defense_team']
                
                # Describe the PI value
                if pi < -0.3:
                    desc = "Excellent defense"
                elif pi < -0.1:
                    desc = "Good defense"
                elif pi < 0.1:
                    desc = "Average defense"
                elif pi < 0.3:
                    desc = "Below average defense"
                else:
                    desc = "Poor defense"
                
                print(f"{rank:<4} {team:<4} {pi:<8.3f} {desc}")
        else:
            print("   No data available")

def show_week_by_week_progression():
    """Show how rankings change week by week."""
    print("\n📈 Week-by-Week Progression")
    print("=" * 60)
    
    # Load the detailed data to see week-by-week changes
    try:
        df = pd.read_parquet("data/fantasy_weekly_stats_complete.parquet")
        df_2024 = df[df['year'] == 2024].copy()
        
        # Calculate fantasy points
        # (This is a simplified version - you might want to use the full calculation)
        df_2024['fantasy_points'] = df_2024.apply(calculate_fantasy_points, axis=1)
        
        # Aggregate by defense team and position for each week
        defense_weekly = df_2024.groupby(['week', 'nfl_opponent', 'position']).agg({
            'fantasy_points': 'sum'
        }).reset_index()
        
        defense_weekly = defense_weekly.rename(columns={'nfl_opponent': 'defense_team'})
        
        # Show sample weekly data
        print("Sample weekly fantasy points allowed:")
        sample = defense_weekly[defense_weekly['position'] == 'QB'].head(10)
        print(sample[['week', 'defense_team', 'fantasy_points']])
        
    except Exception as e:
        print(f"Could not load weekly data: {e}")

def calculate_fantasy_points(row):
    """Simplified fantasy points calculation for viewing."""
    position = row['position']
    
    if position == 'QB':
        return (row.get('passingYards', 0) * 0.04 + 
                row.get('passingTouchdowns', 0) * 4 +
                row.get('rushingYards', 0) * 0.1 +
                row.get('rushingTouchdowns', 0) * 6)
    elif position == 'RB':
        return (row.get('rushingYards', 0) * 0.1 +
                row.get('rushingTouchdowns', 0) * 6 +
                row.get('receivingYards', 0) * 0.1 +
                row.get('receivingReceptions', 0) * 1)
    elif position == 'WR':
        return (row.get('receivingYards', 0) * 0.1 +
                row.get('receivingReceptions', 0) * 1 +
                row.get('receivingTouchdowns', 0) * 6)
    elif position == 'TE':
        return (row.get('receivingYards', 0) * 0.1 +
                row.get('receivingReceptions', 0) * 1 +
                row.get('receivingTouchdowns', 0) * 6)
    elif position == 'K':
        return (row.get('madeExtraPoints', 0) * 1 +
                row.get('madeFieldGoalsFromUnder40', 0) * 3)
    
    return 0

def show_team_summary(rankings):
    """Show summary by team across all positions."""
    print("\n🏆 Team Defense Summary")
    print("=" * 60)
    
    # Filter out empty team names
    clean_rankings = rankings[rankings['defense_team'].str.strip() != ''].copy()
    
    # Calculate average rank across all positions for each team
    team_summary = clean_rankings.groupby('defense_team').agg({
        'rank': 'mean',
        'pi_fantasy_points_allowed': 'mean'
    }).reset_index()
    
    team_summary = team_summary.sort_values('rank')
    
    print(f"{'Rank':<4} {'Team':<4} {'Avg Rank':<8} {'Avg PI':<8} {'Description'}")
    print("-" * 50)
    
    for _, row in team_summary.iterrows():
        avg_rank = row['rank']
        avg_pi = row['pi_fantasy_points_allowed']
        team = row['defense_team']
        
        if avg_pi < -0.2:
            desc = "Strong overall defense"
        elif avg_pi < -0.05:
            desc = "Good overall defense"
        elif avg_pi < 0.05:
            desc = "Average overall defense"
        elif avg_pi < 0.2:
            desc = "Below average overall defense"
        else:
            desc = "Weak overall defense"
        
        print(f"{int(avg_rank):<4} {team:<4} {avg_rank:<8.1f} {avg_pi:<8.3f} {desc}")

def main():
    """Main function to display rankings."""
    rankings = load_rankings()
    
    if rankings is None:
        return
    
    # Show complete rankings
    show_complete_rankings(rankings)
    
    # Show team summary
    show_team_summary(rankings)
    
    # Show week-by-week progression
    show_week_by_week_progression()
    
    print(f"\n📊 Data Summary:")
    print(f"   Total defense-position combinations: {len(rankings)}")
    print(f"   Teams with data: {rankings['defense_team'].nunique()}")
    print(f"   Positions: {', '.join(rankings['position'].unique())}")

if __name__ == "__main__":
    main()

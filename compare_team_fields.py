#!/usr/bin/env python3
"""
compare_team_fields.py

Compare player_team and nfl_team fields in fantasy_weekly_stats.csv
and generate a markdown report of any discrepancies.
"""

import pandas as pd
import numpy as np
from datetime import datetime

def compare_team_fields():
    """Compare player_team and nfl_team fields and generate discrepancy report."""
    
    # Read the CSV file
    print("Reading fantasy_weekly_stats.csv...")
    df = pd.read_csv('data/fantasy_weekly_stats.csv')
    
    # Filter out rows where either field is null/empty
    valid_teams = df[
        (df['player_team'].notna()) & 
        (df['player_team'] != '') & 
        (df['nfl_team'].notna()) & 
        (df['nfl_team'] != '')
    ].copy()
    
    # Find discrepancies
    discrepancies = valid_teams[valid_teams['player_team'] != valid_teams['nfl_team']].copy()
    
    # Generate markdown report
    report_lines = []
    report_lines.append("# Team Field Discrepancy Report")
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Summary statistics
    total_rows = len(df)
    valid_rows = len(valid_teams)
    discrepancy_rows = len(discrepancies)
    
    report_lines.append("## Summary")
    report_lines.append("")
    report_lines.append(f"- **Total rows**: {total_rows:,}")
    report_lines.append(f"- **Rows with both team fields**: {valid_rows:,}")
    report_lines.append(f"- **Discrepancy rows**: {discrepancy_rows:,}")
    report_lines.append(f"- **Discrepancy rate**: {discrepancy_rows/valid_rows*100:.2f}%")
    report_lines.append("")
    
    if discrepancy_rows == 0:
        report_lines.append("## Results")
        report_lines.append("")
        report_lines.append("✅ **No discrepancies found!** All rows have matching `player_team` and `nfl_team` values.")
        report_lines.append("")
    else:
        # Group by player and year to show patterns
        player_discrepancies = discrepancies.groupby(['name', 'year']).agg({
            'week': 'count',
            'player_team': lambda x: list(x.unique()),
            'nfl_team': lambda x: list(x.unique())
        }).reset_index()
        player_discrepancies.columns = ['name', 'year', 'discrepancy_weeks', 'player_teams', 'nfl_teams']
        
        report_lines.append("## Player-Level Discrepancies")
        report_lines.append("")
        report_lines.append("Players with team field mismatches:")
        report_lines.append("")
        
        for _, row in player_discrepancies.iterrows():
            report_lines.append(f"### {row['name']} ({row['year']})")
            report_lines.append(f"- **Weeks affected**: {row['discrepancy_weeks']}")
            report_lines.append(f"- **player_team values**: {', '.join(row['player_teams'])}")
            report_lines.append(f"- **nfl_team values**: {', '.join(row['nfl_teams'])}")
            report_lines.append("")
        
        # Show detailed weekly breakdown
        report_lines.append("## Detailed Weekly Breakdown")
        report_lines.append("")
        report_lines.append("| Player | Year | Week | Position | player_team | nfl_team | opponent |")
        report_lines.append("|--------|------|------|----------|-------------|----------|----------|")
        
        for _, row in discrepancies.iterrows():
            report_lines.append(
                f"| {row['name']} | {row['year']} | {row['week']} | {row['position']} | "
                f"{row['player_team']} | {row['nfl_team']} | {row['opponent']} |"
            )
        report_lines.append("")
        
        # Analysis by year
        report_lines.append("## Analysis by Year")
        report_lines.append("")
        year_stats = discrepancies.groupby('year').agg({
            'name': 'nunique',
            'week': 'count'
        }).reset_index()
        year_stats.columns = ['year', 'unique_players', 'total_discrepancies']
        
        report_lines.append("| Year | Unique Players | Total Discrepancies |")
        report_lines.append("|------|----------------|-------------------|")
        for _, row in year_stats.iterrows():
            report_lines.append(f"| {row['year']} | {row['unique_players']} | {row['total_discrepancies']} |")
        report_lines.append("")
        
        # Analysis by position
        report_lines.append("## Analysis by Position")
        report_lines.append("")
        pos_stats = discrepancies.groupby('position').agg({
            'name': 'nunique',
            'week': 'count'
        }).reset_index()
        pos_stats.columns = ['position', 'unique_players', 'total_discrepancies']
        
        report_lines.append("| Position | Unique Players | Total Discrepancies |")
        report_lines.append("|----------|----------------|-------------------|")
        for _, row in pos_stats.iterrows():
            report_lines.append(f"| {row['position']} | {row['unique_players']} | {row['total_discrepancies']} |")
        report_lines.append("")
    
    # Write report to file
    report_path = "team_field_discrepancies.md"
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"✅ Report generated: {report_path}")
    print(f"📊 Found {discrepancy_rows} discrepancies out of {valid_rows} valid rows")
    
    return report_path

if __name__ == "__main__":
    compare_team_fields()


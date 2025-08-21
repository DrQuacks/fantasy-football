#!/usr/bin/env python3
"""
Extract Position-Specific Datasets

This script extracts separate datasets for each position (QB, RB, WR, TE, K, DEF)
from the complete fantasy weekly stats for separate model training.

Each position will get its own parquet and CSV file with relevant features.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
INPUT_PATH = "data/fantasy_weekly_stats_complete.parquet"
OUTPUT_DIR = "data/positions"

# Position-specific stat columns (from SCORING_RULES.md)
POSITION_STATS = {
    'QB': [
        # Passing stats
        'passingYards', 'passingTouchdowns', 'passing40PlusYardTD', 'passing50PlusYardTD',
        'passingInterceptions', 'passing2PtConversions', 'passing300To399YardGame', 'passing400PlusYardGame',
        # Rushing stats (QBs can rush too)
        'rushingYards', 'rushingTouchdowns', 'rushing40PlusYardTD', 'rushing50PlusYardTD',
        'rushing100To199YardGame', 'rushing200PlusYardGame',
        # Other
        'fumbles', 'lostFumbles'
    ],
    'RB': [
        # Rushing stats
        'rushingYards', 'rushingTouchdowns', 'rushing40PlusYardTD', 'rushing50PlusYardTD',
        'rushing100To199YardGame', 'rushing200PlusYardGame',
        # Receiving stats (RBs can catch too)
        'receivingYards', 'receivingReceptions', 'receivingTouchdowns', 'receiving100To199YardGame',
        'receiving200PlusYardGame',
        # Other
        'fumbles', 'lostFumbles'
    ],
    'WR': [
        # Receiving stats
        'receivingYards', 'receivingReceptions', 'receivingTouchdowns', 'receiving100To199YardGame',
        'receiving200PlusYardGame',
        # Rushing stats (WRs can rush too)
        'rushingYards', 'rushingTouchdowns', 'rushing40PlusYardTD', 'rushing50PlusYardTD',
        'rushing100To199YardGame', 'rushing200PlusYardGame',
        # Other
        'fumbles', 'lostFumbles'
    ],
    'TE': [
        # Receiving stats
        'receivingYards', 'receivingReceptions', 'receivingTouchdowns', 'receiving100To199YardGame',
        'receiving200PlusYardGame',
        # Rushing stats (TEs can rush too)
        'rushingYards', 'rushingTouchdowns', 'rushing40PlusYardTD', 'rushing50PlusYardTD',
        'rushing100To199YardGame', 'rushing200PlusYardGame',
        # Other
        'fumbles', 'lostFumbles'
    ],
    'K': [
        # Kicking stats
        'madeExtraPoints', 'attemptedFieldGoals', 'madeFieldGoalsFromUnder40', 'madeFieldGoalsFrom50Plus'
    ]
}

# Common columns to keep for all positions
COMMON_COLS = [
    'name', 'year', 'playerId', 'week', 'points', 'projected_points', 'winLoss',
    'position', 'acquisitionType', 'nfl_team', 'nfl_opponent', 'isHome', 'date', 'time'
]

def create_output_directory():
    """Create output directory if it doesn't exist."""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {OUTPUT_DIR}")

def extract_position_data(df, position):
    """Extract data for a specific position."""
    print(f"📊 Extracting {position} data...")
    
    # Filter for position
    pos_data = df[df['position'] == position].copy()
    
    if pos_data.empty:
        print(f"   ⚠️  No data found for {position}")
        return None
    
    # Get relevant stat columns for this position
    relevant_stats = POSITION_STATS.get(position, [])
    
    # Keep common columns plus relevant stats
    columns_to_keep = COMMON_COLS + [col for col in relevant_stats if col in pos_data.columns]
    
    # Filter columns (only keep columns that exist in the data)
    available_cols = [col for col in columns_to_keep if col in pos_data.columns]
    pos_data = pos_data[available_cols]
    
    # Fill missing stat columns with 0
    for stat in relevant_stats:
        if stat not in pos_data.columns:
            pos_data[stat] = 0
    
    print(f"   ✅ {len(pos_data)} records, {len(pos_data.columns)} columns")
    return pos_data

def create_defense_dataset(df):
    """Create defense dataset by aggregating opponent stats."""
    print("📊 Creating DEF dataset...")
    
    # Group by defense team (nfl_opponent) and aggregate stats
    defense_data = df.groupby(['year', 'week', 'nfl_opponent']).agg({
        # Sum up all offensive stats allowed
        'passingYards': 'sum', 'passingTouchdowns': 'sum', 'passingInterceptions': 'sum',
        'rushingYards': 'sum', 'rushingTouchdowns': 'sum',
        'receivingYards': 'sum', 'receivingReceptions': 'sum', 'receivingTouchdowns': 'sum',
        'madeExtraPoints': 'sum', 'attemptedFieldGoals': 'sum',
        # Keep team info
        'nfl_team': 'first', 'isHome': 'first', 'date': 'first', 'time': 'first',
        # Count players
        'name': 'count'
    }).reset_index()
    
    # Rename columns for clarity
    defense_data = defense_data.rename(columns={
        'nfl_opponent': 'defense_team',
        'nfl_team': 'offense_team',
        'name': 'players_faced'
    })
    
    # Add position column
    defense_data['position'] = 'DEF'
    
    # Calculate fantasy points allowed (simplified - you might want to use the full scoring system)
    defense_data['points_allowed'] = (
        defense_data['passingYards'] * 0.04 +
        defense_data['passingTouchdowns'] * 4 +
        defense_data['passingInterceptions'] * -2 +
        defense_data['rushingYards'] * 0.1 +
        defense_data['rushingTouchdowns'] * 6 +
        defense_data['receivingYards'] * 0.1 +
        defense_data['receivingReceptions'] * 1 +
        defense_data['receivingTouchdowns'] * 6 +
        defense_data['madeExtraPoints'] * 1 +
        defense_data['attemptedFieldGoals'] * 3  # Simplified
    )
    
    print(f"   ✅ {len(defense_data)} records, {len(defense_data.columns)} columns")
    return defense_data

def save_position_data(pos_data, position):
    """Save position data to parquet and CSV files."""
    if pos_data is None or pos_data.empty:
        return
    
    # Create filenames
    parquet_file = f"{OUTPUT_DIR}/{position.lower()}_data.parquet"
    csv_file = f"{OUTPUT_DIR}/{position.lower()}_data.csv"
    
    # Save files
    pos_data.to_parquet(parquet_file, index=False)
    pos_data.to_csv(csv_file, index=False)
    
    print(f"   💾 Saved to {parquet_file}")
    print(f"   💾 Saved to {csv_file}")

def main():
    """Main function to extract position-specific datasets."""
    print("🏈 Extracting Position-Specific Datasets")
    print("=" * 50)
    
    # Create output directory
    create_output_directory()
    
    # Load complete dataset
    print("📊 Loading complete dataset...")
    df = pd.read_parquet(INPUT_PATH)
    print(f"   Loaded {len(df)} total records")
    
    # Extract data for each position
    positions = ['QB', 'RB', 'WR', 'TE', 'K']
    
    for position in positions:
        pos_data = extract_position_data(df, position)
        save_position_data(pos_data, position)
        print()
    
    # Create defense dataset
    def_data = create_defense_dataset(df)
    save_position_data(def_data, 'DEF')
    
    # Summary
    print("\n📊 Extraction Summary:")
    print("=" * 30)
    for position in positions + ['DEF']:
        parquet_file = f"{OUTPUT_DIR}/{position.lower()}_data.parquet"
        if Path(parquet_file).exists():
            pos_df = pd.read_parquet(parquet_file)
            print(f"   {position}: {len(pos_df)} records")
    
    print(f"\n✅ All position datasets saved to {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()

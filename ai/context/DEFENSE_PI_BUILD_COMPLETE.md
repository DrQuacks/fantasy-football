# Defense PI Build Process with Home/Away Distinctions

## Overview
This document describes how to build defense-adjusted Performance Index (PI) metrics that include separate home and away performance tracking. The process creates features that measure how well defenses perform relative to offensive baselines, with distinct metrics for home vs away games.

## Process Flow

### 1. Build Complete Database
First, ensure you have the complete fantasy football database with team/opponent data:

```bash
# Build the complete database (if not already done)
python3 preprocessing/build_complete_database.py

# Export to CSV/Parquet for inspection
python3 preprocessing/export_database_to_csv.py
```

### 2. Build Defense Table
Create the defense weekly stats table with home/away distinction:

```bash
python3 preprocessing/build_defense_table.py
```

**Key Features:**
- Uses `data/fantasy_weekly_stats_complete.parquet` as input
- Filters out rows with missing team information
- Includes `isHome` field for home/away distinction
- Outputs: `data/defense_weekly_stats.csv/.parquet`

### 3. Compute Defense Adjusted PI
Generate PI metrics with home/away versions:

```bash
python3 analysis/compute_defense_adjusted_metrics.py
```

**Outputs:**
- `data/defense_adjusted_pi.csv`
- `data/defense_adjusted_pi.parquet`

## Defense PI Calculation Process

### Step 1: Load and Validate Data
- Load defense weekly stats from `data/defense_weekly_stats.parquet`
- Validate required columns: `year`, `week`, `defense_team`, `offense_team`, `isHome`
- Convert stat columns to numeric, fill NaN with 0.0

### Step 2: Calculate Offensive Baselines
For each offense team and year, calculate full-season per-game averages:

```python
def offense_full_season_baseline(df: pd.DataFrame, stat_cols):
    """
    Compute full-season per-game baseline for each offense_team and year.
    Returns DataFrame indexed by (year, offense_team) with mean of stat_cols.
    """
    base = (
        df[["year", "offense_team"] + stat_cols]
        .groupby(["year", "offense_team"], as_index=False)
        .mean(numeric_only=True)
    )
    base = base.set_index(["year", "offense_team"])
    base.columns = [f"expected_{c}" for c in base.columns]
    return base
```

### Step 3: Calculate Per-Game PI
For each game, compute PI = (Expected - Actual) / Expected:

```python
def per_game_pi(df: pd.DataFrame, stat_cols):
    """
    For each row/game and stat, compute PI = (Expected - Actual) / Expected.
    If Expected == 0: PI = 0 if Actual == 0 else -1
    """
    for c in stat_cols:
        exp_col = f"expected_{c}"
        pi_col = f"pi_{c}"
        
        exp = df[exp_col].astype(float)
        act = df[c].astype(float)
        
        # Standard PI with safety epsilon
        pi = (exp - act) / (exp + EPS)
        
        # Handle expected == 0 cleanly
        zero_mask = (exp.abs() < EPS)
        pi = np.where(
            zero_mask,
            np.where(act.abs() < EPS, 0.0, -1.0),
            pi
        )
        df[pi_col] = pi
    
    return df
```

### Step 4: Aggregate PI Metrics
Create three types of aggregated PI metrics:

#### A. Last Week (Most Recent Game)
```python
def last_week(df: pd.DataFrame, stat_cols):
    """
    For each (year, defense_team), take only the most recent week.
    Creates: pi_last1_*, pi_last1_home_*, pi_last1_away_*
    """
```

#### B. Last K Weeks (Rolling Window)
```python
def last_k_weeks(df: pd.DataFrame, k: int, stat_cols):
    """
    For each (year, defense_team), take its last k games.
    Creates: pi_last{k}_*, pi_last{k}_home_*, pi_last{k}_away_*
    """
```

#### C. Season to Date (Full Season)
```python
def season_to_date(df: pd.DataFrame, stat_cols):
    """
    Average PI over all games per (year, defense_team).
    Creates: pi_season_*, pi_season_home_*, pi_season_away_*
    """
```

## Feature Naming Convention

### Original Features (All Games Combined)
- `pi_last1_receivingYardsWR` - Last game PI for WR receiving yards
- `pi_last4_receivingYardsWR` - Last 4 games PI for WR receiving yards  
- `pi_season_receivingYardsWR` - Season average PI for WR receiving yards

### New Home/Away Features
- `pi_last1_home_receivingYardsWR` - Last home game PI for WR receiving yards
- `pi_last1_away_receivingYardsWR` - Last away game PI for WR receiving yards
- `pi_last4_home_receivingYardsWR` - Last 4 home games PI for WR receiving yards
- `pi_last4_away_receivingYardsWR` - Last 4 away games PI for WR receiving yards
- `pi_season_home_receivingYardsWR` - Season home games PI for WR receiving yards
- `pi_season_away_receivingYardsWR` - Season away games PI for WR receiving yards

## Stat Categories Included

### Receiving Stats (WR, RB, TE)
- `receivingYards`, `receivingReceptions`, `receivingTouchdowns`
- `receivingTargets`, `receivingYardsAfterCatch`
- `receiving100To199YardGame`, `receiving200PlusYardGame`

### Rushing Stats (RB, QB, WR, TE)
- `rushingYards`, `rushingTouchdowns`, `rushingAttempts`
- `rushing40PlusYardTD`, `rushing50PlusYardTD`
- `rushing100To199YardGame`, `rushing200PlusYardGame`

### Passing Stats (QB only)
- `passingYards`, `passingTouchdowns`, `passingInterceptions`
- `passingAttempts`, `passingCompletions`, `passingIncompletions`
- `passing40PlusYardTD`, `passing50PlusYardTD`
- `passing300To399YardGame`, `passing400PlusYardGame`, `passing2PtConversions`

### Kicking Stats (K only)
- `madeFieldGoals`, `attemptedFieldGoals`, `madeExtraPoints`, `attemptedExtraPoints`
- `madeFieldGoalsFrom50Plus`, `attemptedFieldGoalsFrom50Plus`
- `madeFieldGoalsFromUnder40`, `attemptedFieldGoalsFromUnder40`

## Data Quality Considerations

### Filtering Empty Teams
The defense table building process filters out rows with missing team information:
```python
# Filter out rows with missing team information
df = df.dropna(subset=['nfl_team', 'nfl_opponent'])
df = df[(df['nfl_team'] != '') & (df['nfl_opponent'] != '')]
```

### Handling Missing Data
- PI calculation uses epsilon (1e-6) for numerical stability
- Expected values of 0 are handled specially
- Missing PI values are filled with NaN (left as missing)

### Home/Away Aggregation
- Some teams may not have both home and away games in certain windows
- Missing home/away features are left as NaN
- Overall features (without home/away suffix) always include all games

## Output Schema

### Final Defense PI Table
Each row represents a defense team in a specific year with features:

**Identifier Columns:**
- `year` - Season year
- `defense_team` - Team abbreviation (e.g., "ARI", "BAL")

**Feature Columns (3x per stat category):**
- `pi_last1_*` - Last game performance
- `pi_last4_*` - Last 4 games average
- `pi_season_*` - Full season average

**Home/Away Variants (2x per feature):**
- `pi_last1_home_*` - Last home game
- `pi_last1_away_*` - Last away game
- `pi_last4_home_*` - Last 4 home games
- `pi_last4_away_*` - Last 4 away games
- `pi_season_home_*` - Season home games
- `pi_season_away_*` - Season away games

## Usage Examples

### Load the Data
```python
import pandas as pd

# Load defense PI data
df = pd.read_parquet("data/defense_adjusted_pi.parquet")

# View available features
print([col for col in df.columns if col.startswith("pi_last4_home_")])
```

### Analyze Home vs Away Performance
```python
# Compare home vs away rushing defense
home_rush = df["pi_season_home_rushingYardsRB"]
away_rush = df["pi_season_away_rushingYardsRB"]

# Positive PI = defense is good (allowing fewer yards than expected)
# Negative PI = defense is poor (allowing more yards than expected)
```

### Feature Engineering for ML
```python
# Create home field advantage feature
df["home_advantage_rush"] = df["pi_season_home_rushingYardsRB"] - df["pi_season_away_rushingYardsRB"]

# Recent form (last 4 games vs season)
df["recent_form_rush"] = df["pi_last4_rushingYardsRB"] - df["pi_season_rushingYardsRB"]
```

## Dependencies

```python
import pandas as pd
import numpy as np
from pathlib import Path
```

## Configuration

### Input/Output Paths
```python
INPUT_PATH = "data/defense_weekly_stats.parquet"
OUTPUT_CSV = "data/defense_adjusted_pi.csv"
OUTPUT_PARQUET = "data/defense_adjusted_pi.parquet"
```

### Key Parameters
```python
EXCLUDE_CURRENT_GAME = False  # Whether to exclude current game from baseline
EPS = 1e-6  # Numerical stability for PI calculations
```

## Troubleshooting

### Common Issues
1. **Missing team data**: Ensure defense table was built with proper filtering
2. **Empty PI values**: Check that offensive baselines are calculated correctly
3. **Missing home/away features**: Some teams may not have both home and away games

### Validation
- Verify that PI values are reasonable (typically between -1 and 1)
- Check that home/away features are populated for teams with both types of games
- Ensure no duplicate (year, defense_team) combinations

This process creates a comprehensive set of defense performance metrics that can be used for fantasy football analysis and machine learning models, with the added benefit of distinguishing between home and away defensive performance.

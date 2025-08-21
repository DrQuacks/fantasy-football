# Fantasy Football Dataset Documentation

## Project Overview

This is a fantasy football machine learning project that analyzes player performance data from ESPN's fantasy football API. The project contains comprehensive player statistics from 2019-2024, including both rostered players and free agents, with weekly performance data enriched with team/opponent information.

## File Structure

```
fantasy-football/
├── data/
│   ├── fantasy_weekly_stats_complete.parquet    # Complete player dataset (74,991 records)
│   ├── fantasy_weekly_stats_complete.csv        # CSV version of complete dataset
│   ├── defense_weekly_stats.parquet             # Defense vs offense weekly stats (43,325 records)
│   ├── defense_adjusted_pi.parquet              # Defense Performance Index calculations (193 records)
│   ├── defense_adjusted_pi.csv                  # CSV version of defense PI
│   ├── defense_fantasy_rankings_2024.parquet    # 2024 defense fantasy rankings
│   ├── defense_fantasy_rankings_2024.csv        # CSV version of 2024 rankings
│   └── positions/                               # Position-specific datasets
│       ├── qb_data.parquet                      # Quarterback dataset (9,745 records)
│       ├── qb_data.csv
│       ├── rb_data.parquet                      # Running back dataset (17,916 records)
│       ├── rb_data.csv
│       ├── wr_data.parquet                      # Wide receiver dataset (25,886 records)
│       ├── wr_data.csv
│       ├── te_data.parquet                      # Tight end dataset (14,773 records)
│       ├── te_data.csv
│       ├── k_data.parquet                       # Kicker dataset (3,888 records)
│       ├── k_data.csv
│       ├── def_data.parquet                     # Defense dataset (3,284 records)
│       └── def_data.csv
├── preprocessing/                               # Data processing scripts
├── analysis/                                    # Analysis and ranking scripts
├── ml/                                         # Machine learning models
├── utils/                                      # Utility scripts
└── docs/                                       # Documentation
```

## Dataset Details

### 1. Complete Player Dataset (`fantasy_weekly_stats_complete.parquet`)

**Purpose**: Master dataset containing all player weekly performance data
**Records**: 74,991 player-week combinations
**Years**: 2019-2024
**Source**: ESPN Fantasy API + ESPN Gamelog API

**Key Columns**:
| Column | Data Type | Description |
|--------|-----------|-------------|
| `name` | string | Player's full name |
| `year` | int64 | NFL season year |
| `playerId` | int64 | ESPN player ID |
| `week` | int64 | NFL week (1-18) |
| `points` | float64 | Actual fantasy points scored |
| `projected_points` | float64 | ESPN's projected fantasy points |
| `winLoss` | int64 | Team win/loss (1=win, 0=loss) |
| `position` | string | Player position (QB, RB, WR, TE, K) |
| `acquisitionType` | string | How player was acquired (rostered, free_agent) |
| `nfl_team` | string | Player's NFL team abbreviation |
| `nfl_opponent` | string | Opponent team abbreviation |
| `isHome` | bool | Whether player's team is home |
| `date` | string | Game date (YYYY-MM-DD) |
| `time` | string | Game time (HH:MM:SS) |

**Statistical Columns** (all float64):
- **Passing**: `passingYards`, `passingTouchdowns`, `passingInterceptions`, `passing40PlusYardTD`, `passing50PlusYardTD`, `passing300To399YardGame`, `passing400PlusYardGame`, `passing2PtConversions`, `passingCompletionPercentage`
- **Rushing**: `rushingYards`, `rushingTouchdowns`, `rushing40PlusYardTD`, `rushing50PlusYardTD`, `rushing100To199YardGame`, `rushing200PlusYardGame`, `rushingYardsPerAttempt`
- **Receiving**: `receivingYards`, `receivingReceptions`, `receivingTouchdowns`, `receivingTargets`, `receivingYardsAfterCatch`, `receivingYardsPerReception`, `receiving100To199YardGame`, `receiving200PlusYardGame`
- **Kicking**: `madeExtraPoints`, `attemptedFieldGoals`, `madeFieldGoalsFromUnder40`, `madeFieldGoalsFrom50Plus`
- **Other**: `fumbles`, `lostFumbles`, `turnovers`, `pointsScored`

### 2. Defense Weekly Stats (`defense_weekly_stats.parquet`)

**Purpose**: Aggregated weekly defensive performance against each position
**Records**: 43,325 defense-week-position combinations
**Structure**: Each row represents how a defense performed against a specific position in a specific week

**Key Columns**:
| Column | Data Type | Description |
|--------|-----------|-------------|
| `year` | int64 | NFL season year |
| `week` | int64 | NFL week |
| `defense_team` | string | Defensive team abbreviation |
| `offense_team` | string | Offensive team abbreviation |
| `isHome` | bool | Whether defense was home team |

**Statistical Columns** (all float64, aggregated by position):
- **QB stats allowed**: `passingYardsQB`, `passingTouchdownsQB`, `passingInterceptionsQB`, etc.
- **RB stats allowed**: `rushingYardsRB`, `rushingTouchdownsRB`, `receivingYardsRB`, etc.
- **WR stats allowed**: `receivingYardsWR`, `receivingReceptionsWR`, `receivingTouchdownsWR`, etc.
- **TE stats allowed**: `receivingYardsTE`, `receivingReceptionsTE`, `receivingTouchdownsTE`, etc.
- **K stats allowed**: `madeFieldGoalsK`, `attemptedFieldGoalsK`, `madeExtraPointsK`, etc.

### 3. Defense Adjusted PI (`defense_adjusted_pi.parquet`)

**Purpose**: Performance Index calculations showing how defenses perform vs expected
**Records**: 193 defense team-year combinations
**Method**: Leave-one-out baseline calculation with extensive home/away breakdowns

**Key Columns**:
| Column | Data Type | Description |
|--------|-----------|-------------|
| `year` | int64 | NFL season year |
| `defense_team` | string | Defensive team abbreviation |

**PI Column Structure** (all float64):
The table contains Performance Index values for different time windows and game contexts:

**Time Windows**:
- `pi_last1_*` - Last game performance
- `pi_last4_*` - Last 4 games performance  
- `pi_season_*` - Full season performance

**Game Contexts**:
- `pi_[timewindow]_[stat][position]` - Overall performance
- `pi_[timewindow]_home_[stat][position]` - Home game performance only
- `pi_[timewindow]_away_[stat][position]` - Away game performance only

**Example Columns**:
- `pi_season_receivingYardsWR` - Season PI for WR receiving yards (all games)
- `pi_season_home_receivingYardsWR` - Season PI for WR receiving yards (home games only)
- `pi_season_away_receivingYardsWR` - Season PI for WR receiving yards (away games only)
- `pi_last4_passingYardsQB` - Last 4 games PI for QB passing yards
- `pi_last4_home_passingYardsQB` - Last 4 games PI for QB passing yards (home games only)
- `pi_last4_away_passingYardsQB` - Last 4 games PI for QB passing yards (away games only)

**PI Interpretation**: 
- Positive PI = Defense allowed fewer points than expected (good defense)
- Negative PI = Defense allowed more points than expected (bad defense)

**Total Columns**: ~600+ columns covering all positions, stats, time windows, and home/away contexts

### 4. Defense Fantasy Rankings 2024 (`defense_fantasy_rankings_2024.parquet`)

**Purpose**: 2024 defense rankings based on fantasy points allowed vs expected
**Records**: Varies by position
**Method**: Fantasy Points Above Expected (FPAOE) calculation

**Key Columns**:
| Column | Data Type | Description |
|--------|-----------|-------------|
| `defense_team` | string | Defensive team abbreviation |
| `position` | string | Position (QB, RB, WR, TE, K) |
| `fantasy_points_above_expected` | float64 | Raw fantasy points above expected |
| `rank` | float64 | Ranking (1 = worst defense, best matchup) |

**Interpretation**: Higher FPAOE = worse defense = better matchup for fantasy players

### 5. Position-Specific Datasets (`data/positions/`)

Each position dataset contains only relevant statistical columns for that position:

#### QB Dataset (`qb_data.parquet`)
**Records**: 9,745
**Key Stats**: All passing stats + rushing stats (QBs can rush)

#### RB Dataset (`rb_data.parquet`)
**Records**: 17,916
**Key Stats**: All rushing stats + receiving stats (RBs can catch)

#### WR Dataset (`wr_data.parquet`)
**Records**: 25,886
**Key Stats**: All receiving stats + rushing stats (WRs can rush)

#### TE Dataset (`te_data.parquet`)
**Records**: 14,773
**Key Stats**: All receiving stats + rushing stats (TEs can rush)

#### K Dataset (`k_data.parquet`)
**Records**: 3,888
**Key Stats**: All kicking stats only

#### DEF Dataset (`def_data.parquet`)
**Records**: 3,284
**Key Stats**: Aggregated offensive stats allowed by each defense team

## Fantasy Scoring System

The project uses standard ESPN fantasy scoring:

**Passing**: 0.04 pts/yard, 4 pts/TD, -2 pts/interception
**Rushing**: 0.1 pts/yard, 6 pts/TD
**Receiving**: 0.1 pts/yard, 1 pt/reception, 6 pts/TD
**Kicking**: 1 pt/extra point, 3 pts/field goal (0-39 yds), 4 pts/field goal (40-49 yds), 5 pts/field goal (50+ yds)

## Data Quality Notes

- **Missing Values**: Most statistical columns use 0 for missing values
- **Team Names**: Some records may have empty team names (""), indicating data quality issues
- **Position Overlap**: Players can have stats from multiple positions (e.g., QBs with rushing stats)
- **Acquisition Type**: Distinguishes between rostered players and free agents
- **Date Range**: Covers NFL regular seasons 2019-2024 (weeks 1-18)

## Machine Learning Considerations

- **Separate Models**: Position-specific datasets enable training separate models for each position
- **Feature Engineering**: Rich statistical features available for each position
- **Temporal Data**: Weekly data structure supports time-series analysis
- **Target Variable**: `points` column serves as the primary target for prediction
- **Baseline**: `projected_points` provides ESPN's baseline predictions for comparison
- **Home/Away Context**: Defense PI table provides extensive home/away performance breakdowns for matchup analysis

## Usage Recommendations

1. **Start with position-specific datasets** for focused model training
2. **Use complete dataset** for cross-position analysis or feature engineering
3. **Leverage defense rankings** for matchup-based features
4. **Consider temporal aspects** when designing features (week-to-week trends)
5. **Handle missing data** appropriately (most stats default to 0)
6. **Use home/away PI columns** for more nuanced defense performance analysis
7. **Combine multiple time windows** (last1, last4, season) for comprehensive defense evaluation

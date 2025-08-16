# Fantasy Football Database - Clean

A clean, simple repository to build a complete fantasy football database with all players and their stats.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure MongoDB is running locally

## Usage

Run the single script to build the complete database:

```bash
python build_database.py
```

This will:
- Clear any existing data
- Fetch all rostered players and free agents from ESPN (2019-2024)
- Get stats for all players
- Build the MongoDB database
- Export to CSV and Parquet files

## Output

- `fantasy_weekly_stats.csv` - Complete dataset
- `fantasy_weekly_stats.parquet` - Complete dataset (Parquet format)

## What's Included

- All players (rostered + free agents) with actual stats
- QB, RB, WR, TE, K positions
- Years 2019-2024
- No problematic columns (player_team, opponent, team_week_key removed)


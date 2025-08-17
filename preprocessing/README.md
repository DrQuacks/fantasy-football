# Data Preprocessing Scripts

This directory contains scripts for cleaning, transforming, and preparing raw data for analysis and machine learning.

## Files:

### Database Operations
- **`build_complete_database.py`** - **NEW**: Comprehensive database builder that combines all functionality
- **`build_database.py`** - Main script to build the fantasy football database
- **`rebuild_table_clean.py`** - Clean rebuild of database tables
- **`createTable.py`** - Database table creation utilities

### Data Cleaning & Fixes
- **`fix_missing_stats.py`** - Fix missing statistics in the dataset
- **`add_free_agents.py`** - Add free agent data to the database
- **`backfill_player_team_from_defense.py`** - Backfill player team information from defense data

## Usage:

### Recommended: Use the Complete Database Builder
```bash
python preprocessing/build_complete_database.py
```

This new script combines all functionality:
1. Fetches all rostered players from ESPN
2. Fetches all free agents from ESPN
3. Enriches data with team/opponent information via ESPN gamelog
4. Runs built-in data quality tests
5. Generates a comprehensive report

### Legacy Process (if needed):
These scripts should be run in order when setting up the database:
1. `createTable.py` - Create database structure
2. `build_database.py` - Build initial database
3. `fix_missing_stats.py` - Clean up missing data
4. `add_free_agents.py` - Add additional player data
5. `backfill_player_team_from_defense.py` - Complete team information

## Data Quality Tests

The `build_complete_database.py` script includes automated tests:
- David Moore 2019 receiving stats verification
- Greg Olsen 2019 team assignment verification
- Christian McCaffrey 2022 week 6 team verification
- Christian McCaffrey 2023 week 7 team verification (team change)

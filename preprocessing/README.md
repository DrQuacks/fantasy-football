# Data Preprocessing Scripts

This directory contains scripts for cleaning, transforming, and preparing raw data for analysis and machine learning.

## Files:

### Database Operations
- **`build_database.py`** - Main script to build the fantasy football database
- **`rebuild_table_clean.py`** - Clean rebuild of database tables
- **`createTable.py`** - Database table creation utilities

### Data Cleaning & Fixes
- **`fix_missing_stats.py`** - Fix missing statistics in the dataset
- **`add_free_agents.py`** - Add free agent data to the database
- **`backfill_player_team_from_defense.py`** - Backfill player team information from defense data

## Usage:
These scripts should be run in order when setting up the database:
1. `createTable.py` - Create database structure
2. `build_database.py` - Build initial database
3. `fix_missing_stats.py` - Clean up missing data
4. `add_free_agents.py` - Add additional player data
5. `backfill_player_team_from_defense.py` - Complete team information

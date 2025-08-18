# Complete Fantasy Football Database Build Guide

## Overview
This document describes how to build a comprehensive fantasy football database that combines rostered players, free agents, and enriched weekly stats with team/opponent information from ESPN APIs.

## Recent Improvements (August 2024)
- **Enhanced Free Agent Collection**: Increased free agent fetch size from 100 to 800 per position to capture all players
- **Data Completeness**: Now includes players like Malik Turner who were previously missing due to limited free agent fetching
- **Improved PI Calculation**: Implemented leave-one-out baseline calculation to prevent data leakage
- **Home/Away Distinction**: Added separate home and away performance tracking in defense PI metrics

## Database Schema

### MongoDB Collection: `player_stats`
Each document represents a player's complete season data:

```json
{
  "_id": ObjectId,
  "name": "Player Name",
  "year": 2022,
  "playerId": 12345,
  "position": "WR",
  "acquisitionType": "add" | "drop" | "roster",
  "stats": {
    // Season aggregate stats
  },
  "weekly_stats": {
    "1": {
      "points": 15.2,
      "projected_points": 12.5,
      "breakdown": {
        "receivingYards": 120,
        "receivingReceptions": 8,
        "receivingTouchdowns": 1,
        // ... all stat categories
      },
      "nfl_team": "CAR",
      "nfl_opponent": "ATL", 
      "isHome": true,
      "date": "2022-09-11",
      "time": "13:00"
    }
    // ... weeks 2-18
  }
}
```

## Key Components

### 1. ESPN Fantasy API Integration
- **League Setup**: Uses `espn_api.football.League` with league ID and year
- **Rostered Players**: `league.box_scores()` to get all rostered players
- **Free Agents**: `league.free_agents(size=800, position=pos)` to get all unrostered players (increased from 100 to 800)
- **Player Details**: `league.player_info(player_id)` for detailed stats

### 2. ESPN Gamelog API Integration
- **Endpoint**: `https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/athletes/{player_id}/gamelog`
- **Purpose**: Enriches weekly stats with team/opponent information
- **Headers**: Requires `User-Agent: Mozilla/5.0` for proper API access
- **Data Structure**: Returns game events with team/opponent context

### 3. Stat Key Mapping
ESPN uses numeric keys for stats. Must map to readable names:

```python
PLAYER_STATS_MAP = {
    "0": "passingAttempts",
    "1": "passingCompletions", 
    "2": "passingIncompletions",
    "3": "passingYards",
    "4": "passingTouchdowns",
    "5": "passingInterceptions",
    "6": "passing40PlusYardTD",
    "7": "passing50PlusYardTD",
    "8": "passing300To399YardGame",
    "9": "passing400PlusYardGame",
    "10": "passing2PtConversions",
    "11": "passingCompletionPercentage",
    "20": "rushingAttempts",
    "21": "rushingYards",
    "22": "rushing40PlusYardTD",
    "23": "rushing50PlusYardTD",
    "24": "rushing100To199YardGame",
    "25": "rushing200PlusYardGame",
    "26": "rushingTouchdowns",
    "27": "rushingYardsPerAttempt",
    "28": "passingTimesSacked",
    "29": "fumbles",
    "30": "lostFumbles",
    "31": "turnovers",
    "40": "receivingReceptions",
    "41": "receivingYards",
    "42": "receivingTouchdowns",
    "43": "receivingTargets",
    "44": "receivingYardsAfterCatch",
    "45": "receivingYardsPerReception",
    "46": "receiving100To199YardGame",
    "47": "receiving200PlusYardGame",
    "50": "madeFieldGoalsFrom50Plus",
    "51": "attemptedFieldGoalsFrom50Plus",
    "52": "madeFieldGoalsFromUnder40",
    "53": "attemptedFieldGoalsFromUnder40",
    "54": "madeFieldGoals",
    "55": "attemptedFieldGoals",
    "56": "madeExtraPoints",
    "57": "attemptedExtraPoints",
    "58": "pointsScored"
}
```

## Core Functions Required

### 1. Data Fetching Functions
```python
def fetch_rostered_players(league, year):
    """Get all rostered players from ESPN Fantasy API"""
    
def fetch_free_agents(league, year):
    """Get all free agents from ESPN Fantasy API"""
    
def fetch_player_stats(player_id, year):
    """Get detailed player stats using league.player_info()"""
    
def fetch_gamelog(player_id, year):
    """Get team/opponent data from ESPN Gamelog API"""
```

### 2. Data Processing Functions
```python
def process_player_stats(stats_obj):
    """Extract and map weekly stats from ESPN stats object"""
    
def extract_week_info(gamelog_data):
    """Extract team/opponent info from gamelog API response"""
    
def enrich_weekly_stats(weekly_stats, gamelog_data):
    """Add team/opponent data to weekly stats"""
```

### 3. Database Functions
```python
def build_complete_database(start_year, end_year, database_name, collection_name):
    """Main function to build complete database"""
    
def export_to_csv():
    """Export database to CSV/Parquet for inspection"""
```

## Process Flow

1. **Initialize MongoDB Connection**
   - Connect to local MongoDB instance
   - Use database: `fantasy_football_complete`
   - Use collection: `player_stats`

2. **Fetch Rostered Players**
   - Get all teams from `league.box_scores()`
   - Extract players from each team's roster
   - Mark as `acquisitionType: "roster"`

3. **Fetch Free Agents**
   - Get all free agents from `league.free_agents()`
   - Mark as `acquisitionType: "add"`

4. **Process Each Player**
   - Get detailed stats via `league.player_info(player_id)`
   - Extract season and weekly stats
   - Map numeric stat keys to readable names
   - Fetch gamelog data for team/opponent enrichment
   - Merge gamelog data with weekly stats

5. **Database Write**
   - Use `UpdateOne` with `upsert=True` for each player
   - Execute bulk writes for efficiency
   - Handle rate limiting (0.1s delay between players)

6. **Export to CSV/Parquet**
   - Flatten weekly stats into rows (one per player per week)
   - Include all stat categories and metadata
   - Save to `data/fantasy_weekly_stats_complete.csv/.parquet`

## Data Quality Tests

Implement these tests to verify data integrity:

```python
def test_david_moore_2019():
    """Test: David Moore has non-zero receiving stats in 2019"""
    
def test_greg_olsen_2019():
    """Test: Greg Olsen is on Carolina and has receiving stats in 2019"""
    
def test_mccaffrey_carolina_2022():
    """Test: Christian McCaffrey is on Carolina in week 6, 2022"""
    
def test_mccaffrey_sanfran_2022():
    """Test: Christian McCaffrey is on San Francisco in week 7, 2022"""
```

## Command Line Interface

```bash
# Build database with default settings (2019-2024)
python3 preprocessing/build_complete_database.py

# Build specific year range
python3 preprocessing/build_complete_database.py --start-year 2020 --end-year 2023

# Use custom database name
python3 preprocessing/build_complete_database.py --database my_fantasy_db

# Dry run (no database writes)
python3 preprocessing/build_complete_database.py --dry-run

# Test only (run tests against existing database)
python3 preprocessing/build_complete_database.py --test-only

# Save dry run to temporary database for testing
python3 preprocessing/build_complete_database.py --save-dry-run
```

## Key Implementation Details

### Rate Limiting
- 0.1 second delay between player API calls
- Use `time.sleep()` to avoid overwhelming ESPN APIs

### Error Handling
- Try/catch blocks around individual player processing
- Continue processing if one player fails
- Log errors but don't stop entire process

### Data Validation
- Skip week 0 (season aggregates)
- Validate numeric week values
- Handle missing or null stat values

### Memory Management
- Process players in batches
- Use bulk writes for database efficiency
- Close MongoDB connections properly

## Output Files

### Database
- **MongoDB**: `fantasy_football_complete.player_stats`
- **Documents**: ~6,600+ player documents (increased from ~3,700)
- **Total Rows**: ~75,000 weekly stat rows (increased from ~55,000)

### Export Files
- **CSV**: `data/fantasy_weekly_stats_complete.csv`
- **Parquet**: `data/fantasy_weekly_stats_complete.parquet`
- **Report**: `docs/complete_database_build_report.md`

## Dependencies

```python
import os
import time
import logging
import argparse
from datetime import datetime
from pymongo import MongoClient, UpdateOne
from espn_api.football import League
import requests
import pandas as pd
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
```

## Environment Setup

1. **MongoDB**: Local instance running on `mongodb://localhost:27017/`
2. **Python**: Virtual environment with required packages
3. **ESPN API**: No authentication required for public data
4. **Rate Limiting**: Respect ESPN API limits

## Data Completeness Improvements

### Enhanced Free Agent Collection
- **Previous Issue**: Only fetched 100 free agents per position, missing players like Malik Turner
- **Solution**: Increased to 800 free agents per position
- **Impact**: Now captures all fantasy-relevant players, improving data completeness

### Leave-One-Out PI Calculation
- **Previous Issue**: Included current game in offensive baseline, causing data leakage
- **Solution**: Implemented leave-one-out baseline calculation
- **Impact**: More accurate PI values that don't suffer from circular reference bias

## Troubleshooting

### Common Issues
- **API Rate Limits**: Increase delay between requests
- **Missing Players**: Check ESPN API availability and free agent fetch size (should be 800 per position)
- **Database Connection**: Verify MongoDB is running
- **Memory Issues**: Process smaller year ranges

### Debugging
- Use `--dry-run` to test without database writes
- Use `--test-only` to verify existing data
- Check logs for specific player failures
- Validate CSV export for data completeness

This guide provides everything needed to reproduce the complete fantasy football database build process from scratch.

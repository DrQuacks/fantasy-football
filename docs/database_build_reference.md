# Fantasy Football Database Build Reference

This document serves as a reference for building and maintaining the fantasy football database.

## Overview

The database contains fantasy football player data from ESPN API for years 2019-2024, including:
- All rostered players from fantasy leagues
- All free agents available in ESPN
- Weekly statistics with team/opponent information
- Season statistics and projections
- Properly mapped ESPN API stats (numeric keys converted to readable names)

## Database Structure

### MongoDB Collection: `player_stats`

Each document contains:
```json
{
  "_id": "ObjectId",
  "name": "Player Name",
  "year": 2023,
  "playerId": 12345,
  "position": "RB",
  "acquisitionType": "rostered" | "free_agent",
  "season_stats": {
    "total_points": 150.5,
    "avg_points": 8.8,
    // ... other season totals
  },
  "weekly_stats": {
    "1": {
      "points": 12.5,
      "avg_points": 12.5,
      "projected_points": 10.2,
      "breakdown": {
        "rushing_yards": 85,
        "rushing_touchdowns": 1,
        "receiving_receptions": 3,
        "receiving_yards": 25,
        "receiving_targets": 5,
        "team_win": 1
        // ... other mapped stats
      },
      "projected_breakdown": {
        // ... projected stats with same mapping
      },
      "projected_avg_points": 0,
      "nfl_team": "CAR",
      "nfl_opponent": "ATL",
      "isHome": true,
      "date": "2023-09-10",
      "time": "13:00:00"
    }
    // ... weeks 2-18
  },
  "added_date": "2024-01-15T10:30:00"
}
```

## Scripts

### Primary Script: `build_complete_database.py`

**Purpose**: Creates a complete fantasy football database from scratch

**What it does**:
1. **Fetches rostered players**: Gets all players from fantasy league rosters (weeks 1-18)
2. **Fetches free agents**: Gets all available free agents for QB, RB, WR, TE, K positions
3. **Combines unique players**: Merges rostered and free agent lists
4. **Processes player stats**: Extracts season and weekly statistics with proper ESPN API mapping
5. **Enriches with gamelog data**: Adds team/opponent information via ESPN gamelog API
6. **Writes to MongoDB**: Stores all data in organized structure
7. **Runs quality tests**: Verifies data integrity

**Key Features**:
- **Proper ESPN API Integration**: Uses correct gamelog endpoint and data structure
- **Stats Mapping**: Converts ESPN's numeric stat keys to readable names (e.g., 41 → "receivingReceptions")
- **Team/Opponent Data**: Enriches weekly stats with NFL team assignments via gamelog API
- **Safe Database Naming**: Won't overwrite existing databases
- **Comprehensive Testing**: Built-in data quality tests

**Usage**:
```bash
# Basic usage (creates fantasy_football_complete database)
python preprocessing/build_complete_database.py

# With custom database name
python preprocessing/build_complete_database.py --database my_fantasy_db

# With suffix to avoid conflicts
python preprocessing/build_complete_database.py --suffix v2

# Dry run with temporary database for testing
python preprocessing/build_complete_database.py --dry-run --save-dry-run

# Test only against existing database
python preprocessing/build_complete_database.py --test-only

# Custom year range
python preprocessing/build_complete_database.py --start-year 2020 --end-year 2023

# Skip tests
python preprocessing/build_complete_database.py --skip-tests
```

**Arguments**:
- `--start-year`: Start year (default: 2019)
- `--end-year`: End year (default: 2024)
- `--database`: MongoDB database name (default: fantasy_football_complete)
- `--collection`: MongoDB collection name (default: player_stats)
- `--suffix`: Optional suffix for database name (e.g., _v2, _test)
- `--rate-delay`: Delay between API calls in seconds (default: 0.5)
- `--skip-tests`: Skip running data quality tests
- `--test-only`: Only run tests against existing database (no data fetching)
- `--dry-run`: Dry run - don't write to database
- `--save-dry-run`: Save dry run data to temporary database for testing

### Legacy Scripts (for reference)

- **`createTable.py`**: Original script that only fetched rostered players
- **`add_free_agents.py`**: Script to add free agents to existing database
- **`build_database.py`**: Comprehensive script that combined rostered + free agents
- **`augment_weekly_team_opponent.py`**: Script to add team/opponent data to existing players

## ESPN API Integration

### Stats Mapping

The script properly maps ESPN's numeric stat keys to readable names:

```python
PLAYER_STATS_MAP = {
    # Receiving Stats
    41: 'receivingReceptions',
    42: 'receivingYards', 
    43: 'receivingTouchdowns',
    58: 'receivingTargets',
    59: 'receivingYardsAfterCatch',
    60: 'receivingYardsPerReception',
    56: 'receiving100To199YardGame',
    57: 'receiving200PlusYardGame',
    
    # Rushing Stats
    23: 'rushingAttempts',
    24: 'rushingYards',
    25: 'rushingTouchdowns',
    35: 'rushing40PlusYardTD',
    36: 'rushing50PlusYardTD',
    37: 'rushing100To199YardGame',
    38: 'rushing200PlusYardGame',
    39: 'rushingYardsPerAttempt',
    
    # Passing Stats
    0: 'passingAttempts',
    1: 'passingCompletions',
    3: 'passingYards',
    4: 'passingTouchdowns',
    20: 'passingInterceptions',
    15: 'passing40PlusYardTD',
    16: 'passing50PlusYardTD',
    17: 'passing300To399YardGame',
    18: 'passing400PlusYardGame',
    21: 'passingCompletionPercentage',
    
    # Other Stats
    68: 'fumbles',
    72: 'lostFumbles',
    73: 'turnovers',
    155: 'teamWin',
    158: 'pointsScored'
}
```

### Gamelog API

Uses the correct ESPN gamelog endpoint for team/opponent data:
- **Endpoint**: `https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{athlete_id}/gamelog`
- **Parameters**: `season=<year>`, `seasontype=2` (regular season)
- **Data**: Team assignments, opponents, home/away status

## Data Quality Tests

The comprehensive builder includes built-in tests:

1. **David Moore Test**: Verify David Moore has non-zero receiving stats in 2019
2. **Greg Olsen Test**: Verify Greg Olsen is on Carolina in 2019
3. **CMC Carolina Test**: Verify Christian McCaffrey is on Carolina in week 6, 2022
4. **CMC San Francisco Test**: Verify Christian McCaffrey is on San Francisco in week 7, 2022

## Database Naming Strategy

To avoid conflicts with existing databases:

```bash
# Default: fantasy_football_complete
python preprocessing/build_complete_database.py

# With suffix: fantasy_football_complete_v2
python preprocessing/build_complete_database.py --suffix v2

# Custom name: my_fantasy_db
python preprocessing/build_complete_database.py --database my_fantasy_db

# Custom name with suffix: my_fantasy_db_test
python preprocessing/build_complete_database.py --database my_fantasy_db --suffix test
```

## Process Flow

1. **Initialize**: Connect to MongoDB and ESPN league
2. **Fetch Rostered**: Get all players from fantasy league rosters
3. **Fetch Free Agents**: Get all available free agents by position
4. **Combine**: Merge unique player IDs
5. **Process Stats**: Extract season and weekly statistics with proper mapping
6. **Enrich**: Add team/opponent data via gamelog API
7. **Write**: Bulk write to MongoDB
8. **Test**: Run data quality tests
9. **Report**: Generate summary report

## Rate Limiting

The script includes rate limiting to avoid overwhelming ESPN's API:
- 1 second delay between week fetches
- 1 second delay between position fetches
- Configurable delay between player processing (default: 0.5s)

## Error Handling

- Graceful handling of API failures
- Logging of all errors and warnings
- Continues processing even if individual players fail
- Bulk write operations for efficiency
- Proper handling of free agents vs rostered players

## Output Files

- **MongoDB Database**: Complete player database with mapped stats
- **Report**: `docs/complete_database_build_report.md`
- **Logs**: Console output with detailed progress

## Troubleshooting

### Common Issues

1. **ESPN API Rate Limits**: Increase `--rate-delay` parameter
2. **MongoDB Connection**: Check MongoDB is running on localhost:27017
3. **Missing Players**: Some players may not have gamelog data available
4. **Test Failures**: May indicate data quality issues or API changes
5. **Free Agent Stats**: Free agents might have different stats structure than rostered players

### Debugging

```bash
# Dry run to see what would be processed
python preprocessing/build_complete_database.py --dry-run

# Save dry run data for testing
python preprocessing/build_complete_database.py --dry-run --save-dry-run

# Test against temporary database
python preprocessing/build_complete_database.py --test-only --database fantasy_football_complete_temp

# Skip tests if they're failing
python preprocessing/build_complete_database.py --skip-tests

# Process fewer years for testing
python preprocessing/build_complete_database.py --start-year 2023 --end-year 2023
```

## Data Sources

- **ESPN Fantasy API**: Player stats and roster information
- **ESPN Gamelog API**: Team/opponent data for weekly stats
- **MongoDB**: Local database storage

## Schema Evolution

The database schema has evolved over time:
- **v1**: Basic player stats (createTable.py)
- **v2**: Added free agents (add_free_agents.py)
- **v3**: Added team/opponent data (augment_weekly_team_opponent.py)
- **v4**: Complete integrated solution with proper ESPN API mapping (build_complete_database.py)

## Key Improvements in v4

1. **Proper ESPN API Integration**: Uses correct endpoints and data structures
2. **Stats Mapping**: Converts numeric keys to readable names
3. **Comprehensive Player Coverage**: Both rostered and free agents
4. **Team/Opponent Enrichment**: Via gamelog API
5. **Built-in Testing**: Data quality verification
6. **Safe Database Management**: Won't overwrite existing data
7. **Efficient Processing**: Bulk operations and rate limiting

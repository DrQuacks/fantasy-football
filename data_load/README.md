# Data Loading Scripts

This directory contains all scripts related to fetching and loading data from external sources (primarily ESPN).

## Files:

### Core Data Fetching
- **`espn_v3_client.py`** - Main ESPN API client for fetching player data
- **`get_espn_credentials.py`** - Handles ESPN API authentication and credentials
- **`fetch_player_data.py`** - Generic player data fetching utility

### Query Scripts
- **`query_espn_players.py`** - Fetch current season player data from ESPN
- **`query_espn_2019_players.py`** - Fetch 2019 season player data from ESPN
- **`query_specific_players.py`** - Fetch data for specific player IDs

### Exploration & Testing
- **`espn_api_explorer.py`** - Interactive ESPN API exploration tool
- **`espn_explorer.py`** - Alternative ESPN API exploration script
- **`simple_espn_query.py`** - Simple ESPN API query examples
- **`getPlayerList.py`** - Utility to get list of available players

## Usage:
Most scripts can be run independently for testing, but the main data pipeline uses `espn_v3_client.py` as the primary interface.

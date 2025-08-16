# Fantasy Football Database - Clean

A clean, organized repository to build a complete fantasy football database with all players and their stats.

## Project Structure

```
fantasy-football/
├── data/                    # Data files (CSV, Parquet)
├── data_load/              # Data fetching scripts (ESPN API)
├── preprocessing/          # Data cleaning and database operations
├── analysis/               # Data analysis and insights
├── ml/                     # Machine learning models and training
├── utils/                  # Utility and debugging scripts
├── logs/                   # Log files
├── models/                 # Saved model files
├── docs/                   # Documentation and reports
├── config/                 # Configuration and sample data
└── jupyter/                # Jupyter notebooks
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure MongoDB is running locally

## Usage

### Data Pipeline

1. **Fetch Data**: Use scripts in `data_load/` to fetch data from ESPN
2. **Preprocess**: Use scripts in `preprocessing/` to clean and build the database
3. **Analyze**: Use scripts in `analysis/` for insights
4. **Train Models**: Use scripts in `ml/` for machine learning

### Quick Start

To build the complete database:

```bash
python preprocessing/build_database.py
```

This will:
- Clear any existing data
- Fetch all rostered players and free agents from ESPN (2019-2024)
- Get stats for all players
- Build the MongoDB database
- Export to CSV and Parquet files

## Output

- `data/fantasy_weekly_stats.csv` - Complete dataset
- `data/fantasy_weekly_stats.parquet` - Complete dataset (Parquet format)

## What's Included

- All players (rostered + free agents) with actual stats
- QB, RB, WR, TE, K positions
- Years 2019-2024
- Defense-adjusted metrics
- Clean, organized codebase

## Directory Details

- **`data_load/`**: ESPN API clients, data fetching scripts
- **`preprocessing/`**: Database operations, data cleaning
- **`analysis/`**: Statistical analysis, insights generation
- **`ml/`**: Machine learning models, training scripts
- **`utils/`**: Debugging tools, development utilities


import pandas as pd
import numpy as np
from pathlib import Path

# ------------------------------
# Config
# ------------------------------
INPUT_PATH = "data/defense_weekly_stats.parquet"   # weekly defense vs offense by position
OUTPUT_CSV = "data/defense_adjusted_pi.csv"
OUTPUT_PARQUET = "data/defense_adjusted_pi.parquet"

# List the position-specific offense stats your table contains (allowed by the defense)
# Add/remove as needed.
STAT_COLS = [
    # Receiving
    "receivingYardsWR", "receivingYardsRB", "receivingYardsTE",
    "receivingReceptionsWR", "receivingReceptionsRB", "receivingReceptionsTE",
    "receivingTouchdownsWR", "receivingTouchdownsRB", "receivingTouchdownsTE",
    "receivingTargetsWR", "receivingTargetsRB", "receivingTargetsTE",
    "receivingYardsAfterCatchWR", "receivingYardsAfterCatchRB", "receivingYardsAfterCatchTE",
    "receiving100To199YardGameWR", "receiving100To199YardGameRB", "receiving100To199YardGameTE",
    "receiving200PlusYardGameWR", "receiving200PlusYardGameRB", "receiving200PlusYardGameTE",
    # Rushing
    "rushingYardsRB", "rushingYardsQB", "rushingYardsWR", "rushingYardsTE",
    "rushingTouchdownsRB", "rushingTouchdownsQB", "rushingTouchdownsWR", "rushingTouchdownsTE",
    "rushingAttemptsRB", "rushingAttemptsQB", "rushingAttemptsWR", "rushingAttemptsTE",
    "rushing40PlusYardTDRB", "rushing40PlusYardTDQB", "rushing40PlusYardTDWR", "rushing40PlusYardTDTE",
    "rushing50PlusYardTDRB", "rushing50PlusYardTDQB", "rushing50PlusYardTDWR", "rushing50PlusYardTDTE",
    "rushing100To199YardGameRB", "rushing100To199YardGameQB", "rushing100To199YardGameWR", "rushing100To199YardGameTE",
    "rushing200PlusYardGameRB", "rushing200PlusYardGameQB", "rushing200PlusYardGameWR", "rushing200PlusYardGameTE",
    # Passing (QB-facing)
    "passingYardsQB", "passingTouchdownsQB", "passingInterceptionsQB",
    "passingAttemptsQB", "passingCompletionsQB", "passingIncompletionsQB",
    "passing40PlusYardTDQB", "passing50PlusYardTDQB",
    "passing300To399YardGameQB", "passing400PlusYardGameQB", "passing2PtConversionsQB",
    # Kicking
    "madeFieldGoalsK", "attemptedFieldGoalsK", "madeExtraPointsK", "attemptedExtraPointsK",
    "madeFieldGoalsFrom50PlusK", "attemptedFieldGoalsFrom50PlusK",
    "madeFieldGoalsFromUnder40K", "attemptedFieldGoalsFromUnder40K",
]

EPS = 1e-6  # numerical stability for divides


def load_table(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".parquet":
        return pd.read_parquet(p)
    elif p.suffix.lower() in (".csv", ".tsv"):
        return pd.read_csv(p)
    else:
        raise ValueError(f"Unsupported input type: {p.suffix}")


def calculate_expected_values(df: pd.DataFrame, stat_cols):
    """
    Calculate expected values using leave-one-out baseline within season, 
    with last season data for Week 1 only (except 2019).
    """
    print("🔄 Calculating expected values...")
    
    # Create a copy to avoid modifying original
    df_copy = df.copy()
    
    # Initialize expected columns
    for c in stat_cols:
        df_copy[f"expected_{c}"] = 0.0  # Default to 0
    
    # For each game, calculate baseline
    total_games = len(df_copy)
    for idx, row in df_copy.iterrows():
        if idx % 1000 == 0:
            print(f"   Processing game {idx+1}/{total_games}")
        
        year = row['year']
        offense_team = row['offense_team']
        week = row['week']
        
        if week == 1 and year > 2019:
            # Week 1 (non-2019): Use last season's data
            last_year = year - 1
            last_year_data = df_copy[
                (df_copy['year'] == last_year) & 
                (df_copy['offense_team'] == offense_team)
            ]
            
            if not last_year_data.empty:
                for c in stat_cols:
                    mean_val = last_year_data[c].mean()
                    df_copy.at[idx, f"expected_{c}"] = mean_val
        elif week > 1:
            # Week 2+: Use leave-one-out baseline within current season
            other_games = df_copy[
                (df_copy['year'] == year) & 
                (df_copy['offense_team'] == offense_team) & 
                (df_copy['week'] != week)
            ]
            
            if not other_games.empty:
                for c in stat_cols:
                    mean_val = other_games[c].mean()
                    df_copy.at[idx, f"expected_{c}"] = mean_val
    
    print("✅ Expected values calculated!")
    return df_copy


def per_game_pi(df: pd.DataFrame, stat_cols):
    """
    For each row/game and stat, compute PI = (Expected - Actual) / Expected.
    If Expected == 0: PI = 0 if Actual == 0 else -1
    Special handling for 2019 Week 1: Set PI to 0 (no prior data)
    """
    print("🔄 Computing per-game PI values...")
    
    for c in stat_cols:
        exp_col = f"expected_{c}"
        pi_col = f"pi_{c}"
        if exp_col not in df.columns:
            raise ValueError(f"Expected column missing: {exp_col}")

        exp = df[exp_col].astype(float)
        act = df[c].astype(float)

        # Special handling for 2019 Week 1: Set PI to 0
        week1_2019_mask = (df['year'] == 2019) & (df['week'] == 1)
        
        # Standard PI with safety epsilon
        pi = (exp - act) / (exp + EPS)

        # Handle expected == 0 cleanly
        zero_mask = (exp.abs() < EPS)
        pi = np.where(
            zero_mask,
            np.where(act.abs() < EPS, 0.0, -1.0),
            pi
        )
        
        # Override 2019 Week 1 with 0
        pi = np.where(week1_2019_mask, 0.0, pi)
        
        df[pi_col] = pi

    return df


def calculate_weekly_defense_metrics(df: pd.DataFrame, stat_cols):
    """
    Calculate defense PI metrics for each week of the season.
    For each (year, defense_team, week), calculate:
    - last1_*: Performance in the most recent game (week N-1)
    - last4_*: Performance over the last 4 games (weeks N-4 to N-1)
    - season_*: Performance over the entire season so far (weeks 1 to N-1)
    - Separate home/away versions for each
    
    Special handling for Week 1 2019: Set all PI columns to 0 (no prior data)
    """
    print("🔄 Calculating weekly defense metrics...")
    
    # Create a list to store results for each week
    weekly_results = []
    
    # Get all unique (year, defense_team, week) combinations
    unique_combinations = df[['year', 'defense_team', 'week']].drop_duplicates().sort_values(['year', 'defense_team', 'week'])
    
    total_combinations = len(unique_combinations)
    for idx, (_, row) in enumerate(unique_combinations.iterrows()):
        if idx % 100 == 0:
            print(f"   Processing combination {idx+1}/{total_combinations}")
        
        year = row['year']
        defense_team = row['defense_team']
        current_week = row['week']
        
        # Initialize result row
        result_row = {
            'year': year,
            'defense_team': defense_team,
            'week': current_week
        }
        
        # Special handling for Week 1 2019: Set all PI columns to 0
        if year == 2019 and current_week == 1:
            for c in stat_cols:
                result_row[f"pi_last1_{c}"] = 0.0
                result_row[f"pi_last4_{c}"] = 0.0
                result_row[f"pi_season_{c}"] = 0.0
                result_row[f"pi_last1_home_{c}"] = 0.0
                result_row[f"pi_last1_away_{c}"] = 0.0
                result_row[f"pi_last4_home_{c}"] = 0.0
                result_row[f"pi_last4_away_{c}"] = 0.0
                result_row[f"pi_season_home_{c}"] = 0.0
                result_row[f"pi_season_away_{c}"] = 0.0
        else:
            # Get all games for this defense team up to the current week (excluding current week)
            historical_games = df[
                (df['year'] == year) & 
                (df['defense_team'] == defense_team) & 
                (df['week'] < current_week)
            ].sort_values('week', ascending=False)
            
            # If no historical games, handle based on year and week
            if historical_games.empty:
                if year == 2019 and current_week == 1:
                    # 2019 Week 1: No prior data, set to 0
                    for c in stat_cols:
                        result_row[f"pi_last1_{c}"] = 0.0
                        result_row[f"pi_last4_{c}"] = 0.0
                        result_row[f"pi_season_{c}"] = 0.0
                        result_row[f"pi_last1_home_{c}"] = 0.0
                        result_row[f"pi_last1_away_{c}"] = 0.0
                        result_row[f"pi_last4_home_{c}"] = 0.0
                        result_row[f"pi_last4_away_{c}"] = 0.0
                        result_row[f"pi_season_home_{c}"] = 0.0
                        result_row[f"pi_season_away_{c}"] = 0.0
                else:
                    # Week 1 2020+: Need to calculate using last season's data
                    # Get last season's games for this defense team
                    last_season_games = df[(df['year'] == year - 1) & (df['defense_team'] == defense_team)]
                    if not last_season_games.empty:
                        # Calculate PI values using last season's games
                        historical_pi_values = []
                        for _, game in last_season_games.iterrows():
                            game_pi = {}
                            offense_team = game['offense_team']
                            
                            # Use last season's data for expected values
                            last_year_data = df[(df['year'] == year - 1) & (df['offense_team'] == offense_team)]
                            if not last_year_data.empty:
                                for c in stat_cols:
                                    expected = last_year_data[c].mean()
                                    actual = game[c]
                                    if abs(expected) < EPS:
                                        pi_val = 0.0 if abs(actual) < EPS else -1.0
                                    else:
                                        pi_val = (expected - actual) / expected
                                    game_pi[c] = pi_val
                            else:
                                for c in stat_cols:
                                    game_pi[c] = 0.0
                            
                            game_pi['isHome'] = game['isHome']
                            historical_pi_values.append(game_pi)
                        
                        # Use last season's PI values for Week 1 metrics
                        if historical_pi_values:
                            # last1 = most recent game from last season
                            last_game_pi = historical_pi_values[0]
                            for c in stat_cols:
                                result_row[f"pi_last1_{c}"] = last_game_pi[c]
                            
                            # last4 = last 4 games from last season
                            last4_pi_values = historical_pi_values[:4]
                            for c in stat_cols:
                                result_row[f"pi_last4_{c}"] = np.mean([pi[c] for pi in last4_pi_values])
                            
                            # season = all games from last season
                            for c in stat_cols:
                                result_row[f"pi_season_{c}"] = np.mean([pi[c] for pi in historical_pi_values])
                            
                            # Home/away splits
                            last_home_pi = [pi for pi in historical_pi_values if pi['isHome'] == True]
                            last_away_pi = [pi for pi in historical_pi_values if pi['isHome'] == False]
                            
                            for c in stat_cols:
                                result_row[f"pi_last1_home_{c}"] = last_home_pi[0][c] if last_home_pi else 0.0
                                result_row[f"pi_last1_away_{c}"] = last_away_pi[0][c] if last_away_pi else 0.0
                                
                                last4_home_pi = [pi for pi in last4_pi_values if pi['isHome'] == True]
                                last4_away_pi = [pi for pi in last4_pi_values if pi['isHome'] == False]
                                result_row[f"pi_last4_home_{c}"] = np.mean([pi[c] for pi in last4_home_pi]) if last4_home_pi else 0.0
                                result_row[f"pi_last4_away_{c}"] = np.mean([pi[c] for pi in last4_away_pi]) if last4_away_pi else 0.0
                                
                                season_home_pi = [pi for pi in historical_pi_values if pi['isHome'] == True]
                                season_away_pi = [pi for pi in historical_pi_values if pi['isHome'] == False]
                                result_row[f"pi_season_home_{c}"] = np.mean([pi[c] for pi in season_home_pi]) if season_home_pi else 0.0
                                result_row[f"pi_season_away_{c}"] = np.mean([pi[c] for pi in season_away_pi]) if season_away_pi else 0.0
                        else:
                            # No last season data, set to 0
                            for c in stat_cols:
                                result_row[f"pi_last1_{c}"] = 0.0
                                result_row[f"pi_last4_{c}"] = 0.0
                                result_row[f"pi_season_{c}"] = 0.0
                                result_row[f"pi_last1_home_{c}"] = 0.0
                                result_row[f"pi_last1_away_{c}"] = 0.0
                                result_row[f"pi_last4_home_{c}"] = 0.0
                                result_row[f"pi_last4_away_{c}"] = 0.0
                                result_row[f"pi_season_home_{c}"] = 0.0
                                result_row[f"pi_season_away_{c}"] = 0.0
                    else:
                        # No last season data, set to 0
                        for c in stat_cols:
                            result_row[f"pi_last1_{c}"] = 0.0
                            result_row[f"pi_last4_{c}"] = 0.0
                            result_row[f"pi_season_{c}"] = 0.0
                            result_row[f"pi_last1_home_{c}"] = 0.0
                            result_row[f"pi_last1_away_{c}"] = 0.0
                            result_row[f"pi_last4_home_{c}"] = 0.0
                            result_row[f"pi_last4_away_{c}"] = 0.0
                            result_row[f"pi_season_home_{c}"] = 0.0
                            result_row[f"pi_season_away_{c}"] = 0.0
            else:
                # Calculate PI values for each historical game
                historical_pi_values = []
                for _, game in historical_games.iterrows():
                    game_pi = {}
                    offense_team = game['offense_team']
                    game_week = game['week']
                    
                    # Calculate expected values for this specific game
                    if game_week == 1 and year > 2019:
                        # Week 1 (non-2019): Use last season's data
                        last_year = year - 1
                        last_year_data = df[(df['year'] == last_year) & (df['offense_team'] == offense_team)]
                        if not last_year_data.empty:
                            for c in stat_cols:
                                expected = last_year_data[c].mean()
                                actual = game[c]
                                if abs(expected) < EPS:
                                    pi_val = 0.0 if abs(actual) < EPS else -1.0
                                else:
                                    pi_val = (expected - actual) / expected
                                game_pi[c] = pi_val
                        else:
                            # No last year data, set PI to 0
                            for c in stat_cols:
                                game_pi[c] = 0.0
                    else:
                        # Week 2+: Use leave-one-out baseline within current season
                        other_games = df[(df['year'] == year) & 
                                       (df['offense_team'] == offense_team) & 
                                       (df['week'] != game_week)]
                        if not other_games.empty:
                            for c in stat_cols:
                                expected = other_games[c].mean()
                                actual = game[c]
                                if abs(expected) < EPS:
                                    pi_val = 0.0 if abs(actual) < EPS else -1.0
                                else:
                                    pi_val = (expected - actual) / expected
                                game_pi[c] = pi_val
                        else:
                            # No other games, set PI to 0
                            for c in stat_cols:
                                game_pi[c] = 0.0
                    
                    game_pi['isHome'] = game['isHome']
                    historical_pi_values.append(game_pi)
                
                # Calculate last1 metrics (most recent game)
                if historical_pi_values:
                    last_game_pi = historical_pi_values[0]
                    for c in stat_cols:
                        result_row[f"pi_last1_{c}"] = last_game_pi[c]
                    
                    # Last1 home/away
                    last_home_pi = [pi for pi in historical_pi_values if pi['isHome'] == True]
                    last_away_pi = [pi for pi in historical_pi_values if pi['isHome'] == False]
                    
                    for c in stat_cols:
                        result_row[f"pi_last1_home_{c}"] = last_home_pi[0][c] if last_home_pi else 0.0
                        result_row[f"pi_last1_away_{c}"] = last_away_pi[0][c] if last_away_pi else 0.0
                else:
                    # No historical games, set all to 0
                    for c in stat_cols:
                        result_row[f"pi_last1_{c}"] = 0.0
                        result_row[f"pi_last1_home_{c}"] = 0.0
                        result_row[f"pi_last1_away_{c}"] = 0.0
                
                # Calculate last4 metrics (last 4 games)
                last4_pi_values = historical_pi_values[:4]
                if last4_pi_values:
                    for c in stat_cols:
                        result_row[f"pi_last4_{c}"] = np.mean([pi[c] for pi in last4_pi_values])
                    
                    # Last4 home/away
                    last4_home_pi = [pi for pi in last4_pi_values if pi['isHome'] == True]
                    last4_away_pi = [pi for pi in last4_pi_values if pi['isHome'] == False]
                    
                    for c in stat_cols:
                        result_row[f"pi_last4_home_{c}"] = np.mean([pi[c] for pi in last4_home_pi]) if last4_home_pi else 0.0
                        result_row[f"pi_last4_away_{c}"] = np.mean([pi[c] for pi in last4_away_pi]) if last4_away_pi else 0.0
                
                # Calculate season metrics (all games up to current week)
                if historical_pi_values:
                    for c in stat_cols:
                        result_row[f"pi_season_{c}"] = np.mean([pi[c] for pi in historical_pi_values])
                    
                    # Season home/away
                    season_home_pi = [pi for pi in historical_pi_values if pi['isHome'] == True]
                    season_away_pi = [pi for pi in historical_pi_values if pi['isHome'] == False]
                    
                    for c in stat_cols:
                        result_row[f"pi_season_home_{c}"] = np.mean([pi[c] for pi in season_home_pi]) if season_home_pi else 0.0
                        result_row[f"pi_season_away_{c}"] = np.mean([pi[c] for pi in season_away_pi]) if season_away_pi else 0.0
        
        weekly_results.append(result_row)
    
    print("✅ Weekly defense metrics calculated!")
    return pd.DataFrame(weekly_results)


def main():
    df = load_table(INPUT_PATH)

    required = ["year", "week", "defense_team", "offense_team"]
    miss = [c for c in required if c not in df.columns]
    if miss:
        raise ValueError(f"Missing required columns: {miss}")

    # Ensure numeric dtype for stat columns
    for c in STAT_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
        else:
            raise ValueError(f"Stat column not found: {c}")

    # Calculate weekly defense metrics (includes PI calculation)
    out = calculate_weekly_defense_metrics(df, STAT_COLS)

    # Sort and save
    out = out.sort_values(['year', 'defense_team', 'week']).reset_index(drop=True)
    
    # Save
    out.to_csv(OUTPUT_CSV, index=False)
    out.to_parquet(OUTPUT_PARQUET, index=False)
    print(f"✅ Wrote:\n - {OUTPUT_CSV}\n - {OUTPUT_PARQUET}")
    
    print(f"✅ Generated {len(out)} weekly defense records")
    print(f"✅ Years covered: {out['year'].unique()}")
    print(f"✅ Teams covered: {len(out['defense_team'].unique())}")

    # Check for NaN values
    nan_count = out.isna().sum().sum()
    print(f"✅ NaN values in final table: {nan_count}")

    # Preview
    preview_cols = ["year", "defense_team", "week"] + [c for c in out.columns if c.startswith("pi_last4_")][:3]
    print("\n📊 Preview of results:")
    print(out[preview_cols].head(10))


if __name__ == "__main__":
    main()

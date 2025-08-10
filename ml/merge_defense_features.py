import pandas as pd
import numpy as np
from pathlib import Path


def load_defense_pi_data(pi_path: str) -> pd.DataFrame:
    """Load defense performance indices data."""
    df = pd.read_parquet(pi_path)
    return df


def get_defense_features_for_player(player_row: pd.Series, defense_pi_df: pd.DataFrame, 
                                   year: int, week: int, opponent: str) -> dict:
    """
    Get defense-adjusted features for a specific player matchup.
    
    Args:
        player_row: Row from player stats with position, player_team, etc.
        defense_pi_df: DataFrame with defense performance indices
        year: Year of the game
        week: Week of the game  
        opponent: Opponent team (defense team)
    
    Returns:
        Dictionary of defense-adjusted features for this matchup
    """
    # Find the defense performance data for this matchup
    defense_data = defense_pi_df[
        (defense_pi_df['year'] == year) & 
        (defense_pi_df['defense_team'] == opponent)
    ]
    
    if defense_data.empty:
        # If no defense data, return zeros
        return {}
    
    # Get the most recent defense data (could be last week, last 4 weeks, or season)
    # For now, use season averages as they're most stable
    defense_row = defense_data.iloc[0]  # Should be one row per defense per year
    
    position = player_row['position']
    features = {}
    
    # Map position-specific defense features
    if position == 'WR':
        # Receiving features for WR
        features.update({
            'def_pi_receivingYards': defense_row.get('pi_season_receivingYardsWR', 0),
            'def_pi_receivingReceptions': defense_row.get('pi_season_receivingReceptionsWR', 0),
            'def_pi_receivingTouchdowns': defense_row.get('pi_season_receivingTouchdownsWR', 0),
            'def_pi_receivingTargets': defense_row.get('pi_season_receivingTargetsWR', 0),
            'def_pi_receivingYardsAfterCatch': defense_row.get('pi_season_receivingYardsAfterCatchWR', 0),
            'def_pi_receiving100To199YardGame': defense_row.get('pi_season_receiving100To199YardGameWR', 0),
            'def_pi_receiving200PlusYardGame': defense_row.get('pi_season_receiving200PlusYardGameWR', 0),
        })
        # Rushing features for WR (if any)
        features.update({
            'def_pi_rushingYards': defense_row.get('pi_season_rushingYardsWR', 0),
            'def_pi_rushingTouchdowns': defense_row.get('pi_season_rushingTouchdownsWR', 0),
            'def_pi_rushingAttempts': defense_row.get('pi_season_rushingAttemptsWR', 0),
        })
        
    elif position == 'RB':
        # Receiving features for RB
        features.update({
            'def_pi_receivingYards': defense_row.get('pi_season_receivingYardsRB', 0),
            'def_pi_receivingReceptions': defense_row.get('pi_season_receivingReceptionsRB', 0),
            'def_pi_receivingTouchdowns': defense_row.get('pi_season_receivingTouchdownsRB', 0),
            'def_pi_receivingTargets': defense_row.get('pi_season_receivingTargetsRB', 0),
            'def_pi_receivingYardsAfterCatch': defense_row.get('pi_season_receivingYardsAfterCatchRB', 0),
            'def_pi_receiving100To199YardGame': defense_row.get('pi_season_receiving100To199YardGameRB', 0),
            'def_pi_receiving200PlusYardGame': defense_row.get('pi_season_receiving200PlusYardGameRB', 0),
        })
        # Rushing features for RB
        features.update({
            'def_pi_rushingYards': defense_row.get('pi_season_rushingYardsRB', 0),
            'def_pi_rushingTouchdowns': defense_row.get('pi_season_rushingTouchdownsRB', 0),
            'def_pi_rushingAttempts': defense_row.get('pi_season_rushingAttemptsRB', 0),
            'def_pi_rushing40PlusYardTD': defense_row.get('pi_season_rushing40PlusYardTDRB', 0),
            'def_pi_rushing50PlusYardTD': defense_row.get('pi_season_rushing50PlusYardTDRB', 0),
            'def_pi_rushing100To199YardGame': defense_row.get('pi_season_rushing100To199YardGameRB', 0),
            'def_pi_rushing200PlusYardGame': defense_row.get('pi_season_rushing200PlusYardGameRB', 0),
        })
        
    elif position == 'TE':
        # Receiving features for TE
        features.update({
            'def_pi_receivingYards': defense_row.get('pi_season_receivingYardsTE', 0),
            'def_pi_receivingReceptions': defense_row.get('pi_season_receivingReceptionsTE', 0),
            'def_pi_receivingTouchdowns': defense_row.get('pi_season_receivingTouchdownsTE', 0),
            'def_pi_receivingTargets': defense_row.get('pi_season_receivingTargetsTE', 0),
            'def_pi_receivingYardsAfterCatch': defense_row.get('pi_season_receivingYardsAfterCatchTE', 0),
            'def_pi_receiving100To199YardGame': defense_row.get('pi_season_receiving100To199YardGameTE', 0),
            'def_pi_receiving200PlusYardGame': defense_row.get('pi_season_receiving200PlusYardGameTE', 0),
        })
        # Rushing features for TE
        features.update({
            'def_pi_rushingYards': defense_row.get('pi_season_rushingYardsTE', 0),
            'def_pi_rushingTouchdowns': defense_row.get('pi_season_rushingTouchdownsTE', 0),
            'def_pi_rushingAttempts': defense_row.get('pi_season_rushingAttemptsTE', 0),
        })
        
    elif position == 'QB':
        # Passing features for QB
        features.update({
            'def_pi_passingYards': defense_row.get('pi_season_passingYardsQB', 0),
            'def_pi_passingTouchdowns': defense_row.get('pi_season_passingTouchdownsQB', 0),
            'def_pi_passingInterceptions': defense_row.get('pi_season_passingInterceptionsQB', 0),
            'def_pi_passingAttempts': defense_row.get('pi_season_passingAttemptsQB', 0),
            'def_pi_passingCompletions': defense_row.get('pi_season_passingCompletionsQB', 0),
            'def_pi_passing40PlusYardTD': defense_row.get('pi_season_passing40PlusYardTDQB', 0),
            'def_pi_passing50PlusYardTD': defense_row.get('pi_season_passing50PlusYardTDQB', 0),
            'def_pi_passing300To399YardGame': defense_row.get('pi_season_passing300To399YardGameQB', 0),
            'def_pi_passing400PlusYardGame': defense_row.get('pi_season_passing400PlusYardGameQB', 0),
            'def_pi_passing2PtConversions': defense_row.get('pi_season_passing2PtConversionsQB', 0),
        })
        # Rushing features for QB
        features.update({
            'def_pi_rushingYards': defense_row.get('pi_season_rushingYardsQB', 0),
            'def_pi_rushingTouchdowns': defense_row.get('pi_season_rushingTouchdownsQB', 0),
            'def_pi_rushingAttempts': defense_row.get('pi_season_rushingAttemptsQB', 0),
            'def_pi_rushing40PlusYardTD': defense_row.get('pi_season_rushing40PlusYardTDQB', 0),
            'def_pi_rushing50PlusYardTD': defense_row.get('pi_season_rushing50PlusYardTDQB', 0),
            'def_pi_rushing100To199YardGame': defense_row.get('pi_season_rushing100To199YardGameQB', 0),
            'def_pi_rushing200PlusYardGame': defense_row.get('pi_season_rushing200PlusYardGameQB', 0),
        })
        
    elif position == 'K':
        # Kicking features for K
        features.update({
            'def_pi_madeFieldGoals': defense_row.get('pi_season_madeFieldGoalsK', 0),
            'def_pi_attemptedFieldGoals': defense_row.get('pi_season_attemptedFieldGoalsK', 0),
            'def_pi_madeExtraPoints': defense_row.get('pi_season_madeExtraPointsK', 0),
            'def_pi_attemptedExtraPoints': defense_row.get('pi_season_attemptedExtraPointsK', 0),
            'def_pi_madeFieldGoalsFrom50Plus': defense_row.get('pi_season_madeFieldGoalsFrom50PlusK', 0),
            'def_pi_attemptedFieldGoalsFrom50Plus': defense_row.get('pi_season_attemptedFieldGoalsFrom50PlusK', 0),
            'def_pi_madeFieldGoalsFromUnder40': defense_row.get('pi_season_madeFieldGoalsFromUnder40K', 0),
            'def_pi_attemptedFieldGoalsFromUnder40': defense_row.get('pi_season_attemptedFieldGoalsFromUnder40K', 0),
        })
    
    return features


def merge_defense_features(player_stats_path: str, defense_pi_path: str, output_path: str):
    """
    Merge defense-adjusted performance indices with player stats.
    
    Args:
        player_stats_path: Path to player stats parquet file
        defense_pi_path: Path to defense performance indices parquet file
        output_path: Path to save merged data
    """
    print("Loading player stats...")
    player_df = pd.read_parquet(player_stats_path)
    
    print("Loading defense performance indices...")
    defense_pi_df = pd.read_parquet(defense_pi_path)
    
    print("Merging defense features...")
    defense_features_list = []
    
    for idx, row in player_df.iterrows():
        if idx % 1000 == 0:
            print(f"Processing row {idx}/{len(player_df)}")
            
        features = get_defense_features_for_player(
            row, defense_pi_df, 
            row['year'], row['week'], row['opponent']
        )
        defense_features_list.append(features)
    
    # Convert to DataFrame
    defense_features_df = pd.DataFrame(defense_features_list)
    
    # Merge with player stats
    merged_df = pd.concat([player_df, defense_features_df], axis=1)
    
    # Fill NaN values with 0
    defense_cols = [col for col in merged_df.columns if col.startswith('def_pi_')]
    merged_df[defense_cols] = merged_df[defense_cols].fillna(0)
    
    print(f"Saving merged data to {output_path}")
    merged_df.to_parquet(output_path)
    
    print(f"✅ Merged data saved with {len(defense_cols)} defense features")
    print(f"Defense features: {defense_cols}")
    
    return merged_df


if __name__ == "__main__":
    PLAYER_STATS_PATH = "data/fantasy_weekly_stats.parquet"
    DEFENSE_PI_PATH = "data/defense_adjusted_pi.parquet"
    OUTPUT_PATH = "data/fantasy_weekly_stats_with_defense.parquet"
    
    merge_defense_features(PLAYER_STATS_PATH, DEFENSE_PI_PATH, OUTPUT_PATH)

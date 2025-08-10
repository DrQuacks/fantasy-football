import pandas as pd
import numpy as np
import json
import os


def compute_normalization_stats(df: pd.DataFrame, feature_keys: list) -> dict:
    stats = {}
    for key in feature_keys:
        mean = df[key].mean()
        std = df[key].std()
        stats[key] = {"mean": mean, "std": std if std > 0 else 1.0}
    return stats


def apply_normalization(df: pd.DataFrame, stats: dict) -> pd.DataFrame:
    norm_df = df.copy()
    for key, s in stats.items():
        if key in norm_df:
            norm_df[key] = (norm_df[key] - s["mean"]) / s["std"]
    return norm_df

def reverse_normalization(data, feature_names, stats):
    """
    Reverse z-score normalization using stats dictionary.
    - data: np.ndarray or torch.Tensor of shape (N, D)
    - feature_names: list of D feature names
    - stats: dict with mean/std for each feature
    Returns: denormalized numpy array
    """
    import numpy as np
    data = data.detach().cpu().numpy() if hasattr(data, 'detach') else data
    denorm = []
    for i, key in enumerate(feature_names):
        mean = stats[key]['mean']
        std = stats[key]['std']
        denorm_col = data[:, i] * std + mean
        denorm.append(denorm_col)
    return np.stack(denorm, axis=1)

def save_stats(stats: dict, path: str):
    with open(path, "w") as f:
        json.dump(stats, f, indent=2)


def load_stats(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


# Example usage:
if __name__ == "__main__":
    INPUT_PARQUET = "data/fantasy_weekly_stats_with_defense.parquet"
    STATS_JSON = "data/normalization_stats.json"
    NORM_PARQUET = "data/fantasy_weekly_stats_normalized.parquet"

    features = [
        'receivingReceptions', 'receivingYards', 'receivingTouchdowns', 'receivingTargets',
        'receivingYardsAfterCatch', 'receiving100To199YardGame', 'receiving200PlusYardGame',
        'passingAttempts', 'passingCompletions', 'passingYards', 'passingTouchdowns',
        'passingInterceptions', 'passing40PlusYardTD', 'passing50PlusYardTD',
        'passing300To399YardGame', 'passing400PlusYardGame', 'passing2PtConversions',
        'rushingAttempts', 'rushingYards', 'rushing40PlusYardTD', 'rushing50PlusYardTD',
        'rushing100To199YardGame', 'rushing200PlusYardGame', 'rushingTouchdowns',
        'passingTimesSacked', 'fumbles', 'lostFumbles', 'turnovers',
        'madeFieldGoalsFrom50Plus', 'attemptedFieldGoalsFrom50Plus',
        'madeFieldGoalsFromUnder40', 'attemptedFieldGoalsFromUnder40',
        'madeFieldGoals', 'attemptedFieldGoals', 'madeExtraPoints', 'attemptedExtraPoints'
    ]

    # Defense features (these will be normalized)
    defense_features = [
        'def_pi_receivingYards', 'def_pi_receivingReceptions', 'def_pi_receivingTouchdowns', 
        'def_pi_receivingTargets', 'def_pi_receivingYardsAfterCatch', 
        'def_pi_receiving100To199YardGame', 'def_pi_receiving200PlusYardGame',
        'def_pi_rushingYards', 'def_pi_rushingTouchdowns', 'def_pi_rushingAttempts',
        'def_pi_rushing40PlusYardTD', 'def_pi_rushing50PlusYardTD', 
        'def_pi_rushing100To199YardGame', 'def_pi_rushing200PlusYardGame',
        'def_pi_passingYards', 'def_pi_passingTouchdowns', 'def_pi_passingInterceptions',
        'def_pi_passingAttempts', 'def_pi_passingCompletions', 'def_pi_passing40PlusYardTD',
        'def_pi_passing50PlusYardTD', 'def_pi_passing300To399YardGame', 
        'def_pi_passing400PlusYardGame', 'def_pi_passing2PtConversions',
        'def_pi_madeFieldGoals', 'def_pi_attemptedFieldGoals', 'def_pi_madeExtraPoints', 
        'def_pi_attemptedExtraPoints', 'def_pi_madeFieldGoalsFrom50Plus', 
        'def_pi_attemptedFieldGoalsFrom50Plus', 'def_pi_madeFieldGoalsFromUnder40', 
        'def_pi_attemptedFieldGoalsFromUnder40'
    ]

    df = pd.read_parquet(INPUT_PARQUET)
    
    # One-hot encode opponent as additional input columns (not normalized)
    if 'opponent' in df.columns:
        opp_dummies = pd.get_dummies(df['opponent'].fillna('UNKNOWN'), prefix='opp')
        df = pd.concat([df, opp_dummies], axis=1)
    
    # Combine all features to normalize
    all_features = features + defense_features
    
    # Filter to only include features that exist in the dataframe
    available_features = [f for f in all_features if f in df.columns]
    print(f"Normalizing {len(available_features)} features: {available_features}")
    
    stats = compute_normalization_stats(df, available_features)
    save_stats(stats, STATS_JSON)

    norm_df = apply_normalization(df, stats)
    norm_df.to_parquet(NORM_PARQUET)
    print(f"✅ Normalized data saved to {NORM_PARQUET}")
    print(f"Total features in normalized data: {len(norm_df.columns)}")

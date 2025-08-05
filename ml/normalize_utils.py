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
    INPUT_PARQUET = "data/fantasy_weekly_stats.parquet"
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

    df = pd.read_parquet(INPUT_PARQUET)
    stats = compute_normalization_stats(df, features)
    save_stats(stats, STATS_JSON)

    norm_df = apply_normalization(df, stats)
    norm_df.to_parquet(NORM_PARQUET)
    print(f"✅ Normalized data saved to {NORM_PARQUET}")

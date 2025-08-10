import pandas as pd
import os


INPUT_PARQUET = "data/fantasy_weekly_stats.parquet"
OUT_CSV = "data/defense_weekly_stats.csv"
OUT_PARQUET = "data/defense_weekly_stats.parquet"


# Feature families and which positions they apply to
RECEIVING_KEYS = [
    'receivingReceptions',
    'receivingYards',
    'receivingTouchdowns',
    'receivingTargets',
    'receivingYardsAfterCatch',
    'receiving100To199YardGame',
    'receiving200PlusYardGame',
]

RUSHING_KEYS = [
    'rushingAttempts',
    'rushingYards',
    'rushing40PlusYardTD',
    'rushing50PlusYardTD',
    'rushing100To199YardGame',
    'rushing200PlusYardGame',
    'rushingTouchdowns',
]

PASSING_KEYS = [
    'passingAttempts',
    'passingCompletions',
    'passingIncompletions',
    'passingYards',
    'passingTouchdowns',
    'passingInterceptions',
    'passing40PlusYardTD',
    'passing50PlusYardTD',
    'passing300To399YardGame',
    'passing400PlusYardGame',
    'passing2PtConversions',
]

KICKING_KEYS = [
    'madeFieldGoalsFrom50Plus',
    'attemptedFieldGoalsFrom50Plus',
    'madeFieldGoalsFromUnder40',
    'attemptedFieldGoalsFromUnder40',
    'madeFieldGoals',
    'attemptedFieldGoals',
    'madeExtraPoints',
    'attemptedExtraPoints',
]

# Exclude ratio/percentage features from aggregation
EXCLUDE_KEYS = {
    'receivingYardsPerReception',
    'rushingYardsPerAttempt',
    'passingCompletionPercentage',
}


def safe_intersection(cols, wanted):
    colset = set(cols)
    return [c for c in wanted if c in colset and c not in EXCLUDE_KEYS]


def aggregate_pos(df: pd.DataFrame, pos: str, keys: list, group_cols: list) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=group_cols)
    subset = df[df['position'] == pos]
    if subset.empty:
        return pd.DataFrame(columns=group_cols)
    agg_cols = safe_intersection(subset.columns, keys)
    if not agg_cols:
        return pd.DataFrame(columns=group_cols)
    g = subset.groupby(group_cols, dropna=False)[agg_cols].sum(min_count=1).reset_index()
    g = g.rename(columns={c: f"{c}{pos}" for c in agg_cols})
    return g


def main():
    df = pd.read_parquet(INPUT_PARQUET)
    # We expect columns: year, week, opponent (defense team key), position, player_team (offense team), plus stat columns
    if not {'year', 'week', 'opponent', 'position', 'player_team'}.issubset(df.columns):
        raise RuntimeError("Input parquet missing required columns: year, week, opponent, position, player_team")

    # Group columns for defense records - now including offense team
    group_cols = ['year', 'week', 'opponent', 'player_team']

    # Receiving: RB/WR/TE
    recv_rb = aggregate_pos(df, 'RB', RECEIVING_KEYS, group_cols)
    recv_wr = aggregate_pos(df, 'WR', RECEIVING_KEYS, group_cols)
    recv_te = aggregate_pos(df, 'TE', RECEIVING_KEYS, group_cols)

    # Rushing: RB/WR/QB/TE (include TE rarely, safe)
    rush_rb = aggregate_pos(df, 'RB', RUSHING_KEYS, group_cols)
    rush_wr = aggregate_pos(df, 'WR', RUSHING_KEYS, group_cols)
    rush_qb = aggregate_pos(df, 'QB', RUSHING_KEYS, group_cols)
    rush_te = aggregate_pos(df, 'TE', RUSHING_KEYS, group_cols)

    # Passing: QB only
    pass_qb = aggregate_pos(df, 'QB', PASSING_KEYS, group_cols)

    # Kicking: K only
    kick_k = aggregate_pos(df, 'K', KICKING_KEYS, group_cols)

    # Start from unique defense keys
    base = df[group_cols].drop_duplicates().reset_index(drop=True)
    out = base.copy()
    for part in [recv_rb, recv_wr, recv_te, rush_rb, rush_wr, rush_qb, rush_te, pass_qb, kick_k]:
        if not part.empty:
            out = out.merge(part, on=group_cols, how='left')

    # Rename columns for clarity
    out = out.rename(columns={'opponent': 'defense_team', 'player_team': 'offense_team'})

    # Sort and save
    out = out.sort_values(['year', 'week', 'defense_team', 'offense_team']).reset_index(drop=True)
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    out.to_parquet(OUT_PARQUET, index=False)
    print(f"✅ Saved defense tables to {OUT_CSV} and {OUT_PARQUET}")


if __name__ == "__main__":
    main()



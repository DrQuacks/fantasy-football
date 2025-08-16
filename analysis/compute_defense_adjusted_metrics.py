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

# If True, offense baseline excludes the current game (safer to avoid leakage).
# You asked to use full season; leaving this False matches that.
EXCLUDE_CURRENT_GAME = False

EPS = 1e-6  # numerical stability for divides


def load_table(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".parquet":
        return pd.read_parquet(p)
    elif p.suffix.lower() in (".csv", ".tsv"):
        return pd.read_csv(p)
    else:
        raise ValueError(f"Unsupported input type: {p.suffix}")


def offense_full_season_baseline(df: pd.DataFrame, stat_cols):
    """
    Compute full-season per-game baseline for each offense_team and year.
    Returns a DataFrame indexed by (year, offense_team) with mean of stat_cols.
    """
    needed = ["year", "offense_team"] + stat_cols
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for baseline: {missing}")

    # Per-game means across the full season
    base = (
        df[["year", "offense_team"] + stat_cols]
        .groupby(["year", "offense_team"], as_index=False)
        .mean(numeric_only=True)
    )
    base = base.set_index(["year", "offense_team"])
    base.columns = [f"expected_{c}" for c in base.columns]
    return base


def attach_expected(df: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    """
    Merge offense full-season per-game baseline expectations onto each game row.
    """
    df2 = df.merge(
        base,
        left_on=["year", "offense_team"],
        right_index=True,
        how="left",
    )
    return df2


def per_game_pi(df: pd.DataFrame, stat_cols):
    """
    For each row/game and stat, compute PI = (Expected - Actual) / Expected.
    If Expected == 0: PI = 0 if Actual == 0 else -1
    """
    for c in stat_cols:
        exp_col = f"expected_{c}"
        pi_col = f"pi_{c}"
        if exp_col not in df.columns:
            raise ValueError(f"Expected column missing: {exp_col}")

        exp = df[exp_col].astype(float)
        act = df[c].astype(float)

        # Standard PI with safety epsilon
        pi = (exp - act) / (exp + EPS)

        # Handle expected == 0 cleanly
        zero_mask = (exp.abs() < EPS)
        pi = np.where(
            zero_mask,
            np.where(act.abs() < EPS, 0.0, -1.0),
            pi
        )
        df[pi_col] = pi

    return df


def last_k_weeks(df: pd.DataFrame, k: int, stat_cols):
    """
    For each (year, defense_team), take its last k games and average the PI stats.
    """
    # Rank games per defense by week to pick most recent k
    df = df.copy()
    df["week_rank_desc"] = df.groupby(["year", "defense_team"])["week"].rank(method="first", ascending=False)
    df_k = df[df["week_rank_desc"] <= k]

    pi_cols = [f"pi_{c}" for c in stat_cols]
    agg = (
        df_k.groupby(["year", "defense_team"], as_index=False)[pi_cols]
            .mean(numeric_only=True)
    )
    # Rename columns to include window suffix
    rename_map = {col: col.replace("pi_", f"pi_last{k}_") for col in pi_cols}
    agg = agg.rename(columns=rename_map)
    return agg


def last_week(df: pd.DataFrame, stat_cols):
    """
    For each (year, defense_team), take only the most recent week and keep PI stats.
    """
    df = df.copy()
    # Find last week per defense/year
    last_weeks = df.groupby(["year", "defense_team"], as_index=False)["week"].max()
    df_last = df.merge(last_weeks, on=["year", "defense_team", "week"], how="inner")

    pi_cols = [f"pi_{c}" for c in stat_cols]
    keep = ["year", "defense_team"] + pi_cols
    df_last = df_last[keep]

    rename_map = {col: col.replace("pi_", "pi_last1_") for col in pi_cols}
    df_last = df_last.rename(columns=rename_map)
    return df_last


def season_to_date(df: pd.DataFrame, stat_cols):
    """
    Average PI over all games (to date) per (year, defense_team).
    """
    pi_cols = [f"pi_{c}" for c in stat_cols]
    agg = (
        df.groupby(["year", "defense_team"], as_index=False)[pi_cols]
          .mean(numeric_only=True)
    )
    rename_map = {col: col.replace("pi_", "pi_season_") for col in pi_cols}
    agg = agg.rename(columns=rename_map)
    return agg


def main():
    df = load_table(INPUT_PATH)

    required = ["year", "week", "defense_team", "offense_team"]
    miss = [c for c in required if c not in df.columns]
    if miss:
        raise ValueError(f"Missing required columns: {miss}")

    # If you want to ensure numeric dtype:
    for c in STAT_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
        else:
            raise ValueError(f"Stat column not found: {c}")

    # Optional: If you want "season to date" rather than full final-season,
    # you could filter df by week <= current_week per year. Here we keep all.

    # Build offense full-season baselines
    if EXCLUDE_CURRENT_GAME:
        # Leave-one-out baseline: compute offense mean excluding each game
        # (More expensive; shown for completeness)
        # For now we'll stick to full-season mean (your request).
        pass

    base = offense_full_season_baseline(df, STAT_COLS)
    df = attach_expected(df, base)
    df = per_game_pi(df, STAT_COLS)

    # Windows
    last1 = last_week(df, STAT_COLS)       # last game
    last4 = last_k_weeks(df, 4, STAT_COLS) # last 4 games
    season = season_to_date(df, STAT_COLS) # full season (mean of all games)

    # Combine into one table
    out = (
        last1.merge(last4, on=["year", "defense_team"], how="outer")
             .merge(season, on=["year", "defense_team"], how="outer")
             .sort_values(["year", "defense_team"])
             .reset_index(drop=True)
    )

    # Save
    out.to_csv(OUTPUT_CSV, index=False)
    out.to_parquet(OUTPUT_PARQUET, index=False)
    print(f"✅ Wrote:\n - {OUTPUT_CSV}\n - {OUTPUT_PARQUET}")

    # (Optional) preview a couple columns
    preview_cols = ["year", "defense_team"] + [c for c in out.columns if c.startswith("pi_last4_")][:5]
    print(out[preview_cols].head(10))


if __name__ == "__main__":
    main()

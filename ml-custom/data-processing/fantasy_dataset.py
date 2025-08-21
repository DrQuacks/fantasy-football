import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

class FantasyDataset(Dataset):
    """
    Returns:
      features_dict:
        - player_features:   (F,)
        - teammate_features: (N_teammates, F)  # strict per-position blocks with slot padding
        - defense_features:  (F,)
      targets: (num_targets,)
    """

    def __init__(self, position, base_df, context_dfs, defense_df, feature_cols, target_cols):
        """
        position: one of {"QB","RB","WR","TE","K"}
        base_df: DataFrame for the focal position (one row per player-week)
        context_dfs: {"QB": qb_df, "RB": rb_df, "WR": wr_df, "TE": te_df, "K": k_df}
                     (K is ignored for non-K models)
        defense_df: defense PI DataFrame (match with defense_team + year if you use PI columns)
        feature_cols: columns from player rows to form feature vectors
        target_cols:  columns from player rows to form target vector
        """
        self.position     = position
        self.base_df      = base_df.reset_index(drop=True)
        self.context_dfs  = context_dfs
        self.defense_df   = defense_df
        self.feature_cols = feature_cols
        self.target_cols  = target_cols

        # Fixed per-position slot limits
        self.slots = {
            "QB": {"QB": 2, "RB": 3, "WR": 5, "TE": 2},
            "RB": {"QB": 2, "RB": 3, "WR": 5, "TE": 2},
            "WR": {"QB": 2, "RB": 3, "WR": 5, "TE": 2},
            "TE": {"QB": 2, "RB": 3, "WR": 5, "TE": 2},
            "K" : {"QB": 1, "RB": 1},
        }

        # Strict bucket order
        self.bucket_order = ["QB", "RB", "WR", "TE"] if position != "K" else ["QB", "RB"]

        # Sorting keys per bucket (descending)
        self.order_keys = {
            "QB": "passingYards",
            "RB": "rushingYards",
            "WR": "receivingYards",
            "TE": "receivingYards",
        }

        # Precompute sizes
        self.F = len(self.feature_cols)
        self.total_teammate_rows = sum(self.slots[position].get(b, 0) for b in self.bucket_order)

    def __len__(self):
        return len(self.base_df)

    # ---------- helpers ----------

    def _build_bucket_block(self, df_bucket: pd.DataFrame, pos: str, max_count: int) -> np.ndarray:
        """
        Produce a (max_count, F) block for a given position bucket.
        - Sort by the position's yardage key (if present), descending.
        - Fill the top slots with available rows.
        - Zero-pad remaining slots of the bucket.
        """
        key = self.order_keys.get(pos)
        if key and key in df_bucket.columns:
            df_bucket = df_bucket.sort_values(key, ascending=False)

        block = np.zeros((max_count, self.F), dtype="float32")
        if not df_bucket.empty:
            vals = df_bucket.head(max_count)[self.feature_cols].to_numpy(dtype="float32")
            n = vals.shape[0]
            block[:n, :] = vals
        return block

    def _get_teammates(self, team: str, year: int, week: int, exclude_player_id: int) -> np.ndarray:
        """
        Build the (N_teammates, F) matrix in strict bucket order with per-bucket padding.
        """
        blocks = []
        for pos in self.bucket_order:
            max_count = self.slots[self.position].get(pos, 0)
            if max_count == 0:
                continue

            df_src = self.context_dfs[pos]
            subset = df_src[
                (df_src["nfl_team"] == team) &
                (df_src["year"] == year) &
                (df_src["week"] == week) &
                (df_src["playerId"] != exclude_player_id)
            ]
            block = self._build_bucket_block(subset, pos, max_count)
            blocks.append(block)

        if blocks:
            return np.vstack(blocks)
        return np.zeros((self.total_teammate_rows, self.F), dtype="float32")

    def _get_defense_stats(self, opponent: str, year: int) -> np.ndarray | None:
        """
        Example: select any columns from defense_df that overlap with feature_cols.
        If you intend to use PI columns (like 'pi_last4_passingYardsQB'), either include them
        in feature_cols or extend this to accept a separate defense_cols list.
        """
        rows = self.defense_df[
            (self.defense_df["defense_team"] == opponent) &
            (self.defense_df["year"] == year)
        ]
        if rows.empty:
            return None
        available = [c for c in self.feature_cols if c in rows.columns]
        if not available:
            return None
        return rows.iloc[0][available].to_numpy(dtype="float32")

    # ---------- main ----------

    def __getitem__(self, idx):
        row = self.base_df.iloc[idx]

        team      = row["nfl_team"]
        year      = int(row["year"])
        week      = int(row["week"])
        opponent  = row["nfl_opponent"]
        player_id = int(row["playerId"])

        # Player features
        player_features = torch.tensor(row[self.feature_cols].to_numpy(), dtype=torch.float32)

        # Teammates (per-bucket slots)
        teammate_features_np = self._get_teammates(team, year, week, player_id)
        teammate_features = torch.tensor(teammate_features_np, dtype=torch.float32)

        # Defense
        def_feats = self._get_defense_stats(opponent, year)
        if def_feats is None:
            def_feats = np.zeros((self.F,), dtype="float32")
        defense_features = torch.tensor(def_feats, dtype=torch.float32)

        # Targets
        targets = torch.tensor(row[self.target_cols].to_numpy(), dtype=torch.float32)

        return {
            "player_features":   player_features,     # (F,)
            "teammate_features": teammate_features,   # (N_teammates, F) — fixed per position
            "defense_features":  defense_features     # (F,)
        }, targets

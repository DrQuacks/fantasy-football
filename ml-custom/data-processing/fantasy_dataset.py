import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

class FantasyDataset(Dataset):
    """
    Returns:
      features_dict:
        - player_features:   (F_player,)
        - teammate_features: (N_teammates, F_player)  # per-bucket slots with zero padding
        - defense_features:  (F_defense,)            # weekly PI features (team, year, week)
      targets: (num_targets,)
    """

    def __init__(
        self,
        position,
        base_df,
        context_dfs,
        defense_df,
        feature_cols,          # player/teammate feature columns (from position tables)
        target_cols,           # training targets
        defense_cols=None      # defense PI columns (from defense_adjusted_pi.parquet)
    ):
        """
        position: {"QB","RB","WR","TE","K"}
        base_df: focal position DataFrame (row = player-week)
        context_dfs: {"QB": qb_df, "RB": rb_df, "WR": wr_df, "TE": te_df, "K": k_df}
                     (K is ignored for non-K models)
        defense_df: defense weekly PI DataFrame (must contain 'defense_team','year','week')
        feature_cols: columns used from player/teammate rows
        target_cols:  columns used for the target tensor
        defense_cols: columns used from defense_df (weekly PI), e.g. ["pi_last4_passingYardsQB", ...]
        """
        self.position     = position
        self.base_df      = base_df.reset_index(drop=True)
        self.context_dfs  = context_dfs
        self.defense_df   = defense_df
        self.feature_cols = feature_cols
        self.target_cols  = target_cols
        self.defense_cols = defense_cols or []

        # Fixed per-position slot limits
        self.slots = {
            "QB": {"QB": 2, "RB": 3, "WR": 5, "TE": 2},
            "RB": {"QB": 2, "RB": 3, "WR": 5, "TE": 2},
            "WR": {"QB": 2, "RB": 3, "WR": 5, "TE": 2},
            "TE": {"QB": 2, "RB": 3, "WR": 5, "TE": 2},
            "K" : {"QB": 1, "RB": 1},
        }

        # Strict teammate bucket order
        self.bucket_order = ["QB", "RB", "WR", "TE"] if position != "K" else ["QB", "RB"]

        # Sorting keys per bucket (descending)
        self.order_keys = {
            "QB": "passingYards",
            "RB": "rushingYards",
            "WR": "receivingYards",
            "TE": "receivingYards",
        }

        # Precompute sizes
        self.F_player   = len(self.feature_cols)
        self.F_defense  = len(self.defense_cols)
        self.total_teammate_rows = sum(self.slots[position].get(b, 0) for b in self.bucket_order)

    def __len__(self):
        return len(self.base_df)

    # ---------- helpers ----------

    def _build_bucket_block(self, df_bucket: pd.DataFrame, pos: str, max_count: int) -> np.ndarray:
        """
        Produce a (max_count, F_player) block for a given position bucket.
        Sort by the position's yardage key (if present), fill top slots, zero-pad the rest.
        """
        key = self.order_keys.get(pos)
        if key and key in df_bucket.columns:
            df_bucket = df_bucket.sort_values(key, ascending=False)

        block = np.zeros((max_count, self.F_player), dtype="float32")
        if not df_bucket.empty:
            vals = df_bucket.head(max_count)[self.feature_cols].to_numpy(dtype="float32")
            n = vals.shape[0]
            block[:n, :] = vals
        return block

    def _get_teammates(self, team: str, year: int, week: int, exclude_player_id: int) -> np.ndarray:
        """
        Build the (N_teammates, F_player) matrix in strict bucket order with per-bucket padding.
        Match on team + year + week; exclude focal player.
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
        return np.zeros((self.total_teammate_rows, self.F_player), dtype="float32")

    def _get_defense_stats(self, opponent: str, year: int, week: int) -> np.ndarray:
        """
        Select (F_defense,) weekly PI vector from defense_df at (defense_team, year, week).
        If no columns found or row missing, returns zeros of length F_defense.
        """
        if self.F_defense == 0:
            return np.zeros((0,), dtype="float32")

        # Filter by team + year + week (weekly PI table)
        rows = self.defense_df.loc[
            (self.defense_df["defense_team"] == opponent) &
            (self.defense_df["year"] == int(year)) &
            (self.defense_df["week"] == int(week)),
            [c for c in self.defense_cols if c in self.defense_df.columns]
        ]
        if rows.empty:
            return np.zeros((self.F_defense,), dtype="float32")

        # Ensure fixed ordering based on requested defense_cols
        # (only keep those that actually existed in df)
        existing = [c for c in self.defense_cols if c in rows.columns]
        vec = rows.iloc[0][existing].to_numpy(dtype="float32")

        # If some requested cols were missing, right-pad zeros to expected length
        if len(existing) < self.F_defense:
            pad = np.zeros((self.F_defense - len(existing),), dtype="float32")
            vec = np.concatenate([vec, pad], axis=0)

        return vec

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

        # Defense (weekly PI features)
        def_feats = self._get_defense_stats(opponent, year, week)
        defense_features = torch.tensor(def_feats, dtype=torch.float32)

        # Targets
        targets = torch.tensor(row[self.target_cols].to_numpy(), dtype=torch.float32)

        return {
            "player_features":   player_features,     # (F_player,)
            "teammate_features": teammate_features,   # (N_teammates, F_player)
            "defense_features":  defense_features     # (F_defense,)
        }, targets

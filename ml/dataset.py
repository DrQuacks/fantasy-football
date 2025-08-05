import torch
from torch.utils.data import Dataset
import pandas as pd
import numpy as np
from typing import List

class FantasyFootballDataset(Dataset):
    def __init__(self, 
                 parquet_path: str,
                 input_features: List[str],
                 target_features: List[str],
                 context_length: int = 5,
                 forecast_length: int = 1,
                 mode: str = "next"
                ):
        self.context_length = context_length
        self.forecast_length = forecast_length
        self.mode = mode
        self.input_features = input_features
        self.target_features = target_features

        # Load and sort the data
        df = pd.read_parquet(parquet_path)
        df = df.sort_values(by=["name", "year", "week"]).reset_index(drop=True)

        # Add season boundary signal
        df["season_change"] = (df["year"].diff() != 0).fillna(0).astype(int)

        # Store as grouped sequences by player and year
        self.sequences = []
        for (name, _), group in df.groupby(["name", "year"]):
            group = group.reset_index(drop=True)
            features = group[self.input_features + self.target_features + ["season_change"]].to_numpy(dtype=np.float32)
            total_len = self.context_length + self.forecast_length
            if len(features) < total_len:
                continue

            if self.mode == "next":
                for i in range(len(features) - total_len + 1):
                    window = features[i : i + total_len]
                    ctx = window[:self.context_length, :len(self.input_features)]
                    tgt = window[self.context_length:, len(self.input_features):-1]
                    mask = tgt.sum(axis=-1) > 0
                    self.sequences.append((ctx, tgt, mask.astype(np.float32)))

            elif self.mode == "full_season":
                ctx = features[:self.context_length, :len(self.input_features)]
                tgt = features[self.context_length:self.context_length + self.forecast_length, len(self.input_features):-1]
                if tgt.shape[0] == self.forecast_length:
                    mask = tgt.sum(axis=-1) > 0
                    self.sequences.append((ctx, tgt, mask.astype(np.float32)))

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        context, target, mask = self.sequences[idx]
        return torch.tensor(context), torch.tensor(target), torch.tensor(mask)


# Example usage:
if __name__ == "__main__":
    input_keys = ["week", "year", "receivingReceptions", "receivingYards"]
    target_keys = ["receivingReceptions", "receivingYards"]

    dataset = FantasyFootballDataset(
        parquet_path="data/fantasy_weekly_stats.parquet",
        input_features=input_keys,
        target_features=target_keys,
        context_length=12,
        forecast_length=4,
        mode="next"
    )

    print("Dataset size:", len(dataset))
    x, y, mask = dataset[0]
    print("Input shape:", x.shape)
    print("Target shape:", y.shape)
    print("Mask shape:", mask.shape)
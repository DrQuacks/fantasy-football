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
                 mode: str = "next"  # or "forecast"
                ):
        self.context_length = context_length
        self.forecast_length = forecast_length
        self.mode = mode
        self.input_features = input_features
        self.target_features = target_features

        # Load and sort the data
        df = pd.read_parquet(parquet_path)
        df = df.sort_values(by=["name", "year", "week"]).reset_index(drop=True)

        # Store as grouped sequences by player and year
        self.sequences = []
        for (name, year), group in df.groupby(["name", "year"]):
            values = group[input_features + target_features].to_numpy(dtype=np.float32)
            if len(values) >= context_length + forecast_length:
                self.sequences.append((name, year, values))

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        name, year, values = self.sequences[idx]

        # Select window from full sequence
        context = values[:self.context_length, :len(self.input_features)]
        targets = values[self.context_length:self.context_length + self.forecast_length, -len(self.target_features):]

        return torch.tensor(context), torch.tensor(targets)

# Example usage:
if __name__ == "__main__":
    input_keys = ["week", "year", "receivingReceptions", "receivingYards"]
    target_keys = ["receivingReceptions", "receivingYards"]

    dataset = FantasyFootballDataset(
        parquet_path="data/fantasy_weekly_stats.parquet",
        input_features=input_keys,
        target_features=target_keys,
        context_length=5,
        forecast_length=1,
        mode="next"
    )

    print("Dataset size:", len(dataset))
    x, y = dataset[0]
    print("Input shape:", x.shape)  # (context_length, input_dim)
    print("Target shape:", y.shape)  # (forecast_length, output_dim)

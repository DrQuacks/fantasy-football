import torch

def collate_fn(batch):
    feature_dicts, targets = zip(*batch)

    player_features   = torch.stack([fd["player_features"]   for fd in feature_dicts])  # (B, F)
    teammate_features = torch.stack([fd["teammate_features"] for fd in feature_dicts])  # (B, N, F)
    defense_features  = torch.stack([fd["defense_features"]  for fd in feature_dicts])  # (B, F)

    return {
        "player_features":   player_features,
        "teammate_features": teammate_features,
        "defense_features":  defense_features
    }, torch.stack(targets)

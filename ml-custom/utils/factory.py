# ml-custom/utils/factory.py
from __future__ import annotations
from typing import Dict, Tuple, Optional
import torch
import torch.nn as nn

from config import TrainConfig  # single source of truth (with overridable defaults)

from models.attention_wr import WRModel
from models.attention_rb import RBModel
from models.attention_te import TEModel
from models.attention_qb import QBModel
from models.attention_k  import KModel

from utils.optim import build_adamw_with_groups  # already supports config + overrides

# Map canonical position -> model class
MODEL_CLASSES = {
    "WR": WRModel,
    "RB": RBModel,
    "TE": TEModel,
    "QB": QBModel,
    "K":  KModel,
}

def infer_dims_from_batch(batch_features: Dict[str, torch.Tensor]) -> Tuple[int, int, int]:
    """
    Given a single batch's features dict:
      {
        "player_features":   (B, F_player),
        "teammate_features": (B, N_teammates, F_player),
        "defense_features":  (B, F_defense)
      }
    return (F_player, F_defense, N_teammates)
    """
    F_player   = int(batch_features["player_features"].shape[-1])
    N_teammate = int(batch_features["teammate_features"].shape[1])
    F_defense  = int(batch_features["defense_features"].shape[-1])
    return F_player, F_defense, N_teammate


def build_model_and_optimizer(
    pos: str,
    F_player: int,
    F_defense: int,
    N_teammates: int,
    config: Optional[TrainConfig] = None,
    *,
    # explicit overrides win over config (and config wins over TrainConfig() defaults)
    lr: Optional[float] = None,
    weight_decay: Optional[float] = None,
    device: Optional[torch.device] = None,
) -> tuple[nn.Module, torch.optim.Optimizer]:
    """
    Create the correct position-specific model + AdamW optimizer with param groups.

    Hyperparam priority:
      1) explicit args (lr, weight_decay) if provided
      2) values from `config` if provided
      3) fall back to TrainConfig() defaults
    """
    if pos not in MODEL_CLASSES:
        raise ValueError(f"Unknown position '{pos}'. Expected one of {list(MODEL_CLASSES)}.")

    cfg = config or TrainConfig()
    use_lr = lr if lr is not None else cfg.lr
    use_wd = weight_decay if weight_decay is not None else cfg.weight_decay

    model_cls = MODEL_CLASSES[pos]
    model = model_cls(F_player, F_defense, num_teammates=N_teammates)
    if device is not None:
        model = model.to(device)

    optimizer = build_adamw_with_groups(
        model,
        config=cfg,            # provides defaults
        lr=use_lr,             # explicit override (if given) beats config
        weight_decay=use_wd,   # explicit override (if given) beats config
    )
    return model, optimizer


def build_all_models_and_optimizers(
    loaders: Dict[str, torch.utils.data.DataLoader],
    config: Optional[TrainConfig] = None,
    *,
    # optional global overrides for all models (wins over config)
    lr: Optional[float] = None,
    weight_decay: Optional[float] = None,
    device: Optional[torch.device] = None,
) -> Dict[str, Dict[str, object]]:
    """
    For each position in `loaders`, infer dims from one batch and build:
      - the correct model (WR/RB/TE/QB/K)
      - an AdamW optimizer with param groups

    Hyperparam priority (for *each* model):
      1) explicit lr / weight_decay args here
      2) values from `config`
      3) TrainConfig() defaults
    """
    cfg = config or TrainConfig()
    results: Dict[str, Dict[str, object]] = {}

    for pos, loader in loaders.items():
        features, _targets = next(iter(loader))  # consumes one batch from this iterator
        if device is not None:
            features = {k: v.to(device) for k, v in features.items()}

        F_player, F_defense, N_teammates = infer_dims_from_batch(features)

        model, optim = build_model_and_optimizer(
            pos=pos,
            F_player=F_player,
            F_defense=F_defense,
            N_teammates=N_teammates,
            config=cfg,
            lr=lr,                  # overrides win if provided
            weight_decay=weight_decay,
            device=device,
        )
        results[pos] = {"model": model, "optimizer": optim}

    return results

from __future__ import annotations
from typing import List, Tuple, Dict, Optional
import torch
import torch.nn as nn
from config import TrainConfig

NO_DECAY_KEYWORDS_DEFAULT = ("bias", "norm", "ln", "layernorm", "bn", "embedding")

def split_params_for_weight_decay(
    model: nn.Module,
    no_decay_keywords: Tuple[str, ...] = NO_DECAY_KEYWORDS_DEFAULT,
) -> Dict[str, List[torch.nn.Parameter]]:
    decay, no_decay = [], []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        name_l = name.lower()
        if (p.ndim <= 1) or any(k in name_l for k in no_decay_keywords):
            no_decay.append(p)
        else:
            decay.append(p)
    return {"decay": decay, "no_decay": no_decay}

def build_adamw_with_groups(
    model: nn.Module,
    config: Optional[TrainConfig] = None,
    *,
    lr: Optional[float] = None,
    weight_decay: Optional[float] = None,
    no_decay_keywords: Tuple[str, ...] = NO_DECAY_KEYWORDS_DEFAULT,
    **adamw_kwargs,
) -> torch.optim.Optimizer:
    """
    Build AdamW with param groups.

    Priority for hyperparams:
      1. Explicit args (lr, weight_decay) if provided
      2. Values from TrainConfig if provided
      3. Fall back to TrainConfig() defaults if nothing passed
    """
    # Source of truth is TrainConfig
    cfg = config or TrainConfig()

    lr = lr if lr is not None else cfg.lr
    weight_decay = weight_decay if weight_decay is not None else cfg.weight_decay

    groups = split_params_for_weight_decay(model, no_decay_keywords=no_decay_keywords)
    return torch.optim.AdamW(
        [
            {"params": groups["decay"], "weight_decay": weight_decay},
            {"params": groups["no_decay"], "weight_decay": 0.0},
        ],
        lr=lr,
        **adamw_kwargs,
    )

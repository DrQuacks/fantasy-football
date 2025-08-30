# ml-custom/utils/optim.py
from __future__ import annotations
from typing import Iterable, List, Tuple, Dict
import torch
import torch.nn as nn

NO_DECAY_KEYWORDS_DEFAULT = ("bias", "norm", "ln", "layernorm", "bn", "embedding")

def split_params_for_weight_decay(
    model: nn.Module,
    no_decay_keywords: Tuple[str, ...] = NO_DECAY_KEYWORDS_DEFAULT,
) -> Dict[str, List[torch.nn.Parameter]]:
    """
    Returns two param lists: {"decay": [...], "no_decay": [...]}

    Rules:
      • no_decay: params with name containing any keyword in no_decay_keywords, OR tensors with ndim <= 1
                  (bias vectors, norm scalars, embeddings, etc.)
      • decay:    everything else (typical weight matrices)
    """
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
    lr: float = 3e-4,
    weight_decay: float = 1e-4,
    no_decay_keywords: Tuple[str, ...] = NO_DECAY_KEYWORDS_DEFAULT,
    **adamw_kwargs,
) -> torch.optim.Optimizer:
    """
    Creates AdamW with two param groups:
      - decay: applies weight_decay
      - no_decay: weight_decay = 0.0
    """
    groups = split_params_for_weight_decay(model, no_decay_keywords=no_decay_keywords)
    return torch.optim.AdamW(
        [
            {"params": groups["decay"], "weight_decay": weight_decay},
            {"params": groups["no_decay"], "weight_decay": 0.0},
        ],
        lr=lr,
        **adamw_kwargs,
    )

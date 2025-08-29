# ml-custom/losses/weighted_multitask.py

from __future__ import annotations
from typing import Dict, List, Literal, Optional
import torch
import torch.nn.functional as F

LossName = Literal["mse", "mae", "huber"]

def _reduce(pred: torch.Tensor) -> torch.Tensor:
    # Ensure shape (B,) for 1D regression heads
    return pred.squeeze(-1)

def weighted_multitask_loss(
    outputs: Dict[str, torch.Tensor],
    targets: torch.Tensor,
    target_names: List[str],
    weights: Optional[Dict[str, float]] = None,
    loss_per_task: Optional[Dict[str, LossName]] = None,
    huber_delta: float = 1.0,
) -> torch.Tensor:
    """
    Compute a weighted sum of per-target losses.

    Args
    ----
    outputs: dict from model forward, e.g. {"points": (B,), "receivingYards": (B,), ...}
             (extra keys like "attn_teammates" are ignored)
    targets: float tensor of shape (B, num_targets), aligned with `target_names`
    target_names: list of column names in the SAME ORDER as `targets`
    weights: optional dict of weights per target; default is 1.0 for "points", 0.3 for others
    loss_per_task: optional dict mapping target -> {"mse","mae","huber"}; default = "mse"
    huber_delta: delta for Huber loss

    Returns
    -------
    torch.Tensor scalar loss
    """
    if weights is None:
        # default: emphasize fantasy points; lighter weight on auxiliary stats
        weights = {}
    if loss_per_task is None:
        loss_per_task = {}

    total = torch.zeros((), device=targets.device, dtype=targets.dtype)

    for i, name in enumerate(target_names):
        if name not in outputs:
            # Skip if this head is not produced by the model (robust to ablations)
            continue

        pred = _reduce(outputs[name])
        tgt = targets[:, i]

        # Choose loss type
        loss_type: LossName = loss_per_task.get(name, "mse")
        if loss_type == "mse":
            li = F.mse_loss(pred, tgt)
        elif loss_type == "mae":
            li = F.l1_loss(pred, tgt)
        elif loss_type == "huber":
            li = F.huber_loss(pred, tgt, delta=huber_delta)
        else:
            raise ValueError(f"Unknown loss type for {name}: {loss_type}")

        # Weight: default 1.0 for "points", else 0.3 unless overridden
        w = weights.get(name, 1.0 if name == "points" else 0.1)
        total = total + w * li

    return total

import torch

CATEGORIES = {
    "passing": [
        "passingAttempts", "passingCompletions", "passingYards", "passingTouchdowns",
        "passingInterceptions", "passing2PtConversions", "passing40PlusYardTD",
        "passing50PlusYardTD", "passing300To399YardGame", "passing400PlusYardGame",
        "passingTimesSacked"
    ],
    "rushing": [
        "rushingAttempts", "rushingYards", "rushingTouchdowns",
        "rushing40PlusYardTD", "rushing50PlusYardTD",
        "rushing100To199YardGame", "rushing200PlusYardGame"
    ],
    "receiving": [
        "receivingReceptions", "receivingYards", "receivingTargets",
        "receivingTouchdowns", "receiving2PtConversions",
        "receivingYardsAfterCatch", "receivingYardsPerReception",
        "receiving100To199YardGame", "receiving200PlusYardGame"
    ],
    "kicking": [
        "madeFieldGoals", "attemptedFieldGoals",
        "madeFieldGoalsFromUnder40", "attemptedFieldGoalsFromUnder40",
        "madeFieldGoalsFrom50Plus", "attemptedFieldGoalsFrom50Plus",
        "madeExtraPoints", "attemptedExtraPoints"
    ]
}

# Define soft constraints
constraints = [
    {"lhs": "passingCompletions", "rhs": "passingAttempts", "type": "le"},
    {"lhs": "lostFumbles", "rhs": "fumbles", "type": "le"},
    {"lhs": "madeFieldGoalsFrom50Plus", "rhs": "attemptedFieldGoalsFrom50Plus", "type": "le"},
    {"lhs": "madeFieldGoalsFromUnder40", "rhs": "attemptedFieldGoalsFromUnder40", "type": "le"},
    {"lhs": "madeFieldGoals", "rhs": "attemptedFieldGoals", "type": "le"},
    {"lhs": "madeExtraPoints", "rhs": "attemptedExtraPoints", "type": "le"},
    {"lhs": "receivingReceptions", "rhs": "receivingTargets", "type": "le"},
    {"lhs": "rushingAttempts", "rhs": "rushingAttempts", "type": "ge"},
    {"lhs": "passingAttempts", "rhs": "passingAttempts", "type": "ge"},
    {"lhs": "passingCompletions", "rhs": "passingCompletions", "type": "ge"},
]

def soft_constraint_loss(preds, constraints=constraints):
    """
    Compute a soft penalty for predicted outputs that violate logical rules.
    """
    loss = 0.0
    for c in constraints:
        lhs = preds.get(c["lhs"])
        rhs = preds.get(c["rhs"])
        if lhs is None or rhs is None:
            continue
        if c["type"] == "le":
            loss += torch.relu(lhs - rhs).mean()
        elif c["type"] == "ge":
            loss += torch.relu(-lhs).mean()
    return loss

def categorical_gate_penalty(context, predictions, features, lambda_=10.0):
    penalty = 0.0
    feature_idx = {name: i for i, name in enumerate(features)}

    for category, feature_list in CATEGORIES.items():
        idxs = [feature_idx[f] for f in feature_list if f in feature_idx]
        if not idxs:
            continue

        context_vals = context[:, :, idxs]  # (B, context_len, C)
        has_nonzero = (context_vals.abs().sum(dim=2) > 0).any(dim=1)  # (B,)

        pred_vals = predictions[:, :, idxs]  # (B, forecast_len, C)
        pred_energy = pred_vals.abs().sum(dim=(1, 2))  # (B,)

        category_penalty = (~has_nonzero).float() * pred_energy  # (B,)
        penalty += category_penalty.mean()

    return lambda_ * penalty

def create_padding_mask(context_tensor):
    """
    Given a (B, context_len, F) tensor, return a (B, context_len) mask with 1s where the row has any nonzero value.
    This is used to build attention masks for the decoder.
    """
    return (context_tensor.abs().sum(dim=-1) > 0).int()

def generate_src_key_padding_mask(context_tensor):
    """
    Convert 1s/0s from create_padding_mask into a boolean mask for Transformer
    True where we want to ignore (i.e. padding), False where data is real.
    """
    return create_padding_mask(context_tensor) == 0
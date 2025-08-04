import torch

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
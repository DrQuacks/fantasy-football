# Statistical Columns (as provided)

PASSING = [
    "passingYards", "passingTouchdowns", "passingInterceptions",
    "passing40PlusYardTD", "passing50PlusYardTD",
    "passing300To399YardGame", "passing400PlusYardGame",
    "passing2PtConversions", "passingCompletionPercentage",
]

RUSHING = [
    "rushingYards", "rushingTouchdowns",
    "rushing40PlusYardTD", "rushing50PlusYardTD",
    "rushing100To199YardGame", "rushing200PlusYardGame",
    "rushingYardsPerAttempt",
]

RECEIVING = [
    "receivingYards", "receivingReceptions", "receivingTouchdowns",
    "receivingTargets", "receivingYardsAfterCatch", "receivingYardsPerReception",
    "receiving100To199YardGame", "receiving200PlusYardGame",
]

KICKING = [
    "madeExtraPoints", "attemptedFieldGoals",
    "madeFieldGoalsFromUnder40", "madeFieldGoalsFrom50Plus",
]

OTHER = [
    "fumbles", "lostFumbles", "turnovers", "points"
]

# Position-specific targets
QB_TARGETS  = PASSING + RUSHING + OTHER                     # QB: passing + rushing + other
SKILL_TARGETS = RUSHING + RECEIVING + OTHER                 # RB/WR/TE: rushing + receiving + other
RB_TARGETS  = SKILL_TARGETS
WR_TARGETS  = SKILL_TARGETS
TE_TARGETS  = SKILL_TARGETS
K_TARGETS   = KICKING + ["points"]                          # K: kicking + points only

# Single map used by dataloaders to auto-pick target_cols
POSITION_TARGETS = {
    "QB": QB_TARGETS,
    "RB": RB_TARGETS,
    "WR": WR_TARGETS,
    "TE": TE_TARGETS,
    "K":  K_TARGETS,
}
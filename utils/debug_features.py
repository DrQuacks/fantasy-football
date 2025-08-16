import pandas as pd
import torch
from ml.model import TransformerDecoderOnly
from ml.dataset import FantasyFootballDataset

# Load the normalized data
df = pd.read_parquet("data/fantasy_weekly_stats_normalized.parquet")
print(f"DataFrame shape: {df.shape}")
print(f"DataFrame columns: {len(df.columns)}")

# Define features
NON_DERIVED_FIELDS = [
    'receivingReceptions', 'receivingYards', 'receivingTouchdowns', 'receivingTargets',
    'receivingYardsAfterCatch', 'receiving100To199YardGame', 'receiving200PlusYardGame',
    'passingAttempts', 'passingCompletions', 'passingYards', 'passingTouchdowns',
    'passingInterceptions', 'passing40PlusYardTD', 'passing50PlusYardTD',
    'passing300To399YardGame', 'passing400PlusYardGame', 'passing2PtConversions',
    'rushingAttempts', 'rushingYards', 'rushing40PlusYardTD', 'rushing50PlusYardTD',
    'rushing100To199YardGame', 'rushing200PlusYardGame', 'rushingTouchdowns',
    'passingTimesSacked', 'fumbles', 'lostFumbles', 'turnovers',
    'madeFieldGoalsFrom50Plus', 'attemptedFieldGoalsFrom50Plus',
    'madeFieldGoalsFromUnder40', 'attemptedFieldGoalsFromUnder40',
    'madeFieldGoals', 'attemptedFieldGoals', 'madeExtraPoints', 'attemptedExtraPoints'
]

DEFENSE_FEATURES = [
    'def_pi_receivingYards', 'def_pi_receivingReceptions', 'def_pi_receivingTouchdowns', 
    'def_pi_receivingTargets', 'def_pi_receivingYardsAfterCatch', 
    'def_pi_receiving100To199YardGame', 'def_pi_receiving200PlusYardGame',
    'def_pi_rushingYards', 'def_pi_rushingTouchdowns', 'def_pi_rushingAttempts',
    'def_pi_rushing40PlusYardTD', 'def_pi_rushing50PlusYardTD', 
    'def_pi_rushing100To199YardGame', 'def_pi_rushing200PlusYardGame',
    'def_pi_passingYards', 'def_pi_passingTouchdowns', 'def_pi_passingInterceptions',
    'def_pi_passingAttempts', 'def_pi_passingCompletions', 'def_pi_passing40PlusYardTD',
    'def_pi_passing50PlusYardTD', 'def_pi_passing300To399YardGame', 
    'def_pi_passing400PlusYardGame', 'def_pi_passing2PtConversions',
    'def_pi_madeFieldGoals', 'def_pi_attemptedFieldGoals', 'def_pi_madeExtraPoints', 
    'def_pi_attemptedExtraPoints', 'def_pi_madeFieldGoalsFrom50Plus', 
    'def_pi_attemptedFieldGoalsFrom50Plus', 'def_pi_madeFieldGoalsFromUnder40', 
    'def_pi_attemptedFieldGoalsFromUnder40'
]

# Check which features exist in the dataframe
available_non_derived = [f for f in NON_DERIVED_FIELDS if f in df.columns]
available_defense = [f for f in DEFENSE_FEATURES if f in df.columns]

print(f"Available non-derived features: {len(available_non_derived)}")
print(f"Available defense features: {len(available_defense)}")

# Build feature lists
OPPONENT_ONE_HOT_COLS = [c for c in df.columns if c.startswith('opp_')]
INPUT_FEATURES = available_non_derived + available_defense + OPPONENT_ONE_HOT_COLS
TARGET_FEATURES = available_non_derived

print(f"Input features: {len(INPUT_FEATURES)}")
print(f"Target features: {len(TARGET_FEATURES)}")
print(f"Opponent one-hot features: {len(OPPONENT_ONE_HOT_COLS)}")

# Print the exact 36 features being predicted
print("\n=== 36 FEATURES BEING PREDICTED BY THE MODEL ===")
for i, feature in enumerate(TARGET_FEATURES, 1):
    print(f"{i:2d}. {feature}")

print(f"\nTotal target features: {len(TARGET_FEATURES)}")

# Create a small dataset
dataset = FantasyFootballDataset(
    parquet_path="data/fantasy_weekly_stats_normalized.parquet",
    input_features=INPUT_FEATURES,
    target_features=TARGET_FEATURES,
    context_length=24,
    forecast_length=4,
    mode="next",
    known_future_features=OPPONENT_ONE_HOT_COLS,
)

print(f"Dataset length: {len(dataset)}")

# Get one sample
context, future_known, targets, masks = dataset[0]
print(f"Context shape: {context.shape}")
print(f"Future known shape: {future_known.shape}")
print(f"Targets shape: {targets.shape}")
print(f"Masks shape: {masks.shape}")

# Create model
model = TransformerDecoderOnly(
    input_dim=len(INPUT_FEATURES),
    model_dim=128,
    num_heads=4,
    num_layers=4,
    dropout=0.1,
    output_dim=len(TARGET_FEATURES),
    context_length=24,
    forecast_length=4,
    known_future_dim=len(OPPONENT_ONE_HOT_COLS),
)

print(f"Model input_dim: {len(INPUT_FEATURES)}")
print(f"Model output_dim: {len(TARGET_FEATURES)}")

# Test forward pass
context_tensor = context.unsqueeze(0)
future_known_tensor = future_known.unsqueeze(0)
output = model(context_tensor, future_known=future_known_tensor)
print(f"Model output shape: {output.shape}")
print(f"Expected target shape: {targets.shape}")

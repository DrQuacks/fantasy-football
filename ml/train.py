import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
import matplotlib.pyplot as plt
from tqdm import tqdm

from model import TransformerDecoderOnly
from dataset import FantasyFootballDataset
from normalize_utils import load_stats, apply_normalization
from soft_constraints import soft_constraint_loss, categorical_gate_penalty, generate_src_key_padding_mask

import pandas as pd

# --- Configuration ---
EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 1e-4
CONTEXT_LENGTH = 24
FORECAST_LENGTH = 4
MODE = "next"
VAL_SPLIT = 0.2

NORMALIZED_PARQUET = "data/fantasy_weekly_stats_normalized.parquet"
STATS_PATH = "data/normalization_stats.json"

# Define base feature lists
BASE_FEATURES = [
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

# Build input feature list dynamically
df_cols = pd.read_parquet(NORMALIZED_PARQUET).columns
OPPONENT_ONE_HOT_COLS = [c for c in df_cols if c.startswith('opp_')]

# Filter to only include features that exist in the data
available_base_features = [f for f in BASE_FEATURES if f in df_cols]
available_defense_features = [f for f in DEFENSE_FEATURES if f in df_cols]

INPUT_FEATURES = available_base_features + available_defense_features + OPPONENT_ONE_HOT_COLS
NON_DERIVED_FIELDS = available_base_features  # These are our target features
KNOWN_FUTURE_FEATURES = OPPONENT_ONE_HOT_COLS  # Only opponent is known in future

print(f"Input features: {len(INPUT_FEATURES)}")
print(f"Target features: {len(NON_DERIVED_FIELDS)}")
print(f"Defense features: {len(available_defense_features)}")
print(f"Opponent one-hot features: {len(OPPONENT_ONE_HOT_COLS)}")

# --- Device setup ---
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")

# --- Load dataset ---
full_dataset = FantasyFootballDataset(
    parquet_path=NORMALIZED_PARQUET,
    input_features=INPUT_FEATURES,
    target_features=NON_DERIVED_FIELDS,
    context_length=CONTEXT_LENGTH,
    forecast_length=FORECAST_LENGTH,
    mode=MODE,
    known_future_features=KNOWN_FUTURE_FEATURES,
)

val_size = int(len(full_dataset) * VAL_SPLIT)
train_size = len(full_dataset) - val_size
train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

# --- Initialize model ---
model = TransformerDecoderOnly(
    input_dim=len(INPUT_FEATURES),
    model_dim=128,
    num_heads=4,
    num_layers=4,
    dropout=0.1,
    output_dim=len(NON_DERIVED_FIELDS),
    context_length=CONTEXT_LENGTH,
    forecast_length=FORECAST_LENGTH,
    known_future_dim=len(KNOWN_FUTURE_FEATURES),
).to(device)

optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
loss_fn = nn.MSELoss(reduction='none')

train_losses, val_losses = [], []

for epoch in range(EPOCHS):
    model.train()
    total_train_loss = 0.0
    for inputs, future_known, targets, masks in tqdm(train_loader, desc=f"Epoch {epoch + 1}/{EPOCHS} [Train]"):
        inputs, future_known, targets, masks = inputs.to(device), future_known.to(device), targets.to(device), masks.to(device)

        optimizer.zero_grad()
        context_mask = generate_src_key_padding_mask(inputs)
        outputs = model(inputs, future_known=future_known, src_key_padding_mask=context_mask.to(device))
        preds_dict = {key: outputs[..., idx] for idx, key in enumerate(NON_DERIVED_FIELDS)}
        constraint_penalty = soft_constraint_loss(preds_dict)

        gate_penalty = categorical_gate_penalty(
            context=inputs,  # shape: (B, context_len, F)
            predictions=outputs,  # shape: (B, forecast_len, F)
            features=NON_DERIVED_FIELDS,
            lambda_=10.0
        )

        # Compute MSE loss
        mse_loss = loss_fn(outputs, targets)  # Shape: (B, forecast_len, num_features)
        # Expand masks to match feature dimensions
        masks_expanded = masks.unsqueeze(-1).expand_as(mse_loss)  # Shape: (B, forecast_len, num_features)
        masked_mse_loss = (mse_loss * masks_expanded).sum() / masks_expanded.sum()

        # Total loss
        total_loss = masked_mse_loss + constraint_penalty + gate_penalty
        total_loss.backward()
        optimizer.step()

        total_train_loss += total_loss.item()

    # Validation
    model.eval()
    total_val_loss = 0.0
    with torch.no_grad():
        for inputs, future_known, targets, masks in tqdm(val_loader, desc=f"Epoch {epoch + 1}/{EPOCHS} [Val]"):
            inputs, future_known, targets, masks = inputs.to(device), future_known.to(device), targets.to(device), masks.to(device)

            context_mask = generate_src_key_padding_mask(inputs)
            outputs = model(inputs, future_known=future_known, src_key_padding_mask=context_mask.to(device))
            preds_dict = {key: outputs[..., idx] for idx, key in enumerate(NON_DERIVED_FIELDS)}
            constraint_penalty = soft_constraint_loss(preds_dict)

            gate_penalty = categorical_gate_penalty(
                context=inputs,
                predictions=outputs,
                features=NON_DERIVED_FIELDS,
                lambda_=1.0
            )

            mse_loss = loss_fn(outputs, targets)  # Shape: (B, forecast_len, num_features)
            # Expand masks to match feature dimensions
            masks_expanded = masks.unsqueeze(-1).expand_as(mse_loss)  # Shape: (B, forecast_len, num_features)
            masked_mse_loss = (mse_loss * masks_expanded).sum() / masks_expanded.sum()

            total_loss = masked_mse_loss + constraint_penalty + gate_penalty
            total_val_loss += total_loss.item()

    avg_train_loss = total_train_loss / len(train_loader)
    avg_val_loss = total_val_loss / len(val_loader)
    train_losses.append(avg_train_loss)
    val_losses.append(avg_val_loss)

    print(f"Epoch {epoch + 1}/{EPOCHS}: Train Loss: {avg_train_loss:.6f}, Val Loss: {avg_val_loss:.6f}")

# Save the model
torch.save(model.state_dict(), "decoder_model.pth")
print("✅ Model saved to decoder_model.pth")

# Plot training curves
plt.figure(figsize=(10, 6))
plt.plot(train_losses, label='Training Loss')
plt.plot(val_losses, label='Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training and Validation Loss')
plt.legend()
plt.grid(True)
plt.savefig('training_val_loss_curve.png')
plt.show()

print(f"✅ Training complete! Final train loss: {train_losses[-1]:.6f}, Final val loss: {val_losses[-1]:.6f}")

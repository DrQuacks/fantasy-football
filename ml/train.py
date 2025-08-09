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

# Build input feature list: numeric stats + one-hot opponent columns
df_cols = pd.read_parquet(NORMALIZED_PARQUET).columns
OPPONENT_ONE_HOT_COLS = [c for c in df_cols if c.startswith('opp_')]
INPUT_FEATURES = NON_DERIVED_FIELDS + OPPONENT_ONE_HOT_COLS
KNOWN_FUTURE_FEATURES = OPPONENT_ONE_HOT_COLS

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
            lambda_=100.0  # strength of penalty
        )

        mse = loss_fn(outputs, targets).mean(dim=-1)
        masked_mse = (mse * masks).sum() / masks.sum().clamp(min=1.0)

        loss = masked_mse + constraint_penalty + gate_penalty
        loss.backward()
        optimizer.step()

        total_train_loss += loss.item()

    avg_train_loss = total_train_loss / len(train_loader)
    train_losses.append(avg_train_loss)

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
                context=inputs,  # shape: (B, context_len, F)
                predictions=outputs,  # shape: (B, forecast_len, F)
                features=NON_DERIVED_FIELDS,
                lambda_=10.0  # strength of penalty
            )

            mse = loss_fn(outputs, targets).mean(dim=-1)
            masked_mse = (mse * masks).sum() / masks.sum().clamp(min=1.0)

            loss = masked_mse + constraint_penalty + gate_penalty
            total_val_loss += loss.item()

    avg_val_loss = total_val_loss / len(val_loader)
    val_losses.append(avg_val_loss)

    print(f"✅ Epoch {epoch + 1} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

# --- Save model ---
torch.save(model.state_dict(), "decoder_model.pth")
print("✅ Model saved to decoder_model.pth")

# --- Plot losses ---
plt.figure(figsize=(10, 6))
plt.plot(range(1, EPOCHS + 1), train_losses, label="Train", marker="o")
plt.plot(range(1, EPOCHS + 1), val_losses, label="Validation", marker="x")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Training and Validation Loss")
plt.legend()
plt.grid(True)
plt.savefig("training_val_loss_curve.png")
plt.show()

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
from tqdm import tqdm

from model import TransformerDecoderModel
from dataset import FantasyFootballDataset
from normalize_utils import load_stats, apply_normalization
from soft_constraints import soft_constraint_loss

import pandas as pd

# --- Configuration ---
EPOCHS = 30
BATCH_SIZE = 32
LEARNING_RATE = 1e-4
CONTEXT_LENGTH = 5
FORECAST_LENGTH = 1
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

# --- Device setup ---
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")

# --- Load dataset ---
dataset = FantasyFootballDataset(
    parquet_path=NORMALIZED_PARQUET,
    input_features=NON_DERIVED_FIELDS,
    target_features=NON_DERIVED_FIELDS,
    context_length=CONTEXT_LENGTH,
    forecast_length=FORECAST_LENGTH,
    mode="next"
)

loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

# --- Initialize model ---
model = TransformerDecoderModel(
    input_dim=len(NON_DERIVED_FIELDS),
    model_dim=128,
    num_heads=4,
    num_layers=4,
    dropout=0.1,
    output_dim=len(NON_DERIVED_FIELDS)
).to(device)

optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
loss_fn = nn.MSELoss()

# --- Training loop ---
epoch_losses = []

for epoch in range(EPOCHS):
    model.train()
    total_loss = 0.0

    for inputs, targets in tqdm(loader, desc=f"Epoch {epoch + 1}/{EPOCHS}"):
        inputs, targets = inputs.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)

        task_loss = loss_fn(outputs, targets)
        preds_dict = {key: outputs[..., idx] for idx, key in enumerate(NON_DERIVED_FIELDS)}
        constraint_penalty = soft_constraint_loss(preds_dict)
        loss = task_loss + constraint_penalty

        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    avg_loss = total_loss / len(loader)
    epoch_losses.append(avg_loss)
    print(f"Epoch {epoch + 1}: loss = {avg_loss:.4f}")

# --- Save model ---
torch.save(model.state_dict(), "decoder_model.pth")
print("✅ Model saved to decoder_model.pth")

# --- Plot training loss ---
plt.figure(figsize=(10, 6))
plt.plot(range(1, EPOCHS + 1), epoch_losses, marker='o')
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Training Loss Over Epochs")
plt.grid(True)
plt.savefig("training_loss_curve.png")
plt.show()
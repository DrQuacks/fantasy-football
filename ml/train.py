import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from model import DecoderOnlyTransformer
from dataset import FantasyFootballDataset
from loss import compute_loss_with_soft_constraints

# --- Configuration ---
EPOCHS = 30
BATCH_SIZE = 32
LEARNING_RATE = 1e-4
SEQ_LENGTH = 5  # number of past weeks or years to use
TARGET_COLUMNS = [...]  # <- fill in with your non-derived features
DATA_PATH = "processed_fantasy_stats.parquet"

# --- Device setup ---
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")

# --- Load data ---
dataset = FantasyFootballDataset(DATA_PATH, seq_length=SEQ_LENGTH, target_columns=TARGET_COLUMNS)
train_loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

# --- Model, optimizer, loss ---
model = DecoderOnlyTransformer(
    input_dim=dataset.input_dim,
    hidden_dim=128,
    num_layers=4,
    num_heads=4,
    dropout=0.1,
    output_dim=dataset.output_dim
).to(device)

optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

# --- Training loop ---
for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0

    for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}"):
        inputs, targets = batch
        inputs, targets = inputs.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)

        loss = compute_loss_with_soft_constraints(outputs, targets, target_columns=TARGET_COLUMNS)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    avg_loss = running_loss / len(train_loader)
    print(f"✅ Epoch {epoch+1}: Loss = {avg_loss:.4f}")

# --- Save model ---
torch.save(model.state_dict(), "decoder_transformer.pth")
print("📦 Model saved to decoder_transformer.pth")
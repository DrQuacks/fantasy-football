import torch
import matplotlib.pyplot as plt
import pandas as pd

from model import TransformerDecoderOnly
from normalize_utils import load_stats, reverse_normalization
from dataset import FantasyFootballDataset

# --- Config ---
MODEL_PATH = "decoder_model.pth"
PARQUET_PATH = "data/fantasy_weekly_stats_normalized.parquet"
NORMALIZATION_STATS = "data/normalization_stats.json"
PLAYER_NAME = "CeeDee Lamb"
YEAR = 2024
CONTEXT_LENGTH = 12
FORECAST_LENGTH = 4
FEATURES = [
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

# --- Load dataset and model ---
dataset = FantasyFootballDataset(
    parquet_path=PARQUET_PATH,
    input_features=FEATURES,
    target_features=FEATURES,
    context_length=CONTEXT_LENGTH,
    forecast_length=FORECAST_LENGTH,
    mode="next"
)

model = TransformerDecoderOnly(
    input_dim=len(FEATURES),
    model_dim=128,
    num_heads=4,
    num_layers=4,
    dropout=0.1,
    output_dim=len(FEATURES),
    context_length=CONTEXT_LENGTH,
    forecast_length=FORECAST_LENGTH
)
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device("cpu")))
model.eval()

# --- Pick a sample for a given player/year ---
df = pd.read_parquet(PARQUET_PATH)
df = df[(df.name == PLAYER_NAME) & (df.year == YEAR)].sort_values("week")

context = df.head(CONTEXT_LENGTH)[FEATURES].to_numpy(dtype="float32")
actual = df.iloc[CONTEXT_LENGTH:CONTEXT_LENGTH + FORECAST_LENGTH][FEATURES].reset_index(drop=True)
context_tensor = torch.tensor(context).unsqueeze(0)  # shape: (1, context_length, input_dim)

# --- Predict ---
with torch.no_grad():
    pred = model(context_tensor).squeeze(0).numpy()  # shape: (forecast_length, feature_dim)

# --- Denormalize ---
stats = load_stats(NORMALIZATION_STATS)
pred_df = pd.DataFrame(reverse_normalization(pred, FEATURES, stats), columns=FEATURES)
pred_df["week"] = list(range(CONTEXT_LENGTH + 1, CONTEXT_LENGTH + FORECAST_LENGTH + 1))
actual_df = pd.DataFrame(reverse_normalization(actual.to_numpy(), FEATURES, stats), columns=FEATURES)
actual_df["week"] = pred_df["week"]

# --- Plot ---
plt.figure(figsize=(10, 6))
for feat in FEATURES:
    plt.plot(pred_df["week"], pred_df[feat], label=f"Predicted {feat}", marker="o")
    plt.plot(actual_df["week"], actual_df[feat], label=f"Actual {feat}", marker="x", linestyle="--")

plt.title(f"Predicted vs Actual Stats for {PLAYER_NAME} Weeks {CONTEXT_LENGTH+1}-{CONTEXT_LENGTH+FORECAST_LENGTH}")
plt.xlabel("Week")
plt.ylabel("Stat Value")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

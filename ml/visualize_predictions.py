import torch
import matplotlib.pyplot as plt
import pandas as pd

from model import TransformerDecoderOnly
from normalize_utils import load_stats, reverse_normalization
import plotly.graph_objects as go


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

# Defense features
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

# --- Build feature lists with opponent one-hot ---
all_cols = pd.read_parquet(PARQUET_PATH).columns
OPPONENT_ONE_HOT_COLS = [c for c in all_cols if c.startswith('opp_')]
INPUT_FEATURES = FEATURES + DEFENSE_FEATURES + OPPONENT_ONE_HOT_COLS
TARGET_FEATURES = FEATURES

model = TransformerDecoderOnly(
    input_dim=len(INPUT_FEATURES),
    model_dim=128,
    num_heads=4,
    num_layers=4,
    dropout=0.1,
    output_dim=len(TARGET_FEATURES),
    context_length=CONTEXT_LENGTH,
    forecast_length=FORECAST_LENGTH,
    known_future_dim=len(OPPONENT_ONE_HOT_COLS),
)
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device("cpu")))
model.eval()

# --- Pick a sample for a given player/year ---
df = pd.read_parquet(PARQUET_PATH)
df = df[(df.name == PLAYER_NAME) & (df.year == YEAR)].sort_values("week")

context = df.head(CONTEXT_LENGTH)[INPUT_FEATURES].to_numpy(dtype="float32")
actual = df.iloc[CONTEXT_LENGTH:CONTEXT_LENGTH + FORECAST_LENGTH][TARGET_FEATURES].reset_index(drop=True)
future_known = df.iloc[CONTEXT_LENGTH:CONTEXT_LENGTH + FORECAST_LENGTH][OPPONENT_ONE_HOT_COLS].to_numpy(dtype="float32") if OPPONENT_ONE_HOT_COLS else pd.DataFrame(index=actual.index).to_numpy(dtype="float32")
context_tensor = torch.tensor(context).unsqueeze(0)  # shape: (1, context_length, input_dim)
future_known_tensor = torch.tensor(future_known).unsqueeze(0)  # shape: (1, forecast_length, known_future_dim)

# --- Predict ---
with torch.no_grad():
    pred = model(context_tensor, future_known=future_known_tensor).squeeze(0).numpy()

# --- Denormalize ---
stats = load_stats(NORMALIZATION_STATS)
pred_df = pd.DataFrame(reverse_normalization(pred, TARGET_FEATURES, stats), columns=TARGET_FEATURES)
pred_df["week"] = list(range(CONTEXT_LENGTH + 1, CONTEXT_LENGTH + FORECAST_LENGTH + 1))
actual_df = pd.DataFrame(reverse_normalization(actual.to_numpy(), TARGET_FEATURES, stats), columns=TARGET_FEATURES)
actual_df["week"] = pred_df["week"]

# # --- Plot ---
# plt.figure(figsize=(10, 6))
# for feat in FEATURES:
#     plt.plot(pred_df["week"], pred_df[feat], label=f"Predicted {feat}", marker="o")
#     plt.plot(actual_df["week"], actual_df[feat], label=f"Actual {feat}", marker="x", linestyle="--")

# plt.title(f"Predicted vs Actual Stats for {PLAYER_NAME} Weeks {CONTEXT_LENGTH+1}-{CONTEXT_LENGTH+FORECAST_LENGTH}")
# plt.xlabel("Week")
# plt.ylabel("Stat Value")
# plt.grid(True)
# plt.legend()
# plt.tight_layout()
# plt.show()


# Create a figure with dropdown
fig = go.Figure()

for feat in TARGET_FEATURES:
    # Predicted trace
    fig.add_trace(go.Scatter(
        x=pred_df["week"], y=pred_df[feat],
        mode="lines+markers",
        name=f"Predicted {feat}",
        visible=(feat == TARGET_FEATURES[0])  # Only show first initially
    ))

    # Actual trace
    fig.add_trace(go.Scatter(
        x=actual_df["week"], y=actual_df[feat],
        mode="lines+markers",
        line=dict(dash="dash"),
        name=f"Actual {feat}",
        visible=(feat == TARGET_FEATURES[0])
    ))

# Create dropdown options
dropdown_buttons = []
for i, feat in enumerate(TARGET_FEATURES):
    visibility = [False] * len(TARGET_FEATURES) * 2
    visibility[i * 2] = True      # Predicted
    visibility[i * 2 + 1] = True  # Actual
    dropdown_buttons.append(dict(
        label=feat,
        method="update",
        args=[{"visible": visibility},
              {"title": f"{feat}: Predicted vs Actual"}]
    ))

fig.update_layout(
    updatemenus=[dict(
        active=0,
        buttons=dropdown_buttons,
        x=1.2,
        y=1.0
    )],
    title=f"{TARGET_FEATURES[0]}: Predicted vs Actual for {PLAYER_NAME}",
    xaxis_title="Week",
    yaxis_title="Value",
    height=550,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="center",
        x=0.5
    )
)

fig.show()


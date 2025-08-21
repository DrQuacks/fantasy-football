
---

# 🔎 Walkthrough: How the Pieces Work

### Step 1 — Data Load
- `load_data.py` reads all `.parquet` files into Pandas DataFrames.
- You now have one DataFrame per position (QB, RB, WR, TE, K) and one for defenses.

### Step 2 — Dataset Construction
When you request, say, the WR dataset:

1. `FantasyDataset` receives:
   - Base DataFrame → `wr_df`
   - Context DataFrames → QB, RB, TE (not WR itself, not K)
   - Defense DataFrame → `defense_df`

2. For each WR row:
   - Extract that player’s features → `player_features`
   - Find teammates:
     - Get **all QBs** on same team/week → sort by `passingYards` → keep top 2 → pad if <2
     - Get **all RBs** → sort by `rushingYards` → keep top 3
     - Get **all WRs (excluding self)** → sort by `receivingYards` → keep top 5
     - Get **all TEs** → sort by `receivingYards` → keep top 2
   - Stack them → `(11, F)` tensor
   - Look up opponent defense in PI table → `defense_features`
   - Return dictionary + targets

### Step 3 — Collation
- The `collate_fn` batches these into tensors:
  - `(batch, F)` for players
  - `(batch, 11, F)` for teammates
  - `(batch, F)` for defense
  - `(batch, num_targets)` for targets

### Step 4 — DataLoaders
- `dataloaders.py` builds one DataLoader per position
- Example: `loaders["WR"]` iterates through WR samples with teammate + defense context included

### Step 5 — Model Input
Your model now receives:
- Player’s own stats
- Teammate stats (as a small set/sequence)
- Opponent defense context

This setup makes it easy to try models that:
- Encode teammates separately (RNN, transformer, pooling)
- Combine player, teammate, and defense embeddings before prediction
- Weight fantasy points more heavily in the loss function (coming in Section 2)


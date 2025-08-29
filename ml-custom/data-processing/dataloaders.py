# ml-custom/data-processing/dataloaders.py

from torch.utils.data import DataLoader
from .load_data import load_base_tables, load_defense_table
from .fantasy_dataset import FantasyDataset
from .collate import collate_fn

# NEW: import the canonical position->targets mapping
from models.targets import POSITION_TARGETS  # assumes ml-custom is on PYTHONPATH

def build_dataloaders(
    feature_cols,
    defense_cols=None,
    batch_size=32,
    override_target_cols_per_pos: dict | None = None,
):
    """
    Build one DataLoader per position with *automatic* target column selection.

    Args
    ----
    feature_cols : list[str]
        Columns from the player/teammate tables used as features.
    defense_cols : list[str] | None
        Columns from defense_adjusted_pi.parquet (weekly PI) to use as defense features.
    batch_size : int
        Batch size for all loaders.
    override_target_cols_per_pos : dict[str, list[str]] | None
        Optional per-position override; e.g. {"WR": ["points","receivingYards", ...]}.
        If provided for a position, it replaces POSITION_TARGETS[pos].

    Returns
    -------
    dict[str, DataLoader]
        A dict mapping position name -> DataLoader.
    """
    base_tables = load_base_tables()
    defense_df = load_defense_table()
    loaders = {}

    for pos, base_df in base_tables.items():
        # context = all other positions except self and K (unless base is K)
        context_dfs = {
            name: df for name, df in base_tables.items()
            if (name != pos and (pos == "K" or name != "K"))
        }

        # Auto-pick target_cols for this position, with optional override
        target_cols = (
            override_target_cols_per_pos[pos]
            if (override_target_cols_per_pos and pos in override_target_cols_per_pos)
            else POSITION_TARGETS[pos]
        )

        dataset = FantasyDataset(
            position=pos,
            base_df=base_df,
            context_dfs=context_dfs,
            defense_df=defense_df,
            feature_cols=feature_cols,
            target_cols=target_cols,     # <— auto-aligned with model heads
            defense_cols=defense_cols,
        )

        loaders[pos] = DataLoader(
            dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn
        )

    return loaders

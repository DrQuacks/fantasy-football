from torch.utils.data import DataLoader
from .load_data import load_base_tables, load_defense_table
from .fantasy_dataset import FantasyDataset
from .collate import collate_fn

def build_dataloaders(feature_cols, target_cols, batch_size=32):
    base_tables = load_base_tables()
    defense_df = load_defense_table()
    loaders = {}

    for pos, base_df in base_tables.items():
        # context = all other positions except self and K (unless base is K)
        context_dfs = {
            name: df for name, df in base_tables.items()
            if (name != pos and (pos == "K" or name != "K"))
        }

        dataset = FantasyDataset(
            position=pos,
            base_df=base_df,
            context_dfs=context_dfs,
            defense_df=defense_df,
            feature_cols=feature_cols,
            target_cols=target_cols,
        )

        loaders[pos] = DataLoader(
            dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn
        )

    return loaders

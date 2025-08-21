import pandas as pd

def load_base_tables():
    """Load all position-specific .parquet tables."""
    qb_df = pd.read_parquet("../data/qb_data.parquet")
    rb_df = pd.read_parquet("../data/rb_data.parquet")
    wr_df = pd.read_parquet("../data/wr_data.parquet")
    te_df = pd.read_parquet("../data/te_data.parquet")
    k_df  = pd.read_parquet("../data/k_data.parquet")

    return {
        "QB": qb_df,
        "RB": rb_df,
        "WR": wr_df,
        "TE": te_df,
        "K" : k_df,
    }

def load_defense_table():
    """Load defense adjusted PI data."""
    return pd.read_parquet("../data/defense_adjusted_pi.parquet")

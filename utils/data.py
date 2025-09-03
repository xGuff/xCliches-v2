import pandas as pd

# Standardized CSV loader for all core data

def load_core_data():
    transcripts_df = pd.read_csv("data/raw/transcripts.csv")
    cliches_df     = pd.read_csv("data/processed/cliche_hits.csv")
    managers_df    = pd.read_csv("data/raw/managers.csv")
    for df in (transcripts_df, cliches_df, managers_df):
        df.columns = [c.strip().lower() for c in df.columns]
    return transcripts_df, cliches_df, managers_df

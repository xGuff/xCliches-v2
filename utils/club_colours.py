import pandas as pd

def get_club_colors():
    df = pd.read_csv("data/raw/club_colours.csv")
    df.columns = [c.strip().lower() for c in df.columns]
    club_col = next((c for c in df.columns if "club" in c), df.columns[0])
    color_col_candidates = [c for c in df.columns if any(k in c for k in ["colour", "color", "hex"])]
    color_col = color_col_candidates[0] if color_col_candidates else df.columns[-1]
    df[color_col] = df[color_col].astype(str).str.strip()
    df[color_col] = df[color_col].str.replace(r"^((?!#).+)$", r"#\1", regex=True)
    return {row[club_col]: row[color_col] for _, row in df.iterrows() if pd.notna(row[color_col])}

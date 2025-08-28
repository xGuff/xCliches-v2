import pandas as pd
from datetime import datetime

# Example: Load manager data from a source (could be scraped or manually updated)
# For now, just read the existing CSV and print it

def load_manager_tenures(csv_path):
    df = pd.read_csv(csv_path)
    print(df)
    return df

if __name__ == "__main__":
    csv_path = "../data/raw/manager_tenures.csv"
    df = load_manager_tenures(csv_path)
    # Add logic here to update or validate tenures as needed
    # For future: scrape or update tenures automatically

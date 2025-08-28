
import requests
import pandas as pd
from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("API_FOOTBALL_KEY")

headers = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}


# Premier League league_id
league_id = 39

def get_season_boundaries(season):
    # Premier League usually starts in August and ends in May
    return date(season, 8, 1), date(season + 1, 5, 30)

def fetch_team_ids(season):
    # teams_url = f'https://v3.football.api-sports.io/teams?league={league_id}&season={season}'
    teams_url = f'https://v3.football.api-sports.io/teams?league={league_id}&season={season}'
    teams_res = requests.get(teams_url, headers=headers)
    print(teams_res.json())
    teams = teams_res.json().get("response", [])
    # print(teams)
    return {team["team"]["id"]: team["team"]["name"] for team in teams}

def parse_date(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").date() if d else None
    except:
        return None

def fetch_manager_tenures_for_season(season):
    SEASON_START, SEASON_END = get_season_boundaries(season)
    team_ids = fetch_team_ids(season)
    tenures = []
    for team_id, team_name in team_ids.items():
        print(f"🔍 {team_name} ({season}/{season+1})")
        coach_url = f"https://v3.football.api-sports.io/coachs?team={team_id}"
        coach_res = requests.get(coach_url, headers=headers)
        if coach_res.status_code != 200:
            print(f"  ❌ Failed: {coach_res.json()}")
            continue
        for coach in coach_res.json().get("response", []):
            name = coach.get("name", "Unknown")
            photo_url = coach.get("photo", "")
            for job in coach.get("career", []):
                job_team_id = job.get("team", {}).get("id")
                if job_team_id != team_id:
                    continue
                start_date = parse_date(job.get("start"))
                end_date = parse_date(job.get("end"))
                if not start_date:
                    continue
                if end_date and end_date < SEASON_START:
                    continue
                if start_date > SEASON_END:
                    continue
                if end_date and (end_date - start_date).days < 14:
                    continue
                effective_start = max(start_date, SEASON_START)
                tenures.append({
                    "club": team_name,
                    "manager": name,
                    "start_date": effective_start,
                    "end_date": end_date,
                    "photo_url": photo_url,
                    "season": f"{season}/{season+1}"
                })
    return tenures

# Blacklist of unwanted managers
BLACKLIST = {
    "J. Tindall",
    "A. Bertoldi",
    "G. Jones",
    "R. Mason",
    "S. Ireland",
    "G. Brazil",
    "J. Klopp"
}

def remove_blacklisted_managers(df, blacklist):
    cleaned_df = df[~df["manager"].isin(blacklist)]
    print(f"✅ Removed {len(df) - len(cleaned_df)} blacklisted managers.")
    return cleaned_df

def update_end_dates_based_on_successors(df):
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    updated_rows = []
    for club, group in df.groupby("club"):
        group_sorted = group.sort_values("start_date").reset_index(drop=True)
        for i in range(len(group_sorted) - 1):
            current = group_sorted.loc[i]
            next_start = group_sorted.loc[i + 1, "start_date"]
            if pd.isna(current["end_date"]) or current["end_date"] > next_start:
                group_sorted.loc[i, "end_date"] = next_start
        updated_rows.append(group_sorted)
    updated_df = pd.concat(updated_rows).sort_values(["club", "start_date"])
    return updated_df


def main():
    # Specify the seasons you want to fetch (e.g., [2024, 2025])
    seasons = [2024, 2025]
    all_tenures = []
    for season in seasons:
        tenures = fetch_manager_tenures_for_season(season)
        all_tenures.extend(tenures)
    df = pd.DataFrame(all_tenures)
    if df.empty:
        print("❌ No manager tenures were fetched. Please check your API key, network connection, and season values.")
        return
    if not set(["season", "club", "start_date"]).issubset(df.columns):
        print(f"❌ DataFrame columns missing: {df.columns.tolist()}")
        return
    df.sort_values(["season", "club", "start_date"], inplace=True)
    # Clean data
    cleaned_df = remove_blacklisted_managers(df, BLACKLIST)
    updated_df = update_end_dates_based_on_successors(cleaned_df)
    # Save
    os.makedirs("data/raw", exist_ok=True)
    updated_df.to_csv("data/raw/managers.csv", index=False)
    print(f"\n✅ Saved {len(updated_df)} manager tenures for all selected seasons to data/raw/managers.csv")

if __name__ == "__main__":
    main()

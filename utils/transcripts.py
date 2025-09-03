import os
import time
from dotenv import load_dotenv
import pandas as pd
import json
from pytube import Playlist, YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime, date
from youtube_transcript_api.proxies import WebshareProxyConfig
import re

load_dotenv()  

# Paths
PLAYLISTS_PATH = "../data/raw/playlists.csv"
MANAGERS_PATH = "../data/raw/managers.csv"
OUTPUT_PATH = "../data/raw/transcripts.csv"

# Load playlists
playlists_df = pd.read_csv(PLAYLISTS_PATH)
# Load manager tenures
managers_df = pd.read_csv(MANAGERS_PATH)
managers_df["From"] = pd.to_datetime(managers_df["From"])
managers_df["Until"] = pd.to_datetime(managers_df["Until"], errors="coerce")

PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")

ytt_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username=PROXY_USERNAME,
        proxy_password=PROXY_PASSWORD,
    )
)

# Load existing transcripts if present
if os.path.exists(OUTPUT_PATH):
    existing_df = pd.read_csv(OUTPUT_PATH)
    existing_video_ids = set(existing_df["video_id"].astype(str))
else:
    existing_video_ids = set()

# Helper: find the manager at a club on a given date
def find_manager(club, date):
    club_tenures = managers_df[managers_df["Club"] == club]
    for _, row in club_tenures.iterrows():
        start = row["From"]
        end = row["Until"] if pd.notna(row["Until"]) else pd.Timestamp.today()
        if start <= date <= end:
            return row["Name"]
    return None

def clean_text(text):
    # Remove punctuation except hyphens, and convert to lowercase
    return re.sub(r'[^\w\s-]', '', text).lower()

PRESEASON_DAY = 10
PRESEASON_MONTH = 8

data = []
for _, row in playlists_df.iterrows():
    club = row["club"]
    season = row["season"]
    playlist_url = row["playlist_url"]
    label = row.get("notes", "")
    if not isinstance(playlist_url, str) or not playlist_url.strip():
        continue
    print(f"🔍 {club} — {season}")
    try:
        playlist = Playlist(playlist_url)
    except Exception as e:
        print(f"  ❌ Could not load playlist: {e}")
        continue
    for video_url in playlist.video_urls:
        try:
            yt = YouTube(video_url)
            video_id = yt.video_id
            if str(video_id) in existing_video_ids:
                print(f"    ⏩ Skipping already saved video: {video_id}")
                continue
            publish_date = yt.publish_date.date()
            season_year = int(season.split("/")[0])
            preseason_cutoff = date(season_year, PRESEASON_MONTH, PRESEASON_DAY)
            if publish_date < preseason_cutoff:
                print(f"    ⏩ Skipping pre-season video ({publish_date})")
                continue
            manager = find_manager(club, pd.to_datetime(publish_date))
            print(f"    ⏩ Fetching transcript for {video_id}")
            transcript = ytt_api.fetch(video_id,languages=['en'])
            
            print(f"    ⏩ Fetched transcript for {video_id}")
            
            segments = [{"text": seg.text, "start": seg.start} for seg in transcript]
            full_text = " ".join([seg["text"] for seg in segments])
            cleaned_transcript = clean_text(full_text)
            
            row_dict = {
                "club": club,
                "season": season,
                "manager": manager,
                "video_id": video_id,
                "video_url": video_url,
                "publish_date": publish_date,
                "transcript_segments": json.dumps(segments),
                "transcript": full_text,
                "transcript_cleaned": cleaned_transcript
            }

            # Save immediately
            df_row = pd.DataFrame([row_dict])
            os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
            df_row.to_csv(
                OUTPUT_PATH,
                mode='a',
                header=not os.path.exists(OUTPUT_PATH),
                index=False
            )
            print(f"    ✅ Saved transcript for {video_id} to {OUTPUT_PATH}")
            existing_video_ids.add(str(video_id))
            data.append(row_dict)  # Also keep in memory for later DataFrame use
            
        except Exception as e:
            print(f"    ❌ Failed for {video_url}: {e}")

# Build full DataFrame for further processing
df = pd.DataFrame(data)
print(f"\n✅ Done! {len(df)} new transcripts processed and appended to {OUTPUT_PATH}")

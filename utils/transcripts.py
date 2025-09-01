import os
import time
import pandas as pd
import json
from pytube import Playlist, YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime, date

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

ytt_api = YouTubeTranscriptApi()

# Helper: find the manager at a club on a given date
def find_manager(club, date):
    club_tenures = managers_df[managers_df["Club"] == club]
    for _, row in club_tenures.iterrows():
        start = row["From"]
        end = row["Until"] if pd.notna(row["Until"]) else pd.Timestamp.today()
        if start <= date <= end:
            return row["Name"]
    return None

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
            publish_date = yt.publish_date.date()
            # Exclude pre-season videos
            season_year = int(season.split("/")[0])
            preseason_cutoff = date(season_year, PRESEASON_MONTH, PRESEASON_DAY)
            if publish_date < preseason_cutoff:
                # print(f"    ⏩ Skipping pre-season video ({publish_date})")
                continue
            manager = find_manager(club, pd.to_datetime(publish_date))
            transcript = ytt_api.fetch(yt.video_id)
            segments = [{"text": seg.text, "start": seg.start} for seg in transcript]
            full_text = " ".join([seg["text"] for seg in segments])
            data.append({
                "club": club,
                "season": season,
                "manager": manager,
                "video_id": yt.video_id,
                "video_url": video_url,
                "publish_date": publish_date,
                "transcript_text": full_text,
                "transcript_segments": json.dumps(segments)
            })
            time.sleep(5)
        except Exception as e:
            print(f"    ❌ Failed for {video_url}: {e}")

# Save output
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df = pd.DataFrame(data)
df.to_csv(OUTPUT_PATH, index=False)
print(f"\n✅ Done! Saved {len(df)} videos to {OUTPUT_PATH}")

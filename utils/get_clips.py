#!/usr/bin/env python3
# get_clips.py
#
# Ultra-simple clipper for cliche_hits_custom.csv
# - Uses start_time column (minus a small buffer)
# - Fixed duration per clip
# - No CLI args — edit the constants below if needed

import csv
import os
import re
import shlex
import subprocess
from pathlib import Path

# --- EDITABLE CONSTANTS ---
CSV_PATH       = "../data/processed/cliche_hits_custom.csv"
OUTPUT_DIR     = "../data/clips/ange"
START_COL      = "start_time"
URL_COL        = "youtube_link"   # if empty, falls back to video_id
ID_COL         = "video_id"
LABEL_COL      = "cliche"         # used in filename if present
START_BUFFER_S = 2.0              # seconds to subtract from start (min 0)
DURATION_S     = 10              # fixed clip length in seconds
YTDLP          = "yt-dlp"         # or full path, e.g., "/opt/homebrew/bin/yt-dlp"
REMUX_CONTAINER = "mp4"           # "mp4" or "mkv"; set "" to skip remux
# ---------------------------

YOUTUBE_WATCH_PREFIX = "https://www.youtube.com/watch?v="

def parse_time_to_seconds(x) -> float:
    """Accepts numbers or HH:MM:SS(.mmm). Returns float seconds."""
    s = str(x).strip()
    if not s:
        raise ValueError("empty time")
    # numeric?
    try:
        return float(s)
    except ValueError:
        pass
    parts = s.split(":")
    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        m, sec = parts
        return float(m) * 60 + float(sec)
    if len(parts) == 3:
        h, m, sec = parts
        return float(h) * 3600 + float(m) * 60 + float(sec)
    raise ValueError(f"Unrecognized time format: {x}")

def secs_to_hhmmssms(t: float) -> str:
    """Format seconds -> HH:MM:SS.mmm string."""
    if t < 0:
        t = 0.0
    ms = int(round((t - int(t)) * 1000))
    total = int(t)
    h = total // 3600
    m = (total % 3600) // 60
    s = (total % 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def sanitize(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[^\w\-.]+", "_", s, flags=re.UNICODE)
    return s[:120] if len(s) > 120 else s

def build_url(row: dict) -> str | None:
    url = (row.get(URL_COL) or "").strip()
    if url:
        return url
    vid = (row.get(ID_COL) or "").strip()
    if vid:
        if vid.startswith("http://") or vid.startswith("https://"):
            return vid
        return f"{YOUTUBE_WATCH_PREFIX}{vid}"
    return None

def run(cmd: list[str]) -> int:
    print("$", " ".join(shlex.quote(c) for c in cmd))
    return subprocess.run(cmd).returncode

def main():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = [fn.strip() for fn in (reader.fieldnames or [])]
        missing = []
        if START_COL not in fields:
            missing.append(START_COL)
        if (URL_COL not in fields) and (ID_COL not in fields):
            missing.append(f"{URL_COL} or {ID_COL}")
        if missing:
            raise SystemExit(f"CSV missing required column(s): {', '.join(missing)}. Found: {fields}")

        for i, row in enumerate(reader, start=2):  # start=2 accounts for header line
            url = build_url(row)
            if not url:
                print(f"Row {i}: no URL/video_id — skipping.")
                continue

            try:
                start_raw = row.get(START_COL, "")
                start_s = parse_time_to_seconds(start_raw)
            except Exception as e:
                print(f"Row {i}: bad {START_COL}='{row.get(START_COL)}' — {e} — skipping.")
                continue

            start_adj = max(0.0, start_s - START_BUFFER_S)
            end_s = start_adj + DURATION_S

            start_tc = secs_to_hhmmssms(start_adj)
            end_tc   = secs_to_hhmmssms(end_s)

            label = sanitize(row.get(LABEL_COL, "")) or "clip"

            # Output template includes video id and the exact time range
            out_template = f"{label}__%(id)s__{start_tc.replace(':','-')}--{end_tc.replace(':','-')}.%(ext)s"
            out_path = str(Path(OUTPUT_DIR) / out_template)

            cmd = [
                YTDLP,
                url,
                "--quiet",
                "--no-warnings",
                "--force-keyframes-at-cuts",
                "--download-sections", f"*{start_tc}-{end_tc}",
                "--output", out_path,
                "-f", "bv*[ext=mp4]+ba[ext=m4a]/b",
                "--retries", "5",
                "--fragment-retries", "5",
                "--concurrent-fragments", "5",
            ]
            if REMUX_CONTAINER:
                cmd += ["--remux-video", REMUX_CONTAINER]

            code = run(cmd)
            if code != 0:
                print(f"Row {i}: yt-dlp exit code {code} for {url} [{start_tc}-{end_tc}]")

if __name__ == "__main__":
    main()

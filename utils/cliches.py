#!/usr/bin/env python3
import ast
import json
import re
from pathlib import Path
import pandas as pd

def load_segments(cell):
    if pd.isna(cell):
        return []
    s = str(cell)
    try:
        return json.loads(s)
    except Exception:
        try:
            return ast.literal_eval(s)
        except Exception:
            return []

_NORM_RE = re.compile(r"[^a-z0-9\s]+")
_WS_RE = re.compile(r"\s+")

def normalize(text: str) -> str:
    if text is None:
        return ""
    t = text.lower()
    t = _NORM_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t

def build_cliche_patterns(cliche_list):
    # store (original, normalized)
    return [(c, normalize(c)) for c in cliche_list if isinstance(c, str) and c.strip()]

def scan_row_for_cliches(row, cliche_patterns):
    """
    Left-to-right greedy scan per cliché with overlap suppression:
      - Prefer single-segment match at i. If present, emit and mark cliché consumed at i.
      - Otherwise check i + (i+1) window. If present, emit and mark cliché consumed through i+1.
      - Skip re-checking a cliché where i <= last_consumed_end[cliché].
    """
    club = row.get("club", "")
    manager = row.get("manager", "")  # <-- Add this line
    season = row.get("season", "")
    publish_date = row.get("publish_date", "")
    video_id = row.get("video_id", "")

    segments = load_segments(row.get("transcript_segments", ""))
    if not isinstance(segments, list) or not segments:
        return

    norm_texts = [normalize(seg.get("text", "")) for seg in segments]
    starts = [seg.get("start", None) for seg in segments]
    raw_texts = [seg.get("text", "") for seg in segments]

    # per-cliché suppression: index up to which we've already “consumed”
    last_consumed_end = {c_raw: -1 for c_raw, _ in cliche_patterns}

    n = len(segments)
    for i in range(n):
        nt_i = norm_texts[i]
        raw_i = raw_texts[i]
        start_i = starts[i]

        for cliche_raw, cliche_norm in cliche_patterns:
            # skip if this cliché was already matched overlapping this index
            if i <= last_consumed_end[cliche_raw]:
                continue
            if not cliche_norm:
                continue

            # 1) Try single-segment match at i
            if cliche_norm in nt_i:
                start_time = float(start_i) if start_i is not None else 0.0
                yield {
                    "club": club,
                    "manager": manager,
                    "season": season,
                    "publish_date": publish_date,
                    "video_id": video_id,
                    "cliche": cliche_raw,
                    "start_time": start_time,
                    "segment_text": raw_i,
                    "youtube_link": f"https://www.youtube.com/watch?v={video_id}&t={int(round(start_time))}s",
                }
                last_consumed_end[cliche_raw] = i  # consume only this segment for this cliché
                continue  # do NOT also check the double window at this i

            # 2) If single didn't match, try cross-boundary (i, i+1)
            if i + 1 < n:
                nt_next = norm_texts[i + 1]
                raw_next = raw_texts[i + 1]
                combined_norm = (nt_i + " " + nt_next).strip()

                if cliche_norm in combined_norm:
                    start_time = float(start_i) if start_i is not None else 0.0
                    yield {
                        "club": club,
                        "manager": manager,
                        "season": season,
                        "publish_date": publish_date,
                        "video_id": video_id,
                        "cliche": cliche_raw,
                        "start_time": start_time,
                        "segment_text": (raw_i + " " + raw_next).strip(),
                        "youtube_link": f"https://www.youtube.com/watch?v={video_id}&t={int(round(start_time))}s",
                    }
                    # consume both segments for this cliché to avoid (i+1) single and future overlaps
                    last_consumed_end[cliche_raw] = i + 1

def main():
    # Hardcoded file paths (edit as needed)
    transcripts_path = Path("../data/raw/transcripts.csv")
    cliches_path = Path("../data/raw/cliches.csv")
    out_path = Path("../data/processed/cliche_hits.csv")

    df_t = pd.read_csv(transcripts_path)
    df_c = pd.read_csv(cliches_path)

    if "cliche" not in df_c.columns:
        raise ValueError("cliches.csv must contain a 'cliche' column.")

    cliche_list = df_c["cliche"].dropna().astype(str).tolist()
    cliche_patterns = build_cliche_patterns(cliche_list)

    out_rows = []
    for _, row in df_t.iterrows():
        for hit in scan_row_for_cliches(row, cliche_patterns):
            out_rows.append(hit)

    cols = ["club", "manager", "season", "publish_date", "video_id", "cliche", "start_time", "segment_text", "youtube_link"]
    df_out = pd.DataFrame(out_rows, columns=cols)

    # Sort for readability
    if not df_out.empty:
        df_out = df_out.sort_values(["club", "manager", "season", "publish_date", "video_id", "start_time", "cliche"])

        # Safety net: drop any residual exact dupes
        df_out = df_out.drop_duplicates(subset=["video_id", "cliche", "start_time", "segment_text"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_path, index=False)
    print(f"Wrote {len(df_out)} rows to {out_path}")

if __name__ == "__main__":
    main()

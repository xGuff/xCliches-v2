from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from dateutil import parser


@dataclass
class Frag:
    videos: pd.DataFrame
    transcripts: pd.DataFrame
    cliche_counts: pd.DataFrame
    aggregates_manager_gw: pd.DataFrame
    gameweeks: pd.DataFrame
    managers: pd.DataFrame
    clubs: pd.DataFrame
    stats: dict




def ensure_data(data_dir: Path, force_seed: bool = False) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    # Seed minimal placeholder data if empty or forced
    needed = [
    "videos.csv", "transcripts.csv", "cliche_counts.csv",
    "aggregates_manager_gw.csv", "gameweeks.csv", "managers.csv", "clubs.csv",
    ]
    if force_seed or any(not (data_dir / f).exists() for f in needed):
        (data_dir / "gameweeks.csv").write_text("gw,start_date,end_date\n1,2025-08-08,2025-08-14\n2,2025-08-15,2025-08-21\n3,2025-08-22,2025-08-28\n4,2025-08-29,2025-09-04\n")
        (data_dir / "managers.csv").write_text("manager_id,name,club_id,tenure_start,tenure_end\nM1,Alex Manager,CL1,2025-06-01,\nM2,Bailey Boss,CL2,2025-06-15,\n")
        (data_dir / "clubs.csv").write_text("club_id,club_name,league\nCL1,Example FC,PL\nCL2,Samples United,PL\n")
        (data_dir / "videos.csv").write_text("video_id,channel_id,club_id,manager_id,published_at,title,url,gw\nv1,c1,CL1,M1,2025-08-09T10:00:00Z,Pre‑match PC 1,https://youtu.be/demo,1\nv2,c2,CL2,M2,2025-08-16T10:00:00Z,Pre‑match PC 2,https://youtu.be/demo,2\n")
        (data_dir / "transcripts.csv").write_text("video_id,lang,is_translated,text,words_total\nv1,en,False,'at the end of the day we take it game by game',12\nv2,en,False,'fine margins but the lads showed character',9\n")
        (data_dir / "cliche_counts.csv").write_text("video_id,manager_id,gw,cliche_key,count\nv1,M1,1,at_the_end_of_the_day,1\nv1,M1,1,take_it_game_by_game,1\nv2,M2,2,fine_margins,1\nv2,M2,2,the_lads_showed_character,1\n")
        (data_dir / "aggregates_manager_gw.csv").write_text(
        "manager_id,club_id,gw,pressers,cliche_count_total,words_total,cliches_per_10k\n"
        "M1,CL1,1,1,2,12,1666.7\n"
        "M2,CL2,2,1,2,9,2222.2\n"
        )




def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()




def load_data_bundle(data_dir: Path) -> Frag:
    v = _read_csv(data_dir / "videos.csv")
    t = _read_csv(data_dir / "transcripts.csv")
    c = _read_csv(data_dir / "cliche_counts.csv")
    a = _read_csv(data_dir / "aggregates_manager_gw.csv")
    g = _read_csv(data_dir / "gameweeks.csv")
    m = _read_csv(data_dir / "managers.csv")
    cl = _read_csv(data_dir / "clubs.csv")


    stats = {
    "n_managers": m["manager_id"].nunique() if not m.empty else 0,
    "n_videos": v["video_id"].nunique() if not v.empty else 0,
    "n_cliches": int(c["count"].sum()) if not c.empty else 0,
    }
    
    return Frag(v, t, c, a, g, m, cl, stats)
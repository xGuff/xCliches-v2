import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from typing import List, Optional

HEADERS = {
    "User-Agent": "PL-Manager-Scraper/1.0 (research use; contact=tjn.aston@gmail.com)"
}

URL = "https://en.wikipedia.org/wiki/List_of_Premier_League_managers"
WIKI_BASE = "https://en.wikipedia.org"

def _clean_text(s: str) -> str:
    """Remove reference markers like [1], non-breaking spaces, and trim."""
    if not s:
        return s
    s = re.sub(r"\[\d+\]", "", s)  # footnote refs
    s = s.replace("\xa0", " ").strip()
    return s

def _extract_nationality(td) -> Optional[str]:
    """Get nationality from flag <img alt> values; fallback to text."""
    alts = [img.get("alt") for img in td.find_all("img") if img.get("alt")]
    alts = [_clean_text(a) for a in alts if a]
    if alts:
        seen, uniq = set(), []
        for a in alts:
            if a not in seen:
                seen.add(a)
                uniq.append(a)
        return " / ".join(uniq)
    txt = _clean_text(td.get_text(" ", strip=True))
    return txt or None

def _extract_text(td) -> str:
    return _clean_text(td.get_text(" ", strip=True))

def _abs_url(href: Optional[str]) -> Optional[str]:
    if not href:
        return None
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return WIKI_BASE + href
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return WIKI_BASE + "/" + href.lstrip("/")

def _pick_first_url_from_srcset(srcset: str) -> Optional[str]:
    # srcset like: "//upload.wikimedia... 1.5x, //upload.wikimedia... 2x"
    if not srcset:
        return None
    # take the first URL (before the first comma) and strip any descriptor
    first = srcset.split(",")[0].strip()
    # descriptor separated by space(s); URL is the first token
    return first.split(" ")[0]

def _extract_img_url(img_tag) -> Optional[str]:
    # Order of preference: data-src, src, data-srcset/srcset (pick first)
    for attr in ("data-src", "src"):
        val = img_tag.get(attr)
        if val:
            return _abs_url(val)
    for attr in ("data-srcset", "srcset"):
        val = img_tag.get(attr)
        if val:
            first = _pick_first_url_from_srcset(val)
            if first:
                return _abs_url(first)
    return None

def _get_manager_image(page_url: str, session: requests.Session, cache: dict) -> Optional[str]:
    """Fetch the manager page and return an image URL (pref. infobox)."""
    if not page_url:
        return None
    if page_url in cache:
        return cache[page_url]
    try:
        r = session.get(page_url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        sp = BeautifulSoup(r.text, "lxml")

        # 1) Prefer infobox photo
        # Typical: table.infobox (variants: 'infobox vcard', etc.)
        infobox = sp.select_one("table.infobox")
        img_url = None
        if infobox:
            # Most reliable: an <a class="image"><img .../></a> inside the infobox
            img = infobox.select_one("a.image img") or infobox.select_one("img")
            if img:
                img_url = _extract_img_url(img)

        # 2) Fallback: first content image in the article
        if not img_url:
            img = sp.select_one("div.mw-parser-output a.image img")
            if img:
                img_url = _extract_img_url(img)

        cache[page_url] = img_url
        return img_url
    except Exception:
        cache[page_url] = None
        return None


def fetch_managers() -> pd.DataFrame:
    with requests.Session() as sess:
        resp = sess.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # Find all tables that contain the columns we care about
        candidate_tables = []
        for tbl in soup.find_all("table", class_="wikitable"):
            header_cells = tbl.find("tr").find_all(["th", "td"])
            headers = [hc.get_text(" ", strip=True) for hc in header_cells]
            norm_headers = [h.replace("\xa0", " ").strip().lower() for h in headers]
            if any("name" == h for h in norm_headers) and \
               any(h.startswith("nat") for h in norm_headers) and \
               any("club" == h for h in norm_headers) and \
               any("from" == h for h in norm_headers) and \
               any("until" == h for h in norm_headers):
                candidate_tables.append(tbl)

        if not candidate_tables:
            raise RuntimeError("Could not find a table with columns Name / Nat. / Club / From / Until")

        rows_out: List[dict] = []
        for tbl in candidate_tables:
            header_row = tbl.find("tr")
            header_cells = header_row.find_all(["th", "td"])
            header_texts = [hc.get_text(" ", strip=True) for hc in header_cells]
            norm = [h.replace("\xa0", " ").strip().lower() for h in header_texts]

            def col_idx(matchers: List[str]) -> Optional[int]:
                for i, h in enumerate(norm):
                    for m in matchers:
                        if h == m or h.startswith(m):
                            return i
                return None

            idx_name = col_idx(["name"])
            idx_nat  = col_idx(["nat", "nationality"])
            idx_club = col_idx(["club"])
            idx_from = col_idx(["from"])
            idx_until = col_idx(["until"])

            if any(i is None for i in [idx_name, idx_nat, idx_club, idx_from, idx_until]):
                continue

            for tr in tbl.find_all("tr")[1:]:
                tds = tr.find_all(["td", "th"])
                if len(tds) < max(idx_name, idx_nat, idx_club, idx_from, idx_until) + 1:
                    continue

                td_name = tds[idx_name]
                td_nat  = tds[idx_nat]
                td_club = tds[idx_club]
                td_from = tds[idx_from]
                td_until = tds[idx_until]

                name = _extract_text(td_name)
                # Link to manager page (if present)
                a = td_name.find("a")
                manager_page = _abs_url(a.get("href")) if a and a.get("href") else None

                nat  = _extract_nationality(td_nat) or ""
                club = _extract_text(td_club)
                from_ = _extract_text(td_from)
                until = _extract_text(td_until)

                # Skip blank rows
                if not (name or nat or club):
                    continue

                rows_out.append({
                    "Name": name,
                    "Nationality": nat,
                    "Club": club,
                    "From": from_,
                    "Until": until,
                    "ManagerPage": manager_page
                })

        df = pd.DataFrame(rows_out).drop_duplicates()
        df = df[(df["Name"] != "") | (df["Club"] != "") | (df["Nationality"] != "")]

        # Parse dates and calculate Duration (days) and Years in League
        def parse_date(s):
            try:
                return pd.to_datetime(s, errors="coerce", dayfirst=True)
            except Exception:
                return pd.NaT

        df["From_dt"] = df["From"].apply(parse_date)
        df["Until_dt"] = df["Until"].apply(parse_date)
        # If Until is blank, use today
        today = pd.Timestamp.today()
        df["Until_dt"] = df["Until_dt"].fillna(today)

        # Format dates to ISO (YYYY-MM-DD)
        df["From"] = df["From_dt"].dt.strftime("%Y-%m-%d")
        df["Until"] = df["Until_dt"].dt.strftime("%Y-%m-%d")

        df["Duration (days)"] = (df["Until_dt"] - df["From_dt"]).dt.days
        df["Years in League"] = (df["Duration (days)"] / 365.25).round(2)

        # Drop helper columns
        df = df.drop(columns=["From_dt", "Until_dt"])

        # Clean up manager names
        def clean_name(name):
            return re.sub(r"[‡†*]+|\s*\[.*?\]$|\s*\d+$", "", str(name)).strip()
        df["Name"] = df["Name"].apply(clean_name)

        # --- NEW: fetch image URLs (memoized) ---
        img_cache = {}
        df["ImageURL"] = df["ManagerPage"].apply(lambda u: _get_manager_image(u, sess, img_cache))
        cols = [c for c in df.columns if c not in ("ManagerPage", "ImageURL")]
        df = df[cols + ["ManagerPage", "ImageURL"]]

        return df.reset_index(drop=True)

def main():
    managers = fetch_managers()
    managers.to_csv("../data/raw/managers.csv", index=False)
    print(f"Saved {len(managers)} rows to ../data/raw/managers.csv")

if __name__ == "__main__":
    main()

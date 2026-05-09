"""
Phase 0: Download all lottery draw data and load into SQLite.
Reads the D423F index CSV, downloads each year's zip, extracts
威力彩_YEAR.csv, and inserts into draws table.
Split: first (N-100) draws → train, last 100 → holdout_100.
"""

import csv
import io
import os
import sqlite3
import zipfile
from pathlib import Path

import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "lottery.db"
INDEX_CSV = BASE_DIR / "data_raw.csv"

DATA_DIR.mkdir(exist_ok=True)


def download_year_zip(year_ad: int, url: str) -> Path:
    zip_path = DATA_DIR / f"{year_ad}.zip"
    if zip_path.exists():
        print(f"  {year_ad}.zip already cached, skipping download")
        return zip_path
    print(f"  Downloading {year_ad}.zip …", end=" ", flush=True)
    r = requests.get(url, timeout=120, verify=False)
    r.raise_for_status()
    zip_path.write_bytes(r.content)
    print(f"{len(r.content):,} bytes")
    return zip_path


def decode_zip_name(raw: str) -> str:
    """Handle both UTF-8 (newer zips) and CP950 (older zips) filenames."""
    if "威力彩" in raw:
        return raw
    try:
        return raw.encode("cp437").decode("cp950")
    except Exception:
        return raw


def extract_weili_csv(zip_path: Path, year_ad: int) -> list[dict]:
    rows = []
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            name = decode_zip_name(info.filename)
            if "威力彩" in name and name.endswith(".csv"):
                content = z.read(info.filename)
                reader = csv.DictReader(
                    io.TextIOWrapper(io.BytesIO(content), encoding="utf-8-sig")
                )
                for row in reader:
                    rows.append(row)
                print(f"    Found {len(rows)} draws in {os.path.basename(name)}")
                break
        else:
            print(f"    WARNING: no 威力彩 CSV in {zip_path.name}")
    return rows


def parse_row(row: dict) -> tuple | None:
    try:
        draw_id = row["期別"].strip()
        draw_date = row["開獎日期"].strip()
        n1 = int(row["獎號1"])
        n2 = int(row["獎號2"])
        n3 = int(row["獎號3"])
        n4 = int(row["獎號4"])
        n5 = int(row["獎號5"])
        n6 = int(row["獎號6"])
        n_zone2 = int(row["第二區"])
        total_sales = int(row.get("銷售總額", 0) or 0)
        return (draw_id, draw_date, n1, n2, n3, n4, n5, n6, n_zone2, total_sales)
    except Exception as e:
        print(f"    Skipping malformed row {row}: {e}")
        return None


def init_db(conn: sqlite3.Connection):
    conn.execute("DROP TABLE IF EXISTS draws")
    conn.execute("""
        CREATE TABLE draws (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            draw_id     TEXT NOT NULL UNIQUE,
            draw_date   TEXT NOT NULL,
            n1 INTEGER, n2 INTEGER, n3 INTEGER,
            n4 INTEGER, n5 INTEGER, n6 INTEGER,
            n_zone2     INTEGER,
            total_sales INTEGER,
            split       TEXT    -- 'train' | 'holdout_100'
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_draw_date ON draws(draw_date)")
    conn.commit()


def main():
    # Read index
    with open(INDEX_CSV, encoding="utf-8-sig") as f:
        index_rows = list(csv.DictReader(f))

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    all_parsed: list[tuple] = []

    for row in index_rows:
        roc_year = int(row["資料所屬年度"])
        year_ad = roc_year + 1911
        url = row["下載連結"].strip()

        if year_ad < 2008:
            print(f"Skipping {year_ad} (威力彩 not yet launched)")
            continue

        print(f"\n[{year_ad}]")
        # Some recent years have alternate URL patterns; try both
        alt_urls = [url]
        if year_ad >= 2025:
            alt_urls += [
                f"https://cdn.taiwanlottery.com.tw/app/FilesForDownload/Download/LottoResult/{year_ad}.zip",
            ]
        downloaded = False
        for try_url in alt_urls:
            try:
                zip_path = download_year_zip(year_ad, try_url)
                downloaded = True
                break
            except Exception as e:
                print(f"  URL failed ({try_url[-30:]}): {e}")
        if not downloaded:
            print(f"  Skipping {year_ad} (no working URL)")
            continue
        try:
            rows = extract_weili_csv(zip_path, year_ad)
            for r in rows:
                parsed = parse_row(r)
                if parsed:
                    all_parsed.append(parsed)
        except Exception as e:
            print(f"  ERROR extracting: {e}")

    # Sort by draw_date then draw_id to guarantee chronological order
    all_parsed.sort(key=lambda x: (x[1], x[0]))

    total = len(all_parsed)
    holdout_start = total - 100
    print(f"\nTotal draws: {total}")
    print(f"Train: {holdout_start} | Holdout: 100")

    insert_sql = """
        INSERT OR IGNORE INTO draws
        (draw_id, draw_date, n1, n2, n3, n4, n5, n6, n_zone2, total_sales, split)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """
    for i, row in enumerate(all_parsed):
        split = "holdout_100" if i >= holdout_start else "train"
        conn.execute(insert_sql, row + (split,))

    conn.commit()
    conn.close()

    print(f"\nDone. Database saved to: {DB_PATH}")
    print("Verify with: SELECT split, COUNT(*) FROM draws GROUP BY split;")


if __name__ == "__main__":
    main()

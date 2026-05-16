"""
一次性歷史回灌：從 2014-01 起抓所有大樂透開獎資料。
全部標 split='train'。
重複跑安全（INSERT OR IGNORE + draw_id UNIQUE），不會塞重複期數。
"""

import sqlite3
import time
from datetime import datetime
from pathlib import Path

import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_PATH = Path(__file__).parent / "lottery.db"
API_URL = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Lotto649Result"
CONTENT_KEY = "lotto649Res"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.taiwanlottery.com/",
}

START_YEAR = 2014
START_MONTH = 1


def iter_months(start_year, start_month, end_year, end_month):
    y, m = start_year, start_month
    while (y, m) <= (end_year, end_month):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m > 12:
            m = 1
            y += 1


def fetch_month(year_month: str) -> list[dict]:
    params = {"month": year_month, "endMonth": year_month, "pageNum": 1, "pageSize": 200}
    r = requests.get(API_URL, headers=HEADERS, params=params, timeout=30, verify=False)
    r.raise_for_status()
    return r.json().get("content", {}).get(CONTENT_KEY) or []


def main():
    conn = sqlite3.connect(DB_PATH)

    today = datetime.now()
    months = list(iter_months(START_YEAR, START_MONTH, today.year, today.month))
    print(f"預計查詢 {len(months)} 個月（{months[0]} ~ {months[-1]}）")

    inserted = 0
    for i, ym in enumerate(months, 1):
        print(f"  [{i}/{len(months)}] {ym} …", end=" ", flush=True)
        try:
            draws = fetch_month(ym)
        except Exception as e:
            print(f"ERROR: {e}")
            continue

        rows = []
        for d in draws:
            nums = d["drawNumberSize"]  # [n1..n6, 特別號]
            row = (
                str(d["period"]),
                d["lotteryDate"][:10].replace("-", "/"),
                nums[0], nums[1], nums[2], nums[3], nums[4], nums[5],
                nums[6],
                d.get("sellAmount", 0) or 0,
                "train",
            )
            rows.append(row)

        cur = conn.cursor()
        cur.executemany(
            """
            INSERT OR IGNORE INTO draws_lotto649
            (draw_id, draw_date, n1, n2, n3, n4, n5, n6, n_zone2, total_sales, split)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            rows,
        )
        new = cur.rowcount
        inserted += new
        conn.commit()
        print(f"{len(draws)} 筆 / 新增 {new}")
        time.sleep(0.3)  # 對 API 友善一點

    conn.close()
    print(f"\n總計新增 {inserted} 期")


if __name__ == "__main__":
    main()

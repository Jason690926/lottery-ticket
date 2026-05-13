"""
增量更新：從台彩官方 API 補入 lottery.db 目前沒有的最新期數。
- API: https://api.taiwanlottery.com/TLCAPIWeB/Lottery/SuperLotto638Result
- 查詢最近 3 個月，只插入 DB 中尚不存在的 draw_id
- 新增的 draw 統一標 split='live'，不動原有 train/holdout_100
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "lottery.db"

API_BASE = "https://api.taiwanlottery.com/TLCAPIWeB"
API_URL = f"{API_BASE}/Lottery/SuperLotto638Result"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.taiwanlottery.com/",
}


def fetch_month(year_month: str) -> list[dict]:
    """查詢單一年月的威力彩開獎資料，回傳原始 dict 列表。"""
    params = {"month": year_month, "endMonth": year_month, "pageNum": 1, "pageSize": 200}
    r = requests.get(API_URL, headers=HEADERS, params=params, timeout=30, verify=False)
    r.raise_for_status()
    return r.json().get("content", {}).get("superLotto638Res") or []


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT draw_id FROM draws")
    existing_ids = {r[0] for r in cur.fetchall()}
    print(f"DB 目前有 {len(existing_ids)} 期")

    cur.execute("SELECT MAX(draw_date) FROM draws")
    latest_date = cur.fetchone()[0]
    print(f"最新日期：{latest_date}")

    # 查最近 3 個月（確保跨月不漏）
    today = datetime.now()
    months = []
    for delta in range(3):
        d = today - timedelta(days=30 * delta)
        months.append(d.strftime("%Y-%m"))
    months = sorted(set(months))

    new_rows: list[tuple] = []
    for ym in months:
        print(f"  查詢 {ym} …", end=" ", flush=True)
        try:
            draws = fetch_month(ym)
            print(f"{len(draws)} 筆")
            for d in draws:
                draw_id = str(d["period"])
                if draw_id in existing_ids:
                    continue
                nums = d["drawNumberSize"]   # [n1,n2,n3,n4,n5,n6, zone2]
                draw_date = d["lotteryDate"][:10].replace("-", "/")  # YYYY/MM/DD
                total_sales = d.get("sellAmount", 0) or 0
                row = (draw_id, draw_date,
                       nums[0], nums[1], nums[2], nums[3], nums[4], nums[5],
                       nums[6], total_sales)
                new_rows.append(row)
        except Exception as e:
            print(f"ERROR: {e}")

    if not new_rows:
        print("\n沒有新期數，DB 已是最新。")
        conn.close()
        return

    new_rows.sort(key=lambda x: (x[1], x[0]))
    print(f"\n新增 {len(new_rows)} 期：")
    for r in new_rows:
        print(f"  {r[0]}  {r[1]}  第一區={list(r[2:8])}  第二區={r[8]}")

    insert_sql = """
        INSERT OR IGNORE INTO draws
        (draw_id, draw_date, n1, n2, n3, n4, n5, n6, n_zone2, total_sales, split)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """
    for row in new_rows:
        conn.execute(insert_sql, row + ("live",))
    conn.commit()

    cur.execute("SELECT split, COUNT(*) FROM draws GROUP BY split ORDER BY split")
    print("\n--- DB 分布 ---")
    for split, cnt in cur.fetchall():
        print(f"  {split}: {cnt} 期")

    cur.execute("SELECT MAX(draw_date), MAX(draw_id) FROM draws WHERE split='live'")
    print("最新 live 期：", cur.fetchone())

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()

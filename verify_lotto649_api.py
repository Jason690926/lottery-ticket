"""
一次性探勘：確認台彩 Lotto649 API endpoint 與回傳欄位。
跑完把找到的欄位名抄到 update_db_lotto649.py / backfill_lotto649.py。
"""
import json
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.taiwanlottery.com/",
}

CANDIDATES = [
    "Lotto649Result",
    "BigLottoResult",
    "Lotto/Lotto649",
    "Lotto649",
]

for name in CANDIDATES:
    url = f"{BASE}/{name}"
    print(f"\n--- 嘗試 {url} ---")
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            params={"month": "2026-04", "endMonth": "2026-04", "pageNum": 1, "pageSize": 5},
            timeout=15,
            verify=False,
        )
        print(f"  status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            content = data.get("content", {})
            if not isinstance(content, dict):
                print(f"  content 不是 dict: {type(content)} -> {content!r:.200}")
                continue
            keys = list(content.keys())
            print(f"  content keys: {keys}")
            for k in keys:
                v = content[k]
                if isinstance(v, list) and v:
                    print(f"  第一筆樣本（key={k}）:")
                    print(json.dumps(v[0], ensure_ascii=False, indent=2))
                    break
            break
    except Exception as e:
        print(f"  ERROR: {e}")


# === 探勘結果（2026-05-16）===
# Endpoint:    https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Lotto649Result
# Content key: 'lotto649Res'
# 範例 record（period=115000048, 2026-04-28）欄位：
#   period          -> 期別（int，如 115000048）
#   lotteryDate     -> 開獎日 'YYYY-MM-DDTHH:MM:SS'
#   drawNumberSize  -> [n1..n6, 特別號]（前 6 個已升冪排序的主號 + 第 7 個為特別號）
#                      例: [6,10,14,25,26,32, 7] → 主號 6/10/14/25/26/32，特別號 7
#   drawNumberAppear-> 開出順序（不使用）
#   sellAmount      -> 銷售額（int）
# 結論：與 update_db.py 的 SuperLotto638Result 結構完全鏡射，
#       只差 endpoint（Lotto649Result）與 content key（lotto649Res）。

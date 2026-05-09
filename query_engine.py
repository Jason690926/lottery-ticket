import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

DB_PATH = Path(__file__).parent / "lottery.db"
Z1_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]
ROLLING = 200


def _get_draws(n: int) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        f"SELECT id, draw_date, n1,n2,n3,n4,n5,n6, n_zone2 "
        f"FROM draws ORDER BY id DESC LIMIT {n + 1}",
        conn,
    )
    conn.close()
    return df.sort_values("id").reset_index(drop=True)


def zone1_analysis(condition_nums: list[int], rolling: int = ROLLING) -> tuple[pd.DataFrame, int, int]:
    """
    For each x in condition_nums: find draws where x appeared,
    count next-draw Z1 frequencies, sum across all conditions.
    Returns (DataFrame sorted by combined count DESC, total_cond_appearances, num_source_draws).
    """
    df = _get_draws(rolling)
    src = df.iloc[:-1].reset_index(drop=True)
    nxt = df.iloc[1:].reset_index(drop=True)
    T = len(src)

    src_p = np.zeros((T, 38), dtype=np.int8)
    nxt_p = np.zeros((T, 38), dtype=np.int8)
    for t, row in enumerate(src[Z1_COLS].itertuples(index=False, name=None)):
        for x in row:
            src_p[t, x - 1] = 1
    for t, row in enumerate(nxt[Z1_COLS].itertuples(index=False, name=None)):
        for x in row:
            nxt_p[t, x - 1] = 1

    result = pd.DataFrame({"號碼": range(1, 39)})
    total_cond = 0

    for x in condition_nums:
        mask = src_p[:, x - 1].astype(bool)
        n_c = int(mask.sum())
        total_cond += n_c
        counts = nxt_p[mask].sum(axis=0)
        freq = (counts / n_c * 100).round(1) if n_c > 0 else np.zeros(38)
        result[f"#{x:02d}次數"] = counts.astype(int)
        result[f"#{x:02d}頻率%"] = freq

    count_cols = [c for c in result.columns if "次數" in c]
    result["合計次數"] = result[count_cols].sum(axis=1)
    result["合計頻率%"] = (
        (result["合計次數"] / total_cond * 100).round(1) if total_cond > 0 else 0.0
    )

    overall = nxt_p.sum(axis=0)
    result[f"近{rolling}期頻率%"] = (overall / T * 100).round(1)

    result = result.sort_values("合計次數", ascending=False).reset_index(drop=True)
    result.insert(0, "排名", range(1, 39))
    return result, total_cond, T


def zone2_analysis(condition_z2: int, rolling: int = ROLLING) -> tuple[pd.DataFrame, int]:
    """
    Given last Zone2 number, count next-draw Z2 frequencies.
    Returns (DataFrame sorted by condition count DESC, n_condition_draws).
    """
    df = _get_draws(rolling)
    src = df.iloc[:-1].reset_index(drop=True)
    nxt = df.iloc[1:].reset_index(drop=True)
    T = len(src)

    mask = src["n_zone2"] == condition_z2
    n_c = int(mask.sum())

    records = []
    for w in range(1, 9):
        k = int((nxt.loc[mask, "n_zone2"] == w).sum())
        ov = int((nxt["n_zone2"] == w).sum())
        records.append({
            "號碼": w,
            f"#{condition_z2}次數": k,
            f"#{condition_z2}頻率%": round(k / n_c * 100, 1) if n_c > 0 else 0.0,
            f"近{rolling}期頻率%": round(ov / T * 100, 1),
        })

    out = pd.DataFrame(records)
    out = out.sort_values(f"#{condition_z2}次數", ascending=False).reset_index(drop=True)
    out.insert(0, "排名", range(1, 9))
    return out, n_c

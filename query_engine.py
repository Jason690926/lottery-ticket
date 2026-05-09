import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

DB_PATH = Path(__file__).parent / "lottery.db"
Z1_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]
ROLLING = 200


def _get_draws(n: int) -> pd.DataFrame:
    """Fetch exactly n most-recent draws, sorted ascending by id."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        f"SELECT id, draw_date, n1,n2,n3,n4,n5,n6, n_zone2 "
        f"FROM draws ORDER BY id DESC LIMIT {n}",
        conn,
    )
    conn.close()
    return df.sort_values("id").reset_index(drop=True)


def zone1_analysis(
    condition_nums: list[int],
    rolling: int = ROLLING,
    lag: int = 1,
) -> tuple[pd.DataFrame, int, int]:
    """
    For each x in condition_nums:
      find source draws (within last `rolling`) where x appeared,
      count frequencies in the draw `lag` periods later.
    Returns (DataFrame sorted by combined count DESC, total_cond_appearances, T).
    """
    df = _get_draws(rolling + lag)
    src = df.iloc[:rolling].reset_index(drop=True)
    nxt = df.iloc[lag : rolling + lag].reset_index(drop=True)
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


def zone1_dual_combined(
    block1_nums: list[int],
    block2_nums: list[int],
    rolling: int = ROLLING,
    w1: float = 0.5,
    w2: float = 0.5,
) -> pd.DataFrame:
    """
    Weighted combination of two independent lag-1 analyses.
    block1 and block2 are separate condition sets (e.g. two different draws).
    Each module's counts are normalised to [0,1] before weighting.
    Returns DataFrame sorted by 綜合分數 DESC.
    """
    df1, _, _ = zone1_analysis(block1_nums, rolling, lag=1)
    df2, _, _ = zone1_analysis(block2_nums, rolling, lag=1)

    merged = df1[["號碼", "合計次數", "合計頻率%", f"近{rolling}期頻率%"]].rename(
        columns={"合計次數": "B1次數", "合計頻率%": "B1頻率%"}
    )
    merged = merged.merge(
        df2[["號碼", "合計次數", "合計頻率%"]].rename(
            columns={"合計次數": "B2次數", "合計頻率%": "B2頻率%"}
        ),
        on="號碼",
    )

    m1_max = merged["B1次數"].max()
    m2_max = merged["B2次數"].max()
    m1_norm = merged["B1次數"] / m1_max if m1_max > 0 else 0.0
    m2_norm = merged["B2次數"] / m2_max if m2_max > 0 else 0.0

    merged["綜合分數"] = (w1 * m1_norm + w2 * m2_norm).round(4)
    merged = merged.sort_values("綜合分數", ascending=False).reset_index(drop=True)
    merged.insert(0, "排名", range(1, 39))
    return merged


def zone2_analysis(condition_z2: int, rolling: int = ROLLING) -> tuple[pd.DataFrame, int]:
    """
    Given last Zone2 number, count next-draw Z2 frequencies (lag-1).
    Returns (DataFrame sorted by condition count DESC, n_condition_draws).
    """
    df = _get_draws(rolling + 1)
    src = df.iloc[:rolling].reset_index(drop=True)
    nxt = df.iloc[1 : rolling + 1].reset_index(drop=True)
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

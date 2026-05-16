-- 大樂透開獎資料表
-- 完整鏡射 draws（威力彩）schema，確保共用引擎 query_engine._get_draws
-- 的 `ORDER BY id` 與 update/backfill 的 `INSERT OR IGNORE`（靠 draw_id UNIQUE）
-- 行為一致。
-- n_zone2 欄存「特別號」（語意延伸自威力彩第二區，避免 query 引擎多一個欄位參數）。

CREATE TABLE IF NOT EXISTS draws_lotto649 (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_id     TEXT NOT NULL UNIQUE,
    draw_date   TEXT NOT NULL,
    n1 INTEGER, n2 INTEGER, n3 INTEGER,
    n4 INTEGER, n5 INTEGER, n6 INTEGER,
    n_zone2     INTEGER,
    total_sales INTEGER,
    split       TEXT    -- 'train' | 'live'（大樂透不切 holdout）
);

CREATE INDEX IF NOT EXISTS idx_lotto649_date ON draws_lotto649(draw_date);

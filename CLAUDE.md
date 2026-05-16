# 彩券選號系統 — Claude 指引

## 工作流程
- **開工指令**：「繼續 lottery-ticket 工作」→ 讀本檔「當前進度」，給摘要，繼續
- **收工指令**：「先停這裡」→ 更新「當前進度」快照，再結束
- **架構決策**：討論完方案後，先更新 `plan.md`，再開始寫程式
- `plan.md` 只在需要查架構細節時才讀（節省 token）
- **假設驗證原則**：每個「我覺得 X 跟 Y 有關」的猜想，必須量化（命中率、p-value、相關係數、AUC 等），不憑感覺

## 跨機同步注意事項（A/B/C 三台）
> ⚠️ 本 repo 曾發生分支分叉（2026-05-13），起因是不同機器各自 commit 後推遠端。

**換電腦開工前，固定執行：**
```powershell
git fetch origin
git status  # 確認是否落後或分叉
```
- **正常落後**（behind）：`git pull` 即可
- **分叉**（diverged）：確認哪台最新後，用最新那台 `git push --force`；其他台執行 `git reset --hard origin/main`
- **不要直接 `git pull`** 在分叉狀態下，會產生多餘的 merge commit

## 專案目標
建構**威力彩選號預測系統**。核心信念：歷史開獎號碼之間可能存在某種模式或關聯，透過數學方法（統計、圖論、機器學習等）找出規律，輔助下期選號。

**開發階段：**
1. **第一階段：威力彩**（第一區 1-38 選 6 + 第二區 1-8 選 1）— 球數較少，當實驗田
2. **第二階段：大樂透**（1-49 選 6）— 第一階段方法跑通後再擴展

## 學術誠實聲明
公平抽獎在數學上應為各期獨立事件（白色雜訊），單純依歷史頻率預測下期單號**理論上無效**。但本專案探索三條仍可能有意義的方向：

1. **機台微小偏差**：實體球機可能因球磨損、機械瑕疵造成微弱長期頻率偏好（過往國外有實證案例）
2. **組合模式分析**：即使單號獨立，「6 號組合」的分布仍有結構（如連號、奇偶、區段分布），可分析是否偏離隨機基準
3. **純統計探索**：把彩券當資料集，練習各種分析方法（時間序列、馬可夫鏈、圖論、聚類等）

**評估態度：** 當分析結果統計上不顯著（p > 0.05、AUC < 0.55、命中率與隨機基準無差異等），會誠實標註「無顯著訊號」，不會為了「神準」強解。最終是否選號押注，由用戶自行決定。

## 當前進度（2026-05-16）

**Phase：統計研究結案，Streamlit 選號工具（威力彩 + 大樂透）已上線**

**Phase 0 ✅ 完成：**
- ✅ Repo 初始化 + push、venv 建立（Python 3.14.4，`.venv/`）
- ✅ SQLite 入庫（`lottery.db`，1,907 期，2008-01-24 ～ 2026-04-30）
  - 訓練集：1,807 期（split = 'train'）
  - **Holdout 鎖死：最後 100 期**（split = 'holdout_100'）⚠️ 不得碰

**Phase 1 ✅ 完成（全部負結果）：**

| 分析方向 | 檢定數 | FDR 顯著 |
|---------|--------|---------|
| 靜態頻率 EDA | 46 | 0 |
| Lag-1/2/3 Transition | 4,332 | 0 |
| Order C Pair→下期 | 26,714 | 0 |
| 滾動時間窗 | 190 | 0 |
| ACF / Fourier / 開獎日 | 114 | 0 |
| **合計** | **31,396** | **0** |

Notebooks：`eda_phase0.ipynb`、`phase1_transition.ipynb`、`phase1_lag23.ipynb`、`phase1_orderC.ipynb`、`phase1_rolling.ipynb`、`phase1_acf_fourier.ipynb`

**Phase 4 ✅ 結案（`final_report.md`）：**
- 結論：1,807 期訓練資料在所有探索維度上與 i.i.d. 無法區分
- Holdout 100 期**全程未解封**，建議保留不開

---

**Streamlit 選號工具 ✅ 開發中（`app.py` + `query_engine.py`）**

啟動指令：`.venv\Scripts\streamlit.exe run app.py`（http://localhost:8501）

套件：新增 `streamlit==1.57.0`、`plotly==6.7.0`（已裝入 `.venv`）

**功能設計（已完成）：**
- 雙區塊輸入：**第一區塊（本期，lag-1）** + **第二區塊（上一期，lag-2）**，各自填入第一區 1–6 個號碼 + 第二區 1 個號碼
- 資料範圍：滾動最近 **200 期**（全部資料，不限 split）
- **第一區分析 Tab 結構**：
  - 🔵 第一區塊：lag-1 頻率表 + 堆疊長條圖 + 折線圖
  - 🟠 第二區塊：lag-2 頻率表 + 堆疊長條圖 + 折線圖
  - ⚖️ 綜合加權：兩區塊次數各自標準化 [0,1] → 加權合計 → 泡泡散布圖 + 貢獻分解長條
- **第二區分析**：各區塊獨立分析；兩個都填時出現「合併比較」Tab（排名表 + 並排長條圖）
- 加權比重可用滑桿即時調整

**核心架構（多彩種，參數化共用引擎）：**
```
query_engine.py
  LotteryConfig (dataclass) + POWERBALL / LOTTO649 兩份設定
  zone1_analysis(nums, rolling, lag, cfg)         # 單區塊頻率分析
  zone1_dual_combined(b1, b2, rolling, w1, w2, cfg)  # 雙區塊加權合併
  zone2_analysis(z2_num, rolling, cfg)            # 第二區/特別號分析

app.py          # 入口：CSS + auto_update（兩彩種）+ 頂層兩個 tab
ui_shared.py    # 共用 UI：palette/plotly_base/render_block_*/render_combined/render_zone2_section
ui_powerball.py # 威力彩 render()（cfg=POWERBALL, key 前綴 pb_）
ui_lotto649.py  # 大樂透 render()（cfg=LOTTO649, key 前綴 lt_）
.streamlit/config.toml  # dark theme 設定
```

---

**大樂透分頁 ✅ 已完成上線（2026-05-16，計畫 17 tasks 全數完成）**

- 資料：`lottery.db` 新表 `draws_lotto649`，**1,401 期**（train 1,377 + live 24），
  範圍 2014/01/03 ~ 2026/05/15；不切 holdout
- 腳本：`backfill_lotto649.py`（一次性回灌）、`update_db_lotto649.py`（增量，app 啟動自動跑）、
  `verify_lotto649_api.py`（API 探勘留檔）、`migrations/001_create_draws_lotto649.sql`
- 引擎重構：sanity check 6 case byte-for-byte 一致，**威力彩行為完全未變**
- 特別號：簡化邏輯（基準 2.04% = 1/49），不排除「特別號落在主號」的不可能組合
- UI：頂層 `🎯 威力彩` / `🍀 大樂透` 兩個 tab，各自副標題顯示自己的「資料最新至」
- ⚠️ Lotto649 API：`Lottery/Lotto649Result`，content key `lotto649Res`，
  `drawNumberSize=[n1..n6, 特別號]`（前 6 已排序 + 第 7 為特別號）

**🐞 時序排序 bug 修正 ✅（2026-05-16）**

- 問題：`draws_lotto649.id`（AUTOINCREMENT）反映插入順序非開獎時序
  （update_db 先跑佔低 id、backfill 後跑且月內 API 降冪、近月被
  INSERT OR IGNORE 跳過 → 1232/1400 列 id↔draw_date 逆序）
- 影響：原 `_get_draws` 用 `ORDER BY id` → **先前交付的大樂透 lag
  分析數字全部無效**（威力彩因 id↔date 0 逆序不受影響）
- 修正：`_get_draws` / `latest_two_draws` 改 `ORDER BY draw_date DESC,
  draw_id DESC`；威力彩輸出位元級不變（已用 zone1/zone2 snapshot 驗證），
  大樂透時序修正

**自動帶入號碼 ✅ 已完成（2026-05-16）**

- 開啟威力彩/大樂透分頁自動帶入最新一期（第一區塊）+ 上一期（第二區塊），分析自動呈現
- 機制：`query_engine.latest_two_draws` + `ui_shared.seed_inputs`
  （draw_id 哨兵：同期只種一次、新期才覆蓋）
- 手改後不被覆蓋；每個 tab 有「↻ 帶回最新期」按鈕；caption 標示帶入的兩期
- 設計：`docs/superpowers/specs/2026-05-16-自動帶入號碼-design.md`
  計畫：`docs/superpowers/plans/2026-05-16-自動帶入號碼.md`
- AppTest 4 情境驗證通過（種子化/手改保留/新期重種/重設）

**未完成 / 待優化（低優先）：**
- ⏸ 設定 MCP：filesystem / sequential-thinking / playwright
- ⏸ 桌面捷徑檔名仍為「威力彩選號工具.bat」（功能正常，未改名；可考慮改為「樂透選號工具.bat」）

## 技術棧
- **主語言**：Python 3.11+
- **資料處理**：`pandas`, `numpy`
- **視覺化**：`matplotlib`, `seaborn`, `plotly`（互動圖）
- **統計檢定**：`scipy.stats`
- **機器學習**（後期）：`scikit-learn`
- **圖論分析**：`networkx`（探索號碼共現關係）
- **資料儲存**：CSV（探索期）→ SQLite（穩定後）
- **開獎資料來源**：台彩官網爬蟲（待確認 URL）/ 政府開放資料平台
- **執行環境**：Jupyter Notebook（探索）+ Python script（穩定後）

## 評估指標（量化標準）
分析任何「規律」都用這些指標衡量是否真有訊號：

| 指標 | 用途 | 「有訊號」門檻 |
|------|------|--------------|
| 命中率 | 預測 vs 實際號碼重疊 | 顯著高於隨機基準 |
| p-value | 統計檢定 | < 0.05 |
| AUC | 分類器辨別力 | > 0.55 |
| Lift | 預測組合中獎機率提升倍數 | > 1.0 且穩定 |
| Brier score | 機率校準 | 低於 baseline |

## 專案基本資訊
- **GitHub**：https://github.com/Jason690926/lottery-ticket
- **本機路徑**：`C:\Users\frodo.MSI\OneDrive\Desktop\lottery-ticket`
- **跨機協作**：A/B/C 三台電腦，靠 git pull 同步

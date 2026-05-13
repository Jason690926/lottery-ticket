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

## 當前進度（2026-05-09）

**Phase：統計研究結案，Streamlit 選號工具開發中**

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

**核心架構：**
```
query_engine.py
  zone1_analysis(nums, rolling, lag)        # 單區塊頻率分析
  zone1_dual_combined(b1, b2, rolling, w1, w2)  # 雙區塊加權合併
  zone2_analysis(z2_num, rolling)           # 第二區分析

app.py  # Streamlit 介面，深色科技風（GitHub dark 配色）
.streamlit/config.toml  # dark theme 設定
```

**未完成 / 待優化（低優先）：**
- ⏸ 設定 MCP：filesystem / sequential-thinking / playwright
- ⏸ 資料自動更新（定期爬最新開獎並補入 lottery.db）
- ⏸ 大樂透擴展（Phase 2）

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

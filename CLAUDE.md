# 彩券選號系統 — Claude 指引

## 工作流程
- **開工指令**：「繼續 lottery-ticket 工作」→ 讀本檔「當前進度」，給摘要，繼續
- **收工指令**：「先停這裡」→ 更新「當前進度」快照，再結束
- **架構決策**：討論完方案後，先更新 `plan.md`，再開始寫程式
- `plan.md` 只在需要查架構細節時才讀（節省 token）
- **假設驗證原則**：每個「我覺得 X 跟 Y 有關」的猜想，必須量化（命中率、p-value、相關係數、AUC 等），不憑感覺

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

## 當前進度（2026-05-03 A 地階段）

**Phase：尚在 Phase 0 之前（建構工作環境）**

**本次完成：**
- ✅ Repo 初始化 + push（CLAUDE.md / plan.md）
- ✅ 安裝 8 個 Skills（commit `911d01b`，已 git 同步給 BC 台）
  - `xlsx`（CSV/Excel 處理）
  - `frontend-design` + `canvas-design`（將來儀表板與圖表）
  - `doc-coauthoring`（寫分析報告）
  - `brainstorming`（找關聯性的多角度發想）
  - `systematic-debugging`（統計結果與假設不符時用）
  - `writing-plans`（跟 plan.md 流程契合）
  - `verification-before-completion`（量化驗證原則）

**未完成（待 B 地或之後處理）：**
- ⏸ 設定 3 個 MCP：filesystem / sequential-thinking / playwright（要編輯 `~/.claude.json`，A 地時間不夠）
- ⏸ 之後再裝：sqlite-mcp、jupyter-mcp（等 Python 環境 + 資料就緒）

**下一步（按優先順序）：**
1. **設定 3 個 MCP**（filesystem / sequential-thinking / playwright）
2. **討論「找關聯性」的具體方法假設**（建議先用 grill-me 對使用者的信念做質詢，逼出可驗證的具體假設）
3. **決定資料來源**：
   - 台彩官網爬蟲？
   - 政府開放資料平台？
   - 手動下載 CSV？
4. **建 Python 環境**（venv 或 conda）+ 安裝套件（pandas, numpy, matplotlib, scipy）
5. **抓威力彩全歷史開獎入庫**（CSV 或 SQLite）
6. **Phase 1 基準線分析開跑**（plan.md 第三節 1-4 項）

**待確認：**
- 開獎資料來源 URL
- 是否用 Jupyter Notebook 做探索（推薦）
- 你的「關聯性」假設細節（grill-me 質詢時釐清）

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

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

## 當前進度（2026-05-09）

**Phase：Phase 0 完成，Phase 1 待開跑**

**Phase 0 已完成：**
- ✅ Repo 初始化 + push（CLAUDE.md / plan.md）
- ✅ 安裝 8 個 Skills + git 同步（`911d01b`）
- ✅ grill-me 質詢完成，方法論釘定（plan.md 第二節）
- ✅ 確認威力彩官方規則（plan.md 第一節）
- ✅ **Python venv 建立**（Python 3.14.4，路徑 `.venv/`）
  - 套件：pandas, numpy, scipy, matplotlib, seaborn, statsmodels, jupyter, sqlalchemy, ipykernel
- ✅ **下載全部歷史資料**（政府開放資料 D423F，2008-2026）
  - 各年度 zip 存放於 `data/` 目錄
- ✅ **SQLite 入庫完成**（`lottery.db`，`draws` 表）
  - 總計 **1,907 期**（2008-01-24 ～ 2026-04-30）
  - 訓練集：1,807 期（split = 'train'）
  - **Holdout 鎖死：最後 100 期**（split = 'holdout_100'）⚠️ Phase 2 前不得碰

**未完成（低優先）：**
- ⏸ 設定 3 個 MCP：filesystem / sequential-thinking / playwright
- ⏸ 之後再裝：sqlite-mcp、jupyter-mcp

**Phase 0 EDA ✅ 完成**（`eda_phase0.ipynb`）：
- 一區/二區頻率均勻性、奇偶比、區段分布、年度趨勢熱力圖
- 所有卡方檢定均無顯著偏差 → 靜態頻率方向（機械偏差）無訊號

**Phase 1 ✅ 完成**（`phase1_transition.ipynb`）：

| 檢定 | 結果 |
|------|------|
| 一區 Test B（38 row χ²） | 原始 p<0.05：**0/38**（隨機期望 ~2） |
| 一區 Test A（1,444 cell binomial + FDR） | q<0.05：**0/1,444** |
| 二區 Test B（8 row χ²） | p<0.05：**0/8** |
| 二區 Test A（64 cell binomial + FDR） | q<0.05：**0/64** |

**🔴 結論：lag-1 transition 方向無顯著跨期關聯訊號。依照預設證偽門檻，建議結案（Phase 4）。**

**Phase 1 延伸（均為負結果）：**
- ✅ Lag-2/3 transition：0/1,444×2 顯著（`phase1_lag23.ipynb`）
- ✅ Order C pair→下期：0/26,714 顯著（`phase1_orderC.ipynb`）
- ✅ 滾動時間窗：MK 趨勢 0/38、各時段 0/38、近 200 期 0/38（`phase1_rolling.ipynb`）
- ✅ ACF/Fourier/開獎日：Ljung-Box 0/38、Fisher's g 0/38、開獎日 χ² 0/38（`phase1_acf_fourier.ipynb`）

**Phase 4 ✅ 結案（`final_report.md`）：**
- 全部 31,396 個統計檢定，FDR 顯著：**0 個**
- 結論：威力彩 1,807 期訓練資料在所有探索維度上與 i.i.d. 無法區分
- Holdout 100 期**全程未解封**，建議保留不開

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

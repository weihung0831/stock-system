# TW 股票篩選器 - 程式碼審查報告

**日期：** 2026-02-15
**審查者：** code-reviewer agent
**範圍：** 完整程式碼庫 (後端 + 前端)
**整體分數：** 6.5 / 10

---

## 範圍

- **後端：** 30 個 Python 檔案，涵蓋 config、models、services、routers、tasks、schemas
- **前端：** 34 個 TypeScript/Vue 檔案，涵蓋 stores、api、types、components、views
- **總程式碼行數：** ~6,500 (後端 ~4,200，前端 ~4,600 含樣式)
- **焦點：** 完整程式碼庫審查

---

## 關鍵問題 (必須修復)

### C1. [安全性] 錯誤訊息向 API 消費者洩露內部詳細資訊

**檔案：**
- `/Users/weihung/Desktop/project/stock-system/backend/app/routers/screening.py` (第 83-85 行)
- `/Users/weihung/Desktop/project/stock-system/backend/app/routers/scheduler.py` (第 111-114 行)
- `/Users/weihung/Desktop/project/stock-system/backend/app/routers/chip_stats.py` (第 58-63, 100-105 行)
- `/Users/weihung/Desktop/project/stock-system/backend/app/routers/backtest.py` (第 72-76, 130-136 行)

多個端點在 HTTP 500 錯誤回應中返回 `str(e)` (例如 `detail=f"Screening failed: {str(e)}"`)。這會向客戶端洩露堆疊追蹤、內部類別名稱和 SQL 詳細資訊。

**修復：** 在生產環境返回通用錯誤訊息。伺服器端記錄實際錯誤。
```python
# 不好
raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

# 好
logger.error(f"Screening failed: {e}", exc_info=True)
raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")
```

### C2. [安全性] 背景任務接收來自請求範圍的 DB session

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/routers/data.py` (第 75 行)

```python
background_tasks.add_task(run_data_collection, db, current_user.id)
```

來自 `get_db()` 依賴的 `db` session 是請求範圍的。當在 `BackgroundTasks` 中使用時，session 將在回應返回後關閉，導致背景任務中出現 `Session is closed` 錯誤。

**修復：** 在背景任務函式內部建立新 session，而不是傳遞請求範圍的 session。
```python
def run_data_collection(user_id: int):
    db = SessionLocal()
    try:
        # ... work
    finally:
        db.close()
```

### C3. [安全性] 登入端點無速率限制

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/routers/auth.py`

`/api/auth/login` 端點沒有速率限制或帳戶鎖定機制，使其容易遭受暴力攻擊。

**修復：** 新增 `slowapi` 或簡單的記憶體速率限制器。至少在每個 IP/使用者名稱的 N 次失敗嘗試後新增指數延遲。

### C4. [安全性] JWT token 無刷新機制，24 小時過期

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/config.py` (第 13 行)

`JWT_EXPIRE_MINUTES: int = 1440` (24 小時)。結合無刷新 token 機制和儲存在 `localStorage` (易受 XSS 攻擊)，這是重大安全風險。

**修復：**
- 將 token 過期時間縮短至 30-60 分鐘
- 使用 httpOnly cookies 實現刷新 token 流程
- 或改用 httpOnly cookie 儲存 JWT

### C5. [安全性] CORS 允許所有方法和所有標頭

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/main.py` (第 85-91 行)

```python
allow_methods=["*"],
allow_headers=["*"],
```

這過於寬鬆。應該限制為實際使用的方法和標頭。

**修復：**
```python
allow_methods=["GET", "POST", "PUT", "DELETE"],
allow_headers=["Authorization", "Content-Type"],
```

### C6. [資料完整性] data_fetch_steps.py 使用錯誤的欄位名稱

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/tasks/data_fetch_steps.py` (第 66-80 行)

程式碼引用與 `DailyPrice` 模型不相符的欄位：
- 使用 `date` 但模型有 `trade_date`
- 使用 `open_price`、`high_price`、`low_price`、`close_price` 但模型有 `open`、`high`、`low`、`close`
- 使用 `Trading_Volume` 但模型有 `volume`

同樣適用於 `Institutional` 和 `MarginTrading` 模型 (第 93-131 行)。

這意味著每日管線資料擷取將**在執行時失敗**。模型定義的是 `trade_date` 而非 `date`，且欄位名稱不相符。

**修復：** 將 `data_fetch_steps.py` 中的欄位名稱與 ORM 模型定義對齊。

---

## 高優先順序 (應該修復)

### H1. [效能] 篩選結果端點中的 N+1 查詢

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/routers/screening.py` (第 56-58, 144-147 行)

`run_screening()` 和 `get_results()` 都為每個分數結果行執行单独的 `db.query(Stock)` 以取得 `stock_name`：
```python
for result in results:
    stock = db.query(Stock).filter(Stock.stock_id == result.stock_id).first()
```

對於 200+ 股票，這意味著每個請求額外 200+ 個查詢。

**修復：** 使用單一 JOIN 查詢或預先批次擷取所有股票名稱：
```python
results = (
    db.query(ScoreResult, Stock.stock_name)
    .join(Stock, ScoreResult.stock_id == Stock.stock_id)
    .filter(...)
    .all()
)
```

### H2. [效能] calculate_performance 中的 N+1 查詢

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/services/backtest_service.py` (第 127-153 行)

對於每個前 N 股票，執行 1 + len(forward_days) 個別查詢 (基準價格 + 每週期一個)。預設設定 (10 股票，3 期間) = 每個請求 40 個查詢。若 top_n=50，則為 200 個查詢。

**修復：** 在單一查詢中批次擷取所有價格，使用日期範圍。

### H3. [效能] `get_historical_top_stocks` 逐日期迴圈

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/services/backtest_service.py` (第 46-58 行)

迭代分數日期並為每個日期發出個別查詢。使用視窗函式或按 score_date 分區的單一查詢搭配 row_number。

### H4. [錯誤] `technical_indicator_chart.vue` 在 `_calculate_ma_score` 中變異輸入 DataFrame

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/services/technical_scorer.py` (第 107-112, 276 行)

方法 `_calculate_ma_score()` 和 `_calculate_volume_score()` 直接向輸入 DataFrame 新增新欄位 (`ma5`、`ma10`、`ma20`、`ma60`、`ma120`、`volume_ma20`)。如果傳入相同的 DataFrame，這會變異共享狀態。

**修復：** 使用 `.copy()` 或在不變異 `df` 的情況下計算值。

### H5. [錯誤] `prompt_templates.py` _format_margin 在 'N/A' 字串時崩潰

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/services/prompt_templates.py` (第 91 行)

```python
f"... (變化: {data.get('margin_change', 'N/A'):+} 張)"
```

`:+` 格式規範需要數值類型。如果 `margin_change` 是字串 `'N/A'`，這將引發 `ValueError`。`llm_analyzer.py` 中的 `_gather_stock_data()` 將這些設為 `'N/A'` 字串 (第 209-214 行)。

**修復：** 格式化前檢查類型，或始終提供數值預設值。

### H6. [類型安全] 前端 `screening-api.ts` 回應類型不符

**檔案：** `/Users/weihung/Desktop/project/stock-system/frontend/src/api/screening-api.ts` (第 8-12 行)

```typescript
export async function getResults(date?: string): Promise<ScoreResult[]> {
  const { data } = await apiClient.get<ScoreResult[]>('/screening/results', { ... })
```

但後端返回 `ScreeningResultsResponse`，其將項目包裝在 `{ items: [], total, threshold, weights }` 中。前端期望平坦陣列但收到物件。

同樣在 `reports-api.ts` 第 19 行 -- `getReportHistory` 將參數作為查詢字串發送，但後端期望路徑參數。

**修復：** 將前端類型與反序列化與實際後端回應格式對齊。

### H7. [錯誤] `reports-api.ts` `getReportHistory` URL 錯誤

**檔案：** `/Users/weihung/Desktop/project/stock-system/frontend/src/api/reports-api.ts` (第 19 行)

```typescript
const { data } = await apiClient.get<PaginatedResponse<LLMReport>>('/reports/history', {
    params: { stock_id: stockId, page },
})
```

但後端將路由定義為 `/reports/history/{stock_id}` (路徑參數，不是查詢參數)。這將永遠 404。

**修復：** 使用 `/reports/history/${stockId}` 作為 URL 路徑。

### H8. [記憶體洩漏] ECharts 實例從未處置

**檔案：**
- `/Users/weihung/Desktop/project/stock-system/frontend/src/components/chip-stats/institutional-trend-chart.vue` (第 87-90 行)
- `/Users/weihung/Desktop/project/stock-system/frontend/src/components/chip-stats/margin-trend-chart.vue` (第 91-94 行)
- `/Users/weihung/Desktop/project/stock-system/frontend/src/components/backtest/backtest-performance-chart.vue` (第 99-102 行)

圖表直接使用 `echarts.init()` 並新增 `window.addEventListener('resize', ...)` 但從未：
1. 在卸載時呼叫 `chartInstance.dispose()`
2. 移除調整大小事件監聽器

**修復：** 新增 `onUnmounted` 鉤子：
```typescript
onUnmounted(() => {
  chartInstance?.dispose()
  window.removeEventListener('resize', handleResize)
})
```

### H9. [錯誤] `chip_stats` 和 `backtest` 路由器 Depends 預設值錯誤

**檔案：**
- `/Users/weihung/Desktop/project/stock-system/backend/app/routers/chip_stats.py` (第 28-29, 71-72 行)
- `/Users/weihung/Desktop/project/stock-system/backend/app/routers/backtest.py` (第 29-30, 84-85 行)

```python
db: Annotated[Session, Depends(get_db)] = None,
current_user: Annotated[User, Depends(get_current_user)] = None
```

為 Depends 參數設定預設值 `= None` 具有誤導性，可能導致問題。FastAPI 仍會解析依賴項，但 `= None` 預設意味著類型註釋說謊 -- 當端點執行時值永遠不會實際為 None。但是，如果有人直接呼叫函式 (測試)，它可能會傳遞 None。

**修復：** 移除 `= None` 預設值：
```python
db: Annotated[Session, Depends(get_db)],
current_user: Annotated[User, Depends(get_current_user)]
```

---

## 中優先順序 (建議)

### M1. [棄用] `datetime.utcnow()` 在 Python 3.12+ 中已棄用

**檔案：**
- `/Users/weihung/Desktop/project/stock-system/backend/app/models/base.py` (第 13, 17, 18 行)
- `/Users/weihung/Desktop/project/stock-system/backend/app/services/auth_service.py` (第 51 行)
- `/Users/weihung/Desktop/project/stock-system/backend/app/routers/data.py` (第 27, 43, 51 行)
- `/Users/weihung/Desktop/project/stock-system/backend/app/services/news_collector.py` (第 72, 75 行)

`datetime.utcnow()` 已棄用。改用 `datetime.now(timezone.utc)`。

### M2. [程式碼品質] 4+ 個元件間重複的深色主題表格樣式

**檔案：**
- `/Users/weihung/Desktop/project/stock-system/frontend/src/components/dashboard/stock-ranking-table.vue` (第 124-149 行)
- `/Users/weihung/Desktop/project/stock-system/frontend/src/components/screening/screening-result-table.vue` (第 79-104 行)
- `/Users/weihung/Desktop/project/stock-system/frontend/src/components/settings/scheduler-config-form.vue` (第 130-146 行)
- `/Users/weihung/Desktop/project/stock-system/frontend/src/components/backtest/historical-result-table.vue` (第 109-130 行)

相同的 `:deep(.el-table)` 深色主題覆蓋至少複製到 4 個元件。

**修復：** 擷取到共享 CSS 檔案或全域 Element Plus 深色主題覆蓋。

### M3. [程式碼品質] `_calculate_pe_score` 返回硬編碼的 50

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/services/fundamental_scorer.py` (第 230-239 行)

```python
def _calculate_pe_score(self, data: list) -> float:
    # ...
    return 50.0  # Always returns neutral
```

P/E 計算不完整，永遠返回 50.0。由於它佔 10% 權重，這會扭曲基本面分數。要麼正確實現它，要么從權重分配中移除。

### M4. [程式碼品質] `scheduler-config-form.vue` 使用硬編碼 mock 資料

**檔案：** `/Users/weihung/Desktop/project/stock-system/frontend/src/components/settings/scheduler-config-form.vue` (第 8-12, 17, 26-27 行)

最近的執行日誌是硬編碼的。手動觸發使用 `setTimeout` 模擬。`saveSchedule` 函式不呼叫任何 API。

**修復：** 連接到實際存在的後端 `/api/scheduler` 端點。

### M5. [程式碼品質] `ScoringEngine` 每個請求都重新實例化

**檔案：**
- `/Users/weihung/Desktop/project/stock-system/backend/app/routers/screening.py` (第 46, 206 行)

```python
engine = ScoringEngine()  # Created fresh every request
```

`ScoringEngine` 每次建立 `HardFilter`、`ChipScorer`、`FundamentalScorer`、`TechnicalScorer` 實例。這些是無狀態的，可以是單例或 FastAPI 依賴項。

### M6. [穩健性] 無 stock_id 輸入驗證

**檔案：**
- `/Users/weihung/Desktop/project/stock-system/backend/app/routers/stocks.py` (路徑參數 `stock_id: str`)
- `/Users/weihung/Desktop/project/stock-system/backend/app/routers/screening.py` (第 180 行)
- `/Users/weihung/Desktop/project/stock-system/backend/app/routers/reports.py` (第 67 行)

`stock_id` 是未驗證的字串路徑參數。應該強制執行模式匹配 (例如，台灣股票 4-6 位數字字串) 以防止注入或無意義查詢。

**修復：** 新增正規表達式驗證：
```python
from fastapi import Path
stock_id: str = Path(..., regex=r"^\d{4,6}$")
```

### M7. [架構] `step_scoring` 忽略其 `stock_ids` 參數

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/tasks/analysis_steps.py` (第 48-85 行)

```python
def step_scoring(db, stock_ids, date_str, weights=None):
    engine = ScoringEngine()
    results = engine.run_screening(db, weights=weights, threshold=2.5)
```

函式從硬篩選器接收 `stock_ids` 但從未使用它 -- 它呼叫 `run_screening()` 會再次執行自己的硬篩選。這重複了工作。

**修復：** 將候選 stock_ids 傳遞給評分引擎，或重構以避免重複篩選。

### M8. [架構] `step_llm_analysis` 擷取全時最高分數，而非今日

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/tasks/analysis_steps.py` (第 103-105 行)

```python
top_scores = db.query(ScoreResult).order_by(desc(ScoreResult.total_score)).limit(top_n).all()
```

無日期過濾 -- 這查詢所有日期的所有分數結果，並取得前 N。應該按今天的日期過濾，以分析今天排名最高的股票。

### M9. [前端] `custom-screening-api.ts` 回應類型可能不符

**檔案：** `/Users/weihung/Desktop/project/stock-system/frontend/src/api/custom-screening-api.ts` (第 14 行)

後端返回 `{ success: True, count: N, results: [...] }` 但前端期望平坦的 `ScoreResult[]`。這將失敗或產生意外的資料。

### M10. [前端] 無路由器 catch-all / 404 路由

**檔案：** `/Users/weihung/Desktop/project/stock-system/frontend/src/router/index.ts`

無 `path: '/:pathMatch(.*)*'` catch-all 路由。導航到未定義路由的使用者會看到空白頁面。

---

## 低優先順序

### L1. 在函式主體內匯入 `json`

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/services/gemini_client.py` (第 64 行)

`import json` 在 `for` 迴圈主體內。移到檔案頂部。

### L2. 管線步驟中類型提示使用小寫 `any`

**檔案：**
- `/Users/weihung/Desktop/project/stock-system/backend/app/tasks/data_fetch_steps.py` (第 19, 147 行)
- `/Users/weihung/Desktop/project/stock-system/backend/app/tasks/analysis_steps.py` (第 17, 53, 88 行)

`Dict[str, any]` 應該是 `Dict[str, Any]` (大寫 A)。

### L3. 未使用的 `and_` 匯入

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/services/custom_screening_service.py` (第 6 行)

`from sqlalchemy import and_` 已匯入但從未使用。

### L4. 未使用的 `Decimal` 匯入

**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/services/fundamental_scorer.py` (第 4 行)
**檔案：** `/Users/weihung/Desktop/project/stock-system/backend/app/services/chip_scorer.py` (第 4 行)

`Decimal` 已匯入但未使用。

### L5. `chip-stats-api.ts` 回應形狀忽略包裝

**檔案：** `/Users/weihung/Desktop/project/stock-system/frontend/src/api/chip-stats-api.ts` (第 16-23 行)

後端返回 `{ success, days, data: [...] }` 但 API 函式將整個回應作為陣列類型返回。應該擷取 `.data`。

### L6. 前端 `LLMReport` 類型包含 `stock_name` 但後端 `LLMReportResponse` 不包含

**檔案：** `/Users/weihung/Desktop/project/stock-system/frontend/src/types/report.ts` (第 4 行)

前端 `LLMReport` 類型有 `stock_name: string` 但後端 `LLMReportResponse` schema 不包含它 (只有 `stock_id`)。此欄位將永遠是 `undefined`。

---

## 超過 200 行的檔案

### 後端 (>200 行)
| 檔案 | 行數 | 建議 |
|------|-------|----------------|
| `services/llm_analyzer.py` | 299 | 將 `_gather_stock_data()` 拆分為獨立資料收集模組 |
| `services/technical_scorer.py` | 298 | 將指標計算方法提取到 `technical_indicators.py` |
| `services/fundamental_scorer.py` | 239 | 提取個別分數計算器 |
| `routers/screening.py` | 224 | 將回應格式化提取到輔助函式 |
| `services/chip_scorer.py` | 222 | 提取子分數計算 |
| `routers/scheduler.py` | 216 | 將 Pydantic 模型提取到 schemas/ |
| `services/finmind_collector.py` | 205 | 可接受 - 主要為文檔字串 |

### 前端 (>200 行)
| 檔案 | 行數 | 建議 |
|------|-------|----------------|
| `views/reports-list-view.vue` | 319 | 將報告卡片提取為獨立元件 |
| `components/stock-detail/technical-indicator-chart.vue` | 267 | 將 KD/RSI 計算器提取到 composable |
| `views/dashboard-view.vue` | 229 | 將樣式提取到共享 |
| `components/stock-detail/llm-report-panel.vue` | 225 | 提取報告區塊卡片 |
| `views/history-backtest-view.vue` | 208 | 邊界，可接受 |

---

## 正面觀察

1. **良好的 ECharts tree-shaking** 在 `main.ts` -- 只匯入需要的圖表類型和元件
2. **正確的 JWT 驗證流程** 搭配 `HTTPBearer`、bcrypt 雜湊，正確的 401/403 區分
3. **清晰的模型設計** 具有適當的唯一限制條件、複合索引和時間戳 mixins
4. **結構良好的 Pydantic schemas** 使用 `from_attributes=True` 實現 ORM 相容性
5. **一致的深色主題** 跨所有 Vue 元件實施，符合規格顏色
6. **帶指數退避的速率限制器** 用於外部 API 呼叫 (FinMind、Gemini)
7. **正確的資料庫連線池** 使用 `pool_size=10`、`max_overflow=20`、`pool_recycle=3600`
8. **延遲路由載入** 在 Vue 路由器中實現程式碼分割
9. **良好的分離** 資料收集、評分和 LLM 分析層之間
10. **Gemini 結構化輸出** 搭配 JSON schema -- 可靠 LLM 回應的良好實踐

---

## 建議的行動 (優先順序)

1. **修復 C6** (data_fetch_steps 欄位不符) -- 管線執行時會崩潰
2. **修復 C2** (背景任務 session 範圍) -- 資料收集將失敗
3. **修復 C1** (錯誤訊息洩露) -- 安全強化
4. **修復 H6/H7** (前端 API 回應不符) -- 多個頁面將損壞
5. **修復 H8** (ECharts 記憶體洩漏) -- 會隨時間退化
6. **修復 C3** (登入速率限制) -- 暴力攻擊防護
7. **修復 H1** (N+1 查詢) -- 大規模效能
8. **修復 H5** (格式化字串崩潰) -- LLM 管線在資料缺失時會崩潰
9. **修復 M8** (step_llm_analysis 日期過濾) -- 分析錯誤的股票
10. **處理 M3** (P/E 分數佔位符) -- 不完整的評分模型

---

## 指標

| 指標 | 數值 |
|------|-------|
| 類型覆蓋率 (後端) | ~90% (Pydantic 模型 + 類型提示) |
| 類型覆蓋率 (前端) | ~85% (TypeScript strict，部分視圖使用 `any`) |
| 測試覆蓋率 | 0% (未找到測試) |
| Linting 問題 | ~8 (未使用匯入、小寫 `any`) |
| >200 行的檔案 (後端) | 7 |
| >200 行的檔案 (前端) | 5 |
| 安全問題 | 5 個關鍵 |
| 效能問題 | 3 個高 |
| 資料完整性問題 | 1 個關鍵 |

---

## 未解決的問題

1. 是否有 `.env.example` 文件記錄所需的環境變數？在審查範圍中未找到。
2. 是否有任何資料庫遷移工具 (Alembic)？目前使用 `Base.metadata.create_all()` 將無法處理 schema 變更。
3. Stock 模型有 `market` 和 `industry` 欄位，但 `data_fetch_steps.py` 只設定 `stock_id` 和 `stock_name` -- `market`/`industry` 值從何而來？
4. `news` 表有可空的 `stock_id`，而 `step_fetch_news` 只擷取一般市場新聞 (無股票特定分配)。如果 `stock_id` 從未設定，`NewsPreparator.prepare_stock_news()` 如何找到股票特定新聞？
5. 不存在使用者註冊端點 -- 初始使用者如何建立？需要 seed 指令碼或管理 CLI。
6. 硬篩選器中的 `threshold` 參數文件化為「成交量比率閾值」(2.5 倍)，但設定視圖滑桿範圍為 0-5，描述說「最低總分」。這些是相同還是不同的參數？

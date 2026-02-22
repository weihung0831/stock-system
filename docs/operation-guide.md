# 操作流程指南

## 日常操作

### 1. 啟動系統

```bash
# 後端 (Terminal 1)
cd backend && uvicorn app.main:app --reload
# → http://localhost:8000

# 前端 (Terminal 2)
cd frontend && npm run dev
# → http://localhost:5173
```

啟動後 APScheduler 會自動排程，每個交易日 16:30 執行 Pipeline。

### 2. 查看 Dashboard

1. 開啟 `http://localhost:5173`
2. 登入帳號
3. Dashboard 顯示最新排名（依 total_score 排序）
4. 頂部統計卡片顯示摘要資訊
5. 每張卡片顯示：排名、股票名、總分、籌碼/基本/技術分數、收盤價、漲跌幅
6. 分頁切換：Top 30，每頁 10 筆，底部分頁按鈕

### 3. 查看個股詳情

1. 在 Dashboard 點選任一股票
2. 顯示三因子評分卡 + 子指標明細
3. 底部顯示 AI 分析摘要（Gemini 產出）

---

## 設定操作

### 調整評分權重

1. 進入 `設定` 頁面（`/settings`）
2. 拖動三個滑桿：籌碼 / 基本面 / 技術面
   - 調一個，另外兩個自動等比例調整，總和維持 100%
3. 權重即時存入 DB，下次 Pipeline 或手動評分會套用

### 自動配置最佳比例

1. 在權重設定區塊，點「自動配置最佳比例」
2. 系統依資料覆蓋率自動分配：
   - 哪個因子的資料越完整 → 給越高權重
   - 資料不足的因子自動降低影響力
3. 權重自動更新到滑桿上

### 調整硬過濾門檻

1. 在設定頁面的「硬過濾門檻」區塊
2. 滑桿範圍 0 ~ 5（預設 2.5）
3. 數值 = 本週成交量 / 上週成交量的倍數
   - 越高 → 只選量能暴增的股票（更少但更極端）
   - 越低 → 放寬條件（更多股票入選）
4. 建議維持 2.5 ~ 3.5

**注意**: FALLBACK_TOP_N=100 意味著即使量能篩選不滿條件，系統也會補入成交量前100檔的股票

---

## 手動觸發操作

### 手動執行完整 Pipeline

**方式 A：透過 API**
```bash
curl -X POST http://localhost:8000/api/scheduler/trigger \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**方式 B：透過 Python**
```python
from app.tasks.daily_pipeline import run_daily_pipeline
result = run_daily_pipeline(trigger_type="manual")
print(result)
# {'status': 'success', 'pipeline_id': 21, 'steps_completed': 3}
```

Pipeline 3 步驟：
1. 資料抓取（收盤價、法人、融資、PER/PBR、營收、財報）
2. 硬篩選（~100 檔候選股，FALLBACK_TOP_N=100）
3. 三因子評分 + 排名 + AI 分析（所有評分股票，無限制）
   - 新聞不再獨立步驟，改為 LLM 分析時按需抓取

### 只重新評分（不抓資料）

1. 在設定頁面點「執行評分計算」
2. 或透過 API：
```bash
curl -X POST http://localhost:8000/api/screening/run \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"weights":{"chip":40,"fundamental":25,"technical":35},"threshold":2.5}'
```
用途：調完權重後立刻看新排名，不用等下次 Pipeline。

---

## 進階功能

### 自訂篩選

1. 進入 `/custom-screening`
2. 設定多重條件組合（成交量、漲跌幅、法人買超等）
3. 執行篩選，查看結果

### 籌碼統計

1. 進入 `/chip-stats`
2. 查看法人買賣超趨勢圖
3. 查看融資融券變化圖
4. 可選擇多檔股票比較

### 歷史回測

1. 進入 `/history-backtest`
2. 選擇回測區間
3. 系統模擬過去的評分排名 vs 實際漲跌
4. 產出績效圖表

### AI 報告

1. 進入 `/reports`
2. 查看歷次 Pipeline 產出的 AI 分析報告（卡片式佈局）
3. 每份報告包含投資建議（項目符號清單）

---

## 表格操作

### 排序功能
- 點擊表格欄位標題可切換排序（升序/降序）
- 排序狀態以箭頭圖示（▲/▼）顯示在欄位名稱旁
- 適用於：篩選結果表、回測結果表、執行紀錄表

### 分頁功能
- 每頁顯示 10 筆資料
- 底部分頁列：上一頁 / 頁碼 / 下一頁
- 當前頁碼以金色高亮顯示
- 邊界按鈕（首頁/末頁）自動停用

### 回到頂部
- 向下捲動超過一定距離後，右下角出現回到頂部按鈕
- 點擊平滑捲動至頁面頂部

---

## 資料維護

### 檢查資料覆蓋率

```python
cd backend && python3 -c "
from app.database import SessionLocal
from app.models.daily_price import DailyPrice
from app.models.revenue import Revenue
from app.models.financial import Financial
from app.models.stock import Stock
from sqlalchemy import func

db = SessionLocal()
print(f'股票總數: {db.query(func.count(Stock.stock_id)).scalar()}')
print(f'有價格: {db.query(func.count(func.distinct(DailyPrice.stock_id))).scalar()}')
print(f'120天+: {db.query(DailyPrice.stock_id).group_by(DailyPrice.stock_id).having(func.count(DailyPrice.trade_date)>=120).count()}')
print(f'有營收: {db.query(func.count(func.distinct(Revenue.stock_id))).scalar()}')
print(f'有財報: {db.query(func.count(func.distinct(Financial.stock_id))).scalar()}')
print(f'有PER/PBR: {db.query(func.count(Stock.stock_id)).filter(Stock.per.isnot(None)).scalar()}')
db.close()
"
```

### 檢查 Pipeline 執行紀錄

```python
cd backend && python3 -c "
from app.database import SessionLocal
from app.models.pipeline_log import PipelineLog
db = SessionLocal()
logs = db.query(PipelineLog).order_by(PipelineLog.id.desc()).limit(5).all()
for l in logs:
    print(f'#{l.id} | {l.status} | {l.steps_completed}/{l.total_steps} | {l.started_at} | {l.trigger_type}')
db.close()
"
```

### FinMind 額度用完 (402 錯誤)

1. FinMind 免費額度有限，用完會回傳 402
2. 等待額度重置（通常幾小時後）
3. 歷史價格改由 TWSE STOCK_DAY 抓取（不受影響）
4. 只有營收 YoY 和季財報需要 FinMind

---

## 問題排查

| 症狀 | 原因 | 解法 |
|------|------|------|
| Dashboard 沒資料 | Pipeline 未執行 | 手動觸發 Pipeline |
| 某些股票 0 分 | 資料不足（<120天或無營收） | 等 Pipeline 補齊歷史資料 |
| Pipeline 失敗 | 外部 API 問題 | 檢查 Pipeline log，等 API 恢復 |
| 評分沒更新 | 權重改了但沒重算 | 按「執行評分計算」 |
| FinMind 402 | 免費額度用完 | 等幾小時重置 |
| 前端 CORS 錯誤 | CORS_ORIGINS 不匹配 | 確認 .env 的 CORS_ORIGINS |
| 登入失敗 | JWT 過期或密碼錯誤 | 重新登入 |

---

## 新增功能操作 (2026-02-22 最新)

### TWSE假期自動偵測
- 系統現在會自動從 TWSE 官方API獲取年度交易假期
- 無需手動維護假期表
- 非交易日時 Pipeline 會自動略過（不產生pipeline_log記錄）
- 手動觸發在非交易日會改用最後交易日數據

### 回測時指定特定股票
- 在使用 backtest API 時，可新增 `stock_ids` 參數
- 例如：只計算特定3檔股票的歷史績效
- 使用 `as_of_date` 參數可查詢過去任意日期的評分

### 右側買法篩選操作 (2026-02-22 新增)

1. 進入 `/right-side`（側邊欄「分析」→「右側買法」）
2. 可使用下列 4 個篩選 toggle 快速過濾：
   - **今日突破**（today_breakout）：量價齊揚且突破20日高點
   - **週趨勢向上**（weekly_trend_up）：MA5>MA20 且 MA5 近3日上升
   - **強力推薦**（strong_recommend）：分數≥60、觸發≥3、週趨勢向上且非高風險
   - **風險等級**（risk_level）：可篩選 low / medium / high 風險
3. 表格顯示：評級、條件標籤、訊號明細、6個信號狀態、觸發數量、加權評分
4. 掃描範圍：Top 100 評分股 + 近7日成交量 > 200 萬股聯集

### Pipeline 簡化與新聞架構優化
- Pipeline 從 5 步驟簡化為 3 步驟
- 新聞不再是獨立步驟，改為 LLM 分析時按需抓取
- NewsPreparator 檢查 DB → 缺失時呼叫 NewsCollector 即時抓取個股新聞
- 新聞回溯期從 7 天增至 14 天

### AI分析全面升級
- 現在所有評分股票都會進行 AI 分析（不再限制Top 10）
- Pipeline 第3步會對所有候選股產出Gemini分析報告
- 利用Gemini 2.5 Flash高速率額度 (0.5秒/次)
- max_tokens 增至 8192，支援更長報告
- 新增截斷檢測與自動重試機制

### 例行維護檢查

定期檢查 Pipeline 狀態：
```bash
# 檢查最近5次 Pipeline 執行
python3 backend/scripts/check_pipeline.py
```

檢查非交易日是否被正確略過：
```bash
# 查詢最近的 pipeline_log，確認只在交易日有記錄
psql -c "SELECT id, status, created_at FROM pipeline_log ORDER BY id DESC LIMIT 10;"
```

---

**最後更新**: 2026-02-22
**版本**: 1.3

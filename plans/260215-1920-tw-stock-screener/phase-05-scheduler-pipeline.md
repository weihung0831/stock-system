# Phase 05: 排程自動化

## Context Links
- [總覽計畫](./plan.md)
- [後端研究報告](./research/researcher-01-backend-data-infra.md)
- 依賴：[Phase 01-03](./phase-01-project-init-data-pipeline.md) (資料收集 + 評分 + LLM 分析)
- 下一階段：[Phase 06 - 進階功能](./phase-06-advanced-features.md)

## Overview
- **日期:** 2026-02-15
- **優先級:** P1
- **狀態:** pending
- **預估:** 4h
- **說明:** 整合 APScheduler，每日 16:30 <!-- Updated: Validation Session 1 --> 自動執行完整 pipeline: 抓資料 → 篩選 → 評分 → LLM 分析

## Key Insights
- APScheduler AsyncIOScheduler 與 FastAPI async 相容
- 透過 lifespan event 管理 scheduler lifecycle
- 台股收盤 13:30，但 FinMind 資料約 15:00-16:30 <!-- Updated: Validation Session 1 --> 更新
- 需處理假日/休市日 (不執行)

## Requirements

### 功能需求
- FR-01: APScheduler 整合 (cron trigger, 每日 16:30 <!-- Updated: Validation Session 1 -->)
- FR-02: 完整 pipeline 串接 (fetch → filter → score → LLM → notify)
- FR-03: 手動觸發 API (不等排程，直接執行)
- FR-04: 執行狀態追蹤 (running/success/failed + 執行時間)
- FR-05: 執行日誌 API (查詢歷史執行紀錄)

### 非功能需求
- NFR-01: 完整 pipeline < 15 分鐘
- NFR-02: 任一步驟失敗記錄 error 但不阻塞
- NFR-03: Graceful shutdown (等待進行中任務完成)

## Architecture

```
tasks/
├── daily-pipeline.py       # 完整 pipeline 編排
├── pipeline-steps.py       # 各步驟封裝
└── pipeline-status.py      # 狀態追蹤

models/
└── pipeline-log.py         # 執行日誌 ORM

routers/
└── scheduler.py            # 排程管理 API
```

## Related Code Files

### 建立檔案
- `backend/app/tasks/daily-pipeline.py` - Pipeline 編排主邏輯
- `backend/app/tasks/pipeline-steps.py` - 各步驟獨立封裝
- `backend/app/tasks/pipeline-status.py` - 狀態管理
- `backend/app/models/pipeline-log.py` - 執行日誌 model
- `backend/app/routers/scheduler.py` - 排程管理 API

### 修改檔案
- `backend/app/main.py` - 加入 APScheduler lifespan

## Implementation Steps

1. **APScheduler 設定**
   - 在 `main.py` lifespan 中初始化 `AsyncIOScheduler`
   - 註冊 cron job: `hour=16, minute=30` (可從 config 讀取) <!-- Validation Session 1 -->
   - Shutdown: `scheduler.shutdown(wait=True)`

2. **Pipeline 步驟封裝**
   ```python
   # pipeline-steps.py
   async def step_fetch_data(date): ...     # 呼叫 finmind-collector
   async def step_fetch_news(): ...          # 呼叫 news-collector
   async def step_hard_filter(date): ...     # 呼叫 hard-filter
   async def step_score(stock_ids): ...      # 呼叫 scoring-engine
   async def step_llm_analyze(top_n): ...    # 呼叫 llm-analyzer
   ```

3. **Pipeline 編排**
   ```python
   # daily-pipeline.py
   async def run_daily_pipeline():
       log = create_pipeline_log(status="running")
       try:
           # Step 1: 檢查是否交易日
           if not is_trading_day(today): return skip
           # Step 2: 抓取資料 (股價/法人/融資融券)
           await step_fetch_data(today)
           # Step 3: 抓取新聞
           await step_fetch_news()
           # Step 4: 硬門檻篩選
           candidates = await step_hard_filter(today)
           # Step 5: 三因子評分
           results = await step_score(candidates)
           # Step 6: Top N 送 LLM
           top_n = results[:20]
           await step_llm_analyze(top_n)
           # Step 7: 更新狀態
           log.status = "success"
       except Exception as e:
           log.status = "failed"
           log.error = str(e)
       finally:
           log.finished_at = now()
           save(log)
   ```

4. **狀態追蹤**
   - PipelineLog model: id, started_at, finished_at, status, steps_completed, error
   - 每步驟完成更新 steps_completed
   - 前端可即時查詢進度

5. **交易日判斷**
   - 簡易版: 排除六日
   - 進階: 維護台股休市日曆 (國定假日/颱風假)
   - 或: 檢查 FinMind 當日有無資料回傳

6. **排程管理 API**
   - `POST /api/scheduler/trigger` - 手動觸發 pipeline
   - `GET /api/scheduler/status` - 目前排程狀態 + 下次執行時間
   - `GET /api/scheduler/logs` - 歷史執行日誌 (分頁)
   - `PUT /api/scheduler/config` - 更新排程時間

## Todo List
- [ ] 在 main.py 整合 APScheduler
- [ ] 實作 pipeline-steps.py (5 個步驟)
- [ ] 實作 daily-pipeline.py (編排邏輯)
- [ ] 實作 pipeline-status.py (狀態追蹤)
- [ ] 建立 pipeline-log model
- [ ] 實作 scheduler router (trigger/status/logs)
- [ ] 交易日判斷邏輯
- [ ] 測試: 手動觸發 pipeline 端對端

## Success Criteria
- 每日 16:30 <!-- Updated: Validation Session 1 --> 自動觸發 pipeline
- Pipeline 各步驟依序執行，日誌完整
- 手動觸發 API 正常運作
- 非交易日自動跳過
- 錯誤不阻塞後續步驟

## Risk Assessment
| 風險 | 機率 | 影響 | 緩解 |
|------|------|------|------|
| FinMind 16:30 <!-- Updated: Validation Session 1 --> 資料尚未更新 | 中 | 中 | 改為 16:30 或加入重試等待 |
| Pipeline 執行中 server 重啟 | 低 | 中 | Graceful shutdown + 重啟後自動補跑 |
| 同時觸發多個 pipeline | 低 | 中 | 加鎖: 一次只允許一個 pipeline |

## Security Considerations
- 手動觸發 API 需認證 (未來可加 API key 或 Basic Auth)
- Pipeline log 不記錄敏感資料 (API key 等)

## Next Steps
- Phase 06: 進階功能頁面 (自訂篩選/籌碼統計/歷史回測)

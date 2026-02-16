# Phase 06: 進階功能

## Context Links
- [總覽計畫](./plan.md)
- 依賴：[Phase 04](./phase-04-frontend-ui.md) (基本 UI), [Phase 05](./phase-05-scheduler-pipeline.md) (排程 + 歷史資料)
- 後續：上線測試 + 持續優化

## Overview
- **日期:** 2026-02-15
- **優先級:** P2
- **狀態:** pending
- **預估:** 4h
- **說明:** 新增自訂篩選、籌碼統計、LLM 報告集中檢視、歷史回測四個進階頁面

## Key Insights
- 自訂篩選需靈活的 query builder UI (Element Plus form + select)
- 籌碼統計用 ECharts 堆疊柱狀圖/折線圖
- 歷史回測核心: 比較過去篩選結果 vs 後續漲跌
- 這些功能可漸進開發，MVP 先求有再求好

## Requirements

### 功能需求
- FR-01: 自訂篩選頁 (依產業/市值/因子門檻自由組合篩選)
- FR-02: 籌碼統計頁 (法人買賣超趨勢圖、融資融券趨勢圖、全市場統計)
- FR-03: LLM 報告頁 (所有候選股報告集中檢視、搜尋/篩選)
- FR-04: 歷史/回測頁 (歷史篩選結果、策略績效追蹤)

### 非功能需求
- NFR-01: 自訂篩選 < 5 秒回應
- NFR-02: 回測計算可接受 10 秒以內

## Architecture

```
# 後端新增
routers/
├── custom-screening.py     # 自訂篩選 API
├── chip-stats.py           # 籌碼統計 API
└── backtest.py             # 歷史回測 API

services/
├── custom-screening-service.py
├── chip-stats-service.py
└── backtest-service.py

# 前端新增
views/
├── custom-screening-view.vue
├── chip-stats-view.vue
├── reports-list-view.vue
└── history-backtest-view.vue

components/
├── screening/
│   ├── filter-builder-form.vue
│   └── screening-result-table.vue
├── chip-stats/
│   ├── institutional-trend-chart.vue
│   └── margin-trend-chart.vue
└── backtest/
    ├── backtest-performance-chart.vue
    └── historical-result-table.vue
```

## Related Code Files

### 建立檔案
- `backend/app/routers/custom-screening.py`
- `backend/app/routers/chip-stats.py`
- `backend/app/routers/backtest.py`
- `backend/app/services/custom-screening-service.py`
- `backend/app/services/chip-stats-service.py`
- `backend/app/services/backtest-service.py`
- `frontend/src/views/custom-screening-view.vue`
- `frontend/src/views/chip-stats-view.vue`
- `frontend/src/views/reports-list-view.vue`
- `frontend/src/views/history-backtest-view.vue`
- `frontend/src/components/screening/*.vue`
- `frontend/src/components/chip-stats/*.vue`
- `frontend/src/components/backtest/*.vue`

### 修改檔案
- `frontend/src/router/index.ts` - 新增 4 條路由
- `frontend/src/components/layout/app-sidebar.vue` - 新增選單項目

## Implementation Steps

1. **自訂篩選頁**
   - 後端: `POST /api/custom-screening` 接收篩選條件 JSON
     - 條件: 產業別、市值範圍、各因子分數門檻、P/E 範圍
     - 回傳: 符合條件的股票列表 + 評分
   - 前端: filter-builder-form.vue
     - el-select (產業)、el-slider (分數門檻)、el-input-number (P/E 範圍)
     - 即時預覽符合條件數量
   - screening-result-table.vue: 結果表格，可點擊進入個股詳情

2. **籌碼統計頁**
   - 後端: `GET /api/chip-stats/institutional?period=30d`
     - 全市場三大法人每日買賣超合計
   - 後端: `GET /api/chip-stats/margin?period=30d`
     - 全市場融資融券餘額趨勢
   - 前端: institutional-trend-chart.vue
     - ECharts 堆疊柱狀圖 (外資/投信/自營商)
   - 前端: margin-trend-chart.vue
     - ECharts 雙軸折線圖 (融資餘額 + 融券餘額)

3. **LLM 報告集中檢視頁**
   - 後端: `GET /api/reports/all?date=&page=` (已有，可能需擴充)
   - 前端: reports-list-view.vue
     - 日期選擇器 + 搜尋框
     - 報告卡片列表 (股票名稱 + 評分 + 建議摘要)
     - 點擊展開完整報告

4. **歷史/回測頁**
   - 後端: `GET /api/backtest/history?start_date=&end_date=`
     - 查詢歷史每日 Top N 股票
   - 後端: `GET /api/backtest/performance?date=`
     - 計算某日 Top N 股票之後 5/10/20 日報酬率
   - 前端: historical-result-table.vue
     - 日期選擇 → 顯示該日 Top N 股票 + 後續表現
   - 前端: backtest-performance-chart.vue
     - ECharts 折線圖: 策略累積報酬 vs 大盤

5. **路由 + 導航更新**
   - 新增路由: /screening, /chip-stats, /reports, /history
   - sidebar 新增 4 個選單項目

## Todo List
- [ ] 實作自訂篩選 API + 前端頁面
- [ ] 實作籌碼統計 API + 圖表元件
- [ ] 實作 LLM 報告集中檢視頁
- [ ] 實作歷史回測 API + 績效圖表
- [ ] 更新 Router + Sidebar 導航

## Success Criteria
- 自訂篩選可靈活組合條件，結果正確
- 籌碼統計圖表互動流暢
- LLM 報告頁可瀏覽所有候選股報告
- 回測頁可查看歷史策略表現

## Risk Assessment
| 風險 | 機率 | 影響 | 緩解 |
|------|------|------|------|
| 回測資料量大導致查詢慢 | 中 | 中 | 預計算週/月統計 summary 表 |
| 自訂篩選條件組合爆炸 | 低 | 低 | 限制條件數量 + 查詢 timeout |

## Security Considerations
- 自訂篩選 API 防止 SQL injection (使用 ORM 參數化查詢)
- 回測 API 限制查詢時間範圍 (防止過大查詢)

## Next Steps
- 上線測試: 實際運行 1-2 週驗證評分準確度
- 持續優化: 根據使用回饋調整因子權重預設值
- 考慮新增: 推播通知 (LINE Notify/Telegram Bot)
- 考慮新增: 多策略比較功能

---

## 未解決問題
1. FinMind API 是否提供產業分類資料？若無，需另外維護股票產業對照表
2. 回測績效計算是否需考慮交易成本（手續費+證交稅）？
3. 台股休市日曆是否需要自動維護？或手動設定？

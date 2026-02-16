# Phase 04: 前端 UI 開發

## Context Links
- [總覽計畫](./plan.md)
- [前端研究報告](./research/researcher-02-frontend-llm-analytics.md)
- **[Prototype](../../prototype/index.html)** — 設計參考 (深色主題+琥珀金、產業分類、RWD 三斷點)
- 依賴：[Phase 01](./phase-01-project-init-data-pipeline.md) (API 端點), [Phase 02](./phase-02-scoring-engine.md) (評分 API), [Phase 03](./phase-03-llm-integration.md) (報告 API)
- 下一階段：[Phase 05 - 排程自動化](./phase-05-scheduler-pipeline.md)

## Overview
- **日期:** 2026-02-15
- **優先級:** P1
- **狀態:** pending
- **預估:** 9h
- **說明:** 開發核心前端頁面 — 登入頁、Dashboard、個股詳情、設定頁，使用 Vue 3 + Element Plus + ECharts <!-- Updated: Validation Session 1 - 新增登入頁 -->

## Key Insights
- Element Plus 企業級元件庫，data table / form / layout 完整
- ECharts Canvas 渲染適合大數據集 (1700+ 股 K 線)
- vue-echarts 封裝 ECharts 為 Vue component
- Pinia 官方狀態管理，適合股票資料快取
- **[Prototype]** 設計系統：深色主題 (bg `#080c14`~`#151d2e`) + 琥珀金 accent (`#e5a91a`) + JetBrains Mono 數字 + Noto Sans TC 中文，漲綠 `#22c55e` / 跌紅 `#ef4444`
- **[Prototype]** 產業分類篩選：排行表上方 Tab 按半導體/電子/金融/傳產分類，個股詳情頁顯示分類標籤
- **[Prototype]** RWD 三斷點：1024px (平板 2 欄)、768px (sidebar 抽屜+漢堡鈕+表格橫滑)、480px (統計卡/因子卡改橫式單列+Tab 橫滑)

## Requirements

### 功能需求
- FR-01: Dashboard 總覽（Top 股票排名表 + **產業分類 Tab 篩選**、評分雷達圖、籌碼異動提醒）<!-- Updated: Prototype -->
- FR-02: 個股詳情頁（**產業分類標籤** + 三因子分數、K線圖、技術指標圖、LLM 報告）<!-- Updated: Prototype -->
- FR-03: 設定頁（權重滑桿、排程設定、LLM 參數、硬門檻倍數）
- FR-04: 共用 Layout（側邊導航 + 頂部列）
- FR-05: API 整合層（axios client + error handling）
- FR-06: 登入頁面 + JWT token 管理 + router auth guard <!-- Updated: Validation Session 1 -->

### 非功能需求
- NFR-01: 首屏載入 < 2 秒
- NFR-02: 響應式設計 — 三斷點 (1024/768/480px)，桌面優先，手機可用 <!-- Updated: Prototype -->
- NFR-03: 圖表互動流暢 (60fps)

## Architecture

```
frontend/src/
├── App.vue
├── main.ts
├── api/
│   ├── client.ts             # axios instance + interceptor
│   ├── stocks-api.ts         # 股票/資料 API
│   ├── screening-api.ts      # 評分 API
│   └── reports-api.ts        # LLM 報告 API
├── router/
│   └── index.ts              # Vue Router 設定
├── stores/
│   ├── auth-store.ts          # 認證狀態 (JWT, user info) <!-- Validation Session 1 -->
│   ├── stock-store.ts        # 股票資料 store
│   ├── screening-store.ts    # 評分結果 store
│   └── settings-store.ts     # 使用者設定 store
├── views/
│   ├── login-view.vue         # 登入頁 <!-- Validation Session 1 -->
│   ├── dashboard-view.vue    # Dashboard 總覽
│   ├── stock-detail-view.vue # 個股詳情
│   └── settings-view.vue     # 設定頁
├── components/
│   ├── layout/
│   │   ├── app-sidebar.vue   # 側邊導航
│   │   └── app-header.vue    # 頂部列
│   ├── shared/
│   │   └── sector-tag.vue           # 產業分類標籤 (半導體/電子/金融/傳產) <!-- Prototype -->
│   ├── dashboard/
│   │   ├── sector-filter-tabs.vue   # 產業分類 Tab 篩選列 <!-- Prototype -->
│   │   ├── stock-ranking-table.vue  # 排行表
│   │   ├── score-radar-chart.vue    # 雷達圖
│   │   └── chip-alert-list.vue      # 籌碼異動
│   ├── stock-detail/
│   │   ├── price-candlestick-chart.vue # K線圖
│   │   ├── technical-indicator-chart.vue # 技術指標
│   │   ├── factor-score-card.vue    # 因子分數卡片
│   │   └── llm-report-panel.vue     # LLM 報告面板
│   └── settings/
│       ├── weight-slider-group.vue  # 權重滑桿組
│       └── scheduler-config-form.vue # 排程設定
└── types/
    ├── stock.ts
    ├── screening.ts
    └── report.ts
```

## Related Code Files

### 建立檔案
- `frontend/src/api/*.ts` - 4 個 API 模組
- `frontend/src/router/index.ts` - 路由設定
- `frontend/src/stores/*.ts` - 4 個 Pinia store (含 auth-store) <!-- Validation Session 1 -->
- `frontend/src/views/*.vue` - 4 個頁面 (含 login-view) <!-- Validation Session 1 -->
- `frontend/src/components/**/*.vue` - 10+ 元件
- `frontend/src/types/*.ts` - TypeScript 型別

## Implementation Steps

1. **API 整合層**
   - `client.ts`: axios instance, baseURL 從 env, JWT token interceptor, 401 重導登入 <!-- Validation Session 1 -->
   - `auth-api.ts`: login(), getCurrentUser() <!-- Validation Session 1 -->
   - `stocks-api.ts`: getStocks(), getStockPrices(), getInstitutional()
   - `screening-api.ts`: runScreening(), getResults(), getStockScore()
   - `reports-api.ts`: getLatestReports(), getStockReport()

2. **Router 設定**
   - `/login` → LoginView (公開路由) <!-- Validation Session 1 -->
   - `/` → DashboardView (需認證)
   - `/stock/:id` → StockDetailView (需認證)
   - `/settings` → SettingsView (需認證)
   - Router beforeEach guard: 無 JWT token → 重導 /login <!-- Validation Session 1 -->
   - (Phase 06 新增: /screening, /chip-stats, /reports, /history)

3. **Pinia Stores**
   - `stock-store.ts`: stocks[], selectedStock, fetchStocks(), fetchPrices()
   - `screening-store.ts`: results[], latestDate, fetchResults()
   - `settings-store.ts`: weights{chip,fundamental,technical}, threshold, 持久化至 localStorage

4. **共用 Layout** <!-- Updated: Prototype — 768px 以下 sidebar 改抽屜式 -->
   - `App.vue`: el-container + el-aside (sidebar) + el-main，RWD 768px 以下 sidebar 改抽屜 overlay
   - `app-sidebar.vue`: el-menu, 路由連結, 收合功能, 手機版漢堡按鈕觸發
   - `app-header.vue`: 頁面標題, 最後更新時間, 手機版顯示漢堡按鈕
   - `sector-tag.vue`: 共用產業分類標籤 (帶顏色圓點 + 分類名稱)

5. **Dashboard 總覽頁** <!-- Updated: Prototype — 新增產業分類 Tab -->
   - `sector-filter-tabs.vue`: 產業分類 Tab (全部/半導體/電子/金融/傳產)，手機版橫向滑動
   - `stock-ranking-table.vue`: el-table, 欄位: 排名/分類圓點/代號/名稱/收盤價/漲跌/籌碼分/基本面分/技術分/總分, 可排序+按分類篩選
   - `score-radar-chart.vue`: ECharts radar chart, 顯示選中股票三因子
   - `chip-alert-list.vue`: 法人連續買超 > 3 天的股票列表

6. **個股詳情頁** <!-- Updated: Prototype — 新增分類標籤 -->
   - Header 區: 股票代號 + `sector-tag` 產業分類標籤 + 股票名稱 + 即時價格
   - `price-candlestick-chart.vue`: ECharts K線 + 成交量, 支援縮放
   - `technical-indicator-chart.vue`: MA/KD/MACD/RSI 子圖
   - `factor-score-card.vue`: 三張 el-card, 圓形進度環顯示分數 (SVG viewBox 自適應)
   - `llm-report-panel.vue`: Markdown 渲染 LLM 報告, 含日期選擇

7. **設定頁**
   - `weight-slider-group.vue`: 3 個 el-slider, 聯動確保總和=100
   - `scheduler-config-form.vue`: 排程開關, 執行時間, 手動觸發按鈕

## Todo List
- [ ] 建立 API 整合層 (axios client + 3 API 模組)
- [ ] 設定 Vue Router
- [ ] 建立 3 個 Pinia stores
- [ ] 實作共用 Layout (sidebar + header)
- [ ] 實作 Dashboard 頁 (排行表 + 雷達圖 + 異動提醒)
- [ ] 實作個股詳情頁 (K線 + 技術指標 + 分數卡 + LLM 報告)
- [ ] 實作設定頁 (權重滑桿 + 排程設定)
- [ ] TypeScript 型別定義

## Success Criteria
- Dashboard 正確顯示 Top N 股票排行
- 個股詳情頁 K 線圖 + 技術指標互動流暢
- LLM 報告面板正確渲染
- 權重滑桿聯動正常，總和固定 100
- API 整合無錯誤，loading/error state 處理完善

## Risk Assessment
| 風險 | 機率 | 影響 | 緩解 |
|------|------|------|------|
| ECharts K 線大數據量卡頓 | 低 | 中 | dataZoom 限制可視範圍 |
| Element Plus 版本衝突 | 低 | 低 | 鎖定版本 |
| 權重滑桿 UX 不直覺 | 中 | 低 | 測試後調整互動邏輯 |

## Security Considerations
- API key 不暴露到前端
- XSS 防護: LLM 報告 sanitize 後渲染
- 前端不存敏感設定 (API key 等由後端管理)

## Next Steps
- Phase 05: 排程自動化，串接完整 pipeline
- Phase 06: 新增自訂篩選/籌碼統計/歷史回測頁面

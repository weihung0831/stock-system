# 📋 代碼庫摘要

## 🗂️ 目錄結構

```
stock-system/
├── backend/                           # FastAPI 後端應用
│   ├── app/
│   │   ├── main.py                   # FastAPI 應用入口
│   │   ├── config.py                 # 配置管理 (環境變數)
│   │   ├── database.py               # SQLAlchemy ORM 設定
│   │   ├── dependencies.py           # 依賴注入
│   │   ├── models/                   # 14 個 ORM 模型 (含 sector_tag, system_setting)
│   │   │   ├── base.py               # 基類 (TimestampMixin)
│   │   │   ├── stock.py              # 股票主檔
│   │   │   ├── daily_price.py        # 每日價格
│   │   │   ├── institutional.py      # 機構投資人持股
│   │   │   ├── margin_trading.py     # 融資融券
│   │   │   ├── revenue.py            # 月營收
│   │   │   ├── financial.py          # 財務報表
│   │   │   ├── news.py               # 新聞記錄
│   │   │   ├── score_result.py       # 最終評分結果 (含籌碼/基本面/技術面子分數)
│   │   │   ├── llm_report.py         # AI 分析報告 (含 right_side_analysis 欄位)
│   │   │   ├── report_usage.py       # 報告使用追蹤 (每日限額記錄)
│   │   │   ├── user.py               # 使用者帳戶 (含 membership_tier, email)
│   │   │   ├── sector_tag.py         # 產業分類標籤
│   │   │   ├── system_setting.py     # 系統設定鍵值
│   │   │   └── pipeline_log.py       # 流程執行日誌
│   │   ├── schemas/                  # Pydantic 驗證模式
│   │   │   ├── auth.py               # 認證 (LoginRequest, RegisterRequest, Token, UserResponse)
│   │   │   ├── admin.py              # 管理 (TierUpdateRequest)
│   │   │   ├── stock.py              # 股票 (Stock, DailyPrice)
│   │   │   ├── screening.py          # 篩選 (ScreeningParams, Result)
│   │   │   ├── report.py             # 報告 (Report, LLMReport)
│   │   │   └── common.py             # 共通模式 (Pagination, Error)
│   │   ├── routers/                  # 13 個 API 路由器
│   │   │   ├── auth.py               # /api/auth/* (登入/註冊/更新令牌，含會員系統)
│   │   │   ├── stocks.py             # /api/stocks/* (股票查詢)
│   │   │   ├── data.py               # /api/data/* (數據收集)
│   │   │   ├── admin.py              # /api/admin/* (會員管理，管理員專用)
│   │   │   ├── screening.py          # /api/screening/* (標準篩選)
│   │   │   ├── reports.py            # /api/reports/* (報告，含 24h 快取 + 會員限流)
│   │   │   ├── scheduler.py          # /api/scheduler/* (排程管理 + 設定持久化)
│   │   │   ├── custom_screening.py   # /api/custom-screening/* (自訂篩選)
│   │   │   ├── chip_stats.py         # /api/chip-stats/* (籌碼統計)
│   │   │   ├── backtest.py           # /api/backtest/* (回測+評分日期)
│   │   │   ├── chat.py               # /api/chat (AI 聊天助手，含會員限流+配額查詢)
│   │   │   ├── sector_tags.py        # /api/sector-tags/* (產業分類標籤)
│   │   │   └── right_side_signals.py # /api/right-side-signals/* (右側買法信號)
│   │   ├── services/                 # 24 個業務邏輯服務
│   │   │   ├── auth_service.py       # JWT & Bcrypt 認證
│   │   │   ├── finmind_collector.py  # FinMind API 整合
│   │   │   ├── news_collector.py     # Google News RSS 爬蟲
│   │   │   ├── rate_limiter.py       # API 速率限制
│   │   │   ├── stock_service.py      # 股票查詢邏輯
│   │   │   ├── hard_filter.py        # 初步篩選 (成交量，FALLBACK_TOP_N=500)
│   │   │   ├── chip_scorer.py        # 籌碼評分
│   │   │   ├── fundamental_scorer.py # 基本面評分
│   │   │   ├── technical_scorer.py   # 技術面評分
│   │   │   ├── scoring_engine.py     # 評分協調器 (加權計算)
│   │   │   ├── custom_screening_service.py # 自訂篩選
│   │   │   ├── chip_stats_service.py # 籌碼統計
│   │   │   ├── backtest_service.py   # 回測引擎 + 評分日期查詢
│   │   │   ├── twse_collector.py    # TWSE 官方 API 資料收集
│   │   │   ├── llm_analyzer.py       # AI 分析 (整合右側信號+籌碼/基本面/技術面，24h 快取)
│   │   │   ├── gemini_client.py      # Google Gemini API 包裝
│   │   │   ├── llm_client.py         # LLM 通用客戶端 (含 generate_chat 自由文字對話)
│   │   │   ├── chat_service.py       # AI 聊天服務 (建構系統提示詞 + 編排 LLM 對話)
│   │   │   ├── chat_rate_limiter.py  # 聊天限流 (會員等級差異: Free 3/min+10/day, Premium 5/min+100/day)
│   │   │   ├── report_rate_limiter.py # 報告生成限流 (Free 5/day, Premium unlimited)
│   │   │   ├── right_side_signal_detector.py # 右側買法信號檢測 (6個信號 + 4個篩選條件 + 動態風報比計算)
│   │   │   ├── news_preparator.py    # 新聞預處理
│   │   │   ├── on_demand_data_fetcher.py # 按需資料抓取 (非 Pipeline 股票)
│   │   │   └── prompt_templates.py   # LLM 提示詞範本 (含右側信號交叉驗證指令)
│   │   └── tasks/                    # 5 個自動化任務檔案
│   │       ├── daily_pipeline.py     # 日常流程協調 (3步驟，16:30 執行)
│   │       ├── data_fetch_steps.py   # 數據收集步驟
│   │       ├── analysis_steps.py     # 評分與即時 LLM 分析步驟（含按需新聞抓取）
│   │       ├── pipeline_status.py    # 進度與日誌
│   │       └── __init__.py
│   ├── tests/                        # 單元測試 (297 個測試，20 個測試檔)
│   │   ├── conftest.py               # Pytest 設定與固件
│   │   ├── test_auth_service.py      # 認證測試 (156 行)
│   │   ├── test_models.py            # 模型測試 (496 行)
│   │   ├── test_config.py            # 配置測試 (299 行)
│   │   ├── test_stock_service.py     # 股票服務測試 (386 行)
│   │   ├── test_hard_filter.py       # 篩選測試 (315 行)
│   │   ├── test_rate_limiter.py      # 速率限制測試 (237 行)
│   │   ├── test_analysis_steps.py    # 分析步驟測試 (115 行)
│   │   ├── test_finmind_collector.py # FinMind 收集器測試 (22 個測試)
│   │   ├── test_chat_service.py      # 聊天服務測試 (22 個測試：build_stock_context/chat_with_assistant/router/限流整合)
│   │   ├── test_chat_rate_limiter.py # 聊天限流測試 (7 個測試：每分鐘限制/每日限制/重置邏輯)
│   │   ├── test_report_cache.py      # 報告快取測試 (5 個測試：24h 快取命中/未命中/邊界)
│   │   ├── test_scoring_engine.py     # 評分引擎測試
│   │   ├── test_right_side_signal_detector.py # 右側信號偵測器測試
│   │   ├── test_dependencies.py       # 依賴注入測試
│   │   └── test_daily_pipeline.py     # 每日 Pipeline 測試
│   ├── requirements.txt               # Python 依賴
│   ├── .env.example                  # 環境變數範本
│   └── pytest.ini                    # Pytest 設定
│
├── frontend/                          # Vue 3 + TypeScript 前端應用
│   ├── src/
│   │   ├── main.ts                   # 應用入口
│   │   ├── App.vue                   # 根元件
│   │   ├── views/                    # 13 個頁面
│   │   │   ├── login-view.vue        # 登入頁面
│   │   │   ├── register-view.vue      # 註冊頁面 (含電郵驗證、密碼強度檢查、會員等級選擇)
│   │   │   ├── profile-view.vue       # 會員資料頁 (顯示會員等級、聊天配額、升級提示)
│   │   │   ├── pricing-view.vue       # 定價頁面 (會員方案比較)
│   │   │   ├── admin-users-view.vue   # 管理員後台 (使用者列表、編輯狀態)
│   │   │   ├── dashboard-view.vue    # 主儀表板 (篩選結果表 + 顯示限制選單)
│   │   │   ├── stock-detail-view.vue # 股票詳情 (K線+評分+AI報告)
│   │   │   ├── custom-screening-view.vue # 自訂篩選介面
│   │   │   ├── chip-stats-view.vue   # 籌碼統計
│   │   │   ├── reports-list-view.vue # 報告清單
│   │   │   ├── history-backtest-view.vue # 回測歷史
│   │   │   ├── right-side-screening-view.vue # 右側買法篩選 (9欄表格含操作/報酬比欄 + 3組標籤式篩選列)
│   │   │   └── settings-view.vue     # 系統設定
│   │   ├── components/               # 22 個可重用元件 (含新增右側買法條件標籤顯示)
│   │   │   ├── ai-assistant/
│   │   │   │   ├── ai-chat-message.vue     # 聊天氣泡訊息元件 (使用者/AI 雙向)
│   │   │   │   └── ai-assistant-widget.vue # 浮動氣泡 + 彈出聊天面板 (整合真實 API + mock fallback)
│   │   │   ├── layout/
│   │   │   │   ├── app-header.vue    # 頂部導航欄 (桌機版含搜尋欄，手機版隱藏搜尋)
│   │   │   │   ├── header-stock-search.vue # 股票搜尋元件 (debounced autocomplete，支援鍵盤導航)
│   │   │   │   └── app-sidebar.vue   # 側邊欄菜單 (手機版內含搜尋欄)
│   │   │   ├── dashboard/
│   │   │   │   ├── stock-ranking-table.vue # 排名表格
│   │   │   │   └── sector-filter-tabs.vue  # 產業篩選
│   │   │   ├── stock-detail/
│   │   │   │   ├── price-candlestick-chart.vue # K 線圖
│   │   │   │   ├── technical-indicator-chart.vue # 技術指標
│   │   │   │   ├── factor-score-card.vue   # 評分卡
│   │   │   │   └── llm-report-panel.vue    # AI 報告面板 (含右側買法信號段落)
│   │   │   ├── screening/
│   │   │   │   ├── filter-builder-form.vue # 篩選條件構建
│   │   │   │   └── screening-result-table.vue # 篩選結果表 (含分頁+排序)
│   │   │   ├── chip-stats/
│   │   │   │   ├── institutional-trend-chart.vue # 機構趨勢
│   │   │   │   └── margin-trend-chart.vue  # 融資融券趨勢
│   │   │   ├── backtest/
│   │   │   │   ├── backtest-performance-chart.vue # 績效圖
│   │   │   │   └── historical-result-table.vue    # 結果表 (含分頁+排序)
│   │   │   ├── settings/
│   │   │   │   ├── scheduler-config-form.vue # 排程設定 (持久化)
│   │   │   │   └── weight-slider-group.vue   # 權重滑桿
│   │   │   └── shared/
│   │   │       ├── sector-tag.vue    # 產業標籤
│   │   │       └── scroll-to-top.vue # 回到頂部按鈕 (全域，位置已調整避免與 AI 氣泡重疊)
│   │   ├── stores/                   # 5 個 Pinia 狀態存儲
│   │   │   ├── auth-store.ts         # 使用者與令牌管理
│   │   │   ├── stock-store.ts        # 股票數據快取
│   │   │   ├── screening-store.ts    # 篩選參數與結果
│   │   │   ├── settings-store.ts     # 使用者偏好
│   │   │   └── sector-tags-store.ts  # 產業分類標籤
│   │   ├── api/                      # 12 個 API 呼叫模組
│   │   │   ├── client.ts             # Axios 實例與攔截器
│   │   │   ├── auth-api.ts           # 認證 API
│   │   │   ├── admin-api.ts          # 管理員 API 客戶端
│   │   │   ├── stocks-api.ts         # 股票查詢 API
│   │   │   ├── screening-api.ts      # 標準篩選 API
│   │   │   ├── custom-screening-api.ts # 自訂篩選 API
│   │   │   ├── chip-stats-api.ts     # 籌碼統計 API
│   │   │   ├── backtest-api.ts       # 回測 API
│   │   │   ├── reports-api.ts        # 報告 API
│   │   │   ├── chat-api.ts           # AI 聊天 API 客戶端
│   │   │   ├── right-side-signals-api.ts # 右側買法信號 API 客戶端
│   │   │   └── sector-tags-api.ts    # 產業標籤 API 客戶端
│   │   ├── types/                    # 5 個 TypeScript 型別定義
│   │   │   ├── auth.ts               # User, LoginRequest, RegisterRequest, Token
│   │   │   ├── stock.ts              # Stock, DailyPrice, Institutional
│   │   │   ├── screening.ts          # ScreeningParams, Result
│   │   │   ├── report.ts             # Report, LLMReport
│   │   │   └── right-side-signals.ts # RightSideSignal, RightSideSignalResult (含 today_breakout, weekly_trend_up, strong_recommend, risk_level, prediction.action, prediction.risk_reward)
│   │   ├── router/                   # Vue Router 設定
│   │   └── assets/                   # 靜態資源 (圖片, 字體)
│   ├── index.html                    # HTML 入口
│   ├── vite.config.ts                # Vite 構建配置
│   ├── tsconfig.json                 # TypeScript 配置
│   ├── tailwind.config.js            # Tailwind CSS (可選)
│   ├── package.json                  # npm 依賴
│   └── .env.example                  # 前端環境變數範本
│
├── docs/                             # 專案文檔
│   ├── project-overview-pdr.md       # 專案概述與 PDR
│   ├── system-architecture.md        # 系統架構詳解
│   ├── codebase-summary.md           # 本文檔 (代碼庫摘要)
│   ├── code-standards.md             # 編碼規範 (待建立)
│   └── development-roadmap.md        # 開發路線圖 (待建立)
│
├── plans/                            # 專案計畫與報告
│   ├── reports/                      # 測試與分析報告
│   │   ├── tester-260215-2106-*.md  # 測試報告
│   │   └── README.md                 # 報告索引
│   └── phases/                       # 開發階段計畫
│
├── prototype/                        # 原型與草稿
├── .git/                             # Git 版本控制
├── .gitignore                        # Git 忽略檔案
├── Claude.md                         # 專案指引 (繁體中文)
├── TESTING_STATUS.md                 # 測試狀態報告
└── README.md                         # (待建立) 專案入門指南

總計: ~160 個檔案, ~25,581 行代碼 (後端 ~15,210 + 前端 ~10,371)
```

## ⚙️ 核心模組說明

### 🔐 認證模組 (AuthService)

```python
# 密碼管理
hash_password(password: str) → hashed_password
verify_password(password: str, hashed: str) → bool

# JWT 令牌
create_access_token(data: dict, expires_delta: timedelta) → token_str
verify_token(token: str) → user_data

# 端點守衛
get_current_user(token: str) → User (依賴注入)
```

**相關檔案**:
- 🗂️ `app/services/auth_service.py` (150+ 行)
- 🔌 `app/routers/auth.py` (API 端點)
- 🗄️ `app/models/user.py` (ORM 模型)
- 🧪 `tests/test_auth_service.py` (18 個測試)

### 📊 評分引擎 (ScoringEngine)

```
流程:
1. HardFilter.filter_by_volume() → 候選股票清單
   ├─ 量能異常比 > 2.5x 或 FALLBACK_TOP_N=500
   └─ 保留: stock_id 列表

2. 逐股評分:
   ├─ ChipScorer.score(stock_id, date)
   │  ├─ 機構持股變化
   │  └─ 融資融券比率
   ├─ FundamentalScorer.score(stock_id, date)
   │  ├─ 淨利成長
   │  └─ 營收成長
   └─ TechnicalScorer.score(stock_id, date)
      ├─ 移動平均趨勢
      └─ 相對強弱指數

3. 加權計算:
   total_score = (chip * 40 + fundamental * 35 + technical * 25) / 100

4. 結果儲存:
   └─ ScoreResult (最終排名 + chip_score/fundamental_score/technical_score 子分數)
```

**相關檔案**:
- 🗂️ `app/services/scoring_engine.py` (200+ 行)
- ⚙️ `app/services/chip_scorer.py`, `fundamental_scorer.py`, `technical_scorer.py`
- 🔍 `app/services/hard_filter.py`
- 🔌 `app/routers/screening.py`

### 📡 數據收集模組

```
每日流程 (預設 16:30 自動執行，可於設定頁面調整):

FinmindCollector (FinMind HTTP API)
├─ fetch_stock_list() → Stock 表（過濾已下市股票，30天 cutoff）
├─ fetch_daily_price() → DailyPrice 表
├─ fetch_institutional() → Institutional 表
└─ fetch_margin_trading() → MarginTrading 表

TWSECollector (TWSE 官方 API)
├─ fetch_latest_prices() → 全市場價格 (STOCK_DAY_ALL)
├─ fetch_latest_prices_fallback() → 全市場價格備援 (MI_INDEX)
├─ fetch_institutional_all() → 全市場法人買賣 (T86)
├─ fetch_margin_all() → 全市場融資融券 (MI_MARGN)
├─ fetch_per_ratio() → 全市場估值 (BWIBBU_ALL)
├─ fetch_monthly_revenue() → 月營收 (t187ap05_L 上市 ~1065 家 + t187ap05_P 上櫃 ~293 家)
└─ fetch_quarterly_financials() → 季度財報 TWSE 備援 (FinMind 402 額度耗盡時啟用，串流 EPS/毛利率/營益率/ROE/負債比；現金流設 null)
├─ fetch_stock_history() → 個股歷史資料

NewsCollector (Google News RSS)
└─ fetch_news() → News 表

RateLimiter (自訂)
├─ 限制 FinMind API 呼叫頻率
└─ 避免超額請求

FinMind 402 全域旗標
├─ 任一 FinMind 呼叫回傳 402 → 設定 finmind_exhausted = True
└─ 後續所有 FinMind 呼叫立即跳過，切換 TWSE 備援
```

**相關檔案**:
- 🗂️ `app/services/finmind_collector.py` (150+ 行)
- 📰 `app/services/news_collector.py`
- 🚦 `app/services/rate_limiter.py`
- 🔌 `app/routers/data.py`

### 🤖 LLM 分析模組

```
流程:
ScoreResult 表 → 收集 5 面向數據 → NewsPreparator → Gemini API → LLMReport 表

數據收集 (_gather_stock_data)
├─ 籌碼面：法人近 10 日買賣超 + 融資融券近 5 日趨勢
├─ 基本面：營收 3 月 YoY + EPS 4 季 + ROE/負債比/現金流
├─ 技術面：收盤價 + 成交量 + MA(5/10/20/60/120) + KD/MACD/RSI
├─ 右側信號：RightSideSignalDetector 偵測 6 信號 + 進出場預測
└─ 新聞：NewsPreparator 按需抓取 14 天個股新聞

Prompt 架構 (prompt_templates.py)
├─ SYSTEM_PROMPT：指示 LLM 進行交叉驗證分析
│  ├─ right_side_analysis：信號與籌碼/技術/基本面交叉驗證
│  └─ recommendation：整合所有面向，含具體進出場價位
├─ 6 個 prompt 段落：籌碼 → 基本面 → 技術面 → 右側信號 → 新聞 → 評分
└─ RESPONSE_SCHEMA：9 個輸出欄位（含 right_side_analysis）

GeminiClient
├─ 調用 Google Generative AI (Gemini 2.5 Pro)
├─ max_tokens: 8192
├─ 截斷檢測 + 自動重試
└─ 速率限制: 0.5 秒/次
```

**相關檔案**:
- 🗂️ `app/services/llm_analyzer.py`
- 🤖 `app/services/gemini_client.py`
- 📰 `app/services/news_preparator.py`
- 📝 `app/services/prompt_templates.py`

### 🏪 前端狀態管理

```
authStore
├─ user: User | null
├─ token: string | null
├─ isLoading: boolean
├─ login(credentials) → async
├─ register(data) → async
└─ logout() → void

screeningStore
├─ weights: { chip: 40, fundamental: 35, technical: 25 }
├─ filters: FilterCondition[]
├─ results: ScreeningResult[]
├─ isLoading: boolean
├─ runScreening() → async
└─ updateWeights(weights) → void

stockStore
├─ stocks: Map<string, Stock>
├─ selectedStock: Stock | null
├─ fetchStocks() → async
├─ fetchStockDetail(id) → async
└─ getStockById(id) → Stock
```

**相關檔案**:
- 🗂️ `src/stores/auth-store.ts`
- 📦 `src/stores/screening-store.ts`
- 📦 `src/stores/stock-store.ts`

### 🔌 API 客戶端

```typescript
// 基礎設定 (client.ts)
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
})

// JWT 令牌自動添加
api.interceptors.request.use(config => {
  const token = authStore.token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 錯誤處理 (401 自動登出)
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      authStore.logout()
    }
    return Promise.reject(error)
  }
)
```

**相關檔案**:
- 🗂️ `src/api/client.ts`
- 🔌 `src/api/*-api.ts` (11 個端點模組)

## 🗄️ 資料庫模型關係

```
Stock (股票主檔)
├── DailyPrice (一對多)
├── Institutional (一對多)
├── MarginTrading (一對多)
├── Revenue (一對多)
├── Financial (一對多)
├── News (一對多)
└── ScoreResult (一對多)

ScoreResult (篩選結果，內含 chip_score/fundamental_score/technical_score 子分數)

User (使用者)
└── (未建立關係，用於認證)

LLMReport (AI 報告)
└── 參考 Stock (不直接外鍵)

PipelineLog (流程日誌)
└── (獨立表，記錄執行狀態)
```

## 🔧 關鍵設定

### 🌐 環境變數 (.env)

```bash
# 資料庫
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/stock_screener

# API 令牌
FINMIND_TOKEN=your_finmind_token
GEMINI_API_KEY=your_gemini_api_key

# JWT 設定
JWT_SECRET_KEY=your_secret_key_for_jwt
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 📦 依賴清單

**後端** (Python)
```
fastapi==0.115.0
sqlalchemy==2.0.35
pymysql==1.1.1
pydantic-settings==2.5.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.2.0
finmind==0.4.12
apscheduler==3.10.4
openai>=1.30.0
requests>=2.31.0
python-multipart==0.0.9
python-dateutil>=2.8.2
feedparser==6.0.11
pandas==2.2.3
numpy==1.26.4
httpx==0.27.0
pytest==7.4.3
```

**前端** (npm)
```
vue@3.3.4
typescript@5.2.2
vite@5.0.2
element-plus@2.4.2
echarts@5.4.3
pinia@2.1.7
axios@1.6.2
tailwindcss (可選)
```

## 📐 編碼約定

### 🏷️ 命名規則

**Python**
- 📄 檔案: `snake_case` (e.g., `auth_service.py`)
- 🏛️ 類別: `PascalCase` (e.g., `AuthService`)
- 🔧 函數: `snake_case` (e.g., `get_current_user`)
- 📌 常數: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)

**TypeScript/Vue**
- 📄 檔案: `kebab-case` (e.g., `auth-store.ts`, `login-view.vue`)
- 🏛️ 類別: `PascalCase` (e.g., `AuthStore`)
- 🔧 函數: `camelCase` (e.g., `getCurrentUser`)
- 📌 常數: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)

### 🎨 代碼樣式

**Python**
- 縮排: 4 空格
- 最大行長: 88 (Ruff 預設)
- 型別提示: 必須

**TypeScript**
- 縮排: 2 空格
- 最大行長: 100
- 嚴格模式: 啟用
- 分號: 必須

## 📈 性能指標

| 指標 | 目標 | 達成 |
|------|------|------|
| API 端點響應 | < 2秒 | ✅ |
| 篩選執行時間 | < 10秒 | ✅ |
| 數據庫查詢 (N+1 優化後) | 3 次 SQL | ✅ |
| 前端首屏載入 | < 3秒 | ✅ |
| 測試覆蓋率 | > 80% | ✅ 100% (核心服務) |

## 🧪 測試覆蓋

```
總計: 297 個測試, 20 個測試檔, 100% 通過率

認證服務        ✅ 156 行代碼，100% 覆蓋
模型           ✅ 496 行代碼，93-100% 覆蓋
配置           ✅ 299 行代碼，100% 覆蓋
股票服務        ✅ 386 行代碼，97% 覆蓋
硬篩選         ✅ 315 行代碼，100% 覆蓋
速率限制        ✅ 237 行代碼，100% 覆蓋
分析步驟        ✅ 115 行代碼，100% 覆蓋
FinMind 收集器  ✅ 22 個測試，100% 覆蓋
聊天服務        ✅ 22 個測試，涵蓋 build_stock_context/chat_with_assistant/router/限流整合
聊天限流        ✅ 7 個測試，涵蓋每分鐘/日限制/重置邏輯/會員差異
報告快取        ✅ 5 個測試，涵蓋 24h 快取命中/未命中/邊界
評分引擎        ✅ test_scoring_engine.py
右側信號偵測    ✅ test_right_side_signal_detector.py
依賴注入        ✅ test_dependencies.py
Pipeline 流程   ✅ test_daily_pipeline.py
會員系統        ✅ ~34 個測試，涵蓋註冊/驗證/等級管理/限流（新增）

持續擴展:
評分服務整合測試 (計畫)
前端元件測試 (計畫)
```

## 🚀 部署檢查清單

- [ ] 環境變數設定正確
- [ ] 資料庫初始化與遷移
- [ ] FinMind & Gemini API 令牌有效
- [ ] CORS 來源設定正確
- [ ] 前端 API 端點設定正確
- [ ] HTTPS/SSL 憑證
- [ ] 日誌輪轉設定
- [ ] 備份策略
- [ ] 監控告警

---

## 📅 最近核心更新 (2026-02-26)

### 🔌 外部 Cron 觸發端點 (d035f99)
- 新增 `POST /api/scheduler/cron-trigger?secret=CRON_SECRET`
- 解決 Zeabur 容器自動休眠導致內部 APScheduler 不觸發問題
- 外部排程服務（如 cron-job.org）定期呼叫此端點，確保 Pipeline 可靠執行
- 環境變數：`CRON_SECRET` (在 `app/config.py`)

### 📊 個股評分一致性修正 (6b7bd14)
- `GET /screening/results/{stock_id}` 改為讀取 Pipeline 預存分數（`score_result` 表）
- 之前版本會即時重算分數，導致 Dashboard 與個股詳情頁分數不一致
- 現已統一由 Pipeline `score_result` 表提供，保證全站分數一致
- Dashboard、篩選列表、個股詳情頁 **共享同一評分結果**

### 🎨 全站分數色彩統一 (b19ba8b)
- Dashboard 新增「三指標 ≥ 70」篩選按鈕
- 統一所有表格的分數顏色門檻：
  - **≥ 69.95** 綠色 (Strong)
  - **≥ 49.95** 黃色 (Hold)
  - **< 49.95** 紅色 (Avoid)
- 覆蓋頁面：dashboard-view、screening-result-table、historical-result-table、right-side-screening-view

### 📋 報告列表 UI 完善 (2c6a11e)
- 報告清單頁補齊右側信號與投資建議區塊
- 顯示格式與個股詳情頁統一，提升用戶體驗一致性

---

**最後更新**: 2026-02-26
**版本**: 3.7
**狀態**: 加入 Cron 觸發備援、評分一致性修正、全站分數標準化；共 297 個測試通過，覆蓋率 57%

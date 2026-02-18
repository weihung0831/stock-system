# 代碼庫摘要

## 目錄結構

```
stock-system/
├── backend/                           # FastAPI 後端應用
│   ├── app/
│   │   ├── main.py                   # FastAPI 應用入口
│   │   ├── config.py                 # 配置管理 (環境變數)
│   │   ├── database.py               # SQLAlchemy ORM 設定
│   │   ├── dependencies.py           # 依賴注入
│   │   ├── models/                   # 13個 ORM 模型
│   │   │   ├── base.py               # 基類 (TimestampMixin)
│   │   │   ├── stock.py              # 股票主檔
│   │   │   ├── daily_price.py        # 每日價格
│   │   │   ├── institutional.py      # 機構投資人持股
│   │   │   ├── margin_trading.py     # 融資融券
│   │   │   ├── revenue.py            # 月營收
│   │   │   ├── financial.py          # 財務報表
│   │   │   ├── news.py               # 新聞記錄
│   │   │   ├── chip_score.py         # 籌碼評分
│   │   │   ├── fundamental_score.py  # 基本面評分
│   │   │   ├── technical_score.py    # 技術面評分
│   │   │   ├── score_result.py       # 最終評分結果
│   │   │   ├── llm_report.py         # AI 分析報告
│   │   │   ├── user.py               # 使用者帳戶
│   │   │   └── pipeline_log.py       # 流程執行日誌
│   │   ├── schemas/                  # Pydantic 驗證模式
│   │   │   ├── auth.py               # 認證 (LoginRequest, Token)
│   │   │   ├── stock.py              # 股票 (Stock, DailyPrice)
│   │   │   ├── screening.py          # 篩選 (ScreeningParams, Result)
│   │   │   ├── report.py             # 報告 (Report, LLMReport)
│   │   │   └── common.py             # 共通模式 (Pagination, Error)
│   │   ├── routers/                  # 9 個 API 路由器
│   │   │   ├── auth.py               # /api/auth/* (登入/註冊/更新令牌)
│   │   │   ├── stocks.py             # /api/stocks/* (股票查詢)
│   │   │   ├── data.py               # /api/data/* (數據收集)
│   │   │   ├── screening.py          # /api/screening/* (標準篩選)
│   │   │   ├── reports.py            # /api/reports/* (報告)
│   │   │   ├── scheduler.py          # /api/scheduler/* (排程管理 + 設定持久化)
│   │   │   ├── custom_screening.py   # /api/custom-screening/* (自訂篩選)
│   │   │   ├── chip_stats.py         # /api/chip-stats/* (籌碼統計)
│   │   │   └── backtest.py           # /api/backtest/* (回測+評分日期)
│   │   ├── services/                 # 19 個業務邏輯服務
│   │   │   ├── auth_service.py       # JWT & Bcrypt 認證
│   │   │   ├── finmind_collector.py  # FinMind API 整合
│   │   │   ├── news_collector.py     # Google News RSS 爬蟲
│   │   │   ├── rate_limiter.py       # API 速率限制
│   │   │   ├── stock_service.py      # 股票查詢邏輯
│   │   │   ├── hard_filter.py        # 初步篩選 (成交量，FALLBACK_TOP_N=50)
│   │   │   ├── chip_scorer.py        # 籌碼評分
│   │   │   ├── fundamental_scorer.py # 基本面評分
│   │   │   ├── technical_scorer.py   # 技術面評分
│   │   │   ├── scoring_engine.py     # 評分協調器 (加權計算)
│   │   │   ├── custom_screening_service.py # 自訂篩選
│   │   │   ├── chip_stats_service.py # 籌碼統計
│   │   │   ├── backtest_service.py   # 回測引擎 + 評分日期查詢
│   │   │   ├── twse_collector.py    # TWSE 官方 API 資料收集
│   │   │   ├── llm_analyzer.py       # AI 分析 (新聞摘要，0.5s 速率限制)
│   │   │   ├── gemini_client.py      # Google Gemini API 包裝
│   │   │   ├── news_preparator.py    # 新聞預處理
│   │   │   ├── on_demand_data_fetcher.py # 按需資料抓取 (非 Pipeline 股票)
│   │   │   └── prompt_templates.py   # LLM 提示詞範本
│   │   └── tasks/                    # 5 個自動化任務檔案
│   │       ├── daily_pipeline.py     # 日常流程協調 (3步驟，16:30 執行)
│   │       ├── data_fetch_steps.py   # 數據收集步驟
│   │       ├── analysis_steps.py     # 分析與評分步驟（含按需新聞抓取）
│   │       ├── pipeline_status.py    # 進度與日誌
│   │       └── __init__.py
│   ├── tests/                        # 單元測試 (140+ 個測試)
│   │   ├── conftest.py               # Pytest 設定與固件
│   │   ├── test_auth_service.py      # 認證測試 (156 行)
│   │   ├── test_models.py            # 模型測試 (496 行)
│   │   ├── test_config.py            # 配置測試 (299 行)
│   │   ├── test_stock_service.py     # 股票服務測試 (386 行)
│   │   ├── test_hard_filter.py       # 篩選測試 (315 行)
│   │   ├── test_rate_limiter.py      # 速率限制測試 (237 行)
│   │   ├── test_analysis_steps.py    # 分析步驟測試 (115 行)
│   │   └── test_finmind_collector.py # FinMind 收集器測試 (22 個測試)
│   ├── requirements.txt               # Python 依賴
│   ├── .env.example                  # 環境變數範本
│   └── pytest.ini                    # Pytest 設定
│
├── frontend/                          # Vue 3 + TypeScript 前端應用
│   ├── src/
│   │   ├── main.ts                   # 應用入口
│   │   ├── App.vue                   # 根元件
│   │   ├── views/                    # 8 個頁面
│   │   │   ├── login-view.vue        # 登入頁面
│   │   │   ├── dashboard-view.vue    # 主儀表板 (篩選結果表 + 顯示限制選單)
│   │   │   ├── stock-detail-view.vue # 股票詳情 (K線+評分+AI報告)
│   │   │   ├── custom-screening-view.vue # 自訂篩選介面
│   │   │   ├── chip-stats-view.vue   # 籌碼統計
│   │   │   ├── reports-list-view.vue # 報告清單
│   │   │   ├── history-backtest-view.vue # 回測歷史
│   │   │   └── settings-view.vue     # 系統設定
│   │   ├── components/               # 20 個可重用元件
│   │   │   ├── layout/
│   │   │   │   ├── app-header.vue    # 頂部導航欄 (含搜尋欄)
│   │   │   │   ├── header-stock-search.vue # 股票搜尋 (autocomplete)
│   │   │   │   └── app-sidebar.vue   # 側邊欄菜單
│   │   │   ├── dashboard/
│   │   │   │   ├── stock-ranking-table.vue # 排名表格
│   │   │   │   ├── score-radar-chart.vue   # 評分雷達圖
│   │   │   │   ├── sector-filter-tabs.vue  # 產業篩選
│   │   │   │   └── chip-alert-list.vue     # 籌碼警報
│   │   │   ├── stock-detail/
│   │   │   │   ├── price-candlestick-chart.vue # K 線圖
│   │   │   │   ├── technical-indicator-chart.vue # 技術指標
│   │   │   │   ├── factor-score-card.vue   # 評分卡
│   │   │   │   └── llm-report-panel.vue    # AI 報告面板
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
│   │   │       ├── sector-tag.vue   # 產業標籤
│   │   │       └── scroll-to-top.vue # 回到頂部按鈕 (全域)
│   │   ├── stores/                   # 4 個 Pinia 狀態存儲
│   │   │   ├── auth-store.ts         # 使用者與令牌管理
│   │   │   ├── stock-store.ts        # 股票數據快取
│   │   │   ├── screening-store.ts    # 篩選參數與結果
│   │   │   └── settings-store.ts     # 使用者偏好
│   │   ├── api/                      # 8 個 API 呼叫模組
│   │   │   ├── client.ts             # Axios 實例與攔截器
│   │   │   ├── auth-api.ts           # 認證 API
│   │   │   ├── stocks-api.ts         # 股票查詢 API
│   │   │   ├── screening-api.ts      # 標準篩選 API
│   │   │   ├── custom-screening-api.ts # 自訂篩選 API
│   │   │   ├── chip-stats-api.ts     # 籌碼統計 API
│   │   │   ├── backtest-api.ts       # 回測 API
│   │   │   └── reports-api.ts        # 報告 API
│   │   ├── types/                    # 3 個 TypeScript 型別定義
│   │   │   ├── auth.ts               # User, LoginRequest, Token
│   │   │   ├── stock.ts              # Stock, DailyPrice, Institutional
│   │   │   ├── screening.ts          # ScreeningParams, Result
│   │   │   └── report.ts             # Report, LLMReport
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

總計: ~150 個檔案, ~15,000 行代碼
```

## 核心模組說明

### 認證模組 (AuthService)

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
- `app/services/auth_service.py` (150+ 行)
- `app/routers/auth.py` (API 端點)
- `app/models/user.py` (ORM 模型)
- `tests/test_auth_service.py` (18 個測試)

### 評分引擎 (ScoringEngine)

```
流程:
1. HardFilter.filter_by_volume() → 候選股票清單
   ├─ 量能異常比 > 2.5x 或 FALLBACK_TOP_N=50
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
   ├─ ScoreResult (最終排名)
   ├─ ChipScore (個別評分記錄)
   ├─ FundamentalScore
   └─ TechnicalScore
```

**相關檔案**:
- `app/services/scoring_engine.py` (200+ 行)
- `app/services/chip_scorer.py`, `fundamental_scorer.py`, `technical_scorer.py`
- `app/services/hard_filter.py`
- `app/routers/screening.py`

### 數據收集模組

```
每日流程 (預設 16:30 自動執行，可於設定頁面調整):

FinmindCollector (FinMind HTTP API)
├─ fetch_stock_list() → Stock 表（過濾已下市股票，30天 cutoff）
├─ fetch_daily_price() → DailyPrice 表
├─ fetch_institutional() → Institutional 表
└─ fetch_margin_trading() → MarginTrading 表

TWSECollector (TWSE 官方 API)
├─ fetch_all_daily_prices() → 全市場價格 (STOCK_DAY_ALL)
├─ fetch_all_institutional() → 全市場法人買賣 (T86)
├─ fetch_all_margin_trading() → 全市場融資融券 (MI_MARGN)
├─ fetch_all_valuation() → 全市場估值 (BWIBBU_ALL)
├─ fetch_monthly_revenue() → 月營收 (t187ap05_P)
└─ fetch_stock_history() → 個股歷史資料

NewsCollector (Google News RSS)
└─ fetch_news() → News 表

RateLimiter (自訂)
├─ 限制 FinMind API 呼叫頻率
└─ 避免超額請求
```

**相關檔案**:
- `app/services/finmind_collector.py` (150+ 行)
- `app/services/news_collector.py`
- `app/services/rate_limiter.py`
- `app/routers/data.py`

### LLM 分析模組

```
流程:
ScoreResult 表 (所有評分股票) → NewsPreparator → Gemini API → LLMReport 表

NewsPreparator（新架構：按需新聞）
├─ 建構子注入 NewsCollector
├─ 檢查 News 表是否有該股票新聞
├─ 若無 → 呼叫 NewsCollector.fetch_news(stock_id, days=14)
├─ 格式化文本
└─ 準備提示詞

GeminiClient（改進版）
├─ 調用 Google Generative AI (Gemini 2.5 Flash)
├─ max_tokens: 8192（支援更長報告）
├─ 截斷檢測：finish_reason='length' 時自動重試
├─ 欄位長度限制（每欄 150 字元，最多 3 個風險提示）
├─ 處理回應
├─ 錯誤重試
└─ 速率限制: 0.5 秒/次

NewsCollector（修正版）
├─ URL 編碼：urllib.parse.quote 處理特殊字元
├─ HTML 標籤過濾：清理 RSS 摘要
└─ Google News RSS 搜尋

PromptTemplates
├─ 新聞摘要範本
├─ 投資建議範本
└─ 情緒分析範本
```

**相關檔案**:
- `app/services/llm_analyzer.py`
- `app/services/gemini_client.py`
- `app/services/news_preparator.py`
- `app/services/prompt_templates.py`

### 前端狀態管理

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
- `src/stores/auth-store.ts`
- `src/stores/screening-store.ts`
- `src/stores/stock-store.ts`

### API 客戶端

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
- `src/api/client.ts`
- `src/api/*-api.ts` (8 個端點模組)

## 資料庫模型關係

```
Stock (股票主檔)
├── DailyPrice (一對多)
├── Institutional (一對多)
├── MarginTrading (一對多)
├── Revenue (一對多)
├── Financial (一對多)
├── News (一對多)
└── ScoreResult (一對多)

ScoreResult (篩選結果)
├── ChipScore (一對多)
├── FundamentalScore (一對多)
└── TechnicalScore (一對多)

User (使用者)
└── (未建立關係，用於認證)

LLMReport (AI 報告)
└── 參考 Stock (不直接外鍵)

PipelineLog (流程日誌)
└── (獨立表，記錄執行狀態)
```

## 關鍵設定

### 環境變數 (.env)

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

### 依賴清單

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

## 編碼約定

### 命名規則

**Python**
- 檔案: `snake_case` (e.g., `auth_service.py`)
- 類別: `PascalCase` (e.g., `AuthService`)
- 函數: `snake_case` (e.g., `get_current_user`)
- 常數: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)

**TypeScript/Vue**
- 檔案: `kebab-case` (e.g., `auth-store.ts`, `login-view.vue`)
- 類別: `PascalCase` (e.g., `AuthStore`)
- 函數: `camelCase` (e.g., `getCurrentUser`)
- 常數: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)

### 代碼樣式

**Python**
- 縮排: 4 空格
- 最大行長: 88 (Ruff 預設)
- 型別提示: 必須

**TypeScript**
- 縮排: 2 空格
- 最大行長: 100
- 嚴格模式: 啟用
- 分號: 必須

## 性能指標

| 指標 | 目標 | 達成 |
|------|------|------|
| API 端點響應 | < 2秒 | ✅ |
| 篩選執行時間 | < 10秒 | ✅ |
| 數據庫查詢 | < 500ms | ✅ |
| 前端首屏載入 | < 3秒 | ✅ |
| 測試覆蓋率 | > 80% | ✅ 100% (核心服務) |

## 測試覆蓋

```
總計: 160+ 個測試, 100% 通過率

認證服務        ✅ 156 行代碼，100% 覆蓋
模型           ✅ 496 行代碼，93-100% 覆蓋
配置           ✅ 299 行代碼，100% 覆蓋
股票服務        ✅ 386 行代碼，97% 覆蓋
硬篩選         ✅ 315 行代碼，100% 覆蓋
速率限制        ✅ 237 行代碼，100% 覆蓋
分析步驟        ✅ 115 行代碼，100% 覆蓋
FinMind 收集器  ✅ 22 個測試，100% 覆蓋（新增）

持續擴展:
評分服務整合測試 (計畫)
API 路由器測試 (計畫)
前端元件測試 (計畫)
```

## 快速導航

### 新增功能

1. **添加新 API 端點**
   - 建立 `app/schemas/*.py` (Pydantic 驗證)
   - 建立 `app/routers/new_feature.py` (路由)
   - 更新 `app/main.py` (掛載路由)
   - 新增對應服務 (app/services/)
   - 新增測試

2. **添加新評分因子**
   - 擴展 `app/services/scoring_engine.py`
   - 新增對應評分器 (e.g., `sentiment_scorer.py`)
   - 更新模型與資料庫
   - 修改權重邏輯

3. **添加前端頁面**
   - 建立 `src/views/new-view.vue`
   - 建立 `src/stores/new-store.ts`
   - 建立 `src/api/new-api.ts`
   - 更新路由器
   - 製作相關元件

## 部署檢查清單

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

## 近期更新摘要

### 2026-02-18: 已下市股票過濾 + FinMind 收集器測試

**FinMind 收集器改進**
- `fetch_stock_list()` 新增已下市股票過濾：基於 `date` 欄位，排除 30 天以上未更新的股票
- 減少資料庫中的無效股票資料，提升後續評分效率

**新增測試**
- `test_finmind_collector.py`: 22 個測試涵蓋 `_get` 方法、`fetch_stock_list` 過濾邏輯、各 fetch 方法
- 測試涵蓋：API 成功/失敗、429 限速重試、逾時重試、已下市過濾、邊界日期、可選欄位

### 2026-02-17: 股票搜尋 + 按需資料抓取

**新功能：Header 股票搜尋**
- `header-stock-search.vue`: debounced autocomplete 搜尋欄，支援鍵盤導航
- 整合至 `app-header.vue`，過濾 6+ 位代碼（排除權證）

**新功能：按需資料抓取**
- `on_demand_data_fetcher.py`: 查看非 Pipeline 股票時自動從 FinMind 抓取缺失資料
- 支援 prices / institutional / margin / revenue / financial

**Bug 修正**
- stocks/reports router: 無資料回傳空值（非 404）
- stock-detail-view: watch + immediate 修正路由切換不刷新
- **競態條件修正**（`stock-detail-view.vue`）
  - 問題：非 Pipeline 股票（搜尋欄查詢）僅顯示 1 天價格資料
  - 修復：`getStockScore()` 與 `fetchPrices()` 從並行改為循序執行
  - 結果：確保按需資料抓取完成後再查詢價格，取得完整 6 個月歷史資料

### 2026-02-17: Pipeline 簡化與新聞架構優化 + UI 體驗優化

**Pipeline 架構變更（5步驟 → 3步驟）**
- Step 1: 資料抓取（價格、法人、融資、營收、財報）
- Step 2: 硬篩選（量能異常 > 2.5x 或 Top 50）
- Step 3: 綜合評分 + LLM 分析
- 新聞不再是獨立步驟，改為 LLM 分析時按需抓取

**新聞架構重構**
- 舊：`daily_pipeline.py` → `step_fetch_news()` → 批次抓「台股」通用新聞 → News 表
- 新：LLM 分析時 → NewsPreparator 檢查 DB → 缺失時呼叫 NewsCollector.fetch_news()
- NewsPreparator 依賴注入 NewsCollector（建構子注入）
- 新聞回溯期：7 天 → 14 天

**LLM 客戶端改進**
- max_tokens: 4096 → 8192（支援更長報告）
- 新增截斷檢測：finish_reason='length' 時自動重試
- 欄位長度限制（每欄 150 字元，最多 3 個風險提示）

**NewsCollector 修正**
- URL 編碼：urllib.parse.quote 處理特殊字元
- HTML 標籤過濾：清理 RSS 摘要

**前端優化**
- 表格「名稱」欄位可排序（dashboard-view, stock-ranking-table, screening-result-table）
- Sidebar：個股詳情頁 (/stock/*) 顯示 dashboard 為 active

**新增元件**
- `scroll-to-top.vue`: 全域回到頂部按鈕（App.vue 層級整合）

**表格分頁排序功能**
- `screening-result-table.vue`: 多欄位排序 + 分頁（每頁 10 筆）
- `historical-result-table.vue`: 多欄位排序 + 分頁（每頁 10 筆）
- `settings-view.vue` 執行紀錄表: 排序 + 分頁 + 水平捲動

**UI 優化**
- Dashboard: 統計卡片 + 分頁切換（Top 30，每頁 10 筆）
- Reports: 卡片式佈局 + 項目符號推薦清單
- Stock Detail: 介面強化
- App Header/Sidebar: 功能增強
- 圖表 tooltip 改進（籌碼趨勢圖、融資融券圖）
- 回測績效圖 grid 位置調整

**環境變數**
- 前端支援 `VITE_API_BASE_URL` 環境變數設定 API 端點

### 2026-02-16: 後端功能增強

- `test_analysis_steps.py`: 7 個測試涵蓋管道分析步驟
- 評分服務支援 `as_of_date` 歷史日期評分
- TWSE 假期自動化（動態 API + 快取）
- Pipeline 非交易日略過、Backtest 支援特定股票篩選
- LLM 分析擴展至所有評分股票
- `bcrypt` 4.1.1 → 4.2.0, 新增 `requests`

**最後更新**: 2026-02-18
**版本**: 1.6

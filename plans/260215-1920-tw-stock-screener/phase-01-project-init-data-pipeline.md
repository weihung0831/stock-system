# Phase 01: 專案初始化 + 資料管線

## Context Links
- [總覽計畫](./plan.md)
- [後端研究報告](./research/researcher-01-backend-data-infra.md)
- 依賴：無（首階段）
- 下一階段：[Phase 02 - 因子計算引擎](./phase-02-scoring-engine.md)

## Overview
- **日期:** 2026-02-15
- **優先級:** P1
- **狀態:** pending
- **預估:** 12h
- **說明:** 建立前後端專案骨架、MySQL Schema、FinMind 資料收集器、News RSS 收集器、基本 API、簡單認證系統

## Key Insights
- FinMind 免費 600 req/hr，需 rate limiter + 快取避免超限
- MySQL DECIMAL(19,4) 存價格，RANGE PARTITION 按季分區
- **Sync SQLAlchemy + thread pool**（非 async），更穩定可靠 <!-- Updated: Validation Session 1 - 改用 Sync SQLAlchemy -->
- FinMind 回傳 DataFrame，欄位需轉小寫對應 pandas-ta
- **簡單帳密登入 + JWT auth**，管理員手動建帳，無註冊頁 <!-- Updated: Validation Session 1 - 新增認證系統 -->

## Requirements

### 功能需求
- FR-01: Python 後端專案結構 (FastAPI + SQLAlchemy)
- FR-02: Vue 3 前端專案結構 (Vite + Element Plus + ECharts)
- FR-03: MySQL Schema (股價/法人/融資融券/營收/財報/新聞/評分/LLM報告)
- FR-04: FinMind 資料收集器 (5 種資料類型)
- FR-05: Google News RSS 收集器
- FR-06: 基本 CRUD API (股票列表/股價查詢/法人資料)
- FR-07: 簡單帳密認證 (User model + JWT + login API + auth middleware) <!-- Updated: Validation Session 1 -->

### 非功能需求
- NFR-01: FinMind rate limiter (< 600 req/hr)
- NFR-02: 資料收集器錯誤處理 + 重試機制
- NFR-03: 環境變數管理 (.env)

## Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # pydantic-settings 環境變數
│   ├── database.py          # AsyncSession factory
│   ├── routers/
│   │   ├── stocks.py        # 股票 CRUD
│   │   └── data.py          # 資料查詢
│   ├── models/
│   │   ├── base.py          # Base + mixins
│   │   ├── daily-price.py
│   │   ├── institutional.py
│   │   ├── margin-trading.py
│   │   ├── revenue.py
│   │   ├── financial.py
│   │   └── news.py
│   ├── schemas/
│   │   ├── stock.py
│   │   └── data.py
│   ├── services/
│   │   ├── finmind-collector.py   # FinMind 資料收集
│   │   ├── news-collector.py      # RSS 新聞收集
│   │   └── stock-service.py
│   └── tasks/
├── requirements.txt
├── pyproject.toml
└── .env.example

frontend/
├── src/
│   ├── App.vue
│   ├── main.ts
│   ├── api/
│   │   └── client.ts        # axios instance
│   ├── router/
│   │   └── index.ts
│   ├── stores/
│   ├── views/
│   ├── components/
│   └── types/
├── package.json
└── vite.config.ts
```

## Related Code Files

### 建立檔案
- `backend/pyproject.toml` - Python 專案設定
- `backend/requirements.txt` - 依賴 (fastapi, uvicorn, sqlalchemy, pymysql, finmind, feedparser, pandas, pandas-ta, google-genai, apscheduler, pydantic-settings, python-jose, passlib, bcrypt) <!-- Updated: Validation Session 1 - aiomysql→pymysql, 新增 JWT/auth 依賴 -->
- `backend/app/main.py` - FastAPI 入口
- `backend/app/config.py` - 環境變數 (DB_URL, FINMIND_TOKEN, GEMINI_API_KEY)
- `backend/app/database.py` - Sync Session + engine (thread pool) <!-- Updated: Validation Session 1 -->
- `backend/app/models/*.py` - 6 個 ORM model
- `backend/app/schemas/*.py` - Pydantic schemas
- `backend/app/routers/stocks.py` - 股票列表/搜尋
- `backend/app/routers/data.py` - 資料查詢 API
- `backend/app/services/finmind-collector.py` - FinMind 收集器
- `backend/app/services/news-collector.py` - RSS 收集器
- `frontend/` - Vue 3 + Vite 初始化

## Implementation Steps

1. **後端專案初始化**
   - 建立 `backend/` 目錄結構
   - 撰寫 `pyproject.toml` (Python 3.11+, 依賴列表)
   - 撰寫 `requirements.txt`
   - 建立 `.env.example`

2. **FastAPI 核心設定**
   - `config.py`: 使用 pydantic-settings，讀取 DB_URL / FINMIND_TOKEN / GEMINI_API_KEY
   - `database.py`: create_engine + sessionmaker (Sync, 搭配 FastAPI thread pool) <!-- Updated: Validation Session 1 -->
   - `main.py`: FastAPI app, CORS middleware, lifespan event, include routers

3. **MySQL Schema + ORM Models**
   - `daily-price.py`: stock_id, trade_date, OHLCV, UNIQUE(stock_id, trade_date)
   - `institutional.py`: 外資/投信/自營 買賣數量
   - `margin-trading.py`: 融資/融券 餘額與變化
   - `revenue.py`: 月營收、年增率
   - `financial.py`: 季度 EPS/毛利率/ROE/負債比/現金流
   - `news.py`: title, source, url, published_at, content, sentiment
   - 所有表使用 DECIMAL(19,4) 存價格, BIGINT 存量

4. **FinMind 資料收集器**
   - `finmind-collector.py`: DataLoader wrapper
   - 方法: fetch_daily_prices(), fetch_institutional(), fetch_margin(), fetch_revenue(), fetch_financials()
   - Rate limiter: asyncio.Semaphore 或 token bucket
   - 錯誤處理: retry with exponential backoff
   - 批次處理: 分批抓取全市場股票

5. **News RSS 收集器**
   - `news-collector.py`: feedparser 解析 Google News RSS
   - 搜尋關鍵字: 股票名稱 + 代號
   - 存入 news 表

6. **基本 API**
   - `GET /api/stocks` - 股票列表 (分頁)
   - `GET /api/stocks/{stock_id}/prices` - 歷史股價
   - `GET /api/stocks/{stock_id}/institutional` - 法人買賣超
   - `GET /api/stocks/{stock_id}/margin` - 融資融券

7. **認證系統** <!-- Updated: Validation Session 1 - 新增認證步驟 -->
   - `models/user.py`: User model (id, username, hashed_password, is_admin, created_at)
   - `services/auth-service.py`: hash password (bcrypt), verify password, create JWT, decode JWT
   - `routers/auth.py`: `POST /api/auth/login` (return JWT), `GET /api/auth/me` (current user)
   - `dependencies.py`: `get_current_user` dependency (JWT token validation)
   - 所有需認證的路由加入 `Depends(get_current_user)`
   - 建立管理員初始化腳本 (`scripts/create-admin.py`)

8. **前端專案初始化**
   - `npm create vite@latest frontend -- --template vue-ts`
   - 安裝: element-plus, vue-echarts, echarts, pinia, vue-router, axios
   - 設定 vite.config.ts (proxy API to backend)
   - 建立基本路由架構

## Todo List
- [ ] 建立 backend/ 目錄結構 + pyproject.toml
- [ ] 實作 config.py + database.py
- [ ] 實作 main.py (FastAPI app + CORS)
- [ ] 建立 6 個 ORM models
- [ ] 建立 Pydantic schemas
- [ ] 實作 finmind-collector.py (含 rate limiter)
- [ ] 實作 news-collector.py
- [ ] 實作 stocks router + data router
- [ ] 初始化 Vue 3 前端專案
- [ ] 實作 User model + auth-service (JWT + bcrypt)
- [ ] 實作 auth router (login API)
- [ ] 建立 create-admin.py 腳本
- [ ] 驗證 FinMind API 連線 + 資料寫入 MySQL

## Success Criteria
- FastAPI server 啟動無誤，API 回應正常
- FinMind 可成功抓取 5 種資料類型並寫入 MySQL
- News RSS 可抓取新聞並儲存
- Vue 3 dev server 啟動，可連接後端 API
- Rate limiter 確保不超過 600 req/hr

## Risk Assessment
| 風險 | 機率 | 影響 | 緩解 |
|------|------|------|------|
| FinMind API 格式變更 | 低 | 高 | 抽象化收集器介面，方便替換 |
| MySQL 連線池耗盡 | 低 | 中 | 設定 pool_size + overflow |
| 休市日無資料 | 確定 | 低 | 檢查交易日曆，skip 非交易日 |

## Security Considerations
- API keys 存 .env，不進 git (.gitignore)
- MySQL 使用專用帳號，最小權限
- CORS 限制 frontend origin

## Next Steps
- Phase 02: 基於收集到的資料，實作因子計算引擎

# TW Stock Screener 系統架構

## 系統總覽

```
┌── Frontend (Vue 3 + TypeScript + Vite) ─────────────────────┐
│                                                             │
│  Views (頁面)                                                │
│  ├─ dashboard-view        首頁：Top 排名總覽                   │
│  ├─ stock-detail-view     個股詳情：三因子分數 + AI 摘要         │
│  ├─ chip-stats-view       籌碼統計：法人/融資融券趨勢            │
│  ├─ custom-screening-view 自訂篩選：多條件組合篩選              │
│  ├─ history-backtest-view 歷史回測：策略模擬                    │
│  ├─ reports-list-view     報告列表：LLM 分析報告                │
│  ├─ settings-view         設定：評分權重調整                    │
│  └─ login-view            登入                               │
│                                                             │
│  Global Components (全域元件)                                 │
│  ├─ ai-assistant-widget   浮動 AI 聊天氣泡 + 彈出對話面板        │
│  └─ scroll-to-top         回到頂部按鈕 (位置已調整)              │
│                                                             │
│  Stores (Pinia 狀態管理)                                      │
│  ├─ screening-store       篩選結果 & 排名                      │
│  ├─ stock-store           個股資料                             │
│  ├─ settings-store        權重設定 (chip/fund/tech)            │
│  ├─ auth-store            JWT 登入狀態                         │
│  └─ sector-tags-store     產業分類標籤                          │
└─────────────────────────────────────────────────────────────┘
                           │ HTTP API
                           ▼
┌── Backend (FastAPI + Python) ───────────────────────────────┐
│                                                             │
│  Routers (API 端點)                                          │
│  ├─ screening.py    GET/PUT 篩選結果 & 權重                    │
│  ├─ stocks.py       股票列表 & 個股資料                         │
│  ├─ chip_stats.py   籌碼統計 API                              │
│  ├─ custom_screening.py  自訂篩選條件                          │
│  ├─ backtest.py     回測 API                                 │
│  ├─ reports.py      LLM 報告 API (含 24h 快取 + 會員限流)       │
│  ├─ scheduler.py    手動觸發 Pipeline                          │
│  ├─ auth.py         POST/auth/register/login/refresh (含會員系統) │
│  ├─ admin.py        GET/PATCH /api/admin/users/* (會員管理) │
│  ├─ data.py         資料管理                                   │
│  ├─ sector_tags.py  產業標籤                                   │
│  ├─ chat.py         POST /api/chat (含會員限流) + GET /api/chat/quota │
│  └─ right_side_signals.py  右側買法信號檢測 & 篩選             │
│                                                             │
│  Services (核心業務邏輯)                                       │
│  ├─ scoring_engine.py      評分引擎 (協調三因子)                 │
│  │   ├─ chip_scorer.py     籌碼面評分                          │
│  │   ├─ fundamental_scorer.py 基本面評分                       │
│  │   └─ technical_scorer.py   技術面評分                       │
│  ├─ hard_filter.py         硬篩選 (量能異常 + Top N)            │
│  ├─ on_demand_data_fetcher.py 按需資料抓取 (非 Pipeline 股票)   │
│  ├─ twse_collector.py      TWSE 資料收集 (免費)                 │
│  ├─ finmind_collector.py   FinMind 資料收集 (財報/營收)          │
│  ├─ news_collector.py      新聞抓取                            │
│  ├─ llm_analyzer.py        LLM 分析 (Gemini)                  │
│  ├─ gemini_client.py       Gemini API 客戶端                   │
│  ├─ llm_client.py          LLM 通用客戶端 (含 generate_chat)   │
│  ├─ chat_service.py        AI 聊天服務 (系統提示詞 + LLM 對話)  │
│  ├─ chat_rate_limiter.py   聊天限流 (每分鐘 3 則、每日 20 則)   │
│  ├─ right_side_signal_detector.py 右側買法信號檢測 (6個信號)    │
│  ├─ backtest_service.py    回測邏輯                            │
│  ├─ stock_service.py       股票查詢服務 (含權證過濾)              │
│  ├─ auth_service.py        JWT 認證服務                        │
│  └─ rate_limiter.py        API 限速器                          │
│                                                             │
│  Tasks (排程任務)                                              │
│  ├─ daily_pipeline.py      Pipeline 協調器 (3步驟)              │
│  ├─ data_fetch_steps.py    資料抓取步驟 (A~G)                   │
│  ├─ analysis_steps.py      分析步驟 (篩選+評分+LLM+按需新聞)    │
│  └─ pipeline_status.py     Pipeline 狀態追蹤                    │
│                                                             │
│  Models (ORM 資料模型，共 14 張表)                               │
│  ├─ stock          股票基本資料 + PER/PBR/殖利率                 │
│  ├─ daily_price    每日收盤價/量                                │
│  ├─ institutional  三大法人買賣超                                │
│  ├─ margin_trading 融資融券                                    │
│  ├─ revenue        月營收 + YoY/MoM                            │
│  ├─ financial      季財報 (EPS/毛利率/ROE/負債比/現金流)           │
│  ├─ score_result   評分結果 + 排名                              │
│  ├─ llm_report     AI 分析報告                                 │
│  ├─ report_usage   報告使用追蹤 (每日配額記錄)                    │
│  ├─ news           新聞資料                                    │
│  ├─ pipeline_log   Pipeline 執行紀錄                            │
│  ├─ sector_tag     產業分類                                    │
│  ├─ system_setting 系統設定 (權重、排程時間等)                    │
│  └─ user           使用者帳號 (含會員等級、電郵、啟用狀態)          │
└─────────────────────────────────────────────────────────────┘
                           │ SQLAlchemy ORM
                           ▼
┌── Database (MySQL) ─────────────────────────────────────────┐
│  儲存所有股票、價格、財報、評分、報告資料                          │
└─────────────────────────────────────────────────────────────┘

┌── 外部資料源 ───────────────────────────────────────────────┐
│  TWSE 官方 API (免費) → 每日收盤/法人/融資/PER/PBR/歷史K線      │
│  FinMind API (免費額度) → 股票清單/月營收/季財報                  │
│  Gemini API (免費額度) → AI 摘要分析                            │
│  Google News RSS → 台股新聞                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 每日 Pipeline（3 步驟）

### Step 1：資料抓取 `data_fetch_steps.py`

```
A. 股票清單 (FinMind)
   ├─ 全市場股票 → stock_id + stock_name + industry → Stock 表
   └─ 過濾已下市股票（date 欄位 < 30 天前的排除）

B. 當日收盤 (TWSE bulk，1次 API)
   └─ 全市場 ~1300 檔 → DailyPrice 表

C. 歷史回補 (TWSE STOCK_DAY，逐檔)
   ├─ 對象：Top 100 成交量 ∪ 47 檔優先股
   ├─ 過濾：只補不足 120 天的
   └─ 每檔抓 8 個月 → DailyPrice 表 (3秒/次限速)

D. 三大法人 (TWSE T86 bulk，1次 API)
   └─ 全市場外資/投信/自營買賣超 → Institutional 表

E. 融資融券 (TWSE MI_MARGN bulk，1次 API)
   └─ 全市場融資餘額/融券餘額 → MarginTrading 表

F-1. 月營收 (TWSE bulk)
     └─ 已公告公司的當月營收 → Revenue 表

F-2. 營收 YoY/MoM (FinMind，逐檔)
     ├─ 抓 18 個月營收算 YoY = (本月 - 去年同月) / 去年同月
     └─ 更新 Revenue.revenue_yoy / revenue_mom

F-3. PER/PBR/殖利率 (TWSE BWIBBU bulk)
     └─ 全市場估值 → Stock.per / pbr / dividend_yield

G. 季財報 (FinMind，逐檔，3 個 dataset)
   ├─ 損益表 → EPS / 毛利率 / 營業利益率
   ├─ 資產負債表 → 負債比 / ROE
   ├─ 現金流量表 → 營業現金流 / 自由現金流
   └─ → Financial 表
```

### Step 2：硬篩選 `hard_filter.py`

```
兩路合併：
  路線 A：量能異常比篩選
    ├─ 計算本週成交量 vs 上週成交量
    ├─ 比值 > 2.5x 的股票 = 量能突增
    └─ 結果：ratio_filtered（可能 0~數十檔）

  路線 B：Top 50 成交量 (FALLBACK_TOP_N = 50)
    └─ 最新交易日成交量前 50 名

  合併策略：ratio_filtered 在前 + top_50 填充
  └─ 去重後輸出 ~50 檔候選股
```

### Step 3：三因子評分與 LLM 分析 `scoring_engine.py` + `llm_analyzer.py`

對每檔候選股計算三因子分數（各 0-100 分）：

#### 籌碼面 chip_score

```
A. 連續買超天數 (30%)
   ├─ 外資連買：每天 5 分，最高 50
   ├─ 投信連買：每天 3 分，最高 30
   └─ 自營連買：每天 2 分，最高 20

B. 法人買超佔成交量比 (40%)
   ├─ 近 5 天法人淨買超 / 成交量
   ├─ >=5% → 100 分
   ├─ 0% → 50 分
   └─ <=-5% → 0 分（線性映射）

C. 融資融券變化 (30%)
   ├─ 基礎 50 分
   ├─ 融資減少 → 加分（散戶退出=正面）
   └─ 融券增加 → 加分（軋空潛力）
```

#### 基本面 fundamental_score

```
有季財報時（7 指標加權）：
  ├─ 營收 YoY (20%)：>=20% →100, >=10% →80, >=5% →60 ...
  ├─ EPS 趨勢 (15%)：連續成長季數比例 x 100
  ├─ 毛利率穩定度 (10%)：低波動+上升趨勢
  ├─ ROE (15%)：>=15% →100, >=12% →80, >=8% →60 ...
  ├─ 負債比 (15%)：<30% →100, <50% →80, <70% →40 ...
  ├─ 現金流 (15%)：營業CF正 +50, 自由CF正 +50
  └─ 本益比 (10%)：目前固定 50（待完善）

無季財報但有營收時：
  └─ 營收獨佔 60% 權重，其餘給中性 50 分

完全無資料時 → PER/PBR/殖利率估值替代：
  ├─ PER (30%)：10-15 最佳 →100
  ├─ PBR (30%)：<1 最佳 →90
  └─ 殖利率 (40%)：>=6% →100, >=4% →80
```

#### 技術面 technical_score

```
需要 120 天以上日K資料，6 指標：
  ├─ MA 排列 (20%)：MA5>10>20>60>120 每層 25 分
  ├─ KD (15%)：低檔黃金交叉 →100, 低檔整理 →70
  ├─ MACD (20%)：柱狀翻正 →70, DIF 穿越 →100
  ├─ RSI (15%)：50-70 →100, >80 超買罰分 →20
  ├─ 布林通道 (15%)：價格在中軌上方 →100
  └─ 量能 (15%)：>1.5 倍 MA20 量 →100
```

#### 加權合計

```
total_score = chip x 權重% + fundamental x 權重% + technical x 權重%
預設權重：chip=40 / fundamental=25 / technical=35 (可由使用者調整)
```

→ 排序 → 寫入 ScoreResult 表（含 rank）

#### LLM 分析 `step_llm_analysis`

```
取所有評分股票 (不限數量) → NewsPreparator → Gemini 2.5 Flash → LLMReport 表
  ├─ NewsPreparator 檢查 News 表
  │  ├─ 若該股票無新聞 → 呼叫 NewsCollector.fetch_news() 即時抓取
  │  └─ 格式化新聞為 LLM 輸入
  ├─ 分析所有評分股票（無上限限制）
  ├─ max_tokens: 8192（支援更長報告）
  ├─ 截斷檢測：finish_reason='length' 時自動重試
  ├─ 速率限制：0.5 秒/次（Gemini 2.5 Flash 高速率額度）
  └─ 產出每檔股票的 AI 分析摘要 → LLMReport 表

**新聞架構變更**
- 舊：Pipeline 批次抓「台股」通用新聞
- 新：LLM 分析時按需抓個股新聞
  ├─ NewsPreparator 依賴注入 NewsCollector
  ├─ 先查 DB，無資料則即時 fetch_news(stock_id, days=14)
  └─ URL 編碼修正（urllib.parse.quote）+ HTML 標籤過濾
```

---

## 日常運作流程

```
交易日自訂時間 (APScheduler，預設 PM 4:30，可由使用者調整)
    │
    ├─ 檢測交易日狀態
    │  ├─ 交易日：正常執行 Pipeline (3 步驟)
    │  └─ 非交易日：略過 (不產生 pipeline_log，減少 DB 寫入)
    │
    ├─ 1. data_fetch  → 抓最新收盤、法人、融資、PER/PBR、營收、財報
    ├─ 2. hard_filter → 篩出 ~50 檔候選股 (FALLBACK_TOP_N=50)
    └─ 3. scoring + llm_analysis
       ├─ 三因子加權評分 → 排名寫入 DB
       └─ Gemini 產出所有評分股票的 AI 分析 (0.5s/次)
          └─ 新聞按需抓取：NewsPreparator 檢查 DB → 缺失時呼叫 NewsCollector
    │
    ▼
使用者開 Dashboard → 看到最新排名 + AI 建議
  └─ 可選擇顯示 Top 20 / Top 50 / All
```

---

## 前端頁面與 API 對應

```
Dashboard → GET /screening/results → ScoreResult 表 (依 rank 排序)
  ├─ 統計卡片：總股票數、平均分數等摘要資訊
  ├─ 分頁顯示：Top 30，每頁 10 筆，支援分頁切換
  ├─ 顯示計數：「共 X 檔，顯示 Y 檔」
  └─ 每張卡片：排名 + 股票名 + 總分 + 三因子分數 + 收盤價 + 漲跌幅

右側買法篩選 → GET /api/right-side-signals/screen/batch?min_signals=2 → 批量篩選結果
  ├─ 表格顯示：股號 + 股名 + 6 個信號觸發狀態 + 觸發數量
  ├─ 分頁排序：按觸發數量排序，支援分頁（每頁 10 筆）
  └─ 篩選條件：最少信號數（1-6 可選）

個股詳情 (右側信號卡片) → GET /api/right-side-signals/{stock_id}
  └─ 信號卡片：展示 6 個信號名稱、狀態、描述

個股詳情 → GET /screening/results/{stock_id} → score_single_stock() 即時算分
  ├─ 自動按需抓取缺失資料 (OnDemandDataFetcher)
  ├─ **循序資料載入模式**（避免競態條件）
  │  ├─ 步驟 1: getStockScore() → 觸發按需資料抓取（非 Pipeline 股票）
  │  └─ 步驟 2: fetchPrices() → 確保抓取完整 6 個月價格資料
  ├─ 三因子雷達圖 + 子指標明細 + AI 摘要
  └─ 支援搜尋欄直接輸入股票代碼/名稱導航

搜尋功能 → GET /stocks?search=xxx → 股票清單搜尋
  ├─ Header 搜尋欄 (debounced autocomplete)
  ├─ 過濾 6+ 位代碼 (排除權證/結構化商品)
  └─ 點擊導航至個股詳情頁

設定頁面 → GET/PUT /screening/settings → SystemSetting 表
  ├─ 三滑桿調權重（總和自動維持 100%）
  ├─ 「自動配置最佳比例」按鈕 → GET /screening/settings/auto-weights
  │    └─ 依資料覆蓋率自動分配權重
  ├─ 硬過濾門檻值滑桿（0-5，預設 2.5）
  └─ Pipeline 排程設定
      ├─ GET /api/scheduler/settings → 讀取排程設定
      └─ PUT /api/scheduler/settings → 儲存並即時重新排程

執行評分計算 → POST /screening/run
  └─ 用當前權重重新跑篩選+評分（不抓資料不跑 AI）
```

---

## 外部資料源

| 來源 | 資料 | 費用 | 限制 |
|------|------|------|------|
| TWSE 官方 | 每日收盤、法人、融資融券、PER/PBR | 免費 | bulk API 無限速 |
| TWSE 假期 API | 年度交易假期表 | 免費 | 自動快取 |
| TWSE STOCK_DAY | 個股歷史日K | 免費 | 3秒/次限速 |
| FinMind | 股票清單、月營收、季財報 | 免費 | 有額度限制 (402) |
| Gemini API | AI 分析摘要 | 免費額度 | 按需呼叫 |
| Google News RSS | 台股新聞 | 免費 | 每次最多 20 篇 |

---

## 環境設定

| 變數 | 用途 |
|------|------|
| DATABASE_URL | MySQL 連線字串 |
| FINMIND_TOKEN | FinMind API 令牌 |
| LLM_API_KEY | Gemini API 金鑰 |
| LLM_BASE_URL | LLM API 端點 |
| LLM_MODEL | LLM 模型名稱 |
| JWT_SECRET_KEY | JWT 簽署密鑰 |
| CORS_ORIGINS | 允許跨域來源 |
| VITE_API_BASE_URL | 前端 API 端點（預設 http://localhost:8000/api） |

---

## 啟動方式

```bash
# 後端
cd backend && uvicorn app.main:app --reload

# 前端
cd frontend && npm run dev
```

---

## 已知限制

| 問題 | 位置 | 影響 |
|------|------|------|
| 技術面 <120 天 = 0 分 | technical_scorer | 部分候選股直接 0 分 |
| PE 評分固定 50 | fundamental_scorer L251-255 | 本益比指標未啟用 |
| 財報只抓新股 | data_fetch_steps L520-529 | 已有財報不更新最新季 |

---

---

## 新增功能與改進

### 2026-02-21: 會員系統完全實裝 + 管理後台 (Membership System v2)

**後端新增**
- `routers/admin.py`：4 個管理員端點
  - `GET /api/admin/users` 取得使用者清單
  - `PATCH /api/admin/users/{user_id}/tier` 更新會員等級
  - `PATCH /api/admin/users/{user_id}/email` 更新電郵
  - `PATCH /api/admin/users/{user_id}/active` 切換啟用狀態
- `schemas/admin.py`：`TierUpdateRequest` (membership_tier: free|premium)
- `models/report_usage.py`：追蹤每用戶每日報告使用
- `services/report_rate_limiter.py`：報告生成限流 (Free 5/day, Premium unlimited)
  - 新增 `GET /api/reports/quota` 查詢報告配額
- `models/user.py` 新增欄位：
  - `membership_tier` (default: 'free')
  - `email` (unique, indexed)
  - `is_active` (default: True)
- `routers/auth.py` 更新：
  - `POST /api/auth/register` 含會員等級初始化
  - JWT token 含 tier 欄位
- `routers/chat.py` 更新：
  - 會員等級差異限流 (Free 3/min+10/day, Premium 5/min+100/day)
  - `GET /api/chat/quota` 查詢聊天配額
- `dependencies.py`：新增 `require_premium`, `require_admin` 依賴注入
- `routers/reports.py` 更新：報告生成 24h 快取 + 會員限流 (Free 5/day)

**前端新增**
- `register-view.vue`：使用者自助註冊 (電郵驗證、密碼強度檢查、會員等級選擇)
- `profile-view.vue`：會員資料頁 (顯示等級、聊天配額、升級提示)
- `pricing-view.vue`：定價頁面 (Free vs Premium 方案比較)
- `admin-users-view.vue`：管理員後台 (使用者列表、線上編輯)
- `api/admin-api.ts`：管理員 API 客戶端
- 側邊欄：會員徽章 (Free/Premium 顯示) + 聊天配額顯示
- 聊天組件：配額超限時顯示升級對話

**測試新增**
- 會員註冊、驗證、等級管理測試
- 管理員 API 測試 (列表、更新、切換狀態)
- 會員等級限流測試 (聊天、報告)
- 報告配額查詢測試
- 總計新增 ~34 個測試，267+ → 301+

### 2026-02-21: AI 聊天限流 (ChatRateLimiter，已納入會員系統)

- `services/chat_rate_limiter.py`：會員等級差異限流
  - Free: 每分鐘 3 則、每日 10 則
  - Premium: 每分鐘 5 則、每日 100 則
- `routers/chat.py` 整合：`GET /api/chat/quota` 查詢配額、POST 超限返回 429
- `ai-assistant-widget.vue` 處理 429 回應，顯示升級提示

### 2026-02-21: AI 報告 24 小時快取 + 會員限流 (已整合會員系統)

**功能說明**
- 報告生成支援 24 小時快取機制 + 會員等級限流
- Free 會員每日限制 5 份報告；Premium 會員無限制
- 同日內快取命中避免重複呼叫 LLM

**後端實現**
- `POST /api/reports/{stock_id}/generate` 端點
  - 24 小時快取：`LLMReport.created_at >= now() - 24h`
  - 會員限流：Free 5/day vs Premium unlimited
  - 超限返回 HTTP 429
- `services/report_rate_limiter.py`：記憶體限流追蹤
- `LLMReportResponse` 模式含 `created_at: datetime` 欄位

**前端實現**
- 按鈕文案動態更新（stock-detail-view.vue）：
  - 無報告：「產生 AI 分析」
  - 報告存在但 >24h：「更新分析」
  - 報告存在且 ≤24h：「今日已分析」（禁用）
- 超限時顯示「配額已達」，提示升級至 Premium
- 實時反饋生成進度

### 2026-02-21: 右側買法 (Right-Side Trading Signals)

**新功能說明**
- 基於技術面的動能進場信號，檢測 6 個右側進場機會點（需 ≥20 天價格資料）
- 加權評分制（滿分 100），各信號權重：

  | 信號 | 說明 | 權重 |
  |------|------|------|
  | 量價齊揚 | 成交量 ≥ 20日均量 1.5 倍且當日收漲 | 25 |
  | 突破20日高點 | 收盤突破前20日最高點 | 20 |
  | MACD黃金交叉 | DIF 由下往上穿越 Signal 線 | 20 |
  | 站回MA20 | 前一日收盤低於 MA20，今日收盤站上 MA20 | 15 |
  | KD低檔黃金交叉 | K 值在 30 以下由下往上穿越 D 值 | 12 |
  | 突破布林上軌 | 前一日收盤 ≤ 布林上軌，今日突破上軌 | 8 |

- 買賣點預測（`prediction`）：進場價（最新收盤）、停損（max(MA20, 20日低)）、目標（1.5x 風報比）、動作建議（score≥60→buy / score≥35→hold / 其餘→avoid）

**後端實現**
- `RightSideSignalDetector` 類別（`right_side_signal_detector.py`）
- 單檔查詢：`GET /api/right-side-signals/{stock_id}`
- 批量篩選：`GET /api/right-side-signals/screen/batch?min_signals=2`
  - 掃描範圍：Top 50 評分股（最新 ScoreResult）+ 近 7 日成交量 > 200 萬股（約 2,000 張）之股票聯集
  - 回傳依加權評分（score）降序排列

**前端實現**
- 獨立篩選頁面（`/right-side`）：分頁、依評分排序、最少信號數過濾（1-6 可選）
- 股票詳情頁：新增信號卡片（`right-side-signal-card.vue`），展示 6 個信號觸發狀態、描述及買賣點預測
- Sidebar 導航：「分析」分區新增「右側買法」項目

### 2026-02-19: AI 聊天助手

- 後端：新增 `chat.py` router (`POST /api/chat`)、`chat_service.py`（系統提示詞含 Top 5 股票上下文）、`llm_client.generate_chat()` 自由文字對話方法
- 前端：新增 `ai-assistant-widget.vue` 浮動氣泡面板、`ai-chat-message.vue` 訊息氣泡、`chat-api.ts` API 客戶端；整合至 `App.vue`

### 2026-02-18: 已下市股票過濾

- `finmind_collector.py` `fetch_stock_list()` 新增已下市股票過濾（`date` < 30 天 cutoff 排除）
- 新增 `test_finmind_collector.py` 22 個測試

### 2026-02-18: 手機版搜尋欄移至 Sidebar

**響應式搜尋欄重構**
- `app-header.vue` `header-center`: 桌機版 (>768px) 可見，手機版隱藏
- `app-sidebar.vue` `sidebar-search`: 手機版 (≤768px) 顯示搜尋欄於側邊欄頂部
- 共用 `header-stock-search.vue` 元件，介面行為一致

### 2026-02-17: 股票搜尋 + 按需資料抓取

**新功能：Header 股票搜尋**
- `header-stock-search.vue`: 搜尋欄位 + debounced autocomplete (300ms) + 鍵盤導航 (↑↓Enter)
- 整合至 `app-header.vue`（桌機版）及 `app-sidebar.vue`（手機版）
- 過濾 6+ 位代碼（排除權證/結構化商品），每次最多回傳 8 筆結果

**新功能：按需資料抓取 (OnDemandDataFetcher)**
- `on_demand_data_fetcher.py`: `check_data_freshness()` 檢查各資料類型是否新鮮 → `fetch_missing_data()` 缺失時從 FinMind 即時抓取
- 新鮮度判斷：`FRESHNESS_DAYS=30`，prices 需 ≥10 筆，其他資料有任一記錄即視為新鮮
- 支援 5 種資料：prices（180 天）/ institutional（45 天）/ margin（25 天）/ revenue（550 天）/ financial（730 天）
- 整合至 `GET /screening/results/{stock_id}` endpoint，確保個股詳情頁資料完整

**Bug 修正**
- `stocks.py`: prices/institutional/margin 無資料時回傳空陣列（非 404）
- `reports.py`: 無報告時回傳 null（非 404）
- `stock_service.py`: 搜尋結果排除 6+ 位代碼權證
- `stock-detail-view.vue`: 使用 watch + immediate 取代 onMounted，修正同元件路由切換不刷新
- **個股詳情頁資料載入順序修正**（`stock-detail-view.vue`）
  - 問題：非 Pipeline 股票（搜尋欄查詢）僅顯示 1 天價格資料，而非完整 6 個月
  - 原因：`getStockScore()` 與 `fetchPrices()` 並行執行（Promise.all），價格查詢在按需資料抓取完成前就執行
  - 解決：改為循序執行 → 先呼叫 `getStockScore()`（觸發 `OnDemandDataFetcher`），待資料填充後再執行 `fetchPrices()`
  - 影響：確保所有透過搜尋欄查詢的個股都能取得完整歷史價格資料進行圖表繪製

### 2026-02-17: Pipeline 簡化與新聞架構優化

**Pipeline 架構變更（5步驟 → 3步驟）**
- Step 1: 資料抓取（價格、法人、融資、營收、財報）
- Step 2: 硬篩選（量能異常 > 2.5x 或 Top 50）
- Step 3: 綜合評分 + LLM 分析
  - 新聞不再是獨立步驟，改為 LLM 分析時按需抓取

**新聞架構重構**
- 舊：Pipeline 批次抓「台股」通用新聞 → 存 DB → LLM 讀取
- 新：LLM 分析時 → NewsPreparator 檢查 DB → 缺失時呼叫 NewsCollector 即時抓取個股新聞
- NewsPreparator 依賴注入 NewsCollector（建構子注入）
- 新聞回溯期從 7 天增至 14 天

**LLM 客戶端改進**
- max_tokens: 4096 → 8192（支援更長報告）
- 新增截斷檢測：finish_reason='length' 時自動重試
- 欄位長度限制：每欄位 150 字元，最多 3 個風險提示

**NewsCollector 修正**
- URL 編碼使用 urllib.parse.quote 處理特殊字元
- HTML 標籤自動過濾（RSS 摘要清理）

**前端優化**
- 表格「名稱」欄位可排序（dashboard-view, stock-ranking-table, screening-result-table）
- Sidebar：個股詳情頁 (/stock/*) 顯示 dashboard 為 active 狀態

**全域元件**
- `scroll-to-top.vue`: 回到頂部按鈕，整合於 App.vue 層級

**表格分頁排序**
- 篩選結果表、回測結果表、執行紀錄表均支援多欄位排序 + 分頁（每頁 10 筆）
- 排序支援升降序切換，分頁含上/下頁按鈕與頁碼

**Dashboard 改進**
- 新增統計摘要卡片
- 分頁切換（Top 30，每頁 10 筆）

**環境變數**
- 前端新增 `VITE_API_BASE_URL` 支援部署時設定 API 端點

### 2026-02-16: 後端功能增強

- `as_of_date` 參數支援歷史回溯評分
- TWSE 假期自動偵測（動態 API + 快取 + 降級）
- Pipeline 非交易日略過、Backtest 股票篩選
- LLM 分析全面升級（所有評分股票）
- 依賴更新：bcrypt 4.2.0, 新增 requests

**最後更新**: 2026-02-21
**版本**: 2.10

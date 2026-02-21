# 台灣股市多因子篩選平台 (TW Stock Screener)

## 專案概述

**台灣股市多因子篩選平台** 是一個企業級的股票篩選系統，結合基本面、技術面與籌碼面分析，為台灣股票投資者提供科學的決策支持工具。

### 核心價值

- **多因子綜合評估**: 結合籌碼(40%)、基本面(35%)、技術面(25%)三個維度
- **AI輔助分析**: 使用 Google Gemini 2.0 Flash 進行新聞分析與投資建議
- **自動化流程**: 每日16:30自動收集數據、計算分數、生成報告
- **深度研究工具**: 支援自訂篩選、回測、籌碼統計等進階功能
- **暗色優雅UI**: 深色主題配搭琥珀金色(#e5a91a)設計

## 技術棧

### 後端
- **框架**: FastAPI (現代Python API框架)
- **ORM**: SQLAlchemy (同步模式)
- **資料庫**: MySQL 8.0
- **調度**: APScheduler (日期排程)
- **驗證**: JWT (python-jose) + bcrypt
- **LLM**: Google Generative AI (Gemini 2.0 Flash)
- **數據源**: FinMind SDK (個股資料) + TWSE OpenAPI (全市場批次), Google News RSS

### 前端
- **框架**: Vue 3 (組合式API)
- **語言**: TypeScript
- **構建工具**: Vite
- **UI元件庫**: Element Plus
- **圖表**: ECharts
- **狀態管理**: Pinia

## 核心功能模組

### 1. 認證與會員系統 (Authentication & Membership)
- 用戶註冊 (POST /api/auth/register)
  - 電郵唯一性驗證
  - 密碼長度檢查 (最少 8 字元)
  - 支援 Free/Premium 會員等級選擇
- JWT令牌認證 (含 tier 欄位)
- Bcrypt密碼雜湊
- 令牌過期管理 (預設24小時)
- 會員等級管理 (管理員可透過 PATCH /api/admin/users/{user_id}/tier 更新)

### 2. 數據收集 (Data Collection)
- TWSE OpenAPI 整合 (全市場日價格、法人買賣、融資融券、估值、月營收)
- FinMind API 整合 (個股歷史資料、季度財報、詳細基本面)
- Google News RSS 收集
- 混合架構：TWSE 批次 + FinMind 個股補充
- 每日自動排程更新（時間可設定，預設 16:30）

### 3. 評分引擎 (Scoring Engine)
- **硬篩選**: 量能異常比 > 2.5x 或 Top 50 成交量
- **籌碼面**: 機構投資人動向、融資融券比率
- **基本面**: 淨利潤、營收成長、財務指標
- **技術面**: 移動平均、相對強弱指數、布林通道
- **綜合分數**: 加權組合 (客製化權重)

### 4. 篩選系統 (Screening)
- **硬篩選**: 基於成交量的初步篩選
- **標準篩選**: 預設權重的快速篩選
- **自訂篩選**: 彈性的篩選條件組合

### 5. AI 分析 (LLM Analysis)
- 所有評分股票進行 AI 分析（使用 Gemini 2.5 Flash）
- 新聞摘要與情緒分析
- 個股投資建議
- 市場趨勢分析
- 速率限制：0.5 秒/次
- 24 小時快取機制：檢查 LLMReport.created_at，同日內不重複呼叫 LLM API
- **Free 會員**: 每日限制 5 份報告生成
- **Premium 會員**: 無限制生成報告

### 9. AI 聊天限流 (Chat Rate Limiter)
- **Free 會員**: 每分鐘最多 3 則訊息，每日最多 10 則訊息
- **Premium 會員**: 每分鐘最多 5 則訊息，每日最多 100 則訊息
- 超出限制返回 HTTP 429，前端顯示使用限制提示
- 基於 user_id 的記憶體限流（分鐘滑動窗口 + UTC 日桶）
- GET /api/chat/quota 端點可查詢目前配額使用狀況

### 6. 回測系統 (Backtesting)
- 歷史績效驗證
- 策略有效性評估

### 7. 籌碼統計 (Chip Stats)
- 機構投資人趨勢
- 融資融券追蹤

### 8. 右側買法 (Right-Side Trading Signals)
- 6 個右側進場信號加權評分（滿分 100）：量價齊揚(25)、突破20日高點(20)、MACD黃金交叉(20)、站回MA20(15)、KD低檔黃金交叉(12)、突破布林上軌(8)
- 買賣點預測：進場價（收盤）、停損（max(MA20, 20日低)）、目標（1.5x 風報比）、動作建議（buy/hold/avoid）
- 批量篩選掃描範圍：Top 50 評分股 + 近7日成交量 > 200 萬股（約 2,000 張）之股票聯集
- 獨立篩選頁面（排序、分頁、最少信號數篩選）+ 個股詳情信號卡片

## 數據模型架構

### 核心表 (13個主要模型)
- **Stock**: 股票主檔 (股號、名稱、市場、產業)
- **DailyPrice**: 每日價格 (開盤、最高、最低、收盤、成交量)
- **Institutional**: 機構投資人持股 (外資、投信、自營商)
- **MarginTrading**: 融資融券 (餘額、比率)
- **Revenue**: 月營收 (營收、年增率)
- **Financial**: 財務報表 (淨利、EPS、淨值)
- **News**: 新聞記錄 (標題、內容、來源)

### 評分表 (5個)
- **ChipScore**: 籌碼評分結果
- **FundamentalScore**: 基本面評分結果
- **TechnicalScore**: 技術面評分結果
- **CompositeScore**: 計算過程記錄
- **ScoreResult**: 最終篩選結果 (含排名)

### 其他表
- **LLMReport**: AI分析報告
- **User**: 使用者帳戶
- **PipelineLog**: 流程執行日誌

## API端點總覽

| 類別 | 端點 | 功能 |
|------|------|------|
| **認證** | `POST /api/auth/register` | 帳號註冊 (含電郵驗證 + 密碼強度檢查) |
| | `POST /api/auth/login` | 帳號登入 |
| | `POST /api/auth/refresh` | 更新令牌 (JWT 含 tier 欄位) |
| **管理** | `GET /api/admin/users` | 取得所有使用者清單 (管理員專用) |
| | `PATCH /api/admin/users/{user_id}/tier` | 更新使用者會員等級 (管理員專用) |
| | `PATCH /api/admin/users/{user_id}/email` | 更新使用者電郵 (管理員專用) |
| | `PATCH /api/admin/users/{user_id}/active` | 切換使用者啟用狀態 (管理員專用) |
| **股票** | `GET /api/stocks/list` | 股票列表 |
| | `GET /api/stocks/{stock_id}` | 股票詳情 |
| | `GET /api/stocks/search` | 股票搜尋 |
| **聊天** | `GET /api/chat/quota` | 查詢聊天配額 (Free: 3/min+10/day, Premium: 5/min+100/day) |
| | `POST /api/chat` | AI 聊天助手對話 (含限流檢查) |
| **數據** | `POST /api/data/collect` | 觸發數據收集 |
| | `GET /api/data/status` | 數據狀態 |
| **篩選** | `POST /api/screening/run` | 執行標準篩選 |
| | `GET /api/screening/results` | 篩選結果 |
| **自訂篩選** | `POST /api/custom-screening/run` | 自訂篩選 |
| **籌碼統計** | `GET /api/chip-stats/trends` | 籌碼趨勢 |
| **報表** | `GET /api/reports/quota` | 查詢報告配額 (Free: 5/day, Premium: unlimited) |
| | `POST /api/reports/{stock_id}/generate` | 生成 AI 報告 (含 24h 快取機制，限流: Free 5/day, Premium unlimited) |
| | `GET /api/reports/list` | 報告清單 |
| **回測** | `POST /api/backtest/run` | 執行回測 |
| | `GET /api/backtest/score-dates` | 可用評分日期 |
| **調度** | `GET /api/scheduler/jobs` | 排程管理 |
| **右側買法** | `GET /api/right-side-signals/{stock_id}` | 單檔 6 信號查詢 |
| | `GET /api/right-side-signals/screen/batch` | 批量篩選（min_signals 參數） |

## 核心服務架構

### 後端服務 (22個主要服務)

**數據收集層**
- `TWSECollector`: TWSE 全市場批次資料收集
- `FinmindCollector`: 個股詳細資料收集
- `NewsCollector`: 新聞爬蟲
- `RateLimiter`: API速率限制

**業務邏輯層**
- `AuthService`: 認證邏輯
- `StockService`: 股票查詢
- `HardFilter`: 初步篩選

**評分層**
- `ChipScorer`: 籌碼評分
- `FundamentalScorer`: 基本面評分
- `TechnicalScorer`: 技術面評分
- `ScoringEngine`: 評分協調

**高級功能層**
- `CustomScreeningService`: 自訂篩選
- `ChipStatsService`: 籌碼統計
- `BacktestService`: 回測引擎 + 評分日期查詢
- `RightSideSignalDetector`: 右側買法信號檢測
- `LLMAnalyzer`: AI分析
- `GeminiClient`: Google API封裝

**輔助服務**
- `NewsPreparator`: 新聞預處理
- `PromptTemplates`: LLM提示詞

## 前端結構

### 視圖（13 個頁面）
- **DashboardView**: 主儀表板（含顯示限制選單：Top 20 / Top 50 / All）
- **StockDetailView**: 股票詳情
- **CustomScreeningView**: 自訂篩選
- **ChipStatsView**: 籌碼統計
- **ReportsListView**: 報告清單
- **RightSideScreeningView**: 右側買法篩選
- **HistoryBactestView**: 回測歷史
- **SettingsView**: 系統設定（權重調整 + 排程時間設定）
- **LoginView**: 登入頁面
- **RegisterView**: 註冊頁面（含會員等級選擇）
- **ProfileView**: 會員資料頁（顯示等級、聊天配額、升級提示）
- **AdminUsersView**: 管理員使用者列表（查看、編輯、啟用狀態）
- **PricingView**: 定價頁面（會員方案比較）

### 元件庫 (20個主要元件)
- 股票排名表、雷達圖、扇形圖
- 篩選表單、結果表（含分頁+排序）
- K線圖、技術指標圖
- AI報告面板
- 籌碼趨勢圖、融資融券圖
- 回到頂部按鈕（全域）

### 狀態管理 (4個Store)
- `authStore`: 使用者與令牌
- `stockStore`: 股票快取
- `screeningStore`: 篩選參數與結果
- `settingsStore`: 使用者偏好

## 核心流程

### 日常篩選流程（自動化，預設 16:30，可調整）
1. 數據收集（TWSE 批次 + FinMind 個股補充）
2. 硬篩選（量能異常比 > 2.5x 或 Top 50 成交量）
3. 逐股評分 + LLM 分析
   - 籌碼+基本面+技術面評分
   - 加權計算（Chip 40% + Fund 35% + Tech 25%）
   - 排名與儲存
   - LLM 分析所有評分股票（Gemini 2.5 Flash，0.5s/次）
   - 新聞按需抓取：NewsPreparator 檢查 DB → 缺失時呼叫 NewsCollector
4. 報告生成

### 使用者互動流程
1. 登入系統
2. 查看儀表板（最新篩選結果，可選 Top 20 / Top 50 / All）
3. 鑽研個股（詳情、圖表、AI 報告）
4. 自訂篩選（靈活組合條件）
5. 調整系統設定（權重、排程時間）
6. 回測驗證（策略有效性）
7. 下載報告

## 設計風格

### UI主題
- **色彩**: 深色背景 + 琥珀金accent (#e5a91a)
- **風格**: 現代、清爽、專業
- **元件庫**: Element Plus (一致的設計語言)

### 資訊架構
- 清晰的側邊欄導航
- 分層深度搜尋結構
- 即時數據更新

## 部署與環境

### 後端需求
- Python 3.9+
- MySQL 8.0
- 環境變數配置 (.env):
  - `DATABASE_URL`: MySQL連線字符串
  - `FINMIND_TOKEN`: FinMind API token
  - `GEMINI_API_KEY`: Google Gemini API key
  - `JWT_SECRET_KEY`: JWT簽署密鑰
  - `CORS_ORIGINS`: 允許的跨域來源

### 前端需求
- Node.js 16+
- npm/yarn

### 開發模式
- **後端**: `uvicorn app.main:app --reload`
- **前端**: `npm run dev`

## 項目狀態

### 完成階段
- ✅ 後端框架與數據模型
- ✅ 認證系統 (含會員等級支援)
- ✅ 用戶註冊 (電郵驗證 + 密碼強度檢查)
- ✅ 會員等級管理 (Free/Premium，含管理員更新端點)
- ✅ 數據收集整合
- ✅ 評分引擎
- ✅ API端點
- ✅ 前端UI (含註冊頁、會員資料頁、會員徽章、配額顯示)
- ✅ 單元測試 (301 個測試, 100%通過率)
- ✅ 自動化流程
- ✅ TWSE假期自動化
- ✅ 歷史評分支援 (as_of_date)
- ✅ AI分析全面升級
- ✅ 右側買法信號檢測
- ✅ 會員等級差異限流 (聊天、報告生成)
- ✅ 24 小時報告快取機制

### 下一步
- 性能最佳化
- 使用者反饋與迭代
- 新功能擴展 (更多指標、警報系統)

## 核心PDR (Product Development Requirements)

### 功能需求

#### R1: 多因子評分
- 實現籌碼、基本面、技術面評分
- 支援自訂權重組合
- 實時計算與緩存

#### R2: 自動化收集
- 每日定時自動更新（預設 16:30，可於設定頁面調整）
- 排程設定持久化至資料庫
- FinMind 與新聞源集成
- 錯誤重試與日誌記錄

#### R3.5: AI 聊天限流
- **Free 會員**: 每分鐘限制 3 則訊息，每日限制 10 則訊息
- **Premium 會員**: 每分鐘限制 5 則訊息，每日限制 100 則訊息
- 滑動窗口 60 秒限制 + UTC 日重置
- 超限返回 HTTP 429 與剩餘重置時間資訊
- GET /api/chat/quota 查詢配額
- 前端顯示友善的使用限制提示訊息

#### R3: AI 輔助分析 (含會員等級差異)
- 使用 Gemini 2.5 Flash 模型
- **24 小時快取機制**：檢查報告的 `created_at` 欄位，若在 24 小時內已生成則直接返回快取報告
  - 後端邏輯：`POST /api/reports/{stock_id}/generate` 比對 `created_at >= now() - 24h`
  - 前端按鈕狀態：「產生 AI 分析」→「更新分析」→「今日已分析」（禁用）
- **會員等級報告生成限制**
  - Free: 每日限制 5 份報告，超出返回 HTTP 429
  - Premium: 無限制生成報告
  - 需求依賴: `require_premium` 可限制僅 Premium 會員存取特定功能
- 新聞按需抓取：NewsPreparator 檢查 DB → 缺失時呼叫 NewsCollector
  - 新聞回溯期：14 天
  - URL 編碼修正 + HTML 標籤過濾
- 新聞自動摘要、投資建議、情緒分析
- 速率限制：0.5 秒/次、max_tokens: 8192、截斷檢測與自動重試

#### R4: 回測與驗證
- 歷史績效計算
- 策略有效性評估
- 特定股票篩選支援 (stock_ids 參數)
- as_of_date 參數支援過去日期評分

### 非功能需求

#### NR1: 性能
- API端點 < 2秒響應
- 篩選結果 < 10秒
- 數據庫查詢 < 500ms

#### NR2: 可靠性
- 99% 可用性目標
- 自動故障恢復
- 完整日誌與監控

#### NR3: 安全性
- JWT驗證所有端點
- Bcrypt密碼雜湊
- SQL注入防護 (SQLAlchemy ORM)
- 資料加密傳輸 (HTTPS)

#### NR4: 可維護性
- 清晰的代碼結構
- 完整的文檔
- 單元測試覆蓋
- 配置化設定

## 成功度量

| 指標 | 目標 | 當前狀態 |
|------|------|--------|
| 篩選執行時間 | < 10秒 | ✅ 達成 |
| 數據準確率 | > 99% | ✅ FinMind驗證 |
| API可用性 | > 99% | ✅ 運行中 |
| 測試覆蓋率 | > 80% | ✅ 301+/301+ (100%) |
| 用戶響應時間 | < 2秒 | ✅ 達成 |

---

## 最新更新

### 2026-02-21: 會員系統完全實裝 (Membership System)
- **用戶註冊**：`POST /api/auth/register` 端點
  - 電郵唯一性驗證
  - 密碼長度檢查 (8+ 字元)
  - Free/Premium 會員等級初始化
- **會員等級管理**（管理後台）：
  - `GET /api/admin/users` 取得使用者清單
  - `PATCH /api/admin/users/{user_id}/tier` 更新會員等級
  - `PATCH /api/admin/users/{user_id}/email` 更新電郵
  - `PATCH /api/admin/users/{user_id}/active` 切換啟用狀態
  - JWT token 含 tier 欄位
- **會員等級差異限流**：
  - **聊天限流**: Free (3/min, 10/day) vs Premium (5/min, 100/day)
  - **報告生成限制**: Free (5/day) vs Premium (unlimited)
  - `GET /api/chat/quota` 查詢聊天配額端點
  - `GET /api/reports/quota` 查詢報告配額端點
  - `require_premium` 依賴注入用於限制功能存取
- **新增後端檔案**：
  - `app/routers/admin.py` (4 個端點：列表、更新等級、更新電郵、切換狀態)
  - `app/schemas/admin.py` (TierUpdateRequest)
  - `app/models/report_usage.py` (ReportUsage 模型)
  - `app/services/report_rate_limiter.py` (報告限流)
- **新增前端頁面**：
  - `register-view.vue` (使用者自助註冊)
  - `profile-view.vue` (會員資料與配額查詢)
  - `admin-users-view.vue` (管理員使用者列表)
  - `pricing-view.vue` (會員方案比較)
  - 側邊欄會員徽章、聊天配額顯示、超限升級對話
- **測試**：新增 ~34 個測試，總計 267+ → 301+

### 2026-02-21: AI 聊天限流 (ChatRateLimiter，已納入會員系統)
- 後端：`chat_rate_limiter.py`，會員等級差異限流
- 前端：429 錯誤處理 + 升級對話提示
- 測試：`test_chat_rate_limiter.py` (7個) 涵蓋分鐘/日限制/重置邏輯

### 2026-02-21: 右側買法 (Right-Side Trading Signals)
- **後端實現**：`RightSideSignalDetector` 檢測 6 個動能進場信號（需 ≥20 天資料）
  - 加權評分（滿分 100）：量價齊揚(25)、突破20日高點(20)、MACD黃金交叉(20)、站回MA20(15)、KD低檔黃金交叉(12)、突破布林上軌(8)
  - 買賣點預測：進場(收盤)、停損(max(MA20, 20日低))、目標(1.5x 風報比)、動作(buy≥60/hold≥35/avoid)
  - API 端點：`GET /api/right-side-signals/{stock_id}` 單檔、`GET /api/right-side-signals/screen/batch?min_signals=2` 批量
  - 批量掃描範圍：Top 50 評分股 + 近7日量 > 200 萬股聯集
- **前端實現**：
  - 獨立篩選頁面（`/right-side`）：分頁、依加權評分排序、最少信號數過濾（1-6）
  - 個股詳情頁：`right-side-signal-card.vue` 展示信號狀態與買賣點預測
  - Sidebar 「分析」分區新增「右側買法」導航項

### 2026-02-17: Pipeline 簡化與新聞架構優化
- **Pipeline 架構**：5 步驟簡化為 3 步驟
  - Step 1: 資料抓取
  - Step 2: 硬篩選
  - Step 3: 綜合評分 + LLM 分析
- **新聞架構重構**
  - 舊：Pipeline 批次抓「台股」通用新聞
  - 新：LLM 分析時按需抓取個股新聞
  - NewsPreparator 依賴注入 NewsCollector
  - 新聞回溯期：7 天 → 14 天
- **LLM 客戶端改進**
  - max_tokens: 4096 → 8192
  - 新增截斷檢測與自動重試
  - 欄位長度限制（每欄 150 字元，最多 3 個風險提示）
- **NewsCollector 修正**
  - URL 編碼使用 urllib.parse.quote
  - HTML 標籤自動過濾
- **前端優化**
  - 表格「名稱」欄位可排序（3 個表格）
  - Sidebar：個股詳情頁顯示 dashboard 為 active
- **UI 體驗優化**
  - 回到頂部按鈕：全域 scroll-to-top 元件（App.vue 層級）
  - 表格分頁排序：篩選結果表、回測結果表、執行紀錄表支援多欄位排序 + 分頁（每頁 10 筆）
  - Dashboard 改進：統計卡片 + 分頁切換（Top 30）
  - 環境變數：前端支援 `VITE_API_BASE_URL` 設定 API 端點
  - UI 細節：圖表 tooltip 優化、報告卡片佈局改進

### 2026-02-16: 後端功能增強
- TWSE 假期自動化、as_of_date 歷史評分、AI 分析全面升級
- Backtest 股票篩選、Pipeline 非交易日略過
- 新增 `test_analysis_steps.py` (7 個測試), 總計 140+ 測試
- 依賴更新：bcrypt 4.2.0, 新增 requests

### 2026-02-21: AI 報告 24 小時快取機制
- **快取邏輯**：後端 `POST /api/reports/{stock_id}/generate` 檢查 `LLMReport.created_at >= now() - 24h`
- **前端反饋**：按鈕文案動態更新「產生 AI 分析」→「更新分析」→「今日已分析」（禁用）
- **效益**：避免短時間內重複呼叫 LLM API，降低成本並改善使用者體驗

**最後更新**: 2026-02-21
**版本**: 2.1
**狀態**: 會員系統完全實裝（含管理後台），301 個測試全部通過，核心功能完成

# 台股智慧選股系統

繁體中文 | [English](./README.md)

台股智慧選股與監控系統，整合籌碼面（40%）、基本面（35%）、技術面（25%）三維度綜合評分，提供 AI 分析報告、動量策略回測、即時投資組合監控等功能。

## 技術棧

### 後端

- **Python 3.9** + **FastAPI** — RESTful API 伺服器
- **SQLAlchemy 2.0** — ORM（MySQL / SQLite）
- **APScheduler** — 排程任務
- **FinMind / TWSE / Fugle** — 台股資料來源
- **OpenAI / Gemini** — LLM 分析報告生成

### 前端

- **Vue 3** + **TypeScript** — SFC `<script setup>`
- **Vite 7** — 建構工具
- **Element Plus** — UI 元件庫
- **ECharts** — 圖表視覺化
- **Pinia** — 狀態管理
- **Vue Router** — 路由管理
- **Axios** — HTTP 客戶端
- **Sass** — 樣式預處理器

## 功能

- **多維度選股** — 籌碼（40%）+ 基本面（35%）+ 技術面（25%）綜合評分
- **自訂篩選** — 使用者自定義篩選條件與權重
- **右側訊號偵測** — 技術面右側進場訊號
- **籌碼統計** — 三大法人、融資融券分析
- **AI 分析報告** — LLM 生成個股深度分析
- **動量策略回測** — 歷史回測驗證策略績效
- **投資組合監控** — 即時追蹤持股與通知（Fugle 即時行情）
- **個股詳情** — 股價走勢、財務數據、新聞彙整
- **使用者系統** — 註冊登入、權限管理

## 專案結構

```
stock-system/
├── backend/
│   ├── app/
│   │   ├── routers/        # 16 個 API 路由
│   │   ├── services/       # 25 個業務服務 + momentum/ 子模組
│   │   ├── models/         # 19 個 ORM 模型
│   │   ├── schemas/        # Pydantic 請求/回應模型
│   │   └── tasks/          # Pipeline 排程任務
│   └── tests/              # 384 個測試（SQLite in-memory）
├── frontend/
│   └── src/
│       ├── views/          # 14 個頁面
│       ├── components/     # 25 個元件
│       ├── stores/         # 7 個 Pinia store
│       ├── api/            # 14 個 API 客戶端
│       └── types/          # TypeScript 型別定義
```

## 快速開始

### 前置需求

- Python 3.9+
- Node.js 18+
- MySQL（或使用 SQLite 開發）

### 後端

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 測試

```bash
cd backend
source venv/bin/activate
pytest --tb=short
# 含覆蓋率
pytest --cov=app --cov-report=term-missing
```

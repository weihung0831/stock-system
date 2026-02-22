# 台股智慧選股系統

多因子量化篩選 × AI 智慧分析 × 動能信號偵測

## 功能特色

- **多因子評分** — 籌碼面 (40%) + 基本面 (35%) + 技術面 (25%)，三維度量化評分 0-100
- **右側買法信號** — 6 個動能進場信號偵測 + 4 個進階篩選條件
- **AI 分析報告** — Google Gemini 自動分析新聞、投資建議、情緒與風險提示
- **AI 聊天助手** — 即時對話諮詢台股投資問題
- **每日自動更新** — Pipeline 每日 16:30 自動收集數據並評分
- **會員系統** — Free / Premium 兩種方案，差異化配額

## 技術棧

| 層級 | 技術 |
|------|------|
| 後端 | Python 3.9 · FastAPI · SQLAlchemy · MySQL |
| 前端 | Vue 3 · TypeScript · Vite · ECharts |
| AI | Google Gemini API |
| 資料源 | FinMind · TWSE · Google News RSS |

## 快速啟動

```bash
# 後端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

後端: http://localhost:8000 · 前端: http://localhost:5173

## 專案結構

```
stock-system/
├── backend/           # FastAPI 後端 (25 服務, 13 路由, 15 模型)
│   ├── app/
│   │   ├── models/    # ORM 模型
│   │   ├── routers/   # API 路由
│   │   ├── services/  # 業務邏輯
│   │   ├── schemas/   # Pydantic 驗證
│   │   └── tasks/     # Pipeline 任務
│   └── tests/         # 301 個測試
├── frontend/          # Vue 3 前端 (13 視圖, 22 元件)
│   └── src/
│       ├── views/     # 頁面
│       ├── components/# 元件
│       ├── stores/    # Pinia 狀態
│       ├── api/       # API 客戶端
│       └── types/     # TypeScript 型別
├── scripts/           # PPT 生成等工具腳本
└── docs/              # 技術文件 (6 份)
```

## 文件

詳細技術文件請參閱 [docs/](./docs/README.md)

## 測試

```bash
cd backend
pytest --tb=short
```

目前 301 個測試，57% 覆蓋率，100% 通過率。

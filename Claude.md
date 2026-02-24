# 台股智慧選股系統

所有回答必須使用繁體中文回答

## Commands

```bash
# 後端
cd backend && uvicorn app.main:app --reload --port 8000
# 前端
cd frontend && npm run dev
# 測試（後端）
cd backend && pytest --tb=short
# 測試（含覆蓋率）
cd backend && pytest --cov=app --cov-report=term-missing
```

## Architecture

- `backend/app/routers/` — 13 個 API 路由
- `backend/app/services/` — 24 個業務服務
- `backend/app/models/` — 15 個 ORM 模型
- `backend/app/tasks/` — Pipeline 任務
- `frontend/src/views/` — 13 個頁面
- `frontend/src/components/` — 22 個元件
- `frontend/src/stores/` — 5 個 Pinia store
- `frontend/src/api/` — 12 個 API 客戶端

## Code Style

- 後端: Python 3.9, snake_case, type hints
- 前端: Vue 3 + TypeScript, kebab-case 檔名
- 單一檔案不超過 200 行，超過須拆分
- 評分權重: 籌碼 40% + 基本面 35% + 技術面 25%

## Testing

- 297 個測試, 57% 覆蓋率
- 測試檔案在 `backend/tests/`
- 使用 SQLite in-memory 測試資料庫
- 不可用 mock 繞過測試，必須修正實際問題

## Gotchas

- `FALLBACK_TOP_N=500`（候選池上限）在 `hard_filter.py`
- Pydantic v2 class Config 已棄用，用 `model_config = ConfigDict(...)`
- `.env` 檔案不可提交至 git
- 前端 `components.d.ts` 為自動生成，勿手動編輯

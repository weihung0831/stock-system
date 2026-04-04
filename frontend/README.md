# Taiwan Stock Smart Screening System

[繁體中文](./README.zh-TW.md) | English

A smart stock screening and monitoring system for the Taiwan stock market. Integrates chip analysis (40%), fundamentals (35%), and technicals (25%) into a composite scoring model, with AI-powered reports, momentum strategy backtesting, and real-time portfolio monitoring.

## Tech Stack

### Backend

- **Python 3.9** + **FastAPI** — RESTful API server
- **SQLAlchemy 2.0** — ORM (MySQL / SQLite)
- **APScheduler** — Scheduled tasks
- **FinMind / TWSE / Fugle** — Taiwan stock data sources
- **OpenAI / Gemini** — LLM report generation

### Frontend

- **Vue 3** + **TypeScript** — SFC `<script setup>`
- **Vite 7** — Build tool
- **Element Plus** — UI component library
- **ECharts** — Data visualization
- **Pinia** — State management
- **Vue Router** — Routing
- **Axios** — HTTP client
- **Sass** — CSS preprocessor

## Features

- **Multi-dimensional Screening** — Chip (40%) + Fundamentals (35%) + Technicals (25%) composite scoring
- **Custom Screening** — User-defined filters and weights
- **Right-side Signal Detection** — Technical entry signals
- **Chip Statistics** — Institutional investors & margin trading analysis
- **AI Analysis Reports** — LLM-generated in-depth stock analysis
- **Momentum Strategy Backtesting** — Historical backtest for strategy validation
- **Portfolio Monitor** — Real-time holdings tracking with notifications (Fugle live quotes)
- **Stock Detail** — Price charts, financials, and news aggregation
- **User System** — Registration, login, and role-based access

## Project Structure

```
stock-system/
├── backend/
│   ├── app/
│   │   ├── routers/        # 16 API routes
│   │   ├── services/       # 25 business services + momentum/ submodule
│   │   ├── models/         # 19 ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   └── tasks/          # Pipeline scheduled tasks
│   └── tests/              # 384 tests (SQLite in-memory)
├── frontend/
│   └── src/
│       ├── views/          # 14 pages
│       ├── components/     # 25 components
│       ├── stores/         # 7 Pinia stores
│       ├── api/            # 14 API clients
│       └── types/          # TypeScript type definitions
```

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- MySQL (or SQLite for development)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Testing

```bash
cd backend
source venv/bin/activate
pytest --tb=short
# With coverage
pytest --cov=app --cov-report=term-missing
```

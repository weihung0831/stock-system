# Backend Data Infrastructure Research Report

**Date:** 2026-02-15
**Researcher:** researcher-01
**Topics:** FinMind SDK, FastAPI Structure, MySQL Time-Series Schema

---

## Topic 1: FinMind SDK (Python)

### API Usage & Rate Limits
- **Free tier:** 300 requests/hour (anonymous)
- **Registered tier:** 600 requests/hour (需註冊並驗證 email，取得 token)
- **數據更新頻率:** 每日自動更新
- **數據範圍:** 50+ 台股相關數據集，自 2019-05-29 起超過 3000 萬筆資料

### 安裝與引入
```python
pip install finmind
from FinMind.data import DataLoader
```

### 主要資料獲取方法
| 資料類型 | 方法/API | 說明 |
|---------|---------|------|
| 日股價 | `taiwan_stock_daily()` | OHLC + 成交量 |
| 三大法人 | `add_kline_institutional_investors()` | 外資、投信、自營商買賣 |
| 融資融券 | `add_kline_margin_purchase_short_sale()` | 融資、融券數據 |
| 月營收 | Fundamental API | 每月營收報表 |
| 季財報 | Fundamental API | 綜合損益表、現金流量表、資產負債表 |

### 資料格式
- **回傳:** JSON (透過 REST API) 或 DataFrame (透過 DataLoader)
- **欄位:** 依資料類型而異，通常包含 date, stock_id, 數值欄位

### Gotchas
- Rate limit 容易達到 (600/hr 不算高，需要快取機制)
- 需處理市場休市日、資料延遲或缺失
- API token 需在請求中加入參數

---

## Topic 2: FastAPI Project Structure

### 推薦目錄結構 (中型專案)
```
app/
├── main.py                 # 應用入口
├── config.py               # 配置管理
├── database.py             # DB session 工廠
├── dependencies.py         # 共用依賴注入
├── routers/                # 路由模組 (依功能分)
│   ├── stocks.py
│   ├── screening.py
│   └── data.py
├── models/                 # SQLAlchemy ORM models
│   ├── stock.py
│   └── financial_data.py
├── schemas/                # Pydantic schemas (request/response)
│   ├── stock.py
│   └── screening.py
├── services/               # 業務邏輯層
│   ├── stock_service.py
│   └── screening_service.py
└── tasks/                  # 排程任務
    └── data_sync.py
```

### Router 組織模式
- **依功能/領域分割:** 每個 router 負責單一業務領域 (如 stocks, screening)
- **使用 `APIRouter`:** 模組化路由，保持 main.py 簡潔
- **結構:** `routers/domain.py` → 路由處理 → `services/domain_service.py` → 業務邏輯 → `models/domain.py` → DB 操作

### SQLAlchemy 整合 (Async vs Sync)
- **Async 優先:** FastAPI 是 async-first，建議用 `asyncpg` + `AsyncSession`
- **SessionLocal:** 工廠模式建立 async session
- **依賴注入:**
  ```python
  async def get_db():
      async with AsyncSession() as session:
          yield session
  ```
- **注意:** async route 只能執行 non-blocking 操作，否則阻塞 event loop

### APScheduler 整合
- **用途:** Cron-like 排程任務 (如每日抓取 FinMind 資料)
- **整合方式:**
  - 在 `main.py` 的 `lifespan` event 啟動 scheduler
  - 任務定義在 `tasks/` 資料夾
  - 支援多種 trigger (interval, cron)
- **範例:**
  ```python
  from apscheduler.schedulers.asyncio import AsyncIOScheduler
  scheduler = AsyncIOScheduler()
  scheduler.add_job(sync_daily_data, 'cron', hour=18)
  scheduler.start()
  ```

---

## Topic 3: MySQL Schema Design for Financial Time-Series

### 表格設計最佳實踐
#### 日股價表 (daily_prices)
```sql
CREATE TABLE daily_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_id VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(19,4),
    high_price DECIMAL(19,4),
    low_price DECIMAL(19,4),
    close_price DECIMAL(19,4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock_date (stock_id, trade_date),
    UNIQUE KEY uk_stock_date (stock_id, trade_date)
) PARTITION BY RANGE COLUMNS(trade_date) (
    PARTITION p2024_q1 VALUES LESS THAN ('2024-04-01'),
    PARTITION p2024_q2 VALUES LESS THAN ('2024-07-01'),
    ...
);
```

#### 三大法人表 (institutional_investors)
```sql
CREATE TABLE institutional_investors (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_id VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    foreign_buy BIGINT,
    foreign_sell BIGINT,
    trust_buy BIGINT,
    trust_sell BIGINT,
    dealer_buy BIGINT,
    dealer_sell BIGINT,
    INDEX idx_stock_date (stock_id, trade_date)
) PARTITION BY RANGE COLUMNS(trade_date) (...);
```

### 資料型態選擇
- **金額/價格:** `DECIMAL(19,4)` (避免 FLOAT 精度損失)
- **股票代號:** `VARCHAR(10)`
- **日期:** `DATE` (時間序列主鍵之一)
- **成交量:** `BIGINT`

### 索引策略
- **複合索引:** `(stock_id, trade_date)` - 涵蓋最常見查詢模式
- **唯一約束:** `UNIQUE(stock_id, trade_date)` - 避免重複資料
- **單欄索引:** 視查詢需求調整 (如 `trade_date` 單獨索引用於全市場查詢)

### 分區 (Partitioning)
- **RANGE COLUMNS:** 依 `trade_date` 按季度分區
- **優點:** 查詢特定時間範圍時只掃描相關分區，提升效能
- **維護:** 需定期新增未來季度分區

### SQLAlchemy ORM 模式
```python
from sqlalchemy import Column, String, Date, DECIMAL, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DailyPrice(Base):
    __tablename__ = 'daily_prices'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    open_price = Column(DECIMAL(19, 4))
    close_price = Column(DECIMAL(19, 4))
    volume = Column(BigInteger)

    __table_args__ = (
        Index('idx_stock_date', 'stock_id', 'trade_date'),
        UniqueConstraint('stock_id', 'trade_date', name='uk_stock_date'),
    )
```

### 其他考量
- **替代方案:** TimescaleDB (PostgreSQL extension) 針對時間序列優化，但 MySQL 搭配適當設計已足夠
- **效能優化:** Summary tables (如週線、月線) 可預先計算減少即時運算

---

## 未解決問題
1. FinMind API 在台股盤中是否提供即時資料？還是僅收盤後更新？
2. FastAPI + APScheduler 是否需額外處理 graceful shutdown？
3. MySQL 分區表在 SQLAlchemy 中是否需特殊處理？還是透明運作？

---

## Sources
- [FinMind PyPI](https://pypi.org/project/finmind/)
- [FinMind Documentation](https://finmind.github.io/)
- [FinMind GitHub](https://github.com/FinMind/FinMind)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [FastAPI Project Structure Guide](https://medium.com/@amirm.lavasani/how-to-structure-your-fastapi-projects-0219a6600a8f)
- [FastAPI SQLAlchemy AsyncPG Example](https://github.com/grillazz/fastapi-sqlalchemy-asyncpg)
- [Designing Stock Price Database](https://medium.com/@herefindalex/designing-an-efficient-stock-price-database-from-basic-structure-to-optimization-strategies-44ba2c01fae9)
- [Securities Master Database with MySQL](https://www.quantstart.com/articles/Securities-Master-Database-with-MySQL-and-Python/)

# 籌碼與技術面分數為零問題診斷報告

**日期**: 2026-02-16
**問題**: Pipeline 執行後，所有股票的籌碼分數和技術分數都是 0

---

## 關鍵發現 (Key Findings)

### 1. Institutionals 資料表完全空白
```sql
SELECT COUNT(*) FROM institutionals;
-- 結果: 0 筆資料
```

**根本原因**: FinMind API Free Tier 限制
```
FinMind API error 400: "Your level is free. Please update your user level."
```

- FinMind 的 `TaiwanStockInstitutionalInvestorsBuySell` 批次 API 需要付費方案
- Step D (第 392 行) 使用 `finmind.fetch_all_institutional()` 回傳 `None`
- Fallback TWSE T86 邏輯存在但未正確執行

### 2. Daily Prices 歷史資料嚴重不足

```sql
SELECT trade_date, COUNT(DISTINCT stock_id) as stocks
FROM daily_prices
GROUP BY trade_date
ORDER BY trade_date DESC;
```

結果:
- **2026-02-11**: 1,345 檔股票 ✅
- **2026-02-10 及之前**: 僅 36 檔或更少 ❌

**影響**:
- TechnicalScorer 需要至少 30 天資料 (line 54)
- 大部分股票只有 1 天資料 → technical_score = 0.0

### 3. 實際分數狀況

```sql
SELECT stock_id, chip_score, technical_score, fundamental_score
FROM score_results
ORDER BY score_date DESC
LIMIT 5;
```

| stock_id | chip_score | technical_score | fundamental_score | total_score |
|----------|-----------|-----------------|-------------------|-------------|
| 2330     | 0.00      | 0.00            | 78.90             | 51.29       |
| 3189     | 0.00      | 0.00            | 77.09             | 50.11       |
| 2455     | 0.00      | 0.00            | 73.80             | 47.97       |

**只有基本面分數有值，籌碼和技術面全為 0**

---

## 程式碼分析 (Code Analysis)

### Step D: Institutional Data (Lines 383-448)

```python
inst_df = finmind.fetch_all_institutional(inst_start, date_str)
if inst_df is not None and not inst_df.empty:
    # 成功: 儲存資料
    ...
else:
    # Fallback: TWSE T86
    logger.warning("FinMind institutional empty, fallback to TWSE T86")
    inst_data = twse.fetch_institutional_all(inst_date)
```

**問題點**:
1. FinMind API 因 free tier 回傳 `None`
2. 進入 fallback，但 `inst_date` 使用當前日期
3. 如果當天是休市日，TWSE T86 回傳空陣列
4. 最終沒有任何資料被儲存

**驗證測試**:
```python
# TWSE T86 在交易日有效
twse.fetch_institutional_all('2026-02-11')  # → 13,776 筆資料 ✅
twse.fetch_institutional_all('2026-02-16')  # → 0 筆資料 (週日) ❌
```

### Step C: Historical Backfill (Lines 356-381)

```python
need_backfill = _stocks_needing_backfill(db, all_target_ids, 120)
if need_backfill:
    saved_hist = _fetch_twse_history_batch(twse, db, need_backfill)
```

**問題點**:
- 只針對「需要補足」的股票（< 120 天資料）
- 首次執行時，所有股票都是新的，應該全部補歷史資料
- 但只補了 36 檔（可能是 PRIORITY_STOCKS 的一部分）

---

## 資料庫驗證 (Database Verification)

### Institutionals Table
```bash
mysql> SELECT COUNT(*) FROM institutionals;
+----------+
| COUNT(*) |
+----------+
|        0 |
+----------+
```

### Margin Tradings Table
```bash
mysql> SELECT COUNT(*), MIN(trade_date), MAX(trade_date) FROM margin_tradings;
+----------+----------------+----------------+
| COUNT(*) | MIN(trade_date)| MAX(trade_date)|
+----------+----------------+----------------+
|     1251 | 2026-02-11     | 2026-02-11     |
+----------+----------------+----------------+
```
✅ Margin data 有資料但只有 1 天

### Pipeline Logs
```bash
mysql> SELECT * FROM pipeline_logs ORDER BY started_at DESC LIMIT 1;
+----+---------------------+---------------------+---------+-----------------+-------------+-------+--------------+
| id | started_at          | finished_at         | status  | steps_completed | total_steps | error | trigger_type |
+----+---------------------+---------------------+---------+-----------------+-------------+-------+--------------+
|  6 | 2026-02-16 18:24:47 | 2026-02-16 18:27:09 | success |               5 |           5 | NULL  | manual       |
+----+---------------------+---------------------+---------+-----------------+-------------+-------+--------------+
```
Pipeline 顯示成功但實際資料不完整

---

## 根本原因總結 (Root Causes)

### 原因 1: FinMind Free Tier 限制
- **問題**: Free tier 無法使用批次 API
- **影響**: Step D 無法取得機構投資人資料
- **severity**: 🔴 Critical

### 原因 2: Fallback 邏輯缺陷
- **問題**: TWSE fallback 使用當前日期，如遇休市日會失敗
- **影響**: 即使有 fallback，休市日也無法取得資料
- **severity**: 🟡 High

### 原因 3: 歷史資料回補不完整
- **問題**: Step C 只補部分股票的歷史資料
- **影響**: 多數股票只有 1 天資料，無法計算技術指標
- **severity**: 🟡 High

---

## 解決方案 (Solutions)

### 方案 A: 使用 FinMind Per-Stock API (推薦)
**策略**: Free tier 可使用單檔股票 API

```python
# 修改 Step D: 使用 per-stock API 代替批次 API
for stock_id in all_target_ids:
    inst_df = finmind.fetch_institutional(stock_id, inst_start, date_str)
    if inst_df is not None and not inst_df.empty:
        # 儲存資料
        ...
    time.sleep(0.2)  # Rate limiting
```

**優點**:
- 不需付費升級 FinMind
- 可取得完整 30 天歷史資料
- 已有現成的 `fetch_institutional()` 方法

**缺點**:
- 需要多次 API 呼叫（~100 檔 = 100 次）
- 執行時間較長（~20-30 秒 with rate limiting）

### 方案 B: 改善 TWSE Fallback 邏輯

```python
# 修改 data_fetch_steps.py line 387-390
from sqlalchemy import func as sqlfunc
max_trade_date = db.query(sqlfunc.max(DailyPrice.trade_date)).scalar()
inst_date = str(max_trade_date) if max_trade_date else date_str

# Fallback 時使用正確的交易日
inst_data = twse.fetch_institutional_all(inst_date)
```

**優點**:
- 完全免費，無 API 限制
- 一次取得所有股票

**缺點**:
- 只能取得單一交易日資料
- 無法回補歷史 30 天

### 方案 C: 混合策略（最佳解）

**執行順序**:
1. **Step D-1**: 嘗試 FinMind 批次 API
2. **Step D-2**: 失敗時，使用 TWSE T86 取得最新交易日（所有股票）
3. **Step D-3**: 針對 top 100 + priority stocks，用 FinMind per-stock API 補 30 天歷史

```python
# Step D-1: FinMind bulk (free tier will fail)
inst_df = finmind.fetch_all_institutional(inst_start, date_str)
if inst_df is not None and not inst_df.empty:
    # 付費用戶: 儲存批次資料
    saved_inst = _save_institutional_bulk(db, inst_df)
else:
    # Step D-2: TWSE T86 for latest day (all stocks)
    inst_data = twse.fetch_institutional_all(inst_date)
    saved_inst = len(inst_data)
    for item in inst_data:
        db.add(Institutional(**item))
    db.commit()

    # Step D-3: FinMind per-stock for top stocks (30 days history)
    target_stocks = _get_top_stocks_by_volume(db, limit=100)
    target_stocks = list(set(target_stocks) | set(PRIORITY_STOCKS))

    for stock_id in target_stocks:
        inst_df = finmind.fetch_institutional(stock_id, inst_start, date_str)
        if inst_df is not None and not inst_df.empty:
            for _, row in inst_df.iterrows():
                # 檢查是否已存在（避免重複）
                existing = db.query(Institutional).filter_by(
                    stock_id=stock_id, trade_date=row['date']
                ).first()
                if not existing:
                    db.add(Institutional(...))
        time.sleep(0.2)  # Rate limit
    db.commit()
```

### 方案 D: 改善歷史資料回補

```python
# 修改 Step C: 確保所有目標股票都有足夠歷史資料
need_backfill = _stocks_needing_backfill(db, all_target_ids, 120)

# 如果沒有任何歷史資料，使用較寬鬆的條件
if not need_backfill:
    need_backfill = _stocks_needing_backfill(db, all_target_ids, 30)

if need_backfill:
    logger.info(f"Backfilling {len(need_backfill)} stocks...")
    saved_hist = _fetch_twse_history_batch(twse, db, need_backfill)
```

---

## 建議實作順序 (Implementation Priority)

### 階段 1: 緊急修復（今天）
1. ✅ **修改 Step D** - 使用方案 C 混合策略
2. ✅ **修改 Step E** - 同樣使用 per-stock API 補 margin 資料

### 階段 2: 資料回補（明天）
3. ✅ **執行一次性歷史資料回補**
   - 針對 top 100 + priority stocks
   - 回補 120 天 daily prices
   - 回補 30 天 institutional 資料

### 階段 3: 驗證與測試
4. ✅ **重新執行 pipeline**
5. ✅ **驗證分數計算**
   ```sql
   SELECT stock_id, chip_score, technical_score
   FROM score_results
   WHERE chip_score > 0 AND technical_score > 0
   LIMIT 10;
   ```

---

## 預期結果 (Expected Outcome)

修復後應該看到:
```sql
SELECT stock_id, chip_score, technical_score, fundamental_score, total_score
FROM score_results
ORDER BY total_score DESC
LIMIT 5;
```

| stock_id | chip_score | technical_score | fundamental_score | total_score |
|----------|-----------|-----------------|-------------------|-------------|
| 2330     | 65.30     | 72.40           | 78.90             | 72.15       |
| 2454     | 58.20     | 68.50           | 73.80             | 67.24       |
| 2881     | 62.40     | 65.30           | 70.25             | 66.18       |

**全部三個維度都應該有合理的分數 (> 0)**

---

## 未解決問題 (Unresolved Questions)

1. **為什麼 Step C 只回補了 36 檔股票？**
   - 需要檢查 `_stocks_needing_backfill()` 邏輯
   - 可能是首次執行的特殊情況

2. **TWSE API 的 Rate Limiting 限制？**
   - 目前使用 3 秒延遲（line 349）
   - 是否需要調整？

3. **是否需要考慮升級 FinMind 付費方案？**
   - 付費方案: 批次 API，更快速
   - Free 方案: per-stock API，足夠使用但較慢

---

**報告完成時間**: 2026-02-16 20:26
**狀態**: 已識別根本原因，待實作修復

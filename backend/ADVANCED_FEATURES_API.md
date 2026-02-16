# 進階功能 API 端點

## 1. 自訂篩選 (Custom Screening)

### POST /api/custom-screening
執行自訂多條件篩選。

**需要驗證**: 是

**請求參數** (JSON Body):
```json
{
  "industry": "半導體",                      // 可選：產業篩選
  "min_total_score": 70.0,                   // 可選：最低總分 (0-100)
  "min_chip_score": 60.0,                    // 可選：最低籌碼分數 (0-100)
  "min_fundamental_score": 65.0,             // 可選：最低基本面分數 (0-100)
  "min_technical_score": 55.0,               // 可選：最低技術面分數 (0-100)
  "score_date": "2024-01-15"                 // 可選：目標日期 (預設：最新)
}
```

**回應**:
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "stock_id": "2330",
      "stock_name": "台積電",
      "industry": "半導體",
      "market": "TWSE",
      "score_date": "2024-01-15",
      "chip_score": 75.5,
      "fundamental_score": 80.2,
      "technical_score": 70.8,
      "total_score": 75.5,
      "rank": 1,
      "chip_weight": 0.4,
      "fundamental_weight": 0.35,
      "technical_weight": 0.25
    }
  ]
}
```

---

## 2. 籌碼統計 (Chip Stats)

### GET /api/chip-stats/institutional
取得法人買賣超趨勢（依日期彙總）。

**需要驗證**: 是

**查詢參數**:
- `days` (int, 預設=30): 回溯天數 (1-365)
- `end_date` (date, 可選): 結束日期 (預設：今天)

**回應**:
```json
{
  "success": true,
  "days": 30,
  "data": [
    {
      "trade_date": "2024-01-15",
      "foreign_net": 123456789,      // 外資淨買超
      "trust_net": 45678901,          // 投信淨買超
      "dealer_net": -12345678,        // 自營商淨買超
      "total_net": 156789012          // 總計淨買超
    }
  ]
}
```

### GET /api/chip-stats/margin
取得融資融券趨勢（依日期彙總）。

**需要驗證**: 是

**查詢參數**:
- `days` (int, 預設=30): 回溯天數 (1-365)
- `end_date` (date, 可選): 結束日期 (預設：今天)

**回應**:
```json
{
  "success": true,
  "days": 30,
  "data": [
    {
      "trade_date": "2024-01-15",
      "margin_balance": 987654321,    // 融資餘額
      "margin_change": 12345678,      // 融資增減
      "short_balance": 45678901,      // 融券餘額
      "short_change": -1234567        // 融券增減
    }
  ]
}
```

---

## 3. 回測分析 (Backtest)

### GET /api/backtest/history
取得歷史期間內每個評分日期的 Top N 股票。

**需要驗證**: 是

**查詢參數**:
- `start_date` (date, 必填): 開始日期
- `end_date` (date, 必填): 結束日期
- `top_n` (int, 預設=10): 每個日期的前 N 名股票 (1-50)

**回應**:
```json
{
  "success": true,
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "top_n": 10,
  "data": [
    {
      "score_date": "2024-01-15",
      "top_stocks": [
        {
          "stock_id": "2330",
          "stock_name": "台積電",
          "total_score": 85.5,
          "rank": 1
        }
      ]
    }
  ]
}
```

### GET /api/backtest/performance
計算指定評分日期的 Top N 股票未來表現。

**需要驗證**: 是

**查詢參數**:
- `score_date` (date, 必填): 要分析的評分日期
- `top_n` (int, 預設=10): 分析前 N 名股票 (1-50)
- `forward_days` (List[int], 預設=[5,10,20]): 未來回報期間（天數）

**回應**:
```json
{
  "success": true,
  "score_date": "2024-01-15",
  "stocks": [
    {
      "stock_id": "2330",
      "stock_name": "台積電",
      "total_score": 85.5,
      "rank": 1,
      "base_price": 580.0,
      "return_5d": 2.5,      // 5日報酬率 (%)
      "return_10d": 5.2,     // 10日報酬率 (%)
      "return_20d": 8.7      // 20日報酬率 (%)
    }
  ],
  "average_returns": {
    "return_5d": 2.1,
    "return_10d": 4.5,
    "return_20d": 7.3
  }
}
```

---

## 認證方式

所有端點都需要 JWT Bearer Token 認證：

```
Authorization: Bearer <your_jwt_token>
```

取得 Token 請使用 `/api/auth/login` 端點。

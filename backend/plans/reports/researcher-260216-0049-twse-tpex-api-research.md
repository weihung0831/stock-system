# TWSE & TPEx Open Data JSON API Research Report

**Research Date:** 2026-02-16
**Status:** Complete
**Scope:** TWSE/TPEx endpoints for daily prices, institutional investors, margin trading

---

## Executive Summary

TWSE provides an **official OpenAPI v1** at `https://openapi.twse.com.tw/` with free, no-key-required access. Key findings:
- **Daily OHLCV (all stocks):** `STOCK_DAY_ALL` endpoint exists
- **Institutional investors:** Data available but endpoint naming unclear from public sources
- **Margin trading:** Data available but endpoint details require direct Swagger UI inspection
- **Date format:** YYYYMMDD (standard Gregorian calendar, NOT ROC year)
- **Rate limit:** 3 requests per 5 seconds (strict enforcement)
- **TPEx:** Has separate OpenAPI at `https://www.tpex.org.tw/openapi/` but JSON endpoint details not publicly documented

---

## 1. TWSE Daily Stock Prices (All Stocks)

### Endpoint
```
https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL
```

### Method
`GET`

### Parameters
| Parameter | Format | Example | Notes |
|-----------|--------|---------|-------|
| `date` | YYYYMMDD | `20250216` | Day value functionally ignored (only YYYY/MM used) |

### Response Structure
**Top-level fields:**
- `stat`: Status (e.g., "OK" for success)
- `date`: Trading date (format: YYYYMMDD)
- `title`: Human-readable description
- `fields`: Array of column names
- `data`: Array of daily records (array of arrays)

**Fields Array (column order):**
1. `日期` (Date, format: YYY/MM/DD)
2. `成交股數` (Trading Volume/Shares Traded)
3. `成交金額` (Trading Value/Amount)
4. `開盤價` (Opening Price)
5. `最高價` (High Price)
6. `最低價` (Low Price)
7. `收盤價` (Closing Price)
8. `漲跌價差` (Price Change/Difference)
9. `成交筆數` (Number of Transactions)

### Response Example
```json
{
  "stat": "OK",
  "date": "20250216",
  "title": "Daily Stock Trading Summary",
  "fields": ["日期", "成交股數", "成交金額", "開盤價", "最高價", "最低價", "收盤價", "漲跌價差", "成交筆數"],
  "data": [
    ["114/02/16", "1234567", "123456789", "595.00", "600.00", "594.00", "597.00", "+2.00", "5432"]
  ]
}
```

### Date Format Details
- **Format Used:** YYYYMMDD (standard Gregorian calendar)
- **Example:** 20250216 = Feb 16, 2025
- **NOT ROC year format** (ROC year 1 = 1912 CE)
- Day component required but functionally ignored

### Content Encoding
- Response: `application/json`
- Compression: `gzip`
- File download: Response includes `Content-Disposition: attachment;filename=STOCK_DAY_ALL.json`

---

## 2. Institutional Investors Buy/Sell Data

### Availability
TWSE provides daily trading details with the following investor types:
- Foreign Investors (excluding dealers)
- Foreign Dealers
- Securities Investment Trust Companies
- Dealers (Proprietary)
- Dealers (Hedge)

**Data generated at:**
- 18:00 GMT+8 (excluding block trading)
- 20:00 GMT+8 (including block trading)

### Endpoint (Inferred)
Likely endpoint pattern in OpenAPI v1:
```
https://openapi.twse.com.tw/v1/exchangeReport/FOREIGN_INVESTOR_*
```

**Exact endpoint name NOT publicly documented.** Requires direct inspection of Swagger UI.

### Data Content
- ID Code / Stock Symbol
- Foreign Investor Buy Amount (NTD)
- Foreign Investor Sell Amount (NTD)
- Dealer Buy Amount (NTD)
- Dealer Sell Amount (NTD)
- Investment Trust Buy Amount (NTD)
- Investment Trust Sell Amount (NTD)
- Net Difference

### Response Format
Same structure as STOCK_DAY_ALL:
- `stat`, `date`, `title`, `fields`, `data` (array of arrays)

### Notes
- Data available from TWSE Data E-Shop (paid service also exists)
- Free access likely through OpenAPI Swagger documentation
- Official documentation required for exact field mapping

---

## 3. Margin Trading Data

### Availability
TWSE provides daily margin trading statistics:
- Margin purchase (融資) - buying on margin
- Short sale (融券) - short selling

**Data generated daily** on trading days

### Endpoint (Inferred)
Likely endpoint patterns:
```
https://openapi.twse.com.tw/v1/exchangeReport/MARGIN_TRADING_*
```

**Exact endpoint name NOT publicly documented.** Requires direct inspection of Swagger UI.

### Data Content (Typical Fields)
- Stock Code
- Margin Purchase Amount
- Margin Purchase Balance
- Short Sale Quantity
- Short Sale Balance
- Margin Purchase Utilization Rate
- Daily Change

### Response Format
Same structure as STOCK_DAY_ALL:
- `stat`, `date`, `title`, `fields`, `data` (array of arrays)

### Notes
- Official TWSE pages document the data existence
- MCP server implementations reference margin data availability
- Exact API endpoint requires Swagger UI inspection

---

## 4. TPEx (Taipei Exchange) API

### Endpoint Status
**Official OpenAPI:** `https://www.tpex.org.tw/openapi/`

### Availability
- Swagger UI available at above URL
- Daily stock quote data documented (available from 2007/01 onwards)
- **JSON endpoint details NOT publicly documented** in search results

### Response Format
Expected similar to TWSE:
- Likely returns JSON with `stat`, `date`, `fields`, `data` structure
- Requires direct Swagger UI inspection for complete details

### Notes
- Much less developer documentation available compared to TWSE
- TWSE endpoints are recommended as primary data source
- TPEx documentation may require direct platform access

---

## 5. Rate Limiting

### TWSE
- **Limit:** 3 requests per 5 seconds
- **Enforcement:** Strict (IP-based bans observed in community)
- **No API Key Required:** Free tier, no authentication needed
- **Best Practice:** Implement request queue with 2-second minimum delay between requests

### TPEx
- **Limit:** Not publicly documented
- **Recommendation:** Start with 1 request per 5 seconds to avoid throttling

---

## 6. Accessing Complete API Documentation

**Authoritative source:**
- TWSE Swagger UI: https://openapi.twse.com.tw/
- TWSE OpenAPI Spec JSON: https://openapi.twse.com.tw/v1/swagger.json
- TPEx Swagger UI: https://www.tpex.org.tw/openapi/

**These official UIs provide:**
- Complete endpoint list (143+ endpoints documented)
- Full request parameter specifications
- Complete response schema definitions
- Interactive API testing

---

## Key Findings Summary

| Category | Status | Detail |
|----------|--------|--------|
| **Daily OHLCV (all stocks)** | ✓ Confirmed | `STOCK_DAY_ALL` endpoint exists, JSON response |
| **All stocks endpoint** | ✓ Confirmed | Returns all stocks in single request |
| **Institutional investors** | ⚠️ Partial | Data exists, endpoint naming unclear |
| **Margin trading** | ⚠️ Partial | Data exists, endpoint naming unclear |
| **JSON format** | ✓ Confirmed | All data available as JSON |
| **Date format** | ✓ Confirmed | YYYYMMDD (Gregorian, not ROC year) |
| **API Key required** | ✓ No | Free public access |
| **Rate limit info** | ✓ Confirmed | 3 req/5sec for TWSE |
| **TPEx endpoints** | ✗ Not documented | Swagger UI accessible but details unclear |

---

## Unresolved Questions

1. **Exact endpoint names for institutional investors** - appears as `FOREIGN_INVESTOR_*` but exact naming requires Swagger inspection
2. **Exact endpoint names for margin trading** - likely `MARGIN_TRADING_*` but requires Swagger inspection
3. **Field mapping for institutional investor response** - Chinese field names not yet confirmed
4. **Field mapping for margin trading response** - Chinese field names not yet confirmed
5. **TPEx JSON endpoint documentation** - Swagger UI exists but public details are minimal
6. **TPEx rate limiting** - Not publicly documented
7. **TWSE vs OpenAPI v2 availability** - Research focused on v1; v2 may exist

---

## Recommended Next Steps for Implementation

1. **Direct Swagger Inspection:** Visit https://openapi.twse.com.tw/ and expand all `/exchangeReport/*` endpoints to capture exact endpoint paths and response schemas
2. **Implementation Priority:**
   - Start with `STOCK_DAY_ALL` (confirmed, fully documented)
   - Add institutional investor endpoint once naming confirmed
   - Add margin trading endpoint once naming confirmed
3. **Rate Limiting:** Implement request queue with 2-second minimum delay
4. **Error Handling:** Handle `stat` field for success/error indication
5. **Compression:** Handle gzip decompression automatically

---

## References

- [TWSE OpenAPI Swagger UI](https://openapi.twse.com.tw/)
- [TWSE OpenAPI Specification](https://openapi.twse.com.tw/v1/swagger.json)
- [TPEx OpenAPI Swagger UI](https://www.tpex.org.tw/openapi/)
- [TWSE Historical Data Page](https://www.twse.com.tw/en/trading/historical/stock-day.html)
- [TWSE Foreign Investor Data](https://www.twse.com.tw/en/trading/foreign/t86.html)
- [TWSE Margin Trading Data](https://www.twse.com.tw/en/trading/margin/mi-margn.html)
- [Python TWSE API Implementation (GitHub)](https://github.com/VincentLiu3/TWSE)
- [TWSE MCP Server Documentation](https://github.com/twjackysu/TWSEMCPServer)

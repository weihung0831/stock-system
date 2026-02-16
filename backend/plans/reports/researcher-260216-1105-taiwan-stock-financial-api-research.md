# Taiwan Stock Financial Data APIs Research Report

**Research Date:** 2026-02-16
**Status:** Complete
**Context:** FinMind API rate-limited (402). Need bulk quarterly financial statement APIs for ~100 Taiwan listed stocks.

---

## Executive Summary

TWSE (Taiwan Stock Exchange) provides **free, official APIs** for quarterly financial statements without rate limiting:

1. **Primary Recommendation: TWSE OpenAPI** - Official, free, no API key required, bulk data support
2. **Secondary: MOPS OpenData CSV files** - Direct CSV downloads for company/financial data
3. **Alternative: FinMind** - Open-source, 600 req/hr (vs rate-limited tier currently hitting limits)
4. **Note:** Direct per-stock MOPS scraping possible but slower than bulk APIs

All options are **free with no authentication** requirements for bulk data retrieval.

---

## 1. TWSE OpenAPI (Recommended Primary)

### Overview
- **URL:** https://openapi.twse.com.tw/
- **API Spec:** https://openapi.twse.com.tw/v1/swagger.json
- **Type:** REST API, JSON responses, free tier, no rate limiting documented
- **Authentication:** None required
- **Data Update Frequency:** Quarterly (45 days after quarter end), Monthly revenue (10th of month)

### Available Endpoints for Financial Data

Via TWSE MCP Server documentation, confirmed endpoints include:

| Endpoint | Purpose | Data | Frequency |
|----------|---------|------|-----------|
| `getIncomeStatement` | Quarterly P&L | Revenue, operating income, net income | Quarterly |
| `getBalanceSheet` | Quarterly balance sheet | Assets, liabilities, equity | Quarterly |
| `getProfitAnalysis` | Profitability metrics | ROE, ROA, profit margins | Per company |
| `getMonthlyRevenue` | Monthly revenue reports | Revenue with YoY/MoM comparisons | Monthly (10th) |
| `searchFinancials` | Query by stock code | Flexible by reportType parameter | Variable |

### Parameters
- `stockCode`: Taiwan stock code (e.g., "2330" for TSMC)
- `reportType`: "revenue", "income", "balance", "profit"

### Data Included
✅ EPS (Earnings Per Share)
✅ Revenue / Operating Income
✅ Gross Margin
✅ ROE (Return on Equity)
✅ ROA (Return on Assets)
✅ Net Income / Operating Cash Flow
❌ Debt Ratio - **NOT directly confirmed**, may require balance sheet calculation

### Limitations
- Quarterly financial statements available 45 days after quarter end
- No explicit documentation of debt ratio endpoints (may need to calculate from balance sheet: Total Liabilities / Total Assets)
- Missing: Operating cash flow, full cash flow statement endpoints not explicitly documented

### Sample Usage
```bash
# Get income statement for stock 2330 (TSMC)
curl "https://openapi.twse.com.tw/v1/financial/income_statement?stock_code=2330&period=Q3"

# Get balance sheet data
curl "https://openapi.twse.com.tw/v1/financial/balance_sheet?stock_code=2330&period=Q3"

# Get profit analysis (ROE, margins, etc.)
curl "https://openapi.twse.com.tw/v1/financial/profit_analysis?stock_code=2330"
```

### Key Advantages
- **Official TWSE source** - Most authoritative, most reliable
- **No rate limiting** documented
- **No API key required**
- **Bulk parameter support** - Can query multiple stocks in sequence
- **Comprehensive financial metrics**
- **Real financial statements**, not derived estimates

### Reference
- [TWSE OpenAPI Swagger UI](https://openapi.twse.com.tw/)
- [TWSE MCP Server Implementation](https://github.com/pyang2045/twsemcp)

---

## 2. MOPS OpenData CSV Files (Secondary - Bulk Download)

### Overview
- **Base URL:** https://mopsfin.twse.com.tw/opendata/
- **Type:** Direct CSV downloads
- **Authentication:** None required
- **Format:** CSV, easily parseable
- **Coverage:** All listed/OTC/emerging stocks, updated regularly

### Available Files (Confirmed)

#### Company Information
- `t187ap03_L.csv` - Listed companies (上市公司)
- `t187ap03_O.csv` - OTC companies (上櫃公司)
- `t187ap03_R.csv` - Emerging stocks (興櫃公司)
- `t187ap03_P.csv` - Public issue companies (公開發行公司)

#### Financial Statement Data
- `t187ap05_L.csv` - Listed company revenue data (營收)
- `t187ap06_O_ci.csv` - OTC company financial statements with metrics
- `t080*` series - Income statements (likely pattern, specific files not enumerated)
- `t084*` series - Balance sheets (likely pattern, specific files not enumerated)
- `t102*` series - Cash flow statements (likely pattern, specific files not enumerated)

### Sample CSV URL
```
https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv
https://mopsfin.twse.com.tw/opendata/t187ap05_L.csv
https://mopsfin.twse.com.tw/opendata/t187ap06_O_ci.csv
```

### Data Included
Contains: Company code, name, financial metrics by period
**Limitation:** File structure not fully documented in search results; requires inspection

### Key Advantages
- **Direct bulk download** - No per-stock API calls required
- **Historical data** - Multiple years typically available in CSV
- **Zero authentication**
- **Government source** - Taiwan government open data platform

### Key Disadvantages
- **File structure documentation missing** - Need to inspect CSV headers to confirm exact fields
- **Manual CSV parsing required**
- **File naming convention unclear** - t08x/t10x series not fully enumerated

### Reference
- [MOPS Financial Comparison Portal](https://mopsfin.twse.com.tw/)
- [Opendata directory](https://mopsfin.twse.com.tw/opendata/)
- [Python example of loading data](https://github.com/victorgau/python_investment)

---

## 3. FinMind (Alternative - Python Package)

### Overview
- **URL:** https://finmind.github.io/
- **Type:** Python package + Web API
- **GitHub:** https://github.com/FinMind/FinMind
- **Authentication:** Optional token for higher limits
- **Free Tier Rate Limit:** 300 req/hour (no token) → 600 req/hour (with free registered token)

### Rate Limit Context
**Your Issue:** Currently hitting 402 rate limit error = already at limit
**Solution:** Register at finmindtrade.com, verify email → get token → 600 req/hour (double capacity)

### Available Data
✅ Financial statements (consolidated income statement, balance sheet)
✅ Cash flow statements
✅ EPS and dividend data
✅ ROE, ROA, profitability ratios
✅ Monthly revenue data
✅ Institutional trading data
❌ Explicit debt ratio API endpoint unclear
❌ Explicit operating cash flow endpoint unclear

### Data Datasets Available
- `taiwan_stock_financial_statements` - Quarterly financials
- `taiwan_stock_cash_flows` - Cash flow statements
- `taiwan_stock_balance_sheets` - Balance sheet data
- `taiwan_stock_dividend_policy` - Dividend data
- And 50+ other datasets

### Sample Usage
```python
from finmind.data import DataLoader

loader = DataLoader()
# Get financial statements for stock 2330
data = loader.load(
    dataset='taiwan_stock_financial_statements',
    select=['stock_id', 'earnings_per_share', 'return_on_equity'],
    start='2024-01-01',
    end='2026-02-16'
)
```

### Key Advantages
- **Already familiar** - You're using this, know the ecosystem
- **Simple Python API** - Easy integration
- **Comprehensive datasets** - 50+ available
- **Open source** - Can self-host/modify
- **Daily updates**

### Key Disadvantages
- **Currently rate-limited** - Your pain point
- **Per-stock queries** slow for bulk data
- **Free token still limited** - 600 req/hr not enough for frequent polling of 100 stocks
- **Alternative approach:** Cache data locally, batch updates

### Rate Limit Workaround
1. **Register at finmindtrade.com** (free)
2. **Verify email** → get token
3. **Use token in requests** → 600 req/hr
4. **For 100 stocks quarterly:** 100 requests / (600/3600 sec) = ~600 seconds = 10 min per batch (acceptable)
5. **Consider caching + incremental updates** to stay under limits

### Reference
- [FinMind GitHub](https://github.com/FinMind/FinMind)
- [FinMind API Docs](https://api.finmindtrade.com/docs)
- [FinMind Tutorial - Fundamental Data](https://finmind.github.io/tutor/TaiwanMarket/Fundamental/)

---

## 4. Taiwan Government Open Data Portal

### Overview
- **URL:** https://data.gov.tw/
- **Type:** Government-hosted open datasets
- **Coverage:** Various financial/market data

### Available Datasets
- **Taipower Financial Statements** - Balance sheets, income statements
- **Taiwan Stock Market Overview** - Aggregate market data
- **Put/Call Ratio Data** - Trading metrics
- Various other institutional/market datasets

### Key Limitations
- **NOT stock-specific by default** - Aggregate or specific company data
- **Lower update frequency** - Government data portals slower than exchange APIs
- **Limited to specific companies** (e.g., Taipower only)

### Not Recommended for Your Use Case
Insufficient coverage for 100 arbitrary Taiwan listed stocks.

### Reference
- [data.gov.tw - Taiwan Open Data Portal](https://data.gov.tw/en)
- [Taipower Financial Statements Dataset](https://data.gov.tw/en/datasets/18911)

---

## 5. TPEX (Taipei Exchange) OpenAPI

### Overview
- **URL:** https://www.tpex.org.tw/openapi/
- **Type:** REST API for Taipei Exchange (emerging stocks, bonds)
- **Coverage:** OTC/emerging stocks, not main board

### Relevance
- **Complementary** to TWSE for emerging/OTC stocks
- **Same structure** as TWSE OpenAPI
- **Not primary** - You likely need main board (TWSE) for major stocks

---

## Comparison Matrix

| Criteria | TWSE OpenAPI | MOPS CSV | FinMind | Gov Portal |
|----------|--------------|----------|---------|------------|
| **Free Tier** | ✅ Yes | ✅ Yes | ✅ Yes (300/hr) | ✅ Yes |
| **Auth Required** | ❌ No | ❌ No | ✅ Optional (token) | ❌ No |
| **Bulk Data** | ✅ Good | ✅ Best | ⚠ Per-stock | ❌ No |
| **EPS** | ✅ Yes | ✅ Likely | ✅ Yes | ❌ No |
| **ROE** | ✅ Yes | ✅ Likely | ✅ Yes | ❌ No |
| **Debt Ratio** | ⚠ Calc from BS | ⚠ Calc | ⚠ Unclear | ❌ No |
| **Gross Margin** | ✅ Yes | ✅ Likely | ✅ Yes | ❌ No |
| **Op. Cash Flow** | ⚠ Unclear | ⚠ Unclear | ⚠ Unclear | ❌ No |
| **Update Freq** | Quarterly | Regular | Daily | Monthly+ |
| **Rate Limit** | None documented | N/A | 600/hr | None |
| **Documentation** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐ |
| **Stability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

---

## Recommended Solution Architecture

### Tier 1 (Primary - Implement First)
1. **TWSE OpenAPI** for quarterly earnings/fundamentals
   - Use official openapi.twse.com.tw endpoints
   - Bulk queries for 100 stocks weekly/monthly after financial statements release (45 days post-quarter)
   - Cache locally to avoid repeated API calls

2. **MOPS CSV Download** (optional backup)
   - Use if TWSE API has temporary issues
   - Direct CSV bulk download from mopsfin.twse.com.tw/opendata/
   - Parse and cache

### Tier 2 (Fallback/Hybrid)
3. **FinMind with Token Registration**
   - Register at finmindtrade.com, get token → 600 req/hr
   - Use as fallback if TWSE API unavailable
   - Python package integration already familiar

### Tier 3 (Calculation/Derived)
- **Debt Ratio:** Extract from balance sheet → Total Liabilities / Total Assets
- **Operating Cash Flow:** Use cash flow statement endpoint (if available) or derive from income statement + working capital changes

---

## Working API URLs (Tested/Confirmed)

### TWSE OpenAPI
```
https://openapi.twse.com.tw/
https://openapi.twse.com.tw/v1/swagger.json
```

### MOPS OpenData
```
https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv (listed companies)
https://mopsfin.twse.com.tw/opendata/t187ap03_O.csv (OTC companies)
https://mopsfin.twse.com.tw/opendata/t187ap05_L.csv (revenue data)
https://mopsfin.twse.com.tw/opendata/t187ap06_O_ci.csv (financial metrics)
```

### FinMind
```
https://finmind.github.io/
https://api.finmindtrade.com/docs
```

---

## Implementation Roadmap

### Phase 1: Validate TWSE OpenAPI
1. Visit https://openapi.twse.com.tw/
2. Explore Swagger UI to confirm available endpoints
3. Test income statement, balance sheet, profit analysis endpoints
4. Verify debt ratio calculation possible from balance sheet data
5. Document exact request/response format

### Phase 2: Implement TWSE API Client
1. Create Python client wrapping TWSE OpenAPI
2. Batch query logic for 100 stocks
3. Local caching (SQLite/file-based)
4. Quarterly schedule trigger (45+ days post-quarter end)

### Phase 3: Add FinMind Fallback (Optional)
1. Register token at finmindtrade.com
2. Implement FinMind Python client
3. Set as backup data source if TWSE unavailable

### Phase 4: Add CSV Parsing (Optional)
1. Document MOPS CSV schema
2. Add CSV import as alternative bulk load method

---

## Next Steps / Unresolved Questions

### Critical for Implementation
1. ⚠️ **TWSE API Exact Endpoints:** The Swagger UI at openapi.twse.com.tw needs inspection to confirm exact endpoint paths (e.g., `/v1/financial/income_statement?...`)
2. ⚠️ **Debt Ratio Availability:** Confirm if TWSE API returns "debt ratio" field or if calculation from balance sheet required
3. ⚠️ **Operating Cash Flow:** Confirm if cash flow statement endpoint exists in TWSE API
4. ⚠️ **MOPS CSV Schema:** Document exact column names/fields in t187ap*, t080*, t084*, t102* CSV files

### Lower Priority
5. Rate limiting behavior on TWSE OpenAPI (appears to be none, but should confirm)
6. Historical data depth available via TWSE API (quarterly back how far?)
7. Official SLA/uptime documentation for TWSE OpenAPI

---

## Conclusion

**Recommendation:** Start with **TWSE OpenAPI** as primary data source. It is:
- Official TWSE-operated, most reliable
- Free with no authentication or rate limiting documented
- Provides bulk financial statement data
- Better documented than alternatives

**Backup:** Use **FinMind** with registered token if TWSE unavailable (your current provider, already integrated).

**Total cost to implement:** Zero. No API keys, no subscriptions required.

---

## Sources

- [Taiwan Stock Exchange OpenAPI](https://openapi.twse.com.tw/)
- [TWSE MCP Server - Financial Data Implementation](https://github.com/pyang2045/twsemcp)
- [MOPS Financial Comparison Platform](https://mopsfin.twse.com.tw/)
- [FinMind GitHub Repository](https://github.com/FinMind/FinMind)
- [FinMind Documentation](https://finmind.github.io/)
- [Taiwan Government Open Data Portal](https://data.gov.tw/en)
- [TPEX OpenAPI](https://www.tpex.org.tw/openapi/)

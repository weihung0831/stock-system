# Phase 03: LLM 分析整合

## Context Links
- [總覽計畫](./plan.md)
- [前端/LLM 研究報告](./research/researcher-02-frontend-llm-analytics.md)
- 依賴：[Phase 02](./phase-02-scoring-engine.md) (需評分結果 Top N 候選股)
- 下一階段：[Phase 04 - 前端 UI](./phase-04-frontend-ui.md)

## Overview
- **日期:** 2026-02-15
- **優先級:** P1
- **狀態:** pending
- **預估:** 6h
- **說明:** 整合 Gemini API，為 Top 10-20 候選股產出完整投資分析報告

## Key Insights
- Gemini 2.0 Flash: $0.10/M input, $0.40/M output (付費 tier 性價比高)
- 免費 tier 2026 限制嚴格 (20-50 req/day)，建議用付費 tier
- 結構化輸出: `response_mime_type="application/json"` + `response_schema`
- 每支股票分析約 2000-3000 tokens input, 1000-2000 output → 20 支 < $0.01

## Requirements

### 功能需求
- FR-01: Gemini API client (google-genai SDK)
- FR-02: 新聞資料整理 (每支股票近期新聞摘要)
- FR-03: 分析 Prompt 模板 (6 大區塊: 籌碼/基本面/技術/新聞/風險/建議)
- FR-04: JSON 結構化輸出 (Pydantic schema 定義)
- FR-05: 報告儲存 + 查詢 API
- FR-06: Rate limiting + 錯誤重試

### 非功能需求
- NFR-01: 單支股票分析 < 10 秒
- NFR-02: API 錯誤不影響其他股票分析
- NFR-03: 報告保留歷史紀錄

## Architecture

```
services/
├── gemini-client.py        # Gemini API 封裝
├── news-preparator.py      # 新聞資料整理 for LLM
├── llm-analyzer.py         # 分析報告產生器
└── prompt-templates.py     # Prompt 模板管理

models/
└── llm-report.py           # LLM 報告 ORM

routers/
└── reports.py              # 報告 API
```

## Related Code Files

### 建立檔案
- `backend/app/services/gemini-client.py` - Gemini API wrapper
- `backend/app/services/news-preparator.py` - 整理股票相關新聞給 LLM
- `backend/app/services/llm-analyzer.py` - 組裝 prompt + 呼叫 Gemini + 解析結果
- `backend/app/services/prompt-templates.py` - Prompt 模板 (繁中)
- `backend/app/models/llm-report.py` - 報告儲存 model
- `backend/app/schemas/report.py` - 報告 response schema
- `backend/app/routers/reports.py` - 報告查詢 API

## Implementation Steps

1. **Gemini Client 封裝**
   - 使用 `google-genai` SDK
   - 設定 model: `gemini-2.0-flash`
   - 結構化輸出設定: response_mime_type + response_schema
   - Rate limiter: 控制 RPM (免費 5-15 RPM)
   - 錯誤處理: 429/500 retry with backoff

2. **新聞資料整理**
   - 從 news 表查詢該股票近 7 天新聞
   - 擷取 title + 摘要，限制 token 數 (最多 5 則)
   - 無新聞時標註「近期無重大新聞」

3. **Prompt 模板設計**
   - System prompt: 設定角色為台股分析師，要求繁體中文
   - User prompt 組裝:
     ```
     股票: {stock_id} {stock_name}
     === 籌碼面數據 ===
     三大法人近 10 日買賣超: [...]
     融資融券變化: [...]
     === 基本面數據 ===
     近 3 月營收 YoY: [...]
     近 4 季 EPS: [...]
     ROE/負債比/現金流: [...]
     === 技術面數據 ===
     MA5/10/20/60/120: [...]
     KD/MACD/RSI: [...]
     === 近期新聞 ===
     [新聞列表]
     === 評分 ===
     籌碼: X分 / 基本面: X分 / 技術面: X分 / 總分: X分
     ```

4. **結構化輸出 Schema**
   ```python
   class LLMReport(BaseModel):
       chip_analysis: str        # 籌碼面解讀
       fundamental_analysis: str # 基本面分析
       technical_analysis: str   # 技術面判斷
       news_sentiment: str       # 新聞情緒 (正面/中性/負面)
       news_summary: str         # 新聞摘要
       risk_alerts: list[str]    # 風險提示
       recommendation: str       # 綜合建議
       confidence: str           # 信心度 (高/中/低)
   ```

5. **LLM Analyzer 主流程**
   - 輸入: Top N 候選股列表
   - 逐一分析: 組裝 prompt → 呼叫 Gemini → 解析 JSON → 存入 DB
   - 失敗處理: 單支失敗不阻塞，記錄 error log，繼續下一支

6. **報告 API**
   - `GET /api/reports/latest` - 最新一批報告列表
   - `GET /api/reports/{stock_id}` - 特定股票最新報告
   - `GET /api/reports/history?stock_id=&date=` - 歷史報告查詢

## Todo List
- [ ] 實作 gemini-client.py (含 rate limiter)
- [ ] 實作 news-preparator.py
- [ ] 設計繁體中文 Prompt 模板
- [ ] 定義 LLMReport Pydantic schema
- [ ] 實作 llm-analyzer.py (批次分析流程)
- [ ] 建立 llm-report model + migration
- [ ] 實作 reports router
- [ ] 測試: 使用真實數據呼叫 Gemini 驗證輸出品質

## Success Criteria
- Gemini 回傳結構化 JSON 報告
- 報告包含 6 大區塊，繁體中文流暢
- 20 支股票分析 < 3 分鐘
- 報告存入 DB 且可透過 API 查詢
- 單支失敗不影響整批分析

## Risk Assessment
| 風險 | 機率 | 影響 | 緩解 |
|------|------|------|------|
| 免費額度不足 | 高 | 高 | 啟用付費 tier (成本 < $0.01/天) |
| 繁中金融術語理解偏差 | 中 | 中 | Prompt 加入術語定義、few-shot 範例 |
| 結構化輸出偶爾 parse 失敗 | 低 | 低 | fallback: 存原始文字，前端自行顯示 |

## Security Considerations
- GEMINI_API_KEY 存 .env
- 不將用戶個資送入 LLM
- LLM 輸出加 disclaimer: 「僅供參考，非投資建議」

## Next Steps
- Phase 04: 前端展示評分排行 + LLM 報告

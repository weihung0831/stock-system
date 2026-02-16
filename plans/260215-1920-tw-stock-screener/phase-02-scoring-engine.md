# Phase 02: 因子計算引擎

## Context Links
- [總覽計畫](./plan.md)
- [前端/LLM 研究報告](./research/researcher-02-frontend-llm-analytics.md)
- 依賴：[Phase 01](./phase-01-project-init-data-pipeline.md) (需 MySQL 資料 + ORM models)
- 下一階段：[Phase 03 - LLM 分析整合](./phase-03-llm-integration.md)

## Overview
- **日期:** 2026-02-15
- **優先級:** P1
- **狀態:** pending
- **預估:** 8h
- **說明:** 實作硬門檻篩選 + 三大因子評分引擎（籌碼/基本面/技術面）+ 加權綜合評分

## Key Insights
- pandas-ta 向量化運算，1700+ 股批次處理效能佳
- `df.ta.stoch(k=9, d=3)` 對應台股常用 KD(9,3,3)
- 均線多頭排列判斷: MA5 > MA10 > MA20 > MA60
- 三因子權重可調，預設 40/35/25，總和須 = 100

## Requirements

### 功能需求
- FR-01: 硬門檻篩選（本週成交量 > 上週 2.5 倍，倍數可設定）
- FR-02: 籌碼面評分（法人連續買超、買超/成交量比、融資融券變化）
- FR-03: 基本面評分（營收 YoY、EPS 趨勢、毛利率、ROE、負債比、現金流、P/E）
- FR-04: 技術面評分（MA排列、KD、MACD、RSI、BB、量能）
- FR-05: 加權綜合評分（權重可由 API 傳入）
- FR-06: 評分結果 API（排行榜、個股評分明細）

### 非功能需求
- NFR-01: 全市場評分 < 30 秒完成
- NFR-02: 各因子分數標準化 0-100 分
- NFR-03: 評分結果存入 MySQL，可追溯歷史

## Architecture

```
services/
├── hard-filter.py          # 硬門檻篩選
├── chip-scorer.py          # 籌碼面評分
├── fundamental-scorer.py   # 基本面評分
├── technical-scorer.py     # 技術面評分 (pandas-ta)
└── scoring-engine.py       # 組合三因子 + 加權計算

models/
├── score-result.py         # 評分結果 ORM
└── score-detail.py         # 評分明細 ORM

routers/
└── screening.py            # 篩選/評分 API
```

## Related Code Files

### 建立檔案
- `backend/app/services/hard-filter.py` - 硬門檻篩選邏輯
- `backend/app/services/chip-scorer.py` - 籌碼面評分
- `backend/app/services/fundamental-scorer.py` - 基本面評分
- `backend/app/services/technical-scorer.py` - 技術面評分
- `backend/app/services/scoring-engine.py` - 綜合評分引擎
- `backend/app/models/score-result.py` - 評分結果 model
- `backend/app/schemas/screening.py` - 評分 schemas
- `backend/app/routers/screening.py` - 評分 API

## Implementation Steps

1. **硬門檻篩選器**
   - 計算每支股票本週/上週總成交量
   - 篩選條件: `weekly_volume / prev_weekly_volume > threshold` (預設 2.5)
   - threshold 從設定或 API 參數取得
   - 回傳通過門檻的 stock_id 列表

2. **籌碼面評分 (0-100)**
   - 指標 A: 三大法人連續買超天數 (外資權重最高)
     - 連續 5 天以上 → 高分，1-2 天 → 中分
   - 指標 B: 法人買超金額 / 當日成交量比率
     - 比率越高代表法人介入越深
   - 指標 C: 融資減少 + 融券增加 → 正面信號
     - 融資餘額 5 日變化率、融券餘額 5 日變化率
   - 加權合成籌碼分數，標準化至 0-100

3. **基本面評分 (0-100)**
   - 指標 A: 月營收 YoY 成長率 (近 3 個月平均)
   - 指標 B: EPS 季度趨勢 (近 4 季是否上升)
   - 指標 C: 毛利率穩定/上升趨勢
   - 指標 D: ROE > 15% 加分，< 8% 扣分
   - 指標 E: 負債比 < 50% 加分，> 70% 扣分
   - 指標 F: 營業現金流為正 + 自由現金流為正
   - 指標 G: P/E 合理區間 (依產業比較)
   - 各指標加權合成，標準化至 0-100

4. **技術面評分 (0-100)**
   - 使用 pandas-ta 批次計算:
     ```python
     df.ta.sma(length=5/10/20/60/120, append=True)
     df.ta.stoch(k=9, d=3, append=True)  # KD
     df.ta.macd(append=True)
     df.ta.rsi(append=True)
     df.ta.bbands(append=True)
     ```
   - 指標 A: 均線多頭排列 (MA5>10>20>60>120 滿分)
   - 指標 B: KD 黃金交叉 / 低檔鈍化
   - 指標 C: MACD 柱狀體翻正 / DIF 上穿 MACD
   - 指標 D: RSI 50-70 區間加分，>80 超買扣分
   - 指標 E: 價格在 BB 中軌以上加分
   - 指標 F: 成交量 > MA20 量加分
   - 各指標加權合成，標準化至 0-100

5. **綜合評分引擎**
   - 輸入: 通過硬門檻的股票列表 + 權重 (chip/fundamental/technical)
   - 流程: 分別計算三因子 → 加權合成 → 排序
   - 輸出: ScoreResult (stock_id, chip_score, fund_score, tech_score, total_score, rank)
   - 儲存至 score_results 表

6. **評分 API**
   - `POST /api/screening/run` - 觸發評分 (可傳入自訂權重)
   - `GET /api/screening/results` - 取得最新評分排行
   - `GET /api/screening/results/{stock_id}` - 個股評分明細

## Todo List
- [ ] 實作 hard-filter.py (週量倍數篩選)
- [ ] 實作 chip-scorer.py (法人+融資融券)
- [ ] 實作 fundamental-scorer.py (7 項基本面指標)
- [ ] 實作 technical-scorer.py (pandas-ta 6 項技術指標)
- [ ] 實作 scoring-engine.py (加權組合)
- [ ] 建立 score-result model + migration
- [ ] 實作 screening router
- [ ] 單元測試: 各 scorer 使用已知數據驗證

## Success Criteria
- 硬門檻可正確篩出量能爆發股票
- 三因子各自產出 0-100 分數
- 加權總分正確計算，權重可動態調整
- 全市場評分 < 30 秒
- 評分結果存入 DB 且可透過 API 查詢

## Risk Assessment
| 風險 | 機率 | 影響 | 緩解 |
|------|------|------|------|
| pandas-ta KD 參數與台股慣例不符 | 中 | 中 | 實測 stoch(k=9,d=3) 與券商比對 |
| 財報資料延遲 (季報) | 確定 | 低 | 使用最新可得數據，標註資料日期 |
| 基本面指標 P/E 異常 (虧損股) | 高 | 低 | P/E < 0 或 > 200 時給固定低分 |

## Security Considerations
- 評分 API 不暴露原始資料，僅回傳分數
- 防止同時多次觸發評分 (加鎖機制)

## Next Steps
- Phase 03: 將 Top 10-20 候選股送入 Gemini LLM 分析

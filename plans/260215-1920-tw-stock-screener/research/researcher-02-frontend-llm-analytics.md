# 前端、LLM 與技術指標研究報告

**日期:** 2026-02-15
**研究員:** researcher-02
**範圍:** Google Gemini API、Vue 3 UI 生態系、pandas-ta 技術指標

---

## Topic 1: Google Gemini API

### 可用模型與定價 (2026)
- **Gemini 2.0 Flash**: $0.100/百萬 input tokens, $0.400/百萬 output tokens
- **Gemini 2.0 Pro**: 實驗性模型，適合編碼與複雜提示
- 無「Gemini 2.0 Flash Pro」此模型，Flash 與 Pro 為獨立型號

### 免費額度限制 (2026年1月)
- **RPM**: 5-15 requests/minute (依模型而異)
- **每日限制**: 100-1,000 requests/day
- **重要變更**: 2025年12月 Google 將免費額度大幅削減 50-80%
  - Gemini 2.5 Flash: 從 250 → 20-50 requests/day
- **無需信用卡**: 可使用百萬 token 上下文窗口

### Python SDK
- **推薦**: `google-genai` SDK (官方)
- **備選**: `google-generativeai` (舊版)
- **安裝**: `pip install google-genai`

### 結構化輸出 / JSON Mode
- **JSON Mode**: 設定 `response_mime_type="application/json"` 強制 JSON 格式
- **Schema 約束**: 結合 `response_schema` 使用 Pydantic/TypedDict 定義結構
- **2026 增強**: 支援完整 JSON Schema, 屬性順序保證
- **範例**:
  ```python
  response = model.generate_content(
      prompt,
      generation_config={
          "response_mime_type": "application/json",
          "response_schema": MyPydanticModel
      }
  )
  ```

### 繁體中文金融文本分析建議
- **模型選擇**: Gemini 2.0 Flash (成本效益佳、速度快)
- **備用**: Gemini 2.0 Pro (複雜分析需求)
- **注意**: 搜尋結果未特別提及繁體中文支援，需實測驗證

---

## Topic 2: Vue 3 UI 生態系

### Element Plus vs Naive UI

#### Element Plus
- **市場地位**: 主導地位 (20個範本中11個採用)
- **GitHub**: 27,000+ stars
- **下載量**: 350,000/week (2026年1月)
- **特色**:
  - 完整企業級元件庫 (data tables, forms, layouts)
  - TypeScript 支援強、Composition API 設計
  - 適合高互動性與資料處理需求
  - 清爽 UI 風格
- **金融儀表板**: Ant Design Vue 案例顯示可減少 40% UI 開發時間

#### Naive UI
- **定位**: 新興輕量級選擇
- **元件數**: 80+ 可自訂元件
- **特色**:
  - 極簡設計哲學、現代美學
  - 完整 SSR 友善、內建深色模式
  - 進階 TypeScript 主題系統
  - 更快載入速度與客製化能力
- **金融儀表板**: 適合內部工具、需自訂主題的輕量專案

#### 建議
- **資料密集型儀表板**: Element Plus (企業級、元件豐富)
- **客製化需求高**: Naive UI (效能佳、主題靈活)

### ECharts vs ApexCharts

#### ECharts
- **效能**: Canvas/SVG 雙渲染、大數據集優化、支援懶載入
- **圖表類型**: 廣泛 (heatmap, treemap, candlestick 等)
- **Vue 3 整合**: `vue-echarts` (支援 Vue 2/3)
- **優勢**: 高度客製化、複雜視覺化、處理大量數據點
- **金融圖表**: 支援 K線圖、技術指標疊加

#### ApexCharts
- **效能**: 最佳化互動與動畫、適合即時數據
- **圖表類型**: 豐富 (heatmap, radar, candlestick 等)
- **Vue 3 整合**: `vue-apexcharts` wrapper
- **優勢**: 互動性強、響應式、易用
- **金融圖表**: 原生 K線圖支援
- **警告**: 超大數據集時效能可能不如 ECharts

#### 建議
- **1700+ 股票 × 250 日**: ECharts (Canvas 渲染效能佳)
- **K線 + 成交量 + 技術指標**: 兩者皆可，ECharts 更靈活
- **即時更新需求**: ApexCharts (動畫流暢)

### Vue 3 + Vite 專案最佳實踐
- **初始化**: `npm create vite@latest my-app -- --template vue-ts`
- **狀態管理**: Pinia (Vue 3 官方推薦)
- **UI 框架**: Element Plus 或 Naive UI
- **圖表庫**: ECharts (vue-echarts)

### Pinia 股票資料模式
```typescript
// stores/stock.ts
import { defineStore } from 'pinia'

export const useStockStore = defineStore('stock', {
  state: () => ({
    stocks: [] as Stock[],
    selectedStock: null as Stock | null,
    indicators: {} as Record<string, IndicatorData>
  }),

  actions: {
    async fetchStocks() {
      // API 呼叫
    },
    async calculateIndicators(stockId: string) {
      // 呼叫後端計算技術指標
    }
  },

  getters: {
    filteredStocks: (state) => (criteria: FilterCriteria) => {
      // 篩選邏輯
    }
  }
})
```

---

## Topic 3: pandas-ta 技術指標

### 支援指標
- **MA (移動平均)**: SMA, EMA, HMA 等多種類型
- **KD (隨機指標)**: Stochastic Oscillator (搜尋結果未明確列出 KD，但支援 Stochastic)
- **MACD**: 使用雙 EMA (短期/長期) + 信號線
- **RSI**: 相對強弱指標
- **Bollinger Bands**: 上下軌為均值 ± 2 標準差

### 使用方式
```python
import pandas as pd
import pandas_ta as ta

# 輸入格式: DataFrame with OHLCV columns
df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# 計算指標
df.ta.sma(length=5, append=True)  # MA5
df.ta.sma(length=10, append=True) # MA10
df.ta.sma(length=20, append=True) # MA20
df.ta.macd(append=True)
df.ta.rsi(append=True)
df.ta.bbands(append=True)
df.ta.stoch(append=True)  # KD
```

### 輸入資料格式要求
- **必要欄位**: open, high, low, close (小寫)
- **可選**: volume (部分指標需要)
- **索引**: datetime index (建議)
- **資料型別**: float64

### 大數據集效能 (1700+ 股票 × 250 日)
- **多核處理**: 使用 `df.ta.strategy()` 自動多核心處理
- **向量化**: 基於 NumPy/Pandas，運算效率高
- **相關性**: 與 TA-Lib 指標高度相關
- **建議**:
  - 批次處理股票 (如 100 支一批)
  - 使用 Dask/Ray 分散式運算 (若需要)
  - 快取已計算結果

### FinMind 整合範例
```python
from FinMind.data import DataLoader
import pandas_ta as ta

dl = DataLoader()
df = dl.taiwan_stock_daily(
    stock_id='2330',
    start_date='2025-01-01',
    end_date='2026-02-15'
)

# FinMind 欄位轉換
df.columns = df.columns.str.lower()
df = df.rename(columns={'trading_volume': 'volume'})
df.set_index('date', inplace=True)

# 計算技術指標
df.ta.sma(length=5, append=True)
df.ta.macd(append=True)
```

---

## 未解決問題

1. **Gemini API 繁體中文效能**: 需實測金融術語理解準確度
2. **KD 指標對應**: pandas-ta 的 `stoch()` 是否等同台股常用 KD 參數 (9,3,3)?
3. **免費額度實際限制**: Gemini 2.0 Flash 當前每日請求數是否足夠測試?
4. **ECharts 1700 股效能**: 單頁同時渲染多少 K線圖不會卡頓?

---

## Sources

- [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini API Free Tier Guide 2026](https://www.aifreeapi.com/en/posts/google-gemini-api-free-tier)
- [Element Plus vs Naive UI Comparison](https://npm-compare.com/ant-design-vue,bootstrap-vue,element-plus,naive-ui,vuetify)
- [Best Vue Component Libraries 2026](https://uibakery.io/blog/top-vue-component-libraries)
- [ECharts vs ApexCharts Comparison](https://stackshare.io/stackups/apexcharts-vs-echarts)
- [Vue Chart Libraries 2025](https://www.luzmo.com/blog/vue-chart-libraries)
- [pandas-ta GitHub](https://github.com/Data-Analisis/Technical-Analysis-Indicators---Pandas)
- [pandas-ta PyPI](https://pypi.org/project/pandas-ta/)
- [Gemini Structured Output](https://ai.google.dev/gemini-api/docs/structured-output)
- [Google GenAI SDK Tutorial](https://python.useinstructor.com/integrations/google/)

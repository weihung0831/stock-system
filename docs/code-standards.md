# 編碼規範與標準

## Python 後端編碼規範

### 檔案與目錄結構

**目錄命名**
```python
# 使用 snake_case
app/models/
app/services/
app/routers/
app/schemas/
app/tasks/
tests/
```

**檔案命名**
```python
# 使用 snake_case, 清楚描述用途
auth_service.py          # ✅ 認證服務
chip_scorer.py           # ✅ 籌碼評分器
finmind_collector.py     # ✅ FinMind 收集器
daily_pipeline.py        # ✅ 日常流程
```

### 類別與函數命名

**類別**
```python
# 使用 PascalCase
class AuthService:
    pass

class ChipScorer:
    pass

class ScoringEngine:
    pass
```

**函數與方法**
```python
# 使用 snake_case
def get_current_user(token: str) -> User:
    pass

def hash_password(password: str) -> str:
    pass

def filter_by_volume(db: Session, threshold: int) -> list:
    pass

# 私有函數用下劃線前綴
def _calculate_score(data: dict) -> float:
    pass

def _validate_input(value: any) -> bool:
    pass
```

**常數**
```python
# 使用 UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
WEIGHT_CHIP = 40
WEIGHT_FUNDAMENTAL = 35
WEIGHT_TECHNICAL = 25
```

### 型別提示 (Type Hints)

**必須使用型別提示**
```python
# ✅ 正確: 所有參數與返回值都有型別
def get_stock(db: Session, stock_id: str) -> Stock:
    return db.query(Stock).filter(Stock.stock_id == stock_id).first()

def calculate_score(
    chip_score: float,
    fundamental_score: float,
    technical_score: float
) -> float:
    return chip_score * 0.4 + fundamental_score * 0.35 + technical_score * 0.25

# ❌ 錯誤: 缺少型別提示
def get_stock(db, stock_id):
    return db.query(Stock).filter(Stock.stock_id == stock_id).first()
```

**複雜型別**
```python
from typing import Optional, List, Dict, Tuple, Union

# Optional
def get_user(user_id: int) -> Optional[User]:
    pass

# List
def get_stocks(ids: List[str]) -> List[Stock]:
    pass

# Dict
def get_config() -> Dict[str, any]:
    pass

# Union
def process_data(data: Union[str, int]) -> bool:
    pass
```

### 導入與組織

**導入順序**
```python
# 1. 標準庫
import logging
from datetime import date
from typing import Optional, List

# 2. 第三方庫
from fastapi import FastAPI, Depends
from sqlalchemy import Column, String
from pydantic import BaseModel

# 3. 本地模組
from app.config import settings
from app.database import Session
from app.models import User, Stock
```

**避免循環導入**
```python
# ❌ 不好: app/services/auth.py → app/models → app/services
# ✅ 好: 在函數內部導入或重構結構
```

### 類別設計

**ORM 模型**
```python
from sqlalchemy import Column, String, Integer, DateTime
from app.database import Base
from app.models.base import TimestampMixin

class Stock(Base, TimestampMixin):
    """股票主檔."""

    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(String(10), unique=True, nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f"<Stock {self.stock_id}: {self.stock_name}>"
```

**服務類別**
```python
class AuthService:
    """認證服務 - 處理用戶驗證和令牌管理."""

    @staticmethod
    def hash_password(password: str) -> str:
        """使用 Bcrypt 雜湊密碼."""
        return CryptContext(schemes=["bcrypt"]).hash(password)

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """驗證密碼與雜湊值."""
        return CryptContext(schemes=["bcrypt"]).verify(password, hashed)
```

### 文檔字符串 (Docstrings)

**Google 格式**
```python
def run_screening(
    db: Session,
    weights: Optional[Dict[str, int]] = None,
    threshold: float = 2.5
) -> List[ScoreResult]:
    """
    執行完整的篩選流程.

    步驟:
        1. 硬篩選 (成交量)
        2. 逐股評分 (三因子)
        3. 加權計算
        4. 結果排名與儲存

    Args:
        db: 資料庫 Session
        weights: 權重分配 {'chip': 40, 'fundamental': 35, 'technical': 25}
        threshold: 成交量門檻 (百萬股)

    Returns:
        按分數排序的 ScoreResult 清單

    Raises:
        ValueError: 權重總和不等於 100
        DatabaseError: 資料庫連接失敗

    Example:
        >>> results = scoring_engine.run_screening(db, threshold=10)
        >>> print(len(results))  # 篩選結果數量
    """
    pass
```

**簡短函數的文檔**
```python
def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """取得用戶 (按 ID)."""
    return db.query(User).filter(User.id == user_id).first()
```

### 錯誤處理

**異常處理**
```python
import logging

logger = logging.getLogger(__name__)

def collect_data() -> bool:
    """收集股票數據 - 包含重試邏輯."""
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            # 執行操作
            result = finmind_collector.fetch_stocks()
            return True

        except ConnectionError as e:
            retry_count += 1
            logger.warning(f"連接失敗 (嘗試 {retry_count}/{max_retries}): {e}")

            if retry_count >= max_retries:
                logger.error(f"無法連接 FinMind API: {e}")
                return False

        except Exception as e:
            logger.error(f"未預期的錯誤: {e}", exc_info=True)
            raise

    return False
```

### 日誌記錄

**日誌層級**
```python
import logging

logger = logging.getLogger(__name__)

# 日常操作
logger.info("篩選開始: 候選股票 50 筆")

# 警告情況
logger.warning(f"股票 {stock_id} 無數據: 跳過")

# 錯誤情況
logger.error(f"資料庫連接失敗: {error}")

# 除錯信息
logger.debug(f"評分計算: chip={chip}, fund={fund}, tech={tech}")
```

### 測試規範

**測試命名**
```python
# tests/test_auth_service.py

def test_hash_password_creates_valid_hash():
    """測試密碼雜湊生成."""
    password = "secure_password"
    hashed = AuthService.hash_password(password)
    assert hashed != password
    assert AuthService.verify_password(password, hashed)

def test_hash_password_rejects_wrong_password():
    """測試錯誤密碼驗證失敗."""
    password = "correct_password"
    wrong = "wrong_password"
    hashed = AuthService.hash_password(password)
    assert not AuthService.verify_password(wrong, hashed)
```

**測試結構**
```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_db():
    """提供模擬資料庫."""
    return Mock()

class TestAuthService:
    """認證服務測試套件."""

    def test_create_token(self):
        """測試令牌生成."""
        pass

    def test_verify_expired_token(self):
        """測試過期令牌驗證失敗."""
        pass
```

## TypeScript/Vue 前端編碼規範

### 檔案與目錄結構

**目錄命名**
```typescript
src/
├── views/               # 頁面視圖
├── components/          # 可重用元件
├── stores/              # Pinia 狀態存儲
├── api/                 # API 呼叫
├── types/               # 型別定義
└── assets/              # 靜態資源
```

**檔案命名**
```typescript
// Vue 元件: kebab-case
auth-form.vue            // ✅
login-view.vue           // ✅
stock-ranking-table.vue  // ✅

// TypeScript 檔案: kebab-case
auth-store.ts            // ✅
screening-api.ts         // ✅
stock.ts (types)         // ✅

// ❌ 不要用 PascalCase (Vue 3 慣例)
AuthForm.vue             // ❌
```

### 類別與函數命名

**類別與介面**
```typescript
// PascalCase
interface User {
    id: number
    email: string
    password: string
}

class AuthStore {
    user: User | null = null
}

enum ScreeningStatus {
    Pending = 'pending',
    Running = 'running',
    Completed = 'completed'
}
```

**函數與變數**
```typescript
// camelCase
function getCurrentUser(): User | null {
    return authStore.user
}

const screeningResults: ScreeningResult[] = []

const calculateScore = (chip: number, fund: number, tech: number): number => {
    return chip * 0.4 + fund * 0.35 + tech * 0.25
}

// 私有函數用下劃線前綴
const _processData = (raw: any[]): any[] => {
    return raw.map(item => ({ ...item }))
}
```

**常數**
```typescript
// UPPER_SNAKE_CASE
const MAX_RETRY_ATTEMPTS = 3
const API_BASE_URL = 'http://localhost:8000/api'
const DEFAULT_WEIGHT_CHIP = 40
```

### 型別註解

**必須使用型別**
```typescript
// ✅ 正確: 參數和返回型別都有註解
function getStockById(id: string): Promise<Stock | null> {
    return api.get(`/stocks/${id}`)
}

const calculateScore = (
    chipScore: number,
    fundamentalScore: number,
    technicalScore: number
): number => {
    return chipScore * 0.4 + fundamentalScore * 0.35 + technicalScore * 0.25
}

// ❌ 錯誤: 缺少型別
function getStockById(id) {
    return api.get(`/stocks/${id}`)
}
```

**複雜型別**
```typescript
// Union
type ScoreType = 'chip' | 'fundamental' | 'technical'

// Optional
function getUserProfile(userId: number): Promise<UserProfile | undefined> {
    pass
}

// Generic
interface ApiResponse<T> {
    data: T
    message: string
    success: boolean
}

// Tuple
const coordinates: [number, number] = [25.0, 121.5]
```

### Vue 3 元件規範

**元件結構**
```vue
<template>
  <!-- 簡潔模板 -->
  <div class="stock-table">
    <table>
      <thead>
        <tr>
          <th>股號</th>
          <th>評分</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in stocks" :key="item.id">
          <td>{{ item.stockId }}</td>
          <td>{{ item.score }}</td>
          <td>
            <button @click="viewDetails(item.id)">詳情</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useStockStore } from '@/stores/stock-store'
import type { Stock } from '@/types/stock'

// 定義 Props
interface Props {
  limit?: number
  sortBy?: 'score' | 'name'
}

const props = withDefaults(defineProps<Props>(), {
  limit: 20,
  sortBy: 'score'
})

// Emit 事件
const emit = defineEmits<{
  select: [stock: Stock]
  refresh: []
}>()

// 狀態
const stocks = ref<Stock[]>([])
const loading = ref(false)

// Store
const stockStore = useStockStore()

// 計算屬性
const sortedStocks = computed(() => {
  return [...stocks.value].sort((a, b) => {
    if (props.sortBy === 'score') {
      return b.score - a.score
    }
    return a.name.localeCompare(b.name)
  })
})

// 方法
const viewDetails = (stockId: string) => {
  emit('select', stocks.value.find(s => s.id === stockId)!)
}

const refreshData = async () => {
  loading.value = true
  try {
    stocks.value = await stockStore.fetchStocks()
    emit('refresh')
  } finally {
    loading.value = false
  }
}

// 生命週期
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.stock-table {
  padding: 1rem;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

th {
  background-color: #f3f4f6;
  font-weight: 600;
}

button {
  padding: 0.5rem 1rem;
  background-color: #e5a91a;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
}

button:hover {
  background-color: #d4961a;
}
</style>
```

### Pinia Store 規範

```typescript
// src/stores/screening-store.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as screeningApi from '@/api/screening-api'
import type { ScreeningParams, ScreeningResult } from '@/types/screening'

export const useScreeningStore = defineStore('screening', () => {
  // 狀態
  const weights = ref({
    chip: 40,
    fundamental: 35,
    technical: 25
  })

  const filters = ref<Record<string, any>>({})
  const results = ref<ScreeningResult[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // 計算屬性
  const resultCount = computed(() => results.value.length)

  const topResults = computed(() => {
    return results.value.slice(0, 10)
  })

  // 方法
  const updateWeights = (newWeights: typeof weights.value) => {
    // 驗證: 權重總和 = 100
    const total = Object.values(newWeights).reduce((a, b) => a + b, 0)
    if (total !== 100) {
      throw new Error('權重總和必須等於 100')
    }
    weights.value = newWeights
  }

  const updateFilters = (newFilters: Record<string, any>) => {
    filters.value = newFilters
  }

  const runScreening = async () => {
    isLoading.value = true
    error.value = null

    try {
      const params: ScreeningParams = {
        weights: weights.value,
        filters: filters.value
      }

      const data = await screeningApi.runScreening(params)
      results.value = data
    } catch (e) {
      error.value = e instanceof Error ? e.message : '篩選失敗'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  const reset = () => {
    weights.value = { chip: 40, fundamental: 35, technical: 25 }
    filters.value = {}
    results.value = []
    error.value = null
  }

  return {
    weights,
    filters,
    results,
    isLoading,
    error,
    resultCount,
    topResults,
    updateWeights,
    updateFilters,
    runScreening,
    reset
  }
})
```

### API 呼叫規範

```typescript
// src/api/screening-api.ts
import api from './client'
import type { ScreeningParams, ScreeningResult } from '@/types/screening'

/**
 * 執行標準篩選
 */
export const runScreening = async (
  params: ScreeningParams
): Promise<ScreeningResult[]> => {
  const response = await api.post('/screening/run', params)
  return response.data
}

/**
 * 獲取篩選結果
 */
export const getResults = async (
  limit: number = 20,
  offset: number = 0
): Promise<ScreeningResult[]> => {
  const response = await api.get('/screening/results', {
    params: { limit, offset }
  })
  return response.data
}

/**
 * 更新權重設定
 */
export const updateWeights = async (
  weights: { chip: number; fundamental: number; technical: number }
): Promise<void> => {
  await api.put('/screening/weights', weights)
}
```

## 通用編碼原則

### DRY (Don't Repeat Yourself)

**❌ 不好: 重複的代碼**
```python
def get_stock_by_id(db: Session, stock_id: str) -> Stock:
    return db.query(Stock).filter(Stock.stock_id == stock_id).first()

def get_news_by_id(db: Session, news_id: str) -> News:
    return db.query(News).filter(News.id == str(news_id)).first()
```

**✅ 好: 提取共通方法**
```python
def get_by_id(db: Session, model, record_id):
    """通用查詢方法."""
    return db.query(model).filter(model.id == record_id).first()

# 使用
stock = get_by_id(db, Stock, stock_id)
news = get_by_id(db, News, news_id)
```

### KISS (Keep It Simple, Stupid)

**❌ 複雜的邏輯**
```python
score = (chip_scores[i] * weights['chip'] +
         fund_scores[i] * weights['fundamental'] +
         tech_scores[i] * weights['technical']) / \
        (weights['chip'] + weights['fundamental'] + weights['technical'])
```

**✅ 簡潔清楚**
```python
def calculate_composite_score(
    chip: float,
    fundamental: float,
    technical: float
) -> float:
    """計算綜合評分 (40:35:25)."""
    return chip * 0.4 + fundamental * 0.35 + technical * 0.25
```

### YAGNI (You Aren't Gonna Need It)

不要預先實現可能需要但現在不確定的功能。

**✅ 只實現目前需要的功能**
```python
# 現在實現基本篩選
def filter_stocks(db: Session) -> list:
    return db.query(Stock).filter(Stock.volume > 10000000).all()

# 未來需要時再加入複雜篩選
# def filter_stocks_advanced(db, criteria):
#     ...
```

## 代碼審查清單

- [ ] 所有函數都有型別提示
- [ ] 所有公共類別/函數都有文檔
- [ ] 變數命名清晰易懂
- [ ] 無硬編碼的魔術數字 (用常數替代)
- [ ] 適當的錯誤處理與日誌
- [ ] 測試覆蓋核心邏輯
- [ ] 沒有重複代碼
- [ ] 函數長度合理 (< 50 行)
- [ ] 複雜度適中 (圈複雜度 < 10)
- [ ] 依賴注入而非全局狀態

## 性能考慮

### Python 後端
- 使用 SQLAlchemy 的延遲載入避免 N+1 查詢
- 在評分計算中使用快取結果
- 非同步任務用 APScheduler 而非同步阻塞

### Vue 前端
- 使用 v-if 而非 v-show (大批量)
- 列表項都有唯一的 :key
- 複雜計算使用 computed 而非 watch
- 使用 lazy-load 大型清單

---

**最後更新**: 2026-02-22
**版本**: 1.1

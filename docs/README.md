# 📚 台灣股市多因子篩選平台 - 文檔中心

**最後更新**: 2026-02-22
**版本**: 1.4
**狀態**: ✅ 完整且投入生產

---

## 🗺️ 快速導航

本文檔套件共 6 份文檔，組織如下：

### 📖 入門文檔 (20 分鐘)

**[project-overview-pdr.md](./project-overview-pdr.md)** - 專案概述與需求定義
- 📋 專案簡介與核心價值
- 🛠️ 完整技術棧
- 📦 8 大功能模組
- 🔗 30+ API 端點表
- ⚙️ 25 個後端服務
- 📝 功能與非功能需求
- 🎯 **適合**: 新開發者、項目經理、業務分析師
- ⏱️ **時間**: 20 分鐘

### 🏗️ 架構文檔 (30 分鐘)

**[system-architecture.md](./system-architecture.md)** - 系統架構與設計
- 🏛️ 5 層架構圖
- 🔧 後端模組深度分解
- 🖥️ 前端結構詳解
- 🔄 完整數據流圖
- 🚀 部署架構 (開發/生產)
- 🛡️ 錯誤處理、安全、性能策略
- 🎯 **適合**: 架構師、資深開發者、系統設計師
- ⏱️ **時間**: 30 分鐘

### 🗂️ 代碼摘要 (25 分鐘)

**[codebase-summary.md](./codebase-summary.md)** - 完整代碼庫導航
- 🌳 150+ 個檔案的邏輯結構樹
- 🗄️ 14 個 ORM 模型說明
- ⚙️ 25 個業務邏輯服務
- 🔌 13 個 API 路由器
- 🖼️ 13 個前端視圖與 22 個元件
- 📊 數據庫模型關係圖
- 🧭 快速導航與部署清單
- 🎯 **適合**: 開發者、維護工程師、新團隊成員
- ⏱️ **時間**: 25 分鐘

### 📏 編碼規範 (40 分鐘)

**[code-standards.md](./code-standards.md)** - 開發標準與最佳實踐
- 🐍 Python 後端規範 (命名、型別、文檔、測試)
- 🟦 TypeScript/Vue 前端規範
- 💡 50+ 完整代碼範例
- ♻️ DRY、KISS、YAGNI 原則
- ✅ 代碼審查清單
- ⚡ 性能最佳化建議
- 🎯 **適合**: 所有開發者、代碼審查員、技術領導
- ⏱️ **時間**: 40 分鐘

### 🎮 操作指南 (15 分鐘)

**[operation-guide.md](./operation-guide.md)** - 系統操作與維運指南
- ⏰ 每日 Pipeline 自動執行流程
- 👤 會員系統操作（Free / Premium）
- 📈 右側買法篩選與進階條件
- 🤖 AI 報告生成與配額管理
- 🎯 **適合**: 使用者、維運人員、產品經理
- ⏱️ **時間**: 15 分鐘

### 📍 本文檔 (5 分鐘)

**README.md** - 文檔導航中心 (您現在閱讀的文件)
- 🗺️ 快速導航與文檔用途
- ❓ 常見問題與答案
- 🔄 開發流程指南
- 🛠️ 維護與更新計畫

---

## 🚀 開發工作流程

### 👋 新開發者入門 (1 小時)

1. 📖 **讀入門文檔** (20 分)
   ```
   project-overview-pdr.md (完整閱讀)
   ```

2. 🗂️ **掃代碼庫結構** (15 分)
   ```
   codebase-summary.md → 目錄樹部分
   ```

3. 📏 **了解編碼標準** (20 分)
   ```
   code-standards.md → Python/TypeScript 部分
   ```

4. 💻 **本地環境啟動** (20 分)
   ```bash
   # 後端
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload

   # 前端 (新終端機)
   cd frontend
   npm install
   npm run dev
   ```

### 🔄 功能開發循環

1. 📝 **理解需求**
   ```
   project-overview-pdr.md → 查詢相關需求與 API 端點
   ```

2. 🏗️ **設計方案**
   ```
   system-architecture.md → 參考架構模式
   codebase-summary.md → 查看相似功能實現
   ```

3. 💻 **編碼實現**
   ```
   code-standards.md → 遵循規範
   codebase-summary.md → 參考檔案位置與結構
   ```

4. 🧪 **測試驗證**
   ```
   執行: pytest 或 npm test
   確保測試通過
   ```

5. 🔍 **代碼審查**
   ```
   code-standards.md → 審查清單
   system-architecture.md → 架構一致性檢查
   ```

### 🧠 架構理解 (2 小時)

**目標**: 深度理解系統設計

1. 📖 **閱讀架構文檔** (45 分)
   ```
   system-architecture.md (完整閱讀)
   重點: 架構圖、數據流、模組分解
   ```

2. 🔍 **追蹤一個流程** (45 分)
   ```
   選擇: 篩選流程

   system-architecture.md → 篩選流程圖
   project-overview-pdr.md → API 端點 (/api/screening/*)
   codebase-summary.md → 服務層 (ScoringEngine, ChipScorer 等)

   檢視實際代碼檔案:
   - app/routers/screening.py
   - app/services/scoring_engine.py
   - app/services/chip_scorer.py
   ```

3. ✅ **驗證理解** (20 分)
   ```
   繪製架構圖或寫下流程說明
   與實際代碼對比
   ```

### 🔧 問題排查

🔌 **我想新增一個 API 端點**
```
1. project-overview-pdr.md → API 端點表 (參考現有結構)
2. system-architecture.md → 路由層說明
3. codebase-summary.md → 快速導航 (新增 API 端點的步驟)
4. code-standards.md → Python 規範
```

🎨 **代碼風格問題**
```
1. code-standards.md → 查詢相關規範
2. 查看實際代碼檔案的範例
3. 使用 Ruff (Python) 或 Prettier (TS) 自動修復
```

🏗️ **架構問題**
```
1. system-architecture.md → 查詢模組關係
2. codebase-summary.md → 查看模組實現細節
3. 查看對應的代碼檔案
4. 必要時與技術領導討論
```

🔗 **API 相關問題**
```
1. project-overview-pdr.md → API 端點表 (功能與路徑)
2. system-architecture.md → 錯誤處理策略
3. codebase-summary.md → API 模組組織
4. 實際代碼檔案 (app/routers/)
```

---

## ❓ 常見問題 (FAQ)

### Q1: 我應該從哪份文檔開始?

**A**: 根據您的角色:
- 👨‍💻 **新開發者** → `project-overview-pdr.md` (30 分) + `code-standards.md` (20 分)
- 🏗️ **架構師** → `system-architecture.md` (45 分) + `project-overview-pdr.md` (15 分)
- 🔧 **維護工程師** → `codebase-summary.md` (30 分) + `code-standards.md` (20 分)
- 📊 **項目經理** → `project-overview-pdr.md` (30 分)

### Q2: 文檔多久更新一次?

**A**:
- ⚡ **自動觸發**: 功能新增、架構變更、規範更新時立即更新
- 📅 **定期審查**: 每月一次檢查與同步
- 🏷️ **版本更新**: 關鍵更新標記版本號

### Q3: 我找不到我要找的資訊怎麼辦?

**A**: 按照優先順序:
1. 🔍 使用 Ctrl+F 搜尋當前文檔
2. 📄 檢查其他相關文檔
3. 💻 查看實際代碼檔案
4. 💬 詢問技術領導或同事

### Q4: 文檔中的代碼範例是否最新?

**A**:
- ✅ 大部分範例取自實際代碼
- ⚠️ 某些簡化例子為了清晰性
- 🔄 隨著代碼演進定期檢查

### Q5: 如何報告文檔問題?

**A**:
1. 📋 在相關文檔提出 Issue
2. 📍 提供具體位置與問題描述
3. 💡 建議改進方案
4. ⏰ 文檔維護者會在 1 週內回應

### Q6: 新功能應該如何文檔化?

**A**:
1. 📝 **實裝前** → 更新 `project-overview-pdr.md` (需求與 API)
2. 💻 **實裝中** → 遵循 `code-standards.md`
3. 📦 **實裝後** → 更新 `codebase-summary.md` (代碼結構) + `system-architecture.md` (架構變更)

---

## 📁 文檔結構

```
docs/
├── 📍 README.md                    # 本文檔 (文檔中心導航)
├── 📖 project-overview-pdr.md      # 專案概述與 PDR (需求定義)
├── 🏗️ system-architecture.md       # 系統架構與設計
├── 🗂️ codebase-summary.md          # 代碼庫摘要 (快速查詢)
├── 📏 code-standards.md            # 編碼規範與標準
└── 🎮 operation-guide.md           # 系統操作與維運指南
```

### 🔗 文檔依賴關係

```
┌─────────────────────────────────────────┐
│  📖 project-overview-pdr.md            │
│   (專案概述、需求、API 端點表)         │
└──────────────────┬──────────────────────┘
                   │
         ┌─────────┼─────────┐
         │         │         │
         v         v         v
┌──────────────┐  │  ┌──────────────────┐
│🏗️ system-arch│  │  │🗂️ codebase-summ │
│ (架構設計)   │  │  │ (代碼查詢)       │
└──────────────┘  │  └──────────────────┘
         │        │         │
         └────┬───┘         │
              v             v
        ┌──────────────────────────┐
        │  📏 code-standards.md    │
        │  (編碼規範 & 最佳實踐)  │
        └──────────────────────────┘
```

### 🧭 跨文檔導航

所有文檔都以相對連結互相參考:
```markdown
[參考 X 功能](./codebase-summary.md#x功能)
[查詢 API 設計](./project-overview-pdr.md#api端點總覽)
[遵循 Python 規範](./code-standards.md#python後端編碼規範)
```

---

## 🛠️ 維護與更新

### 📋 更新清單

新功能實裝時的更新檢查:

- [ ] 📖 `project-overview-pdr.md`
  - [ ] 功能模組表
  - [ ] API 端點表
  - [ ] 核心流程圖
  - [ ] 核心 PDR 需求

- [ ] 🏗️ `system-architecture.md`
  - [ ] 架構圖 (如有變更)
  - [ ] 相關模組說明
  - [ ] 數據流圖 (如有新流程)

- [ ] 🗂️ `codebase-summary.md`
  - [ ] 目錄樹
  - [ ] 核心模組說明
  - [ ] 新檔案位置

- [ ] 📏 `code-standards.md`
  - [ ] 新的編碼模式
  - [ ] 新的規範 (如有)

### 📜 版本歷史

| 版本 | 日期 | 變更 | 作者 |
|------|------|------|------|
| 1.4 | 2026-02-22 | 更新數量統計、新增 operation-guide 導航、右側買法進階篩選 | docs-manager |
| 1.3 | 2026-02-21 | 更新右側買法功能文檔（加權評分、批量篩選範圍、買賣點預測） | docs-manager |
| 1.2 | 2026-02-19 | 更新 AI 聊天助手功能文檔 | docs-manager |
| 1.1 | 2026-02-17 | 更新 UI 功能文檔（分頁排序、scroll-to-top、環境變數） | docs-manager |
| 1.0 | 2026-02-15 | 初始創建 (4 份文檔, 1100 行) | docs-manager |

### 🔮 下一步計畫

**短期** (1-2 週)
- [ ] 添加 Mermaid 流程圖
- [ ] 自動化 API 文檔生成
- [ ] 部署操作手冊

**中期** (1 個月)
- [ ] 故障排查指南
- [ ] 性能調優指南
- [ ] 架構決策記錄 (ADR)

**長期** (持續)
- [ ] 貢獻指南
- [ ] API 變更日誌
- [ ] 最佳實踐集合

---

## 📊 文檔品質指標

| 指標 | 目標 | 達成 | 狀態 |
|------|------|------|------|
| 📄 總文檔數 | 4+ | 5 | ✅ |
| 📝 總行數 | 1000+ | 1,500+ | ✅ |
| 💡 代碼範例 | 40+ | 50+ | ✅ |
| 🔗 內部連結 | 有效 | 有效 | ✅ |
| 🌐 語言 | 繁體中文 | 繁體中文 | ✅ |
| 📏 每檔大小 | < 800 行 | 275-520 行 | ✅ |
| 📊 圖表/表格 | 清晰 | 15+ | ✅ |
| 👁️ 可讀性 | 高 | 高 | ✅ |

---

## 🤝 貢獻指南

### 📝 文檔改進

如果您發現文檔問題或有改進建議:

1. 🐛 **報告問題**
   - 位置: 哪份文檔、第幾行
   - 問題: 清晰描述
   - 建議: 改進方案

2. 📤 **提交改進**
   - Fork 專案
   - 編輯相關文檔
   - 提交 PR 與詳細說明

3. 🔍 **審查流程**
   - 技術審查 (內容準確性)
   - 編輯審查 (語言與格式)
   - 合併與發布

### 📏 編碼規範貢獻

若要提議新的編碼規範:

1. 在 `code-standards.md` 中提出
2. 附上實際使用場景與代碼範例
3. 徵求團隊同意
4. 合併後更新所有相關檔案

---

## 🔗 相關資源

### 📂 內部
- [📁 專案根目錄](../)
- [🐍 後端代碼](../backend/app/)
- [🖥️ 前端代碼](../frontend/src/)
- [📋 測試報告](../plans/reports/)

### 🌐 外部
- [FastAPI 官方文檔](https://fastapi.tiangolo.com/)
- [Vue 3 官方文檔](https://vuejs.org/)
- [SQLAlchemy 官方文檔](https://docs.sqlalchemy.org/)
- [TypeScript 官方文檔](https://www.typescriptlang.org/)

---

## 💬 聯繫與支援

### 📮 文檔維護
- **責任人**: 技術領導 + 文檔管理員
- **聯繫方式**: 在 Issue 或 PR 中提出
- **回應時間**: 1-2 個工作天

### 🆘 技術支援
- **快速提問**: 團隊 Slack #tech-support
- **詳細問題**: GitHub Issues
- **架構討論**: 技術委員會會議

---

**文檔套件版本**: 1.4
**最後更新**: 2026-02-22
**下次審查**: 2026-03-22
**狀態**: ✅ 投入生產

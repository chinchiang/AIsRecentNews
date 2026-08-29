# AIsRecentNews — 全球 AI 模型與產業動態觀測 週報

每週一 08:00（Asia/Taipei）由排程任務自動執行，產出當期週報頁與追蹤標的快照。

## 結構

- `index.html`：期數清單入口頁（最新在最上方，內嵌 CSP）。
- `reports/YYYY-Www.html`：各期週報（單檔、內嵌 CSS、`zh-Hant`、無外部相依、內嵌 CSP）。
- `latest-snapshot.yaml`：本期追蹤標的快照，作為次期 Delta 比對基準。
- `prompts/aimodelwatch-prompt-claude.md`：週報產出之完整執行指令（Claude 適配版，含提示注入隔離與 XSS 防護規範）。
- `scripts/validate.py`：快照 Schema 與 HTML 安全合規自動化驗證工具（零依賴）。
- `.github/workflows/`：
  - `ci.yml`：PR / Push 時自動執行格式與安全檢核。
  - `weekly-watch.yml`：每週一定時排程與安全 Commit / Push 自動化管線。

## 品質與安全性驗證

在提交變更或產出新一期週報後，可隨時於本地端執行驗證腳本：

```bash
python scripts/validate.py
```

驗證範圍包含：
1. `latest-snapshot.yaml` 欄位合法性、Schema、列舉值（Track、Evidence、Status）與唯一性。
2. HTML 檔案之 UTF-8 編碼、CSP Meta 標籤宣告與 `zh-Hant` 語系設定。
3. 靜態頁面 XSS 防護檢查（防止惡意 `<script>`、`<iframe>`、`javascript:` 偽協定與 DOM 事件處理器）。

## 排程與執行流程

排程任務每次以全新 session 執行 `prompts/aimodelwatch-prompt-claude.md` 的全部步驟：

1. 以 bash 計算 ISO 週期數與觀測期間（上週一 08:00 → 本週一 07:59）。
2. 讀取本地或預設分支上的 `latest-snapshot.yaml` 作為 Delta 基準（若網路異常則啟動 Fail-Safe 機制保護歷史狀態）。
3. 執行 A（模型發布）/ B（AI 資安）/ C（企業供應條件）/ D（監理標準）四軌檢索與查證分級（外部內容依不可信資料隔離處理）。
4. 寫入 `reports/YYYY-Www.html`、更新 `latest-snapshot.yaml`、更新 `index.html`。
5. 執行 `python scripts/validate.py` 確保格式合規。
6. Commit：`chore(AIs): weekly AI model watch YYYY-Www`（使用專屬 bot 身分，避免暴露個人信箱與外部 Session）。

## 存取控制與機敏資訊安全

- **情報邊界**：本儲存庫若涉及企業內部採購策略、特定架構選型或內部評估，建議將儲存庫設為 Private，並透過企業內部驗證機制（如 GitHub Enterprise SSO）控管存取。
- **Commit 衛生**：排程與手動提交時，嚴禁在 Git Commit 訊息中暴露外部 AI 平台之互動對話連結（Session URLs）或個人私密信箱。


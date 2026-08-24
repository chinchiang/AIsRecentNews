# AIsRecentNews — 全球 AI 模型與產業動態觀測 週報

每週一 08:00（Asia/Taipei）由排程任務自動執行，產出當期週報頁與追蹤標的快照。

## 結構

- `index.html`：期數清單入口頁（最新在最上方）。
- `reports/YYYY-Www.html`：各期週報（單檔、內嵌 CSS、`zh-Hant`、無外部相依）。
- `latest-snapshot.yaml`：本期追蹤標的快照，作為次期 Delta 比對基準。
- `prompts/aimodelwatch-prompt-claude.md`：週報產出之完整執行指令（Claude 適配版）。

## 排程

排程任務每次以全新 session 執行 `prompts/aimodelwatch-prompt-claude.md` 的全部步驟：

1. 以 bash 計算 ISO 週期數與觀測期間（上週一 08:00 → 本週一 07:59）。
2. 讀取預設分支上的 `latest-snapshot.yaml` 作為 Delta 基準（不存在則產出基線建立版）。
3. 執行 A（模型發布）/ B（AI 資安）/ C（企業供應條件）/ D（監理標準）四軌檢索與查證分級。
4. 寫入 `reports/YYYY-Www.html`、覆蓋 `latest-snapshot.yaml`、更新 `index.html`。
5. Commit：`chore(AIs): weekly AI model watch YYYY-Www`。

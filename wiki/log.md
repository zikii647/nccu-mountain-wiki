# Wiki 維護日誌（Log）

依時間順序記錄每次初始化、分批匯入（Ingest）、健康檢查（Lint）與重要架構異動。

---

## [2026-11-22] ingest | 匯入「合歡東峰石門山（2025-09）」計畫書與出隊結算表

- **來源檔案（1 隊共 2 份）**：
  - `raw/09_19-20 合歡東峰石門山計劃書 ver.2.docx`
  - `raw/百年校慶行前合歡出隊結算表.xlsx`
- **新增／異動頁面**：
  - 新增 [trips/2025-09-hehuan-east-shimen.md](./trips/2025-09-hehuan-east-shimen.md)
  - 新增 [guides/trip-settlement-and-finance-sop.md](./guides/trip-settlement-and-finance-sop.md)（提煉社團出隊收費、兩週結算期限與罰則、對外活動分帳 SOP）
  - 更新 [lessons/gear-check-and-winter-warmth-pitfalls.md](./lessons/gear-check-and-winter-warmth-pitfalls.md)（補充 inReach 行前帳號與功能測試提醒）
  - 更新 [index.md](./index.md)
- **個資脫敏執行**：已全數移除 17 名隊員（含師長）、留守與司機之聯絡電話、緊急聯絡人姓名電話，以及結算表內之**山隊郵局匯款帳號**。
- **發現之高風險與異常提醒**：
  - **高風險**：inReach 因帳號問題未帶上山；計畫書無公裝與無線電配置、將頭燈與低音哨標為彈性（`△`）；行前會改用 PPT 取代；留守範例殘留「奇萊」且無逾時通報死線。
  - **文件異常與缺漏**：計畫書內嚮導聯絡電話前後頁不一致；安全委員意見與參考紀錄留白；D1 石門山拍攝 0.5hr 後未計入下山步程；缺實際行走紀錄與檢討報告；結算表更新日（2025/11/02）逾下山後兩週期限。

---

## [2026-11-22] lint | 首輪全站健康檢查與流程更新（納入每批 Commit＋Lint）

- **規則更新**：更新 [AGENTS.md](../AGENTS.md)（4,565 字元，合於 12,000 字元上限），明定每批 Ingest 完成後自動執行 Lint 並建立 Git Commit。
- **Lint 檢查結果（掃描 14 份檔案）**：
  - 個資殘留掃描：**0 筆**（通過）
  - 失效相對連結 / 孤兒頁面 / 缺漏雙向反連：**0 / 0 / 0**（通過）
  - YAML frontmatter 與來源標註：全數通過
  - `raw/` 盤點：總計 21 份，已匯入 **11 份**（大霸群峰 3、領隊實務 1、武陵四秀 7），待匯入 **10 份**。

---

## [2026-11-22] ingest | 匯入「武陵四秀（2024-12）」隊伍檔案

- **來源檔案（1 隊共 7 份）**：
  - `raw/12_14-15 武陵四秀/武陵秀秀秀秀計劃書.docx`
  - `raw/12_14-15 武陵四秀/武陵四秀紀錄.docx`
  - `raw/12_14-15 武陵四秀/檢討--武陵四秀.docx`
  - `raw/12_14-15 武陵四秀/武陵四秀秀秀菜單.xlsx`
  - `raw/12_14-15 武陵四秀/2024-11-23～25武陵四秀.gpx`（他隊 11 月參考軌跡，已摘要總距與海拔範圍）
  - `raw/12_14-15 武陵四秀/武陵秀秀秀秀.pdf`、`武陵秀秀秀秀有路線！.pdf`（魯地圖與手繪路線圖，已摘要未抽圖）
- **新增／異動頁面**：
  - 新增 [trips/2024-12-wuling-four-peaks.md](./trips/2024-12-wuling-four-peaks.md)
  - 更新 [lessons/schedule-and-night-hiking-pitfalls.md](./lessons/schedule-and-night-hiking-pitfalls.md)（補充壓縮行程與重裝配速過快案例）
  - 更新 [lessons/gear-check-and-winter-warmth-pitfalls.md](./lessons/gear-check-and-winter-warmth-pitfalls.md)（補充連續兩年未裝檢、未帶正規擋風板與桃山營地未打好營釘吹破帳篷案例）
  - 更新 [lessons/food-and-menu-pitfalls.md](./lessons/food-and-menu-pitfalls.md)（補充壓縮行程炊煮過久與遺留高麗菜於山屋 LNT 教訓）
  - 更新 [lessons/retreat-and-navigation-emergency-pitfalls.md](./lessons/retreat-and-navigation-emergency-pitfalls.md)（補充過遲服丹木斯、身體不適未即時報備與 D2 果斷安全撤退案例）
  - 更新 [index.md](./index.md)
- **個資脫敏執行**：已全數移除隊員／留守／交通之手機號碼與學號，僅保留姓名與社團角色。
- **發現之高風險與異常提醒**：
  - **高風險**：壓縮四秀為 2 天 1 夜負荷過重、重裝衝太快（上河 0.7）致後半程透支；未做行前裝檢（與隔年大霸群峰重複踩坑）；桃山營地未打好營釘吹破帳篷、漏帶擋風板拉長炊煮；計畫書缺預備天／預備糧、缺品田 V 斷頭盔與確保規劃、留守表與行程表時間差 30 分鐘且無回報死線。
  - **異常提醒**：`檢討--武陵四秀.docx` 頁首學期誤植為 `112-2`（對照 2024.12.15 應為 `113-1`）；GPX 為 2024/11/23–25 他隊參考軌跡而非本隊實走；`武陵四秀秀秀菜單.xlsx` 採買表漏列 D2 早餐與部分 D1 食材，並含南湖範例分頁；無全隊結算表。

---

## [2026-11-22] ingest | 匯入「登山計畫與領隊實務（子豪學長）」建立社團基準

- **來源檔案（1 份共 31 頁簡報）**：
  - `raw/登山計畫與領隊實務（子豪學長）.pdf_`（2023/05/10 政大登山隊高嚮訓練課，講者：黃子豪）
- **新增／異動頁面**：
  - 新增 [guides/mountain-safety-fundamentals.md](./guides/mountain-safety-fundamentals.md)
  - 新增 [guides/trip-planning-sop.md](./guides/trip-planning-sop.md)
  - 新增 [guides/club-leadership-and-team-management.md](./guides/club-leadership-and-team-management.md)
  - 新增 [lessons/retreat-and-navigation-emergency-pitfalls.md](./lessons/retreat-and-navigation-emergency-pitfalls.md)
  - 更新 [templates/safety-audit-checklist.md](./templates/safety-audit-checklist.md)（整合社團分級、新舊比、逐日撤退、公私水與保暖裝檢基準）
  - 更新 [trips/2025-12-daba-four-peaks.md](./trips/2025-12-daba-four-peaks.md)（補上對照社團領隊實務基準之交叉檢核）
  - 更新 [index.md](./index.md)
- **個資脫敏執行**：本簡報僅含講者姓名與公開文史書單，無敏感個資。
- **異常與備註提醒**：
  - `raw/登山計畫與領隊實務（子豪學長）.pdf_` 副檔名多了一個底線 `_`（已直接以 PDF 解析，未更動 `raw/` 原檔；如欲更名為 `.pdf` 建議由使用者確認後處理）。
  - 原始簡報 P.24 與 P.25「隊伍管理」頁面內容完全重複。
  - 講義提及之生火、迷途留痕與丹木斯／類固醇用藥，已於頁面加上 AI 安全提醒區隔法規（國家公園／林班地禁火、LNT）與處方醫囑原則。

---

## [2026-11-22] ingest | 匯入「大霸群峰（2025-12）」隊伍檔案

- **來源檔案（1 隊共 3 份）**：
  - `raw/大霸群峰登山計畫書.docx`
  - `raw/檢討--大霸群峰.docx`
  - `raw/大霸群峰菜單.xlsx`
- **新增／異動頁面**：
  - 新增 [trips/2025-12-daba-four-peaks.md](./trips/2025-12-daba-four-peaks.md)
  - 新增 [lessons/schedule-and-night-hiking-pitfalls.md](./lessons/schedule-and-night-hiking-pitfalls.md)
  - 新增 [lessons/gear-check-and-winter-warmth-pitfalls.md](./lessons/gear-check-and-winter-warmth-pitfalls.md)
  - 新增 [lessons/food-and-menu-pitfalls.md](./lessons/food-and-menu-pitfalls.md)
  - 更新 [index.md](./index.md)
- **個資脫敏執行**：已全數移除隊員／留守人／包車司機之電話、學號、緊急聯絡人姓名與電話、車牌號碼及信箱，僅保留隊員姓名／暱稱與社團角色。
- **發現之高風險與異常提醒**：
  - **高風險**：D1 計畫時間低估（誤參考騎車／單人快腳紀錄且未採納安委拉長時間建議）導致冬季摸黑、晚餐延至 20:00、新進隊員輕微失溫及高反；期末考未執行裝檢導致未核對保暖層及漏帶爐頭；計畫書缺預備糧、冬季裝備表漏勾毛帽／保暖手套、未明列隊內無線電頻率與備用電池。
  - **缺漏檔案**：本次無大霸實際逐點紀錄檔與全隊結算表。
  - **異常分頁**：`raw/大霸群峰菜單.xlsx` 中「第二組採買清單」疑似殘留舊隊伍資料（與第二組菜單不符）；另有南湖群峰 `（example)菜單` 與 `(Example)採買清單` 範例分頁，已於頁面明確區隔避免誤用。

---

## [2026-11-22] init | 初始化登山計劃書 LLM Wiki 骨架

- **建立檔案**：
  - `AGENTS.md`（核心定位、個資脫敏、出處細度、跨年份矛盾處理、安全把關與 Ingest/Query/Lint 工作流）
  - `.gitignore`（排除 `raw/` 以保護含個資原始檔）
  - `wiki/index.md`、`wiki/log.md`
  - `wiki/templates/safety-audit-checklist.md`、`wiki/templates/page-templates.md`
  - 資料夾骨架：`wiki/trips/`、`wiki/guides/`、`wiki/lessons/`、`wiki/templates/`
- **目前 `raw/` 待匯入盤點（未執行 Ingest，待使用者確認架構後分批處理）**：
  - 隊伍資料：武陵四秀（資料夾含計畫書、紀錄、檢討、菜單、PDF、GPX）、大霸群峰（計畫書、菜單、檢討）、合歡東峰石門山（計畫書＋百年校慶行前合歡出隊結算表）、湖湖哈哈（計畫書兩版、菜單、體訓）、辣辣辣辣（計畫書、菜單）、白姑大山（檢討）、馬比杉線（紀錄）
  - 領隊實務：`登山計畫與領隊實務（子豪學長）.pdf_`
- **異常檔待確認提醒**：
  - `raw/湖湖哈哈計劃書.docx` 與 `raw/湖湖哈哈計劃書(1).docx` 為疑似重複／不同版本，待匯入該隊時比對確認。
  - `raw/登山計畫與領隊實務（子豪學長）.pdf_` 副檔名多了一個底線 `_`，待匯入時向使用者確認是否更名或直接解析。

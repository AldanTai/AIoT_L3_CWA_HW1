# Taiwan Weather Forecast 開發流程

本文件將專案拆分為可逐步完成與驗證的工作階段。建議每完成一個階段就進行測試並建立 Git commit。

## 整體資料流程

```text
CWA Open Data API
        │
        ▼
  Requests 取得 JSON
        │
        ▼
  解析、清理與驗證資料
        │
        ▼
  SQLite 儲存氣溫預報
        │
        ▼
  Pandas 查詢與整理
        │
        ├──────────────┐
        ▼              ▼
Streamlit 圖表     Folium 台灣地圖
        └──────┬───────┘
               ▼
       互動式天氣儀表板
```

## 階段一：建立專案環境

1. 建立 Python 虛擬環境。
2. 安裝必要套件：

   ```bash
   pip install requests pandas streamlit folium streamlit-folium
   ```

3. 建立 `requirements.txt`：

   ```bash
   pip freeze > requirements.txt
   ```

4. 建立 `.gitignore`，至少排除：

   ```gitignore
   .venv/
   __pycache__/
   *.py[cod]
   .streamlit/secrets.toml
   .env
   data.db
   ```

驗收條件：Python 可正常匯入所有套件，且密鑰與本機資料庫不會被 Git 追蹤。

## 階段二：取得 CWA API 資料

1. 至中央氣象署開放資料平台註冊帳號。
2. 取得 API 授權碼。
3. 選擇所需的天氣預報資料集。
4. 使用 `requests.get()` 呼叫 API，設定合理的逾時時間。
5. 使用 `response.raise_for_status()` 檢查 HTTP 狀態。
6. 使用 `response.json()` 將回應轉為 Python 物件。

建議檢查：

- HTTP 狀態是否成功。
- API 回應中的 `success` 是否為 `true`。
- `records`、地區及天氣元素欄位是否存在。
- 無網路、錯誤 API Key、逾時或資料格式異常時，是否顯示清楚訊息。

驗收條件：程式可成功取得並印出至少一個地區的原始 JSON 天氣資料。

## 階段三：解析與整理 JSON

1. 找出地區清單所在位置。
2. 從每個地區擷取 `MinT` 與 `MaxT`。
3. 將開始時間或預報日期統一轉為日期格式。
4. 將溫度字串轉為數值型別。
5. 整理為一致的紀錄格式：

   ```python
   {
       "regionName": "中部地區",
       "dataDate": "2026-04-14",
       "mint": 20.0,
       "maxt": 30.0,
   }
   ```

6. 轉為 Pandas DataFrame 並檢查：

   - 欄位名稱是否一致。
   - 日期是否可排序。
   - 溫度是否為數值。
   - 是否存在空值或重複資料。

驗收條件：能產生包含 `regionName`、`dataDate`、`mint`、`maxt` 的乾淨 DataFrame。

## 階段四：建立 SQLite 資料庫

建議資料表：

```sql
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT NOT NULL,
    dataDate TEXT NOT NULL,
    mint REAL NOT NULL,
    maxt REAL NOT NULL,
    UNIQUE (regionName, dataDate)
);
```

寫入資料時可使用 UPSERT：

```sql
INSERT INTO TemperatureForecasts (regionName, dataDate, mint, maxt)
VALUES (?, ?, ?, ?)
ON CONFLICT(regionName, dataDate)
DO UPDATE SET
    mint = excluded.mint,
    maxt = excluded.maxt;
```

資料庫操作原則：

- 使用 `with sqlite3.connect(...) as conn` 自動管理交易。
- 使用 `?` 參數化查詢，不直接拼接使用者輸入。
- 批次寫入時優先使用 `executemany()`。
- 每次更新後驗證資料筆數與內容。

驗收條件：重複執行匯入流程不會產生重複紀錄，且查詢結果正確。

## 階段五：查詢與驗證資料

基本查詢：

```sql
SELECT regionName, dataDate, mint, maxt
FROM TemperatureForecasts
ORDER BY regionName, dataDate;
```

依地區查詢：

```sql
SELECT dataDate, mint, maxt
FROM TemperatureForecasts
WHERE regionName = ?
ORDER BY dataDate;
```

應驗證以下情境：

- 指定地區有資料。
- 指定地區沒有資料。
- 日期排序正確。
- `mint` 不高於 `maxt`。
- 相同地區與日期只有一筆紀錄。

## 階段六：建立 Streamlit 基本介面

1. 建立 `app.py`。
2. 設定頁面標題與版面配置。
3. 從 SQLite 載入可用地區。
4. 使用 `st.selectbox()` 建立地區下拉選單。
5. 依選取地區查詢 DataFrame。
6. 使用 `st.dataframe()` 顯示資料。
7. 無資料或發生錯誤時使用 `st.info()`、`st.warning()` 或 `st.error()` 提示。

驗收條件：執行 `streamlit run app.py` 後，可切換地區並看到對應資料表。

## 階段七：繪製氣溫折線圖

1. 將日期欄位轉成 `datetime`。
2. 依日期由舊到新排序。
3. 將日期設為圖表索引。
4. 同時顯示 `mint` 與 `maxt` 兩條線。
5. 清楚標示單位為攝氏溫度（°C）。

驗收條件：切換地區時，圖表與資料表同步更新，最高與最低溫圖例清楚可辨。

## 階段八：加入台灣地圖

1. 準備各地區代表點的經緯度對照表。
2. 使用 Folium 建立以台灣為中心的地圖。
3. 讓使用者選擇日期。
4. 查詢該日期各地區的溫度資料。
5. 使用 Marker、CircleMarker 或顏色分級呈現氣溫。
6. Popup 至少顯示地區、日期、最低溫與最高溫。
7. 使用 `streamlit-folium` 將地圖嵌入 Streamlit。

參考色階：

| 溫度 | 顏色 |
| --- | --- |
| 低於 20°C | 藍色 |
| 20–25°C | 綠色 |
| 25–30°C | 黃色或橘色 |
| 高於 30°C | 紅色 |

驗收條件：切換日期後，地圖標記及 Popup 資訊同步更新。

## 階段九：整合與品質優化

- 將 API、JSON 解析、資料庫與 UI 分離成模組。
- 將共用設定集中管理。
- 對 API 與資料庫操作加入例外處理。
- 使用 Streamlit cache 減少不必要的 API 與資料庫查詢。
- 顯示資料最後更新時間。
- 避免重複執行時重複寫入資料。
- 為核心解析與資料庫函式加入測試。
- 確認程式碼具有函式說明與必要註解。

建議最少測試項目：

1. 正常 JSON 可產生正確紀錄。
2. 缺少 `MinT` 或 `MaxT` 時不會造成未處理例外。
3. 重複資料可更新但不會新增第二筆。
4. SQL 查詢無法被地區輸入改變結構。
5. 空資料時 UI 仍能正常顯示提示。

## 階段十：GitHub 版本管理

建議依功能建立小型 commit：

```text
docs: add project README and workflow
feat: fetch forecast data from CWA API
feat: parse min and max temperature records
feat: persist forecasts in SQLite
feat: add Streamlit region dashboard
feat: add Folium weather map
test: cover parsing and database operations
```

提交前檢查：

```bash
git status
git diff
git add .
git commit -m "描述本次變更"
git push origin main
```

請再次確認 API Key、`.env`、`secrets.toml` 與本機敏感資料未被加入版本控制。

## 完成定義

專案完成時應符合以下條件：

- [x] 使用有效 API Key 完成 CWA 線上資料驗收。
- [x] 已實作 CWA API 請求與逾時、HTTP、JSON 錯誤處理。
- [x] 可正確解析最低與最高氣溫。
- [x] SQLite 表格與唯一限制建立完成。
- [x] 重複執行不會重複插入相同資料。
- [x] 可依地區查詢與切換資料。
- [x] 可顯示氣溫折線圖與資料表。
- [x] 可依日期顯示台灣天氣地圖。
- [x] API 或資料異常時有清楚提示。
- [x] API Key 未提交至 GitHub。
- [x] 文件與套件清單完整，可由他人重新安裝並啟動。
- [x] 單元測試與 Streamlit 啟動煙霧測試通過。

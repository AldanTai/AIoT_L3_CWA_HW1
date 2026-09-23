# Taiwan Weather Forecast

以中央氣象署（CWA）開放資料為來源的台灣天氣預報互動式 Web App。本專案將 CWA API 回傳的 JSON 氣溫預報資料整理後存入 SQLite，並透過 Streamlit、Pandas 與 Folium 呈現各地區的氣溫趨勢、資料表格及台灣地圖。

## 專案目標

- 練習呼叫中央氣象署 Open Data API。
- 理解並解析 JSON 巢狀資料。
- 使用 Pandas 清理與整理天氣資料。
- 使用 SQLite 建立、儲存及查詢氣溫預報。
- 使用 Streamlit 建立互動式資料儀表板。
- 使用 Folium 在台灣地圖上呈現天氣資訊。
- 熟悉 Git 與 GitHub 的版本管理流程。

## 預計功能

1. 從 CWA API 取得各地區天氣預報。
2. 擷取日期、最低氣溫與最高氣溫。
3. 將資料寫入 SQLite，避免重複新增相同紀錄。
4. 依地區查詢並顯示氣溫資料。
5. 使用下拉選單切換地區。
6. 繪製最低與最高氣溫折線圖。
7. 顯示整理後的天氣資料表。
8. 依日期在台灣地圖顯示各地區氣溫。

## 技術工具

- Python
- Requests
- JSON
- Pandas
- SQLite
- Streamlit
- Folium
- streamlit-folium
- Git / GitHub

## 資料來源

本專案使用[交通部中央氣象署開放資料平台](https://opendata.cwa.gov.tw/)提供的天氣預報資料。使用 API 前須先在平台註冊並取得授權碼（API Key）。

> 請勿將 API Key 直接寫入程式或提交到 GitHub。建議使用環境變數或 Streamlit Secrets 管理。

## 建議專案結構

```text
AIoT_L3_CWA_HW1/
├── app.py                  # Streamlit Web App 入口
├── fetch_weather.py        # CWA API 請求與 JSON 解析
├── database.py             # SQLite 建表、寫入與查詢
├── map_view.py             # Folium 台灣天氣地圖
├── data.db                 # 執行後產生的本機資料庫
├── requirements.txt        # Python 套件清單
├── .gitignore              # 排除密鑰、快取與資料庫
├── .streamlit/
│   ├── secrets.toml.example # API Key 範例
│   └── secrets.toml         # 本機 API Key（不可提交）
├── tests/                  # API、資料庫與地圖單元測試
├── README.md
└── workflow.md
```

## 資料庫設計

主要資料表 `TemperatureForecasts`：

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `id` | INTEGER | 主鍵，自動遞增 |
| `regionName` | TEXT | 地區名稱 |
| `dataDate` | TEXT | 預報日期 |
| `mint` | REAL | 最低氣溫（°C） |
| `maxt` | REAL | 最高氣溫（°C） |

建議對 `regionName` 與 `dataDate` 設定唯一限制，避免同一地區、同一日期被重複寫入。

## 安裝與執行

### 1. 建立虛擬環境

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. 安裝套件

```bash
pip install requests pandas streamlit folium streamlit-folium
```

若專案已提供 `requirements.txt`：

```bash
pip install -r requirements.txt
```

### 3. 設定 API Key

建立 `.streamlit/secrets.toml`：

```toml
CWA_API_KEY = "你的中央氣象署 API Key"
```

### 4. 啟動應用程式

```bash
streamlit run app.py
```

啟動後依終端機顯示的網址，在瀏覽器開啟天氣儀表板。

## 執行測試

```bash
python -m unittest discover -s tests -v
```

目前測試涵蓋 JSON 解析、異常溫度、空白 API Key、SQLite UPSERT、參數化查詢、資料庫限制與地圖產生。

## 畫面規劃

- 側邊欄：地區與日期選擇。
- 溫度折線圖：比較每日最低與最高氣溫。
- 資料表：顯示日期、最低氣溫與最高氣溫。
- 台灣地圖：以標記或顏色呈現不同地區的氣溫。
- 資料更新：重新向 CWA API 取得最新資料。

## 開發注意事項

- 對 API 逾時、連線失敗與異常回應加入錯誤處理。
- 解析 JSON 前先檢查欄位是否存在，避免格式變更造成程式中斷。
- 使用參數化 SQL，避免字串拼接 SQL 查詢。
- 寫入資料庫時使用唯一鍵或 UPSERT，避免重複紀錄。
- 將 API 呼叫、資料庫操作與 UI 分成不同模組，方便測試與維護。

## 開發流程

完整實作步驟與驗收方式請參考 [workflow.md](./workflow.md)。

## 授權與聲明

本專案作為 AI 創新微課程與程式學習用途。氣象資料的使用規範以中央氣象署開放資料平台公告為準。

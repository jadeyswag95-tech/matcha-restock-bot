# 丸久小山園抹茶補貨/降價/新品 LINE 通知機器人

每 30 分鐘檢查一次官網抹茶頁面，有新品上架、補貨、降價就推播到你的 LINE。
不需要付費主機、不用 AI，全部靠 GitHub Actions 免費排程執行。

## 你需要做的設定（約 15 分鐘）

### 1. 建立 LINE Official Account

1. 前往 https://developers.line.biz/console/ 用你的 LINE 帳號登入
2. 建立一個 Provider（隨意命名，例如「Jade Tools」）
3. 在該 Provider 下建立一個 **Messaging API** channel（Channel 名稱、圖示隨意）
4. 進入該 channel 的「Messaging API」分頁：
   - 找到 **Channel access token**，按「Issue」產生一組長效 token，複製起來
   - 找到頁面上的 **QR code**，用你手機的 LINE 掃描，加這個機器人為好友
     （廣播訊息只會送給好友，所以這一步一定要做）

### 2. 建立 GitHub repo

1. 如果還沒有 GitHub 帳號，先到 https://github.com/signup 註冊（免費）
2. 建立一個新 repo，例如取名 `matcha-restock-bot`
   - 建議設為 **Public**（內容不含個資，設 Public 才能用完全免費、不限額的 Actions 執行分鐘數；設 Private 也可以，免費額度是每月 2000 分鐘，這個排程一個月大約用 1400-1500 分鐘，也夠用但比較緊）
3. 把這個資料夾（`matcha-restock-bot`）的內容上傳到這個 repo（我可以幫你執行 git 指令，只是需要你先建好 repo 並提供網址）

### 3. 把 Channel Access Token 存進 GitHub Secrets

1. 進入你的 repo → Settings → Secrets and variables → Actions
2. 按「New repository secret」
3. Name 填 `LINE_CHANNEL_ACCESS_TOKEN`，Value 貼上第 1 步拿到的 token
4. 儲存

### 4. 手動觸發測試一次

1. 進入 repo 的 Actions 分頁 → 選「Check Matcha Restock」→「Run workflow」手動跑一次
2. 第一次執行因為沒有舊快照，理論上不會發通知（因為所有商品都是「第一次看到」，程式會直接記錄為基準，不會誤判成 48 個新品——這點我已經在程式邏輯裡處理過）
3. 之後排程就會照每 30 分鐘自動跑，有變化才會通知你

## 小提醒

- GitHub 有個機制：如果 repo **超過 60 天完全沒有任何 commit**，排程會被自動停用，需要手動去 Actions 頁面重新啟用。正常情況下不太會發生，但如果你發現機器人突然不通知了，先去 repo 的 Actions 分頁確認排程有沒有被停用。
- 想暫停通知，直接去 repo 的 Actions 分頁把 workflow 停用即可，不用刪 repo。
- 想改檢查頻率，改 `.github/workflows/check-matcha.yml` 裡的 `cron: "*/30 * * * *"`（目前是每 30 分鐘）。

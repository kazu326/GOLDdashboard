# 運用前チェックリスト

Phase 1 MVPをサロン運用前にリハーサルするための最終チェックです。新機能追加ではなく、Windowsローカルで安定して起動・更新・通知できることを確認します。

## 1. 前提確認

- [ ] PowerShellで `py --version` が Python 3.11以上を返す。
- [ ] `node --version` と `npm.cmd --version` が成功する。
- [ ] `C:\Users\kukyo\Documents\GOLDdashboard\backend\.venv\Scripts\python.exe` が存在する。
- [ ] backend tests が成功する。

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
.\.venv\Scripts\Activate.ps1
py -m pytest
```

期待結果:

```text
7 passed
```

## 2. Backend起動確認

標準ポート:

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
.\.venv\Scripts\Activate.ps1
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

確認URL:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/api/dashboard/current`

PowerShell確認:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/docs
Invoke-RestMethod http://127.0.0.1:8000/api/dashboard/current
```

確認項目:

- [ ] `/health` が `200`。
- [ ] `/docs` が表示できる。
- [ ] `/api/dashboard/current` がJSONを返す。
- [ ] 無料データ取得に失敗しても `unknown` / `要確認` が返り、500で落ちない。

## 3. 代替ポート利用時

8000番が使用中の場合:

```powershell
netstat -ano | findstr :8000
taskkill /PID <表示されたPID> /F
```

停止できない場合は、Backendを代替ポートで起動します。

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
.\.venv\Scripts\Activate.ps1
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

代替ポートを使う場合は、`frontend\.env.local` も同じポートへ変更します。

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8010
```

注意:

- [ ] `.env.local` を変更した後は、Next.js dev serverを再起動する。
- [ ] API確認URLも `8000` ではなく `8010` に置き換える。
- [ ] `DASHBOARD_PUBLIC_URL` はフロントのURLなので、通常は `http://localhost:3000` のままでよい。

## 4. Frontend確認

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\frontend
Copy-Item .env.example .env.local
npm.cmd install
npm.cmd run dev
```

確認URL:

- `http://localhost:3000`

確認項目:

- [ ] ダッシュボード画面が表示される。
- [ ] 上部に総合評価、注意度、重要イベントが表示される。
- [ ] 市場指標カードが表示される。
- [ ] 取得失敗時も画面が壊れず `要確認` が表示される。
- [ ] 下部に参考リンクが表示される。
- [ ] フッターに「投資助言ではなく、市場環境の整理と原典確認を目的」と表示される。

ビルド確認:

```powershell
npm.cmd run build
npm.cmd audit --audit-level=moderate
```

期待結果:

- [ ] build成功。
- [ ] auditが `found 0 vulnerabilities`。

## 5. Discord実投稿前の.env確認

実投稿前に、リポジトリ直下の `.env` を確認します。

必須:

```text
DATABASE_URL=sqlite:///./gold_dashboard.db
TIMEZONE=Asia/Tokyo
DASHBOARD_PUBLIC_URL=http://localhost:3000
FRONTEND_ORIGIN=http://localhost:3000
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

任意:

```text
FRED_API_KEY=
ALPHA_VANTAGE_API_KEY=
FMP_API_KEY=
```

確認項目:

- [ ] `DISCORD_WEBHOOK_URL` が投稿先チャンネルのWebhook URLである。
- [ ] `DASHBOARD_PUBLIC_URL` がDiscord投稿から開かせたいURLである。
- [ ] `TIMEZONE=Asia/Tokyo` になっている。
- [ ] `.env` を変更した後、FastAPIまたは手動ジョブの実行環境を再起動している。
- [ ] 実投稿前にサロン本番チャンネルではなく、テスト用チャンネルで確認する。

Webhook未設定時の安全確認:

```powershell
Invoke-WebRequest -UseBasicParsing -Method POST http://127.0.0.1:8000/api/discord/test
```

期待結果:

```json
{"status":"skipped","reason":"DISCORD_WEBHOOK_URL is not set"}
```

Webhook設定後の実投稿確認:

```powershell
Invoke-WebRequest -UseBasicParsing -Method POST http://127.0.0.1:8000/api/discord/test
```

確認項目:

- [ ] Discordに1件だけ投稿される。
- [ ] 投稿に総合評価、注意度、主要指標、ダッシュボードURLが含まれる。
- [ ] 文面が投資助言や売買指示に見えない。
- [ ] 失敗時はAPIレスポンスと `discord_notifications` を確認する。

代替ポート利用時は `8000` を起動中のポートに置き換えます。

## 6. タスクスケジューラ登録前確認

登録前に手動で実行します。

データ更新:

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
.\.venv\Scripts\python.exe -m app.jobs.refresh
```

Discord通知:

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
.\.venv\Scripts\python.exe -m app.jobs.notify
```

確認項目:

- [ ] `refresh` がJSONで `{"status":"ok", ...}` を返す。
- [ ] `notify` がWebhook未設定時は `skipped`、設定時は `sent` またはエラー内容を返す。
- [ ] `gold_dashboard.db` が `backend` フォルダ内に作成される。
- [ ] タスク登録では `py` ではなく `.venv\Scripts\python.exe` をProgramに指定する。
- [ ] `Start in` は必ず `C:\Users\kukyo\Documents\GOLDdashboard\backend` にする。

## 7. タスクスケジューラ登録内容

更新タスク:

```text
Program:
C:\Users\kukyo\Documents\GOLDdashboard\backend\.venv\Scripts\python.exe

Arguments:
-m app.jobs.refresh

Start in:
C:\Users\kukyo\Documents\GOLDdashboard\backend
```

通知タスク:

```text
Program:
C:\Users\kukyo\Documents\GOLDdashboard\backend\.venv\Scripts\python.exe

Arguments:
-m app.jobs.notify

Start in:
C:\Users\kukyo\Documents\GOLDdashboard\backend
```

推奨スケジュール:

- [ ] 朝: `refresh` の2〜5分後に `notify`
- [ ] NY前: `refresh` の2〜5分後に `notify`
- [ ] 初期想定は `07:00 JST` と `21:00 JST`

登録後確認:

- [ ] タスクスケジューラの「履歴」を有効化する。
- [ ] 手動で「実行」し、Last Run Result が `0x0` になる。
- [ ] `gold_dashboard.db` の更新時刻が変わる。
- [ ] Discord通知タスクの後、テストチャンネルに投稿される。

## 8. ログ・エラー確認

SQLiteには以下が保存されます。

- `source_fetches`: providerごとの取得成功/失敗とエラー。
- `market_snapshots`: ダッシュボードのスナップショット。
- `indicator_statuses`: 各指標の色・理由・原典。
- `discord_notifications`: Discord通知の成功/skip/失敗。

PowerShellで直近ログを確認する例:

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
.\.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('gold_dashboard.db'); print(c.execute('select provider,status,fetched_at,error_message from source_fetches order by id desc limit 10').fetchall())"
.\.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('gold_dashboard.db'); print(c.execute('select status,response_code,sent_at,error_message from discord_notifications order by id desc limit 10').fetchall())"
```

確認項目:

- [ ] 取得失敗は `source_fetches.error_message` に残る。
- [ ] Discord skip/失敗は `discord_notifications` に残る。
- [ ] 1日2回運用後、`market_snapshots` が増えている。
- [ ] 取得失敗があってもダッシュボードは `要確認` と原典リンクを表示する。

## 9. サロン投稿前の最終確認

- [ ] README冒頭に「投資助言、売買シグナル、予測ツールではない」と明記されている。
- [ ] UIフッターに「投資助言ではなく、市場環境の整理と原典確認を目的」と表示される。
- [ ] Discord投稿文が売買指示に見えない。
- [ ] 重要経済指標と地政学ニュースはPhase 1ではリンク確認中心である。
- [ ] データ取得できない項目を推定していない。


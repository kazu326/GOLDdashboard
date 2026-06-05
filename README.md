# GOLD環境認識ダッシュボード

FXサロン向けのGOLD環境認識ダッシュボードです。Phase 1は、朝とNYオープン前に「今日はどんな市場環境か」を30秒で確認するためのMVPです。

このアプリは投資助言、売買シグナル、予測ツールではありません。無料で取得できるデータと原典リンクを整理し、ユーザー自身が確認するための視認性特化ツールです。

## 構成

```text
frontend/  Next.js dashboard
backend/   FastAPI + SQLite + collectors + Discord notification
```

## Phase 1で表示する項目

- 米10年金利
- ドル指数、または代替ドル指数
- VIX
- GOLD価格
- S&P500
- 重要経済指標リンク
- 地政学ニュースリンク

取得できない項目は推定せず、画面上では `要確認` として原典リンクを表示します。

## Windowsローカル起動手順

以下は PowerShell で実行します。PowerShellで `npm` が実行ポリシーに止められる場合は、必ず `npm.cmd` を使ってください。

運用リハーサル前の確認項目は [docs/operation-checklist.md](docs/operation-checklist.md) にまとめています。

### 1. 前提確認

Python 3.11+ と Node.js が必要です。

```powershell
py --version
node --version
npm.cmd --version
```

`py --version` が `No installed Python found!` になる場合は、Python 3.11以上をインストールしてから続行してください。

### 2. 環境変数ファイル

リポジトリ直下で `.env` を作ります。

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard
Copy-Item .env.example .env
```

主な設定:

```text
DATABASE_URL=sqlite:///./gold_dashboard.db
TIMEZONE=Asia/Tokyo
DASHBOARD_PUBLIC_URL=http://localhost:3000
FRONTEND_ORIGIN=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
DISCORD_WEBHOOK_URL=
FRED_API_KEY=
ALPHA_VANTAGE_API_KEY=
FMP_API_KEY=
```

APIキーが未設定でも起動します。その場合、該当データは `要確認` になります。

### 3. Backendセットアップ

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`py -3.11` が使えない場合は、インストール済みのPythonが3.11以上であることを確認したうえで次を使います。

```powershell
py -m venv .venv
```

### 4. Backendテスト

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
.\.venv\Scripts\Activate.ps1
py -m pytest
```

### 5. FastAPI起動

ユーザー指定の確認コマンド:

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
.\.venv\Scripts\Activate.ps1
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

もし `py -m uvicorn` が仮想環境外のPythonを見に行く場合は、仮想環境のPythonを明示します。

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

確認URL:

- Health: `http://127.0.0.1:8000/health`
- Dashboard API: `http://127.0.0.1:8000/api/dashboard/current`
- FastAPI docs: `http://127.0.0.1:8000/docs`

PowerShell確認:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/dashboard/current
```

8000番が使用中で起動できない場合:

```powershell
netstat -ano | findstr :8000
taskkill /PID <表示されたPID> /F
```

停止できないプロセスが8000番を掴んでいる場合は、確認用に一時的に別ポートを使えます。

```powershell
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

代替ポートを使う場合は、`frontend\.env.local` のAPI接続先も同じポートへ変更し、Next.js dev serverを再起動してください。

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8010
```

### 6. Discord通知確認

Webhook未設定の場合はエラーで落ちず、`skipped` が返ります。

```powershell
Invoke-WebRequest -UseBasicParsing -Method POST http://127.0.0.1:8000/api/discord/test
```

Discordへ実際に投稿する場合は、リポジトリ直下の `.env` に設定します。

```text
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

設定後、FastAPIを再起動してから同じエンドポイントを実行します。

### 7. Frontendセットアップ

Next.jsは `frontend/.env.local` を読みます。Backend URLを明示するため、初回はコピーしてください。

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\frontend
Copy-Item .env.example .env.local
npm.cmd install
npm.cmd run dev
```

ブラウザで `http://localhost:3000` を開きます。

Backendが未起動でも、UIは壊れず `要確認` のフォールバック表示になります。Backend起動後は `/api/dashboard/current` の内容を表示します。

### 8. Frontendビルド

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\frontend
npm.cmd run build
npm.cmd audit --audit-level=moderate
```

## 手動ジョブ

FastAPIサーバーとは別に、Windowsタスクスケジューラから以下を実行できます。

データ更新:

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
.\.venv\Scripts\Activate.ps1
py -m app.jobs.refresh
```

Discord通知:

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
.\.venv\Scripts\Activate.ps1
py -m app.jobs.notify
```

## Windowsタスクスケジューラ例

登録前に、以下の手動ジョブが成功することを確認してください。

```powershell
Set-Location C:\Users\kukyo\Documents\GOLDdashboard\backend
.\.venv\Scripts\python.exe -m app.jobs.refresh
.\.venv\Scripts\python.exe -m app.jobs.notify
```

Program:

```text
C:\Users\kukyo\Documents\GOLDdashboard\backend\.venv\Scripts\python.exe
```

Arguments:

```text
-m app.jobs.refresh
```

Start in:

```text
C:\Users\kukyo\Documents\GOLDdashboard\backend
```

通知ジョブは Arguments を次に変更します。

```text
-m app.jobs.notify
```

初期想定は `07:00 JST` と `21:00 JST` です。

## API

- `GET /health`
- `GET /api/dashboard/current`
- `POST /api/refresh`
- `POST /api/discord/test`

## 無料データ取得元

Phase 1では以下をadapterとして実装しています。

- 米10年金利: U.S. Treasury XML Feed、FRED `DGS10`
- ドル指数: FMP DXY候補、FRED `DTWEXBGS` 代替ドル指数
- VIX: Cboe VIX CSV、FRED `VIXCLS`
- GOLD価格: Alpha Vantage、FMP `GCUSD`
- S&P500: FRED `SP500`、FMP `^GSPC`
- 経済指標: BEA / BLS / Fed の公式リンク
- 地政学ニュース: ReliefWeb / GDELT / U.S. Treasury press releases のリンク

無料APIは仕様、制限、ライセンス、レスポンス形式が変わる可能性があります。取得に失敗した場合は `要確認` と原典リンクを表示します。

## 色判定

色は売買シグナルではありません。GOLD環境認識の補助表示です。

- `追い風`: GOLD目線で環境が比較的追い風
- `中立`: 強い偏りなし
- `注意`: 注意度が高い、または逆風になりやすい材料
- `要確認`: 無料データを安定取得できず原典確認が必要

## 今後のPhase

Phase 2:

- 経済指標の自動取得精度向上
- 地政学ニュースの簡易分類
- provider優先順位の設定ファイル化
- 過去スナップショット一覧

Phase 3:

- ログイン
- ユーザー別設定
- 管理画面
- 有料API provider連携
- 複数銘柄対応

売買シグナル、AI予測、投資助言にはしません。

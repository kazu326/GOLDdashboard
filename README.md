# GOLD数値監視ダッシュボード

GOLD価格に影響する主要な数値指標を自動取得し、現在の市場モードを一画面で整理するダッシュボードです。ニュース収集や売買推奨は行いません。

## 監視指標

- GOLD価格: Alpha Vantage、FMPフォールバック
- 米10年実質金利: FRED `DFII10`
- 米10年名目金利: FRED `DGS10`
- 10年期待インフレ率: FRED `T10YIE`
- ドル指数 DXY: FMP、FRED `DTWEXBGS`代替フォールバック
- S&P500: FMP、FRED `SP500`フォールバック
- VIX: FRED `VIXCLS`

## 市場モード

以下の順序で判定します。

1. 相関ブレイク警戒
2. 通常の金利低下によるGOLD追い風
3. 金利・ドル高によるGOLD向かい風
4. リスクオフ買いの可能性
5. 中立

必要な前日比が不足する場合は「データ不足」と表示します。VIXは20以上を警戒、30以上を強い市場ストレスとして扱います。

## セットアップ

Python 3.11以上とNode.jsが必要です。リポジトリ直下の`.env.example`を`.env`へコピーし、利用するAPIキーを設定してください。

```text
DATABASE_URL=sqlite:///./gold_dashboard.db
TIMEZONE=Asia/Tokyo
DASHBOARD_PUBLIC_URL=http://localhost:3000
FRONTEND_ORIGIN=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
FRED_API_KEY=
ALPHA_VANTAGE_API_KEY=
FMP_API_KEY=
DISCORD_WEBHOOK_URL=
```

Backend:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
Set-Location frontend
npm.cmd install
npm.cmd run dev
```

## API

- `GET /health`
- `GET /api/dashboard/current`
- `POST /api/refresh`
- `POST /api/discord/test`

ダッシュボードAPIは`schema_version: 2`を返します。旧形式の保存済みスナップショットを検出した場合、新形式へ自動更新します。旧ニュース用DBテーブルは既存データ保護のため削除せず、利用停止のみとしています。

## Webhookの注意

Discord Webhook URLを`.env.example`やGitへ保存しないでください。過去にサンプルファイルへ入れたWebhook URLは漏えい済みとしてDiscord側で失効・再発行してください。

## 免責

このダッシュボードは売買シグナル、投資助言、価格予測ではありません。市場環境の整理と元データ確認を目的としています。

# 運用チェックリスト

## Backend

- [ ] `backend\.venv\Scripts\python.exe -m pytest` が成功する
- [ ] `GET /health` が `{"status":"ok"}` を返す
- [ ] `GET /api/dashboard/current` が `schema_version: 2` を返す
- [ ] APIに `economic_events` と `geo_news` が含まれない
- [ ] 7指標が返り、取得不能な指標は「データ不足」になる
- [ ] 旧スナップショットがある場合、新形式のスナップショットが自動生成される

## Frontend

- [ ] `npm.cmd run build` が成功する
- [ ] 上段にGOLD現在値、市場モード、主要因、警戒シグナルが表示される
- [ ] 7指標カードと数値データ参照元が表示される
- [ ] ニュース・経済イベント欄が表示されない
- [ ] モバイル幅で1列表示になる

## 定期更新・Discord

- [ ] `backend\.venv\Scripts\python.exe -m app.jobs.refresh` が成功する
- [ ] Discord通知に市場モード、主要因、警戒シグナル、7指標が含まれる
- [ ] Discord通知にニュース・重要イベント欄が含まれない
- [ ] Webhook未設定時は安全に`skipped`となる

## 秘密情報

- [ ] `.env.example`の`DISCORD_WEBHOOK_URL`が空である
- [ ] APIキーとWebhook URLをGit管理対象へ保存していない
- [ ] 過去に公開・共有されたWebhook URLをDiscord側で失効し、新しいURLへローテーションした

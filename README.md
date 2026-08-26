# 宅食図鑑（takushokuzukan.pages.dev）

個人 × Claude Codeによる宅配食（食品宅配）アフィリエイト事業のリポジトリ。

- サイト名: **宅食図鑑**
- 公開URL: **https://takushokuzukan.pages.dev**（Cloudflare Pages 無料プラン / 独自ドメインなし）
- サイト名決定経緯: `docs/SITE_NAME_DOMAIN_DECISION_2026_08.md`
- 無料公開・デプロイ手順: `docs/DEPLOYMENT_GUIDE_2026_08.md`

## コンセプト

「AIが生成できる文章」ではなく、**継続的に蓄積する構造化データ（独自DB）＋自動更新システム**で差別化する。

- 最新の初回キャンペーン情報を毎週更新（AIがリアルタイムに答えられない領域）
- メニュー別栄養DB・価格DBを蓄積
- 購入意図の強いKWからアフィリエイトCVを獲得

## ディレクトリ構成

```
data/      独自DB（サービスマスタ・キャンペーン・メニュー栄養・送料・出典台帳）
config/    アフィリエイトリンク管理・監視対象URL
tools/     ビルド・監視スクリプト
site/      生成された静的サイト（デプロイ対象）
docs/      調査・意思決定ドキュメント
```

## 使い方

```bash
# サイト生成（data/*.json → site/）
python tools/build.py

# 価格・キャンペーン変更の監視（週1回推奨）
python tools/watch.py
```

## デプロイ

Cloudflare Pages の無料プラン + pages.dev で公開する。

- 推奨: CloudflareネイティブのGitHub連携（Build command: `python tools/build.py` / Output directory: `site`）
- 代替: `deploy.ps1`（Wrangler直接アップロード）
- 詳細は `docs/DEPLOYMENT_GUIDE_2026_08.md`

## サイト名・URL設定

`config/site.json` で管理する（name / url / search_console_meta）。Cloudflareプロジェクト名が変わった場合は `url` を更新する。

## アフィリエイト設定

ASP提携承認後、`config/affiliates.json` の `actual_url` を埋めると全ページのCTAがアフィリエイトリンクになる。

## ドキュメント

- `docs/AFFILIATE_MARKET_ENTRY_RESEARCH_2026_08.md` — 市場調査本編（24ジャンル評価）
- `docs/AFFILIATE_MARKET_ENTRY_SHORTLIST_2026_08.md` — TOP10ショートリスト
- `docs/DELIVERY_FOOD_AFFILIATE_NEXT_ACTION_2026_08.md` — 本プロジェクトの次の一手・実装判断

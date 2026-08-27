# URL正規化 実装記録（2026-08-28）

作成日: 2026-08-28
作成者: Claude Code
範囲: `docs/URL_NORMALIZATION_AUDIT_2026_08_28.md`（監査）の推奨に基づく実装。**commit/push/deployは行っていない**（ユーザー指示によりワーキングツリー上の変更のみ）。
方針: サイト全体の正規URLを拡張子なしURL（例: `/ranking`, `/services/nosh`）に統一。TOPは`/`。

---

## 1. 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `tools/sitegen/templates.py` | `page_header()`のcanonical生成、`build_sitemap()`の`<loc>`生成、内部リンク約35箇所（nav/footer/CTA/カード/比較表/診断ツールJSの`detail_url`/404ページ等）を拡張子なしURLに変更 |
| `tools/sitegen/generators.py` | `compute_comparison_links()`内の比較ページURL生成（`url = f"/comparisons/{a_id}-vs-{b_id}"`）を拡張子なしに変更 |

`data/*.json` `config/*.json` は変更していない（差分ゼロ、§4で確認）。

---

## 2. 変更箇所の詳細

### 2.1 canonical / sitemap（正規化の起点）

- `page_header(title, description, canonical_path, ...)`: 呼び出し側（13箇所）は従来通り`.html`付きの値を渡す仕様のまま変更せず、関数内部で`canonical_path.removesuffix(".html")`により正規化。TOPページ（`canonical_path == "index.html"`）のみ特別扱いし、`SITE_URL + "/"`（ルート）を返す。
- `build_sitemap(pages)`: `pages`（実ファイル書き込みパス、`.html`付き、`generators.py`が保持）はそのまま維持し、`<loc>`生成時にのみ同じロジックで正規化。ファイル書き込み側には触れていない。

### 2.2 内部リンク（約35箇所）

`href="/xxx.html"`形式の静的・動的リンクを全て拡張子なしに変更。対象: ヘッダーnav（比較一覧/初回キャンペーン/診断ツール）、フッター（プライバシー/免責/運営者/お問い合わせ）、サービスカード・比較表・関連サービス・目的別導線チップ・比較ページ間リンク・診断ツールのJS内`detail_url`・404ページ、他。

TOPへのリンク（`href="/"`、ロゴ・404の戻りリンク）はもともと正しかったため無変更。

### 2.3 データ由来フィールドの扱い（`article_link`）

`data/services.json`の`article_link`フィールドは`"/articles/chef-muten-tukuritoki-kuchikomi.html"`（`.html`付き）のまま**データを変更していない**。表示側の`templates.py`（`build_service_page`）で`_art_link.removesuffix(".html")`を適用し、レンダリングされるhrefのみ正規化した。

### 2.4 比較ページURL生成（コード側、データ側ではない）

`generators.py:95`の`compute_comparison_links()`が生成する`url`は`config/comparisons.json`のペア定義（データ）から動的に組み立てられるコード側の値であり、データファイル自体は変更していない。ここを拡張子なしに変更したことで、`templates.py`側の`comparison_links_block()`・比較ページ一覧（`comparison_pairs_block`相当）双方に自動的に反映される（テンプレート側は無変更）。

---

## 3. 確認結果

### 3.1 ビルド・検証

| 手順 | 結果 |
|---|---|
| `python tools/build.py` | 成功（32ページ + sitemap.xml + robots.txt を再生成、エラーなし） |
| `python -m sitegen.validate`（`tools/`から実行） | 終了コード0（`generators.py`内で`validate.validate_services()`はbuild時に既に自動実行されており、価格schemaエラーなし） |

### 3.2 全32ページのcanonical/sitemap整合性

生成された`site/sitemap.xml`の`<loc>`32件と、生成された全32ページの`<link rel="canonical">`をそれぞれ抽出し、両方に`.html`が0件であることを確認。TOPは`https://ret4853.2070abe.workers.dev/`、他31ページは`.../ranking`, `.../services/nosh`等の拡張子なし形で、**sitemapとcanonicalが1件ずつ完全一致**（32/32）。

内部リンク中に`.html`付きの内部href（`href="/...html"`）が残っていないことも全生成ファイルへの走査で確認済み（0件）。`og:url`（OGPメタ）も同様に0件。

### 3.3 実URLの200確認

`site/sitemap.xml`記載の32 URL全てに対し、現在ライブ稼働中のCloudflare Workers（`https://ret4853.2070abe.workers.dev`）へ直接アクセスして確認した（コードの変更点はテンプレート生成ロジックのみで、この拡張子なしURL自体はCloudflare側の`html_handling=auto-trailing-slash`により本監査以前から既に200を返す実URLだったため、**未デプロイの現時点でも実サーバーでの200確認が可能**）。

**32/32 URL全て200 OK**（`/`、`/ranking`、`/campaigns`、`/tool/diagnosis`、`/articles/...`、`/verification`、法務4ページ、サービス15ページ、比較7ページ）。

### 3.4 `.html` URLのリダイレクト確認

`/index.html`→307→`/`、`/ranking.html`→307→`/ranking`等、本監査時点と同じ307リダイレクト挙動を再確認し、変更していないことを確認（`wrangler.toml`は今回一切変更していない）。

### 3.5 affiliate / CTA遷移先

`aff_link()`関数・`data/affiliates.json`由来の`actual_url`は無変更。診断ツールをPlaywrightで実際に操作（「一人暮らし」選択→診断実行）し、結果カードの「公式サイト」リンク（例: `https://nosh.jp/`）が外部URLのまま変わっていないこと、「詳しく見る」リンクが新しい`detail_url`（例: `/services/nosh`）になっていることを確認。

### 3.6 data/config差分

`git diff --stat -- data/ config/` の出力は空。差分ゼロを確認。

### 3.7 Playwrightによる実画面確認

生成済み`site/`をローカルの`python -m http.server`（一時的、QA後に停止・後始末済み）で配信し、以下を確認（本番未デプロイのため、実際にデプロイされるHTMLをローカルで検証）。

| ページ | 確認内容 | 結果 |
|---|---|---|
| TOP (`index.html`) | 表示・console error | 正常、エラー0件 |
| 比較一覧 (`ranking.html`) | 表示・console error | 正常、エラー0件 |
| 診断ツール (`tool/diagnosis.html`) | 表示・実操作（条件選択→診断実行）・結果リンク・console error | 正常、エラー0件、`detail_url`/公式サイトリンクとも正しい |
| サービス詳細 (`services/nosh.html`) | 表示・console error | 正常、エラー0件 |
| 比較ページ (`comparisons/nosh-vs-watami-takushoku.html`) | 表示・console error | 正常、エラー0件 |
| サービス詳細（モバイル375px幅） | 横スクロール有無 | `scrollWidth === clientWidth`（360px、横スクロールなし）、レイアウト崩れなし |

### 3.8 git diff監査

`git diff -- tools/sitegen/generators.py tools/sitegen/templates.py` を全件目視確認。**全ハンクが`.html`拡張子の除去（href/canonical/sitemap/detail_url/comparison URL）と、それを説明する最小限のコメント追加のみ**。CSS・タイトル・description・診断ロジック・データ構造・UIコンポーネントへの変更は無し。

---

## 4. 残存問題・未対応事項

- **本番へのデプロイは未実施**。ライブサイト（`https://ret4853.2070abe.workers.dev`）の実HTML（canonical/sitemap）は旧仕様（`.html`付き）のまま。次回`npx wrangler deploy`実施まで、Google Search Console上の状態（`docs/GOOGLE_INDEX_REQUEST_LOG_2026_08_28.md`時点の未登録URL群）は変化しない。
- `docs/URL_NORMALIZATION_AUDIT_2026_08_28.md` P2で指摘した「HTTP（非TLS）がHTTPSへ強制リダイレクトされない」問題は、本実装のスコープ外（Cloudflare側設定領域であり、テンプレート生成ロジックの変更では対応不可）。今回は未対応のまま。
- デプロイ後は、`docs/GOOGLE_INDEX_REQUEST_LOG_2026_08_28.md`のURL検査を新しい正規URL（拡張子なし）に対して再実施し、Googleが新URLを正しくインデックスするかを追跡する必要がある（次のアクション、今回は未実施）。

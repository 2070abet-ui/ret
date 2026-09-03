# Google Search Console 個別インデックス登録リクエスト 実施記録（2026-08-28）

作成日: 2026-08-28
作成者: Claude Code（URL選定・記録） / ユーザー（GSC実操作）
範囲: 本記録は**GSC管理画面上の操作記録のみ**。コード/data/config変更・sitemap変更・commit/push/deployは一切行っていない。新規SEOページも作成していない。
前提: `docs/SEARCH_TRAFFIC_ZERO_CAUSE_AUDIT_2026_08_28.md`（検索流入ゼロの原因監査）の「次に1つやるべきこと」の実行記録。

---

## 1. 選定したURL（7件、全てsitemap.xml記載の実在URL）

| # | カテゴリ | URL | リクエストする価値 |
|---|---|---|---|
| 1 | TOP | `/index.html` | ブランド指名検索の受け皿。canonical(`/index.html`)と全ページ内部リンク(`/`)の不整合（原因監査§4）があり、登録状態の確認自体に技術的意味があった |
| 2 | 比較一覧 | `/ranking.html` | 検討初期〜中期ユーザーの入口。11社比較の一覧ページで、サイト内で最もCVに近い一覧導線 |
| 3 | 診断ページ | `/tool/diagnosis.html` | サイト内回遊の中核。診断結果から各サービス詳細・A8リンクへの主要導線 |
| 4 | 比較ページ | `/comparisons/nosh-vs-watami-takushoku.html` | noshは11社中ブランド認知度最高。直接比較は検討後期ユーザーの受け皿 |
| 5 | サービス詳細 | `/services/nosh.html` | ブランド認知度最高のサービス。指名検索の受け皿として最重要 |
| 6 | サービス詳細 | `/services/chef-muten-tukuritoki.html` | A8提携・記事1本のCV先。商標ロングテールSEOで既存調査上の最優先(★★★★★) |
| 7 | 記事 | `/articles/chef-muten-tukuritoki-kuchikomi.html` | 個人サイトが実測SERP上位を取れると既存調査で確認済みの商標ロングテール記事 |

---

## 2. 実施結果（2026-08-28、ユーザー実施・報告）

### 2.1 URL検査結果（全件共通）

**選定した7件は全てGoogle未登録（インデックス未登録）だった。**

これは原因監査（`SEARCH_TRAFFIC_ZERO_CAUSE_AUDIT_2026_08_28.md` §3）の時点でルート`/`のみ「インデックス登録済み」だったこととの重要な差分である。今回`/index.html`（canonical・sitemapが記載する側のURL）を検査したところ**未登録**と判明した。これは同監査§4で指摘した「内部リンクは`/`、canonical/sitemapは`/index.html`」という不整合の実害を裏付ける一次証拠であり、Googleが`/`と`/index.html`を別URL扱いし、canonical側（`/index.html`）はまだインデックスされていないことが確認された。

### 2.2 リクエスト実施状況

| # | URL | 状態 |
|---|---|---|
| 1 | `/index.html` | 未登録 → **インデックス登録をリクエスト済み** |
| 2 | `/ranking.html` | 未登録 → **インデックス登録をリクエスト済み** |
| 3 | `/tool/diagnosis.html` | 未登録 → **インデックス登録をリクエスト済み** |
| 4 | `/comparisons/nosh-vs-watami-takushoku.html` | 未登録・**未リクエスト**（GSCの1日あたりリクエスト上限に到達したため） |
| 5 | `/services/nosh.html` | 未登録・**未リクエスト**（同上） |
| 6 | `/services/chef-muten-tukuritoki.html` | 未登録・**未リクエスト**（同上） |
| 7 | `/articles/chef-muten-tukuritoki-kuchikomi.html` | 未登録・**未リクエスト**（同上） |

**登録済みでスキップしたURL**: 0件（7件全て未登録だったため、スキップ対象は無かった）。

**今はリクエスト不要と判断したURL**: 該当なし（7件は全て優先度に基づき選定済みで、リクエスト自体は全件必要と判断している。#4〜7は「不要」ではなく「本日の上限到達により先送り」）。

---

## 3. 残りの対応（2026-08-29予定）

GSCの個別インデックス登録リクエストには1日あたりの上限があり、本日は#1〜3の3件で到達した。以下を翌日以降に実施する。

- [ ] `/comparisons/nosh-vs-watami-takushoku.html` のURL検査・リクエスト
- [ ] `/services/nosh.html` のURL検査・リクエスト
- [ ] `/services/chef-muten-tukuritoki.html` のURL検査・リクエスト
- [ ] `/articles/chef-muten-tukuritoki-kuchikomi.html` のURL検査・リクエスト

残り4件は1日の上限内に収まる件数のため、翌日1回の作業で完了する見込み。

---

## 4. 副次的な発見（技術的フォローアップ候補・今回は未対応）

`/index.html` が未登録だった事実は、原因監査§4で「影響は限定的」と暫定評価していたcanonical/内部リンク不整合が、**実際にインデックス範囲を狭めている可能性を示す一次証拠**に格上げされる。次のような追加確認が今後の判断材料になる。

- リクエスト後、`/index.html` が実際にインデックスされるかを1〜2週間後に再確認する。
- インデックスされた場合、`/`（内部リンクが指す先）と`/index.html`（canonicalが指す先）のどちらが検索結果に表示されるURLとして扱われるかを確認する。
- 上記の結果次第で、canonical/sitemapを内部リンクと同じ`/`に統一する修正（`tools/sitegen/templates.py`のTOPページ`page_header`呼び出し）を次フェーズの候補として検討する。**今回はコード変更を行っていない**。

---

## 5. 追記（2026-09-02）: 残り4件を新URL形式でリクエスト

URL正規化デプロイ（`docs/URL_NORMALIZATION_PRODUCTION_AUDIT_2026_08_28.md`）後、§3で「先送り」としていた残り4件は旧`.html`付きURL宛てのままだったため、現在の正規URL（拡張子なし）で改めてGSC URL検査→インデックス登録リクエストを実施した（Playwright・ログイン済みGSCセッション使用）。

| # | URL | 検査結果 | リクエスト結果 |
|---|---|---|---|
| 1 | `/comparisons/nosh-vs-watami-takushoku` | 未登録（未クロール、参照元サイトマップ未検出） | **リクエスト済み**（"Indexing requested"） |
| 2 | `/services/nosh` | 未登録（同上） | **リクエスト済み**（"Indexing requested"） |
| 3 | `/services/chef-muten-tukuritoki` | 未登録（同上） | **未リクエスト**（3件目で「Quota Exceeded」＝日次上限到達） |
| 4 | `/articles/chef-muten-tukuritoki-kuchikomi` | 未実施 | **未リクエスト**（上限到達のため未着手） |

**残タスク（翌日以降）**:
- [ ] `/services/chef-muten-tukuritoki` のURL検査・リクエスト
- [ ] `/articles/chef-muten-tukuritoki-kuchikomi` のURL検査・リクエスト

2件は日次上限内に収まる件数のため、翌日1回の作業で完了する見込み。GSC上の操作のみで、コード/data/config変更・commit/push/deployは行っていない。

---

## 6. 追記（2026-09-04）: 最後の残タスク（chef-mutenサービス詳細）をリクエスト完了

`/services/chef-muten-tukuritoki`（拡張子なし正規URL）に対し、GSC URL検査→インデックス登録リクエストを実施した（Playwright・ログイン済みGSCセッション使用）。**これで§5追記時点の残タスクは全件完了した。**

| URL | 検査結果 | リクエスト結果 |
|---|---|---|
| `/services/chef-muten-tukuritoki` | 未登録（**URL is unknown to Google**＝未クロール、最終クロールN/A、参照元サイトマップ未検出） | **リクエスト済み**（"Indexing requested"ダイアログ確認: "URL was added to a priority crawl queue"） |

- リクエスト前のGSC挙動: 「Request indexing」クリック時にライブテスト（Testing if live URL can be indexed）が自動実行され、完了後に優先クロールキューへの追加が確認された。
- 状態把握メモ（同日の`docs/GSC_STATUS_AND_STRATEGY_2026_09_04.md`参照）: `/services/chef-muten-tukuritoki` はこの時点でGoogleに一度もクロールされていないページ群（"Discovered - currently not indexed"相当）の一部。リクエスト後は1〜2週間を目安に再確認する。
- コード/data/config変更・commit/push/deployは行っていない（GSC上の操作のみ）。

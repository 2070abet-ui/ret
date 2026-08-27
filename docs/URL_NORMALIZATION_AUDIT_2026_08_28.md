# URL正規化監査：canonical / sitemap / 内部リンク / 実サーバー挙動（2026-08-28）

作成日: 2026-08-28
作成者: Claude Code
範囲: 本監査は**調査・原因特定のみ**。コード/data/config/CSS/HTML生成ロジックの変更、commit/push/deployは一切行っていない。問題はP1/P2/P3に整理するのみで、その場修正はしていない。
前提: `docs/GOOGLE_INDEX_REQUEST_LOG_2026_08_28.md` で判明した「`/index.html`が未登録、`/`のみ登録済み」という差分を起点に、サイト全32ページで同種の不整合が無いかを監査する。
基準: [Google Search Central: canonical URLの統合方法を確認する](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls) 、[サイトマップについて](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap) の公式仕様（いずれも「canonicalおよびsitemap記載URLはリダイレクトなしで200を返す最終URLであるべき」という原則）。

---

## 0. 先に結論

**サイト全体で、canonical・sitemap・内部リンクが宣言する正規URLと、実サーバーが最終的に200を返すURLが一致していない。これはTOPページ固有の問題ではなく、`/index.html`↔`/`の不一致と同じ構造の不整合が、`.html`拡張子を持つ他31ページすべてに存在する、サイト全域のP1問題である。**

原因はCloudflare Workers Static Assetsの設定（`wrangler.toml`の`html_handling = "auto-trailing-slash"`）にある。この設定下では、`.html`拡張子付きURLへのリクエストは**すべて拡張子なしURLへ307リダイレクトされる**（実測で確認済み、§3）。一方、`tools/sitegen/templates.py`が生成するcanonicalタグ・`sitemap.xml`・サイト内のほぼ全ての内部リンクは**`.html`拡張子付きURLを一貫して使用**している。結果として、**Googleに「これが正規URLだ」と伝えている32ページ全てのURLが、実際には200を返さずリダイレクトするURLになっている**。

例外はTOPページのみで、内部リンク（ロゴ・404ページの戻りリンク）だけが`href="/"`（拡張子なしのルート）を使っており、これが実際の200提供URLと一致する。この1点のみ「内部リンクが実URLと一致し、canonical/sitemapが不一致」という、他31ページ（内部リンクもcanonical/sitemapと共に不一致）とは逆パターンになっている。

---

## 1. 監査対象ごとの結果

### 1.1 全ページの `<link rel="canonical">`

`tools/sitegen/templates.py` の `page_header(title, description, canonical_path, ...)` が生成する。

```python
canonical_url = f"{SITE_URL}/{canonical_path}"
...
<link rel="canonical" href="{canonical_url}">
```

`canonical_path` は全32ページの呼び出し箇所で**例外なく`.html`拡張子付き**（例: `"ranking.html"`, `"services/nosh.html"`, `"index.html"`）。TOPページも`"index.html"`を渡しており、`/`という拡張子なしの形は一切生成されない。

→ **canonicalは全ページで`.html`付き、自己完結して一貫している**（他の生成箇所とのブレは無い）。問題はこの値自体ではなく、この値が指すURLが実サーバー上でリダイレクトすることにある（§3）。

### 1.2 `sitemap.xml` の全 `<loc>`

`generators.py`の`pages`リスト（ファイル書き込み時に`.append()`されるパス、全32件）をそのまま`templates.build_sitemap()`に渡し、`<loc>{SITE_URL}/{p}</loc>`として出力。`pages`リストの中身は書き込んだファイルパスそのもの（`.html`拡張子付き）。

→ **sitemapもcanonicalと完全に同じ値・同じ形式**（`.html`付き）。両者は内部的に矛盾なく一致しているが、これは「実サーバーの挙動と食い違う値で一致している」状態。

### 1.3 サイト内の内部リンク（href）

`templates.py`内の`href=`を全数調査（約35箇所）。分類すると:

| リンク先パターン | 該当箇所数（概算） | 拡張子 |
|---|---|---|
| `/services/{id}.html` | 8箇所（一覧・詳細・比較ページ内） | `.html`付き |
| `/ranking.html` | 8箇所（ヘッダーnav・CTA・診断結果・404等） | `.html`付き |
| `/campaigns.html` | 6箇所 | `.html`付き |
| `/tool/diagnosis.html` | 5箇所 | `.html`付き |
| `/verification.html` | 2箇所 | `.html`付き |
| `/comparisons/{a}-vs-{b}.html`（`generators.py:95`で生成） | 比較リンク全箇所 | `.html`付き |
| `/privacy.html` `/disclaimer.html` `/operator.html` `/contact.html` | フッター等 計8箇所 | `.html`付き |
| 診断ツールJSの`detail_url`（`templates.py:1627`） | JS動的生成リンク | `/services/{id}.html`（`.html`付き） |
| `href="/"`（ロゴ・404の戻りリンク） | **2箇所のみ** | 拡張子なし（ルート） |

→ **内部リンクの98%以上（2箇所を除く全て）が`.html`付きで、canonical・sitemapと完全に一致している。** ユーザーが懸念していた「内部リンクが大量にcanonicalと違うURLを指している」状態ではなく、**逆に内部リンクはcanonicalに忠実**。問題は内部リンクではなく、その先（`.html`付きURL自体）がサーバー側でリダイレクトされることにある。

例外の2箇所（`href="/"`）は、TOPページのcanonical（`index.html`）と食い違う。

### 1.4 URL生成ロジック（`tools/sitegen/templates.py` 等）

- `page_header()`: canonical生成の単一ポイント。`canonical_path`引数をそのまま`.html`付きで結合。拡張子を外す処理は無い。
- `build_sitemap()`（`templates.py:2329`付近）: `pages`リストをそのまま`.append`。拡張子を外す処理は無い。
- `generators.py`: 各ページ生成時に`pages.append(f"...html")`と`.html`拡張子付きファイル名をそのまま記録し、これがcanonical/sitemap両方の入力になる。**ロジック上、拡張子を外すのか付けるのかという判断がどこにも存在しない**（一貫して「付ける」設計）。
- 唯一の例外は`templates.py:1050`（ロゴ）と`:2130`（404ページ）の`href="/"`。これは意図的な正規化ではなく、単に「トップページへのリンクは`/`で書く」という個別の書き方の揺れと見られる（`page_header(..., "index.html")`との対応関係を意識した形跡はコード上に無い）。

### 1.5 `/` と `/index.html` の実際のHTTPレスポンス・リダイレクト・canonical（実測）

`https://ret4853.2070abe.workers.dev` に対し、`curl`で直接検証した（2026-08-27時点の実測値）。

| リクエストURL | 実際の応答 | 備考 |
|---|---|---|
| `/` | **200 OK**（本文55,787 bytes） | 最終提供URL |
| `/index.html` | **307 Temporary Redirect** → `Location: /` | canonical/sitemapが指す値 |
| `/ranking.html` | **307** → `Location: /ranking` | canonical/sitemapが指す値 |
| `/ranking` | **200 OK**（本文91,547 bytes） | 最終提供URL（内部リンクからは到達しない） |
| `/ranking.html/`（末尾スラッシュ） | **404** | |
| `/services/nosh.html` | **307** → `Location: /services/nosh` | |
| `/services/nosh` | **200 OK** | 最終提供URL |
| `/services/nosh/`（末尾スラッシュ） | **307** → `Location: /services/nosh` | |
| `/tool/diagnosis.html` | **307** → `Location: /tool/diagnosis` | |
| `/tool/diagnosis` | **200 OK** | 最終提供URL |
| `http://`（TLSなし）でのルートアクセス | **200 OK**（httpのままリダイレクトされない） | §2.4参照 |

**この挙動はページ固有ではなく、`wrangler.toml`の`html_handling = "auto-trailing-slash"`（Cloudflare Workers Static Assetsの標準設定）による、全`.html`ファイルに対する一律の仕様。** 個別ページのバグではなく、設定と生成ロジックの不整合が全ページに一律に効いている。

### 1.6 robots.txt / sitemap.xml の参照関係

```
User-agent: *
Allow: /
Sitemap: https://ret4853.2070abe.workers.dev/sitemap.xml
```

robots.txt自体に問題は無い（Sitemap行のURLは実在し200で取得可能）。ただし、robots.txtが正しく指し示すsitemap.xmlの中身（`<loc>`）が§1.2の通り全てリダイレクトURLであるため、**robots.txt→sitemap.xmlの参照経路は正常でも、その先で案内されるURL自体に問題がある**。

---

## 2. 確認事項チェックリスト（ユーザー指定項目への回答）

| 確認項目 | 結果 |
|---|---|
| 同一ページを`/`と`/index.html`の複数URLで参照していないか | TOPページのみ該当。ただし片方が307でもう片方へリダイレクトするため、Google上で同時に別ページとして重複インデックスされるリスクは低い。問題は「重複」ではなく「canonicalが自己参照できていない」こと |
| canonical・sitemap・内部リンクが同じ正規URLを指しているか | **TOP以外の31ページ**: canonical・sitemap・内部リンクの3者は**互いに一致**（全て`.html`付き）。ただし3者ともサーバーの実際の最終提供URL（拡張子なし）とは**不一致**。**TOPページのみ**: canonical・sitemapは一致（`index.html`付き）だが、内部リンク（`/`）だけが異なる |
| 全ページでcanonicalが自己参照になっているか | **いいえ。32ページ全てで自己参照が成立していない。** 各ページのcanonical URLにアクセスすると、そのページ自身のHTMLではなく307リダイレクトが返る（TOPは`/`へ、他31ページはそれぞれの拡張子なしURLへ）。「自己参照canonical」の定義（canonical URL＝そのページを200で返すURL自身）を満たしていない |
| sitemapにcanonicalではないURLが含まれていないか | 含まれていない（sitemapとcanonicalは全ページで同一値）。ただし両者とも同じ問題（リダイレクトURL）を共有している |
| 内部リンクがcanonicalではないURLを大量に指していないか | **いいえ、逆**。内部リンクの大多数（35箇所中33箇所）はcanonicalと一致した`.html`付きURLを指している。canonicalと異なるのはTOPページの2箇所のみ |
| trailing slash・index.html・相対/絶対・http/https・www有無の不一致 | ①trailing slash: `/services/nosh/`のような末尾スラッシュは307で拡張子なしURLへ集約される。サイト側もそのようなURLは生成していないため実害小。②index.html: §1.5の通り最大の問題点。③相対/絶対: 全内部リンクはroot相対の絶対パス（`/`始まり）で統一されており不整合なし。④http/https: **`http://`（非TLS）でのアクセスがhttpsへリダイレクトされず200で応答する**ことを確認（§1.5末尾）。canonical/sitemapはhttps固定のため実害は限定的だが、http版URLが別途クロール・インデックスされうる余地は残る。⑤www有無: サイトはwww非使用のworkers.devサブドメインのみで、www付きバリアントは存在しないため対象外 |
| GoogleがA選択し得るURLとサイト側が指定しているURLに矛盾がないか | **矛盾を実例で確認済み**。`docs/GOOGLE_INDEX_REQUEST_LOG_2026_08_28.md`で、Googleは`/index.html`ではなく`/`をインデックスした（サイト側の指定＝`/index.html`とは逆）。他31ページも同一パターンのため、Googleは今後同様に拡張子なしURLを選ぶ可能性が高いと推測されるが、**これは`/`以外では未検証（推測）**であり、断定はしない |
| 32ページそれぞれについて一致しているか | §3の表を参照 |

---

## 3. 32ページ全件の状態一覧

| # | ページ | canonical/sitemap | 内部リンクの主形式 | 実サーバーの最終URL | 3者一致？ |
|---|---|---|---|---|---|
| 1 | TOP | `/index.html` | `/`（ロゴ等、例外） | `/` | ❌（内部リンクのみ実URLと一致、canonical/sitemapは不一致） |
| 2 | `/ranking.html` | `.html`付き | `.html`付き | `/ranking` | ❌（canonical/sitemap/内部リンクは一致、実URLとのみ不一致） |
| 3 | `/campaigns.html` | 同上 | 同上 | `/campaigns` | ❌ 同上パターン |
| 4 | `/tool/diagnosis.html` | 同上 | 同上 | `/tool/diagnosis` | ❌ 同上パターン |
| 5 | `/articles/chef-muten-tukuritoki-kuchikomi.html` | 同上 | 同上 | `/articles/chef-muten-tukuritoki-kuchikomi` | ❌ 同上パターン |
| 6 | `/verification.html` | 同上 | 同上 | `/verification` | ❌ 同上パターン |
| 7 | `/privacy.html` | 同上 | 同上 | `/privacy` | ❌ 同上パターン |
| 8 | `/disclaimer.html` | 同上 | 同上 | `/disclaimer` | ❌ 同上パターン |
| 9 | `/operator.html` | 同上 | 同上 | `/operator` | ❌ 同上パターン |
| 10 | `/contact.html` | 同上 | 同上 | `/contact` | ❌ 同上パターン |
| 11–25 | `/services/{15サービスID}.html`（15ページ） | 同上 | 同上 | `/services/{id}` | ❌ 同上パターン（15ページとも） |
| 26–32 | `/comparisons/{7ペア}.html`（7ページ） | 同上 | 同上 | `/comparisons/{pair}` | ❌ 同上パターン（7ページとも） |

**32ページ中32ページ全てで、canonical/sitemapが指すURLが実サーバー上の最終提供URLと不一致。** うち31ページは内部リンクもcanonical/sitemap側に揃っており（＝実URLとズレる）、TOPページ1件のみ内部リンクが実URL側に揃っている（＝canonical/sitemapとズレる）という逆パターン。

---

## 4. 重要度別まとめ

### P1（最優先・サイト全域に影響）

- **全32ページのcanonical/sitemap記載URLが、実サーバーでは307リダイレクトするURLであり、Googleの公式ガイドラインが定める「canonical/sitemapは最終URL・自己参照であるべき」に反している。** `docs/GOOGLE_INDEX_REQUEST_LOG_2026_08_28.md`で`/index.html`が未登録だった事実は、この問題が実際にインデックス形成を阻害していることの一次証拠。他31ページも同一メカニズムで今後同様の問題が起きる可能性が高い。

### P2（軽微〜中程度）

- **HTTP（非TLS）が明示的なHTTPS強制リダイレクトなしに200を返す。** canonical自体はhttps固定のため実害は限定的だが、httpバリアントが独立にクロールされる余地を残している。
- **TOPページの内部リンク（`href="/"`）だけが他ページと異なる規則（拡張子なし）を使っている。** P1修正時に同じルールへ統一する必要がある。

### P3（実害なし・記録のみ）

- 末尾スラッシュ付きURL（`/services/nosh/`等）は307で正しく集約されており、追加対応不要。
- www有無の不整合は対象ドメインの性質上そもそも存在しない。

---

## 5. 推奨する正規URL

**拡張子なしURL（例: `/ranking`, `/services/nosh`, `/tool/diagnosis`、TOPは`/`）を正規URLとして統一することを推奨する。**

理由:
- Cloudflare側の設定（`html_handling = "auto-trailing-slash"`）は既にこの形を「最終的に200を返すURL」として実現しており、`wrangler.toml`自体のコメントも「"/foo.html" はスラッシュなしで配信」という拡張子なし優先の設計意図を記している。**サーバー設定を変更せず、生成ロジック側をサーバーの実挙動に合わせる方が変更範囲が小さい**（逆に`.html`付きを正規化しようとすると、Cloudflare側の`html_handling`設定変更または明示的なリダイレクトルール追加が必要になり、変更範囲・リスクとも大きくなる）。
- 実際にGoogleが選んだ結果（`/`をインデックスし`/index.html`は非インデックス）とも整合する。
- 拡張子なしURLは一般的なcanonical URLの慣習（クリーンURL）とも合致する。

---

## 6. 修正する場合の変更箇所（実施はしない・参考情報）

| ファイル | 変更内容（案） |
|---|---|
| `tools/sitegen/templates.py` `page_header()` | `canonical_path`から`.html`拡張子を除去してURL生成する処理を追加。TOPページ（`"index.html"`）は特別に`SITE_URL + "/"`に正規化 |
| `tools/sitegen/templates.py` `build_sitemap()` | `pages`リストの各要素から`.html`を除去し、`index.html`は空文字列（ルート）として`<loc>`を生成 |
| `tools/sitegen/templates.py` 内の全`href="...html"`（約33箇所） | `.html`拡張子を除去。TOPへのリンク（`href="/"`、2箇所）はそのまま維持（既に正しい形） |
| `tools/sitegen/templates.py:1627` `detail_url` | `f"/services/{svc['id']}.html"` → `f"/services/{svc['id']}"` |
| `tools/sitegen/generators.py:95` 比較ページURL生成 | `f"/comparisons/{a_id}-vs-{b_id}.html"` → 拡張子なしに変更 |
| `tools/sitegen/generators.py` `pages`リスト | **変更不要**（実ファイル書き込み用のパスとして`.html`付きのまま維持してよい。sitemap生成時にのみ変換すれば十分） |
| Cloudflare側（http→https強制） | P2対応として、`wrangler.toml`または別途Cloudflareのリダイレクトルールで`http://` → `https://`を強制する設定を追加（本リポジトリ外の設定領域の可能性あり、要確認） |

修正後は`python tools/sitegen/validate.py`と`python tools/build.py`で再生成し、生成された`site/sitemap.xml`・各ページのcanonicalが拡張子なしURLで統一されていることを確認する。

---

## 7. 今すぐ修正すべきか、インデックス形成後でよいか

**今すぐ修正すべき（P1として先送りしない）。**

理由:
- サイトは公開2日目で、現時点でインデックス済みのページは`/`の1件のみ（`docs/GOOGLE_INDEX_REQUEST_LOG_2026_08_28.md`時点）。**「守るべき既存のインデックス資産」がまだほぼ無い**ため、修正によって失うものが無い。
- 逆に、この不整合を放置したまま追加でインデックス登録リクエストやクロールを重ねるほど、Googleが`.html`付きURL（リダイレクト元）とその情報を紐付けてクロール履歴・シグナルを蓄積してしまい、**後から直すほど「間違ったURL形での実績」を再学習させ直すコストが増える**。
- 修正自体は`tools/sitegen/templates.py`・`generators.py`内の機械的な文字列置換が中心で、data/differentiate要素・デザイン・機能には一切触れない低リスクな変更。
- ただし本監査のスコープでは実施しない（ユーザー指示により監査のみ）。次の指示で実装するかどうかはユーザー判断に委ねる。

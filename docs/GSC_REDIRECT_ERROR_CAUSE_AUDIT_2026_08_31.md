# GSC「Redirect error」原因監査（2026-08-31）

作成日: 2026-08-31
作成者: Claude Code
範囲: **読み取り専用**。本番URL（`https://ret4853.2070abe.workers.dev`）へのHTTP/HTTPS実測と、リポジトリ内の設定・生成ロジック・既存docの調査のみ。**コード/data/config変更・commit/push/deployは一切行っていない**。
対象URL: `https://ret4853.2070abe.workers.dev/tool/diagnosis.html`（GSC URL検査で「Page is not indexed: Redirect error」「Page fetch: Failed: Redirect error」と表示されたURL）
前提: `docs/GOOGLE_INDEX_REQUEST_LOG_2026_08_28.md`（`.html`版URLへインデックス登録リクエスト実施）と `docs/URL_NORMALIZATION_PRODUCTION_AUDIT_2026_08_28.md`（URL正規化デプロイ確認）の続き。

---

## 0. 先に結論

**原因は、`.html`付き旧URLが返す「307 Temporary Redirect」である。**

- 本件の検査対象URL `…/tool/diagnosis.html` は、サーバー設定（`wrangler.toml` の `html_handling = "auto-trailing-slash"`）により **307（一時リダイレクト）で拡張子なしURL `…/tool/diagnosis` へ転送**される。
- このURLは **2026-08-28にGSCから「インデックス登録をリクエスト」された旧URL**（当時はcanonical/sitemapも`.html`付きだった）。同日のURL正規化で正規URLは拡張子なしに移行したが、Googleは**リクエスト済みの旧URLを後日クロール**した。
- Googleは**301（恒久）と異なり、307（一時）を「恒久的な移転」として処理しない**。旧URLが「自分ではコンテンツを返さず（リダイレクトのみ）、正規URLもまだ未クロール・未インデックス」の状態にあるため、検査結果が「Redirect error（リダイレクト処理に失敗）」となった。
- 現時点のリダイレクト自体は**10/10回一貫して正常**（断続的な障害やループではない）。問題はリダイレクトの**存在**ではなく、**ステータスコードが307**であること。

**推奨修正**: `.html`→拡張子なしのリダイレクトを **301 Permanent Redirect** に変更する。これによりGoogleは旧URLを恒久移転として正規URLへ集約できる。加えて、正規URL（拡張子なし）のインデックスをGSCで促す（sitemap再送信・個別リクエスト）。

---

## 1. 実測データ（2026-08-31）

### 1.1 検査対象URLと周辺URLのレスポンス

| URL | HTTP | リダイレクト先 | 備考 |
|---|---|---|---|
| `/tool/diagnosis.html`（検査対象） | **307** | `…/tool/diagnosis` | **これが原因** |
| `/tool/diagnosis`（正規URL） | 200 | — | canonical=`/tool/diagnosis`、content-type=`text/html`、GTM有 |
| `/tool/diagnosis/` | 307 | `…/tool/diagnosis` | 末尾スラッシュ除去（既存挙動、実害小） |
| `/index.html` | 307 | `…/` | ルート旧URL |
| `/ranking.html` | 307 | `…/ranking` | 旧URL |
| `/services/nosh.html` | 307 | `…/services/nosh` | 旧URL |
| `/404.html` | 307 | `…/404` | — |
| `/googlef4d8b0b633188b1b.html` | 307 | `…/googlef4d8b0b633188b1b` | Google所有権確認ファイル（後述§4.2） |
| `/nonexistent` | 404 | — | 404ページ配信（正常） |

### 1.2 リダイレクトの一貫性・チェーン

- 10回連続リクエスト → **10/10回すべて 307 → `…/tool/diagnosis`**（断続的失敗なし）
- Googlebot UA・`Accept-Encoding: gzip`付きでも同一挙動
- チェーン長: **1ホップ**（`307 → 200`）。ループなし、上限（10ホップ）にも非該当
- robots.txt: `Allow: /`（ブロックなし）／対象ページに`noindex`・`meta refresh`・JSリダイレクトなし
- 対象ページのcanonical: `…/tool/diagnosis`（自己参照、正規URLと一致）

### 1.3 GSCが示した事実（ユーザー提供）

- 最終クロール: **2026-08-29 03:47**（Googlebot smartphone）
- Page fetch: **Failed: Redirect error**
- 参照サイトマップ: **なし**（`sitemap.xml`は拡張子なしURLを記載しているため、旧`.html`URLには紐づかない。整合）
- User-declared canonical: **N/A**（リダイレクトレスポンスにはcanonicalが無いため。整合）
- Google-selected canonical: **N/A**

---

## 2. 時系列（なぜ旧URLがクロールされたか）

| 日付 | 出来事 |
|---|---|
| 〜08-27 | `.html`付きURLがcanonical/sitemap。`/tool/diagnosis.html`等は直接200で配信 |
| 08-28 | URL正規化（3d5952d）デプロイ。canonical/sitemap/内部リンクを拡張子なしへ統一。以降`.html`は307で拡張子なしへ転送 |
| 08-28 | GSCから`.html`版URL（`/tool/diagnosis.html`等）へ「インデックス登録をリクエスト」（`docs/GOOGLE_INDEX_REQUEST_LOG_2026_08_28.md`） |
| 08-29 03:47 | Googleがリクエスト済み旧URL `…/tool/diagnosis.html` をクロール → 307を検出 → 「Redirect error」 |
| 08-31 | 本監査 |

→ 旧URLのクロールは「正規化前にindexリクエストした残留タスク」。正規URL（拡張子なし）はsitemapに載っているが、GSC確認時点で未クロール（`docs/GSC_POST_DEPLOY_STATUS_2026_08_28.md` §5）のため、転送先がまだインデックスされていない状態で旧URLが検査された。

---

## 3. なぜ「Redirect error」になるのか（メカニズム）

1. `html_handling = "auto-trailing-slash"` のCloudflare既定挙動により、`.html`付きURLは**307**を返す（301ではなく）。
2. Googleは307を「一時的な転送」と解釈する。301（恒久）のように旧URLのシグナルを新URLへ集約せず、**旧URL自体を「将来コンテンツを返すべきページ」として扱い続ける**。
3. しかし旧URLは実体として常にリダイレクトを返すため、旧URL単体ではインデックス不能。かつ転送先の正規URLも未クロールのため、「旧URL → 有効なインデックス済みページ」という解決がまだ成立していない。
4. 結果、GSCは「このURLはインデックスできない（リダイレクト処理上のエラー）」と判定。

補足: 転送先（`…/tool/diagnosis`）が200で正常・canonical自己参照・robots許可であることは実測済み。**転送先自体には問題は無い**。転送先がインデックスされ次第、301化した旧URLは自然に集約される見込み。

---

## 4. 推奨修正（未実施・承認待ち）

### 4.1 主修正: `.html` → 拡張子なしを301化

- 現在: `html_handling = "auto-trailing-slash"` が自動生成する**307**
- 変更後: **301 Permanent Redirect** を明示返却

**実装案（Worker + Static Assets構成へ移行）**:

1. `src/worker.js` を新規作成（`site/`外。`site/`は`tools/build.py`が毎回`rmtree`で全削除するため生成物内には置けない）。

```js
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // .html 付き旧URL → 拡張子なし正規URLへ 301 Permanent Redirect
    if (path !== '/' && path.endsWith('.html')) {
      let newPath = path.slice(0, -5);              // ".html" を除去
      if (newPath.endsWith('/index')) newPath = newPath.slice(0, -6) + '/';  // ディレクトリindex → 末尾スラッシュ
      if (newPath === '') newPath = '/';            // ルート
      const target = new URL(newPath, url.origin);
      target.search = url.search;                   // クエリは維持
      return Response.redirect(target.toString(), 301);
    }

    // それ以外は静的アセットとして配信（html_handling / not_found_handling が適用される）
    return env.ASSETS.fetch(request);
  },
};
```

2. `wrangler.toml` に `main = "src/worker.js"` を追記し、`[assets]` に `run_worker_first = true` を明示（Workerを全リクエストの先頭で実行し、`.html`を301化してからアセットへ委譲するため）。

```toml
name = "ret4853"
main = "src/worker.js"          # 追加
compatibility_date = "2026-08-26"

[assets]
directory = "./site"
not_found_handling = "404-page"
html_handling = "auto-trailing-slash"
run_worker_first = true          # 追加
```

3. `npx wrangler deploy` で本番反映。

**変更後の挙動（予測）**:

| URL | 変更後 |
|---|---|
| `/tool/diagnosis.html` | **301** → `/tool/diagnosis` |
| `/index.html` | **301** → `/` |
| `/ranking.html` | **301** → `/ranking` |
| `/tool/diagnosis` | 200（アセット配信、現状維持） |
| `/nonexistent` | 404（現状維持） |
| `/services/nosh/` | 307（auto-trailing-slashのまま。実害小のため変更しない） |

### 4.2 副次的な確認事項

- **Google所有権確認ファイル** `googlef4d8b0b633188b1b.html`: 現状307で拡張子なしへ転送されるが、転送先（`/googlef4d8b0b633188b1b`）が同じ内容を200で返すため、所有権確認は成立済み（GSC表示自体が確認済み）。301化しても転送先が同内容を返すため影響なし。
- **HTTP（非TLS）がHTTPSへリダイレクトされない**（既知P2、`docs/URL_NORMALIZATION_AUDIT_2026_08_28.md` §2.4）: 本件の直接原因ではないため今回のスコープ外。任意で後日対応。
- **正規URLのインデックス促進**: 301化だけでは正規URLのクロールは前倒しされない。GSCで (a) `sitemap.xml` を再送信、(b) 拡張子なし正規URL（`/tool/diagnosis`, `/ranking`, `/services/nosh` 等）へ個別「インデックス登録をリクエスト」を実施することを推奨。

---

## 5. 判断のための補足（307 vs 301）

- 旧URL（`.html`付き）は今後 canonical/sitemap/内部リンクとして二度と使わないURLであり、**恒久的に移転済み**の扱いが正しい → 301が適切。
- 301化によりブラウザ/Googleは転送先をキャッシュするが、転送先URLは安定しているため実害なし。
- Cloudflareの`html_handling`で返る307は設定変更では301に変えられないため、本実装（Workerで明示返却）が必要。

---

## 6. 次のアクション（未実施・承認待ち）

- [x] `src/worker.js` 新規作成と `wrangler.toml` 変更（§4.1）→ **2026-08-31 実装済み**
- [x] `npx wrangler deploy` による本番反映 → **2026-08-31 デプロイ済み（Version ID: 910fa6c4-1b34-460f-8062-04c88bbeef84）**
- [x] 反映後の再実測（§7に詳細）→ **全件成功**
- [ ] GSC: `sitemap.xml` 再送信 ＋ 拡張子なし正規URLへの個別インデックスリクエスト → **GSC操作のためユーザー実施（保留）**
- [ ] 1〜2週間後にGSCで旧URLの「Redirect error」解消と正規URLのインデックス状況を再確認 → **保留**

---

## 7. 実装・デプロイ結果（2026-08-31）

承認後に以下の変更を実施した。**本セクションの変更内容は監査（§1〜5、読み取り専用）の後に追加された実装記録である。**

### 7.1 変更内容

| ファイル | 変更 |
|---|---|
| `src/worker.js` | 新規作成。`.html`→拡張子なしURLへの301リダイレクトを返し、他は`env.ASSETS.fetch()`で配信 |
| `wrangler.toml` | `main = "src/worker.js"`、`[assets] binding = "ASSETS"`、`run_worker_first = true` を追加 |

- `site/` は `tools/build.py` が毎回 `rmtree` するため、Workerは `site/` 外（`src/`）に配置。
- `run_worker_first = true` の際は assets binding が必須（wranglerの警告で検出し`binding = "ASSETS"`を追加）。

### 7.2 本番実測（デプロイ後）

| URL | 結果 |
|---|---|
| `/tool/diagnosis.html` | **301** → `/tool/diagnosis` |
| `/index.html` | **301** → `/` |
| `/ranking.html` | **301** → `/ranking` |
| `/services/nosh.html` | **301** → `/services/nosh` |
| `/googlef4d8b0b633188b1b.html` | **301** → `/googlef4d8b0b633188b1b`（転送先が同内容を200で配信 → 所有権確認に影響なし） |
| `/tool/diagnosis` ほか正規URL（sitemap 34件） | **全34件が200** |
| 旧`.html` URL 全36件 | **全36件が301** |
| `/nonexistent` | 404（維持） |
| `/tool/diagnosis/`（末尾スラッシュ） | 307 → `/tool/diagnosis`（従来挙動のまま・実害小） |

- Googlebot UAでも301を返すことを確認。
- リダイレクトチェーンは1ホップ（301→200）でループなし、5回連続で一貫。
- 正規URLのcanonicalは自己参照（拡張子なし）のまま維持（`/services/nosh`→canonical=`…/services/nosh`）を確認。

### 7.3 GSC操作の実施結果（2026-08-31、Playwrightで実施）

**① `sitemap.xml` 再送信: 完了 ✅**
- GSC Sitemaps で `sitemap.xml` を再送信 → 「Sitemap submitted successfully」を確認
- テーブル更新: Submitted = **Aug 31, 2026** / Status = Success / 検出ページ = 34

**② 拡張子なし正規URLへの個別「インデックス登録をリクエスト」: 4件成功 ✅（5件目は日次上限）**
| URL | 結果 |
|---|---|
| `/tool/diagnosis` | ✅ リクエスト成功（本件の対象URL） |
| `/ranking` | ✅ リクエスト成功 |
| `/services/nosh` | ✅ リクエスト成功（「Indexing requested」ダイアログ確認） |
| `/articles/chef-muten-tukuritoki-kuchikomi` | ✅ リクエスト成功（「Indexing requested」ダイアログ確認） |
| `/services/chef-muten-tukuritoki` | ❌ **Quota Exceeded**（日次上限到達。翌日再試行） |

- 旧`.html`URLへのリクエストは**未実施**（設計どおり。301化済みのため不要）

**③ 旧URL `.html` のライブテスト（301化後の確認）: 改善確認 ✅**
- `https://ret4853.2070abe.workers.dev/tool/diagnosis.html` を「Test live URL」で実測（Aug 31, 8:16 AM）
- 結果: **「URL is available to Google」「Page can be indexed」**
- 307時代のキャッシュ結果（「Redirect error」「Page fetch: Failed: Redirect error」）から**解消**。Google index タブの旧クロール結果（Aug 29）は、次回クロールで更新される見込み
- 証跡スクリーンショット: `.playwright-mcp/gsc-live-test-tool-diagnosis-html-301-ok.png`

**④ 残タスク**
- `/services/chef-muten-tukuritoki` のインデックス登録リクエスト → **翌日（日次上限リセット後）再試行**
- 1〜2週間後にGSCで旧URLの「Redirect error」解消（次回クロール反映）と、正規URL（`/tool/diagnosis` 等）のインデックス状況を再確認

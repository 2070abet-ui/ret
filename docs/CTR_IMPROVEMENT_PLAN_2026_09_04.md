# CTR（クリック数）改善 実装計画（2026-09-04）

作成日: 2026-09-04
作成者: Claude Code
範囲: **計画立案のみ**。コード/data/config変更・commit/push/deploy・GSC操作は**未実施**（実行は承認後）。
前提: `docs/SEARCH_CLICK_RATE_RESEARCH_2026_09_04.md`（調査記録）の続き。表示中ページは`/articles/chef-muten-tukuritoki-kuchikomi`・`/tool/diagnosis`・`/`（表示回数6・クリック0・平均順位38.2）。

---

## 0. 方針

- クリック数の主因は「順位が圏外（38.2）」のため、**本計画は順位を直接上げるものではなく「検索結果での見え方を改善し、上位に入ったときにクリックされる確率を上げる＋スニペット質を上げる」**フェーズ。順位向上は記事追加（独自価値）と被リンク待ち（別計画）が本命。
- 今フェーズで実装する価値が高いのは **(1) 露出中記事の`<title>`/冒頭の改善** と **(2) Breadcrumb JSON-LD導入**。**(3) 検証手順** を付す。
- FAQPageは**廃止済み（2026年5月）**のため不採用。Product/Reviewマークアップは**保留**（自己都合レビュー禁止・affiliate審査リスクのため別途判断）。

---

## 1. 実装①: 露出中記事（chef-muten口コミ）の`<title>`改善

### 1.1 現状と問題
| 項目 | 値 |
|---|---|
| 対象 | `/articles/chef-muten-tukuritoki-kuchikomi`（現在表示回数が発生中） |
| 場所 | `tools/sitegen/templates.py:2311`（`title`）、`2320/2349/2365`に「2026年8月」直書き |
| 現title | `シェフの無添つくりおきの口コミ・評判を徹底検証！料金・送料・メニュー・「まずい？」まで【2026年8月】` |
| 問題 | 約55字＋` | 宅食図鑑`で**60字超**。デスクトップでもモバイルでも末尾が切り詰められやすい。「徹底検証！〜まで」が冗長で、重要語（口コミ・評判）と補助語（料金・まずい?）が離れている。「【2026年8月】」が**直書き**＝月が替わると鮮度ズレ（ranking側は`LAST_VERIFIED_DATE`から自動化済み: `templates.py:1456` 参照）。 |

### 1.2 変更案（承認後にどちらかを採用）
**案A（中程度の短縮・推奨）**
```python
title = "シェフの無添つくりおきの口コミ・評判を検証｜料金・送料・まずい？の真相も解説"
```
**案B（強めの短縮・先頭一致重視）**
```python
title = "シェフの無添つくりおき 口コミ・評判は？料金・まずい？まで検証"
```
- 月表記は**`LAST_VERIFIED_DATE`から自動生成**（`{_lv_year}年{int(_lv_month)}月`）にし、直書きをやめる（ranking/comparisonの方式に統一）。
- クエリ語「シェフの無添つくりおき 口コミ」を先頭に残す。**メニュー/送料等の網羅語は削ってよい**（本文に存在すれば良く、titleで全網羅する必要は無い）。
- 併せて`<h1>`（`templates.py` 該当記事のh1）と、必要な場合は`desc`（2312）も揃えて更新する。

### 1.3 期待効果とリスク
- 期待: 検索結果でタイトルが最後まで読まれ、クエリ意図（口コミ・評判）が一見で伝わる → 同順位でのCTR向上。スニペット採用時に冒頭文の質も寄与。
- リスク: タイトルのキーワード網羅を減らすため、**マイナーなロングテール（「送料」「メニュー」等）で露出を失う可能性はある**。ただし現状はそれらで露出が発生していない（表示は「口コミ」系のみ）ため実害は小さい。

---

## 2. 実装②: Breadcrumb JSON-LD導入（全ページ）

### 2.1 変更場所
- `tools/sitegen/templates.py`
  - `page_header()`（1262〜）に任意引数 `crumbs: list[str] | None = None` を追加
  - `crumbs` が渡されたときだけ`<script type="application/ld+json">`で`BreadcrumbList`を出力（`crumbs=None`は現状どおり何も出さない＝**既存ページ無変更で安全**）
  - `_meta_block()`（1192〜）に隣接して共通のJSON-LD生成関数を追加

### 2.2 サイト階層マップ（crumbs定義案）
内部リンク実体（TOP→比較一覧=rankingがhub）に合わせる:
| ページ | crumbs（右端=現在ページ） |
|---|---|
| `/`（TOP） | なし（WebSiteのみ） |
| `/ranking` | ホーム ＞ 宅配食 比較一覧 |
| `/services/{s_id}` | ホーム ＞ 宅配食 比較一覧 ＞ {サービス名} |
| `/comparisons/{a}-vs-{b}` | ホーム ＞ 宅配食 比較一覧 ＞ {A}と{B}の比較 |
| `/articles/{slug}` | ホーム ＞ 宅配食の記事（URL無し）＞ {記事タイトル} |
| `/tool/diagnosis` | ホーム ＞ 診断ツール |
| `/campaigns` | ホーム ＞ 初回キャンペーン |
| legal / verification | ホーム ＞ {ページ名}（任意） |

- 各`build_*`関数が自ページの名前を持っているので、**crumbsを渡す形で実装**（全ページを1度にやらず、まず表示中ページ群＝記事・診断・TOP/rankingから段階適用も可）。
- 表示確認はデプロイ後に Rich Results Test（実URL）で実施。

### 2.3 注意（公式指針との整合）
- Breadcrumb markup は**ページ上の実際の階層と整合**させるのが推奨（公式）。中間項目（例: 記事一覧URL無し）はURL無しcrumbとして出力可能。
- リッチリザルト（パンくず表示）は**Googleが表示を決定**し、保証は無い。期待は限定的に持つ。
- **可視パンくずUIの追加は今回はしない**（UI変更を伴うため別計画。マークアップのみ先行）。

---

## 3. 実装③: 記事冒頭のスニペット源最適化（chef-muten記事）

- 目的: クエリ「口コミ」に対し、**スニペットは本文から生成される**ため、冒頭に「口コミ・評判」へ直接応える文を置く。
- 現状: 冒頭は「結論：向いている人」（2318〜）から始まり、`<h1>`直後の1文目で口コミへの言及が薄い。
- 変更例（ARTICLE_WRITING_PRINCIPLES準拠・機械的表現を避け読者目線で）:
  > 「シェフの無添つくりおき」の口コミ・評判でよく聞かれる「まずい？」「量が多い？」といった声について、公式サイト・公式FAQの一次情報を基に検証しました。
- 置き場所: `<h1>`直後〜結論カード前のリード文。既存の結論カード（2318〜）の前に1文追加する形。
- この変更は**本文コピー**なので、記事の検証・規約（出典は公式情報のみ）を守ること。

---

## 4. デプロイ後の検証手順
1. `python tools/sitegen/validate.py` → `python tools/build.py` でsite/再生成・差分確認
2. デプロイ（`npx wrangler deploy`）
3. 本番URLで確認: title/meta/JSON-LD（curl または Playwright）
4. **Rich Results Test**（`https://search.google.com/test/rich-results`）でBreadcrumbListの検証
5. 変更した記事URL（`/articles/chef-muten-tukuritoki-kuchikomi`）へ GSC URL検査 → **Request indexing（1回のみ）**
6. **2〜4週間後**: GSC Performance で
   - クエリ別CTR・掲載順位（特に「シェフの無添つくりおき 口コミ」系）
   - 順位20位前後に到達したクエリがあれば、そのページのtitle/meta/冒頭を次のチューニング対象にする
   - 表示回数（9/2以降分）の伸び

---

## 5. 変更対象ファイルまとめ
| ファイル | 変更内容 | データ/schema変更 |
|---|---|---|
| `tools/sitegen/templates.py` | ①chef-muten記事title（2311）/h1/冒頭文、②page_headerにcrumbs任意引数＋BreadcrumbList JSON-LD、③該当build_*へcrumbs渡し | 無し（コード内文字列のみ） |
| `docs/FINAL_REDESIGN_SPEC.md` | 今回は該当なし（可視UI変更なし） | — |

**data/*.json・config/*.jsonは変更しない。site/は再生成物。commit/pushはユーザー明示まで行わない。**

---

## 6. 非採用・保留（理由つき）
| 項目 | 判断 | 理由 |
|---|---|---|
| FAQPage構造化データ | 不採用 | 2026年5月に公式がFAQリッチリザルト廃止・ドキュメント削除 |
| Product/Review（星）マークアップ | 保留 | 自己都合レビュー禁止。affiliateサイトとして審査リスク。適用可否は「実ユーザーレビューに基づくか」を整理してから別途判断 |
| 有料リンク / 過剰なindexリクエスト | 不採用 | スパムポリシー違反 / 効果なし（公式） |
| 可視パンくずUI | 保留 | UI変更を伴うため別計画（マークアップ先行で十分） |

---

## 7. 実装結果（2026-09-04・監査後）

監査（§0〜6の内容を`tools/sitegen/templates.py`実体と突合）を実施し、問題なしと判断して実装した。監査で判明した**計画からの修正点1件**を適用済み。

| 項目 | 実施内容 | 監査での修正 |
|---|---|---|
| ① title簡略化 | chef-muten記事の`title`/`h1`を短縮（**案A採用**）。`【2026年8月】`トークンをtitle/h1から削除 | **月の自動化は不採用**。自動化するとtitleが再び長くなり切詰められるため、鮮度は本文`最終確認日`とmeta descで担保。body内の日付（最終確認日: 2026年8月26日等）は「確認日」の事実なので据え置き |
| ② Breadcrumb JSON-LD | `breadcrumb_jsonld()`追加・`page_header()`に`crumbs`任意引数（既定None＝無出力で後方互換）。対象: services/ranking/campaigns/comparisons/diagnosis/記事5本 | 変更なし |
| ③ 冒頭リード文 | `<h1>`直後の`price-meta`行の後（結論カード前）に「口コミ・評判・まずい？を一次情報で検証」のリードを1文追加 | 挿入位置を`price-meta`直後と確定 |

**実装後の検証**:
- `python -m py_compile` OK／`python tools/build.py`（38ページ生成）OK／`python -m sitegen.validate` exit=0
- 生成HTMLで確認: chef記事title短縮・各対象ページに`BreadcrumbList`JSON-LDが出力（JSONパースOK）。TOP/法務/検証/404には出力されないことを確認
- 例（services/nosh）: 宅食図鑑 ＞ 比較一覧 ＞ nosh（ナッシュ）

**変更ファイル**: `tools/sitegen/templates.py`（data/schema・configは変更なし）

---

## 8. デプロイ・検証結果（2026-09-04）

| 手順 | 結果 |
|---|---|
| push | ✅ `origin/main` 反映（87e3f5b） |
| デプロイ | ✅ `npx wrangler deploy`（Version ID: b8239a1d-3729-48cd-b145-4d72818abf45）。本番URLで新title・Breadcrumb JSON-LD・リード文の反映を確認 |
| **Rich Results Test**（記事URL） | ✅ **Breadcrumbs: 1 valid item detected**（"Valid items are eligible for Google Search's rich results."）。クロール成功（Sep 4, 2026） |
| **記事URLのRequest indexing** | ✅ `/articles/chef-muten-tukuritoki-kuchikomi` をGSC URL検査→リクエスト（"URL was added to a priority crawl queue"）。1回のみ実施 |
| 2〜4週間後の再確認 | ⏳ 予定（2026-09-07以降至近）: GSC Performanceでクエリ別CTR・掲載順位・表示回数（9/2以降分）を確認 |

**備考**: 本番デプロイはWindows環境変数`CLOUDFLARE_API_TOKEN`（User）をPowerShellから読み込んで実行した（このセッションのBash環境には未継承のため）。Workers BuildsのGit連携による自動デプロイは未設定の模様（push後も本番が更新されないことを確認）。

# TOP 段階開示（Progressive Disclosure）実装報告（2026-08-28）

前段：`docs/TOP_PROGRESSIVE_DISCLOSURE_FINAL_AUDIT_2026_08_28.md`（判定「このまま実装してよい」）
本書：上記設計どおり実装し、build/validate/Playwright実画面確認/4ページ回帰確認までを行った結果報告。

**commit・push・deployは一切行っていない。**

---

## 0. 制約文書の更新（実装に先立って実施）

ユーザー指示により`docs/UI_DESIGN_PRINCIPLES.md` 8章の評価・ランキング条項を、全面禁止から条件付き許可へ更新した。

- 変更前：「根拠のないランキング・★評価・ブラックボックススコア（「1位が最良」と誤読されるUI）」を恒久的にやらないことの一項目として全面禁止。
- 変更後：8.1節を新設し、「原則として安易な★評価・総合ランキングは導入しない。ただし十分なデータ量・明示された評価基準・再現可能な算定方法・検証可能な根拠が揃った場合は、別途監査・承認のうえ導入可能とする」と条件付き許可に変更。あわせて「今回（TOP段階開示UI）ではランキングを導入しない」「将来導入時は独立した評価基準・データ品質・バイアス・表示方法を事前監査する」「根拠のない『おすすめNo.1』『編集部評価』は引き続き禁止」を明記。

今回の段階開示実装自体は、この条項変更後も**新規の評価基準を一切導入していない**（既存の`services.json`記載順をそのまま使う表示上の切り分けのみ）。

---

## 1. 変更ファイル

| ファイル | 内容 |
|---|---|
| `docs/UI_DESIGN_PRINCIPLES.md` | 8章の評価・ランキング条項を条件付き許可へ更新（上記0節） |
| `tools/sitegen/templates.py` | TOP段階開示UIの実装本体（詳細は2章） |

`data/*.json`・`config/*.json`は無変更。

---

## 2. 変更内容

### 2.1 サービスカードの分割（`build_index_page()`）

- 従来の単一ループを`_svc_card_html(svc, extra_class="")`という内部ヘルパー関数に切り出し、`services`配列を**並び替えずにスライスするだけ**で3グループに分割：
  - `services[:4]`：常時表示（PC・モバイル共通）
  - `services[4:6]`：`svc-extra-initial`クラス付与。PC（900px以上）のみ常時表示、モバイルはCSSで非表示
  - `services[6:]`：`<details class="svc-more">`内に格納し、初期状態は閉
- 各カードに`id="svc-{service_id}"`を付与（目的チップからのアンカー先）。
- カード内部の構造（名前→価格→target→タグ→CTA）・`_price_inline_html()`・`aff_link()`の呼び出しは無変更。

### 2.2 「残りを見る」（ネイティブ`<details>/<summary>`）

- 既存のFAQアコーディオン（`service_faq_block()`、`<details class="faq-item">`）と同じ**JS不要のネイティブHTML機構**を採用。新規JSライブラリ・フレームワークは追加していない。
- `<summary>残り{N}社をすべて見る</summary>`のNは`len(svc_more_list)`から動的算出（ハードコードなし）。
- CSSは既存トークン（`--color-primary`・`--color-border-strong`・`--space-*`・`--radius-sm`）のみを使用し、新規の色・新規のデザインシステムは作っていない。見た目は`.btn-primary`（実CTA）と明確に区別した中立トーン（枠線のみ、押し売り感のない文言）。

### 2.3 目的チップ→カードへのアンカー連携（`purpose_chips_block()`）

- `with_anchor`引数を新設（既定False、TOPのみTrue）。TOP呼び出し時のみ、各サービスリンクの隣に`#svc-{id}`へのページ内アンカー（「↓」、`aria-label`付き）を追加。
- 既存の詳細ページへの直リンクはそのまま維持し、アンカーは**選択肢を1つ追加するだけ**。他ページ（`ranking.html`等で使われる同関数呼び出し）は`with_anchor`未指定＝Falseのままで無変更。

### 2.4 任意の補助JS（約10行、コア機能には不要）

- フラグメント遷移（`#svc-xxx`）で対象カードが閉じた`<details>`内にある場合、Chromium系ブラウザはHTML標準のネイティブ挙動で自動的に開く。非対応ブラウザ向けの保険として、`location.hash`を見て該当`<details>`を開くだけの最小限のインラインJSを追加（`svc_more_list`が存在する場合のみ出力）。
- このJSが動かなくても、「`<summary>`の位置までは到達し、もう1クリックで見える」という軽微な劣化に留まり、機能自体は失われない。

### 2.5 `page_header()`/`build_index_page()`のその他

第1段階（`container-top`・`service-grid`・`trust-panel-compact`・`purpose-section-top`）から**変更なし**。今回追加したのは上記2.1〜2.4のみ。

---

## 3. build/validate結果

```
python tools/build.py   → 生成完了: 32ページ + sitemap.xml + robots.txt（exit 0）
python -m sitegen.validate → exit 0（エラーなし）
```

---

## 4. QA結果（10項目）

Playwrightで`http://localhost:8791/`（ビルド後のローカル配信）を確認。

| # | 項目 | 結果 |
|---|---|---|
| 1 | `python tools/build.py` | ✓ exit 0、32ページ生成 |
| 2 | `python -m sitegen.validate` | ✓ exit 0 |
| 3 | PC（1440×900）：初期6社→全15社への展開 | ✓ 初期表示6枚（2行×3列）、「残り9社をすべて見る」クリックで9枚が同一`.service-grid`スタイルのまま展開。展開後は第1段階の見た目とピクセル単位で同一 |
| 4 | モバイル（375×812）：初期4社→全15社への展開 | ✓ 初期表示4枚、タップで9枚展開。console errorなし |
| 5 | 「残りを見る」の開閉・キーボード操作・表示状態 | ✓ `summary`にフォーカス→Enterキーで`details.open`が`true`に切り替わることを確認。マーカーが▾→▴に変化 |
| 6 | 目的チップから該当カードへのアンカー遷移 | ✓ 折りたたみ内（7枚目以降）のカードへのアンカー（例：マッスルデリ）をクリックし、`<details>`が自動的に開いて対象カードがビューポート最上部（top≈0px）に来ることを実測確認 |
| 7 | 横スクロール・カード高さ崩れ・CTA折返し | ✓ PC/モバイルとも`body.scrollWidth ≤ innerWidth`（横スクロールなし）。展開後のカード群は第1段階と同一CSSのため崩れなし |
| 8 | 既存4ページ（比較一覧・詳細・診断・比較）の回帰確認 | ✓ 4ページとも`<main class="container">`（1000px、無変更）を確認。`.svc-more`・`.purpose-anchor`・`.container-top`はいずれのページのHTML本文にも一切出現せず。診断ツールはチェック→診断実行→「あなたの条件に近い上位3社」の表示まで正常動作 |
| 9 | console error | ✓ TOP（PC/モバイル）・4回帰ページすべてで0件 |
| 10 | data/config/affiliate/SEO/診断ロジックの差分 | ✓ `git diff`で`data/`・`config/`ディレクトリの差分ゼロを確認。`aff_link()`関数本体・`page_header()`のtitle/canonical生成部・`build_diagnosis_tool()`（診断ロジック）への差分もゼロ（grep監査済み） |

---

## 5. Playwright実測値（Before/After）

| 指標 | 実装前（第1段階のみ） | 実装後（段階開示） | 変化 |
|---|---|---|---|
| PC総ページ高さ | 2616px | **2057px** | ▲21% |
| PC サービス一覧セクションの高さ（初期状態） | 1192px | **603px** | ▲49% |
| モバイル総ページ高さ | 5819px | **3195px** | ▲45% |
| モバイル サービス一覧セクションの高さ（初期状態） | 3702px | **1019px** | ▲72% |
| PC初期表示カード数 | 15枚（全件） | **6枚**（＋展開で15枚） | — |
| モバイル初期表示カード数 | 15枚（全件） | **4枚**（＋展開で15枚） | — |

---

## 6. 残存問題

なし。前回監査（`TOP_PROGRESSIVE_DISCLOSURE_FINAL_AUDIT_2026_08_28.md`）で判定した設計をそのまま実装し、QA10項目・実測値ともに想定どおりの結果が得られた。スコープ外の追加変更（リファクタリング等）は行っていない。

---

## 7. git diff監査サマリー

- 変更ファイル：`docs/UI_DESIGN_PRINCIPLES.md`（条項更新）、`tools/sitegen/templates.py`（実装本体）の2件のみ。
- `data/*.json`・`config/*.json`：差分ゼロ。
- `aff_link()`本体・href/rel生成ロジック：差分ゼロ（`cls`引数の値は既存の`text-link`のまま、今回変更なし）。
- `page_header()`のcanonical/title/meta生成部：差分ゼロ。
- `build_diagnosis_tool()`（診断ロジック）：差分ゼロ。
- 新規クラス（`.svc-more` `.svc-extra-initial` `.purpose-anchor` `.purpose-service-link`）はTOP専用で、他ページ生成コードには一切登場しない（コード上・生成HTML上の両方で確認済み）。

commit・push・deployは行っていない。次のステップとしてユーザー承認後にcommit/pushを行う想定。

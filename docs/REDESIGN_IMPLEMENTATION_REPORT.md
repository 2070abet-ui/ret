# 宅食図鑑 全面リデザイン 実装報告（2026-08-27）

作成日: 2026-08-27
作成者: Claude Code
基準文書: `docs/FINAL_REDESIGN_SPEC.md`
commit/push: **未実施**（指示により実施しない）

---

## 1. 実装内容

`FINAL_REDESIGN_SPEC.md` 13.3節の分類のうち、**MUST MATCH・COPY BASELINE・DIFFERENTIATEに分類された項目のみ**を実装した。DATA FIRST/DEFER/DO NOT BUILDには一切着手していない。

### MUST MATCH
1. **TOPページのキャンペーン表示に実額を反映**：`campaigns.json`の`discount_type`（実額）を使用し、確認済み（`requires_verification:false`）のキャンペーンを優先して最大3件表示するよう変更。
2. **service detailの「こんな方におすすめ」早期セクション**：既存`target`フィールドを、基本情報テーブルの1行から独立した早期カードへ格上げ。
3. **TOP・rankingの目的別導線カード**：既存`tags`/`target`の部分一致のみで5カテゴリ（無添加/高齢者/減塩/一人暮らし/ダイエット）を算出し、新規データ・新規エンジンなしで実装。

### COPY BASELINE
4. service detailのCTA回数を2→3に（ページ末尾に公式サイトCTAを追加）。
5. 確認日のH1直下再掲（`service.last_checked`をそのまま表示）。
6. diagnosis結果の上位3件キャップ＋一致理由表示。
7. service detailへのFAQセクション新設（`cancellation_note`/`shipping.notes`/`target`の再構成のみ、新規データ収集なし）。

### DIFFERENTIATE
8. **検証カバレッジ表示**：TOP・ranking・verification.htmlで共有する集計ロジック（`compute_verification_coverage`）を新設し、33項目中の確認済み件数を表示。
9. **「全項目確認済み」バッジ**：**CONFIRMEDのみを対象とし、DERIVEDは含めない**厳格な判定（`compute_fully_verified_ids`）。ranking.htmlのサービス名セルに表示、並び順には一切影響させない。
10. **比較ページの差分自動強調**：両社とも価格がconfirmed/derivedの場合のみ価格差を算出（`_comparison_price_diff_html`）、targetの集合差分を「Aが向いている人／Bが向いている人／どちらでも」に分解表示（`_comparison_target_diff_html`）。

### ranking.htmlの名称変更（5章の最終判断を反映）
「ランキング」の呼称・数値順位付けを廃止し、「比較一覧」に変更。**確認済み項目数などいかなる基準でも並び順は変更していない**（`services.json`記載順を維持）。URL（`ranking.html`）・グローバルナビの文言（「おすすめ比較」）は仕様書の指示通り変更していない。

---

## 2. 仕様書との対応表

| FINAL_REDESIGN_SPEC.md 項番 | 実装状況 |
|---|---|
| 6章 TOP設計 | 実装済み（目的別カード→検証カバレッジ→キャンペーン実額→診断→11社リストの順） |
| 7章 ranking設計 | 実装済み（名称変更・目的別カード共有・カバレッジ・全項目確認済みバッジ） |
| 8章 service detail設計 | 実装済み（こんな方におすすめ・確認日再掲・FAQ・CTA3回） |
| 9章 comparison設計 | 実装済み（結論の先出し・向いている人の差分） |
| 10章 diagnosis設計 | 実装済み（上位3件キャップ・一致理由・全件は比較一覧へ誘導） |
| 11章 campaigns設計 | **変更なし**（既存が既に実額表示済みと確認済みのため対応不要、仕様書通り） |
| 12章 verification設計 | 実装済み（集計サマリー追加。TOP/rankingからの直接導線は目的別カード経由で確保） |
| 13.1 CTA設計 | 実装済み（2階層維持、service detailのみ回数調整） |
| 13.2 モバイル設計 | 変更なし（横スクロール方式を維持する、という設計の通り不変更） |

---

## 3. 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `tools/sitegen/generators.py` | `PURPOSE_CATEGORIES`定義、`compute_purpose_matches`/`compute_verification_coverage`/`compute_fully_verified_ids`を追加。`main()`で計算し各build_*関数に渡す配線を追加 |
| `tools/sitegen/templates.py` | `coverage_stat_html`/`purpose_cards_block`/`fully_verified_badge`/`service_recommend_block`/`service_faq_block`/`_comparison_price_diff_html`/`_comparison_target_diff_html`を新規追加。`build_index_page`/`build_ranking_page`/`build_verification_dashboard`/`build_service_page`/`build_comparison_page`/`build_diagnosis_tool`を変更。CSSに`.vfull-badge`を1行追加 |
| `data/*.json` / `config/*.json` | **変更なし**（`git status`で確認済み） |

`site/`配下24ページすべてが再生成された（新規ページ0、削除ページ0）。

---

## 4. UI変更箇所（実際の生成物で確認）

- **TOP**: 目的別カード（5カテゴリ、カード内ネストなし）→検証カバレッジ一言→キャンペーン実額表示（nosh「初回¥1,500 OFF＋継続割引」等）→診断導線→11社カードリストの順で確認。
- **比較一覧（ranking.html）**: タイトル/H1が「宅配食 比較一覧【2026年8月最新】」に変更されたことを確認。目的別カード・カバレッジ一言を追加。シェフの無添つくりおき・食楽膳の2社のみに「3項目とも確認済み」バッジが付き、健康直球便（価格が算出値のため対象外）には付いていないことを実際のHTMLで確認。
- **service detail**: 健康直球便のページで、H1直下に「最終確認日: 2026-08-26」、「こんな方におすすめ」カード（高齢者・塩分制限・健康志向）、FAQ（3問）、末尾CTA（実際のA8リンク）が正しく挿入されていることを確認。
- **comparison**: 食楽膳vs健康直球便で「食楽膳の方が1食あたり227円安い」（351円と578円の差、算出正解）を確認。nosh vs 三ツ星ファームでは、noshの価格が未確認のため価格差は表示されず、targetの差分（時短／おいしさ重視／共通3件）のみ表示されることを確認（存在しない精度を主張しない設計が機能している）。
- **diagnosis**: JS変更をコードトレースで確認（5章参照）。
- **campaigns.html**: 変更なし（意図通り）。
- **verification.html**: 集計サマリー「計33項目中11件を公式一次情報で確認済み（算出値2件・確認中1件は含みません）」を追加。自己参照リンクは出していない。

---

## 5. テスト結果

| # | チェック内容 | 結果 |
|---|---|---|
| 1 | build成功 | ✅ 24ページ生成（増減なし） |
| 2 | 2回連続buildで完全一致 | ✅ `diff -rq`で差分ゼロ（デザイン修正後に再検証済み） |
| 3 | 全26スクリプトブロックの構文検証 | ✅ `node --check`で全て合格 |
| 4 | 内部リンクの網羅チェック | ✅ 26ページ中、存在しないパスへの`href`はゼロ |
| 5 | CSS括弧の対応 | ✅ 開き35・閉じ35で一致 |
| 6 | サービス詳細ページのCTA数 | ✅ 11社すべてで3個（`rel="nofollow sponsored"`の出現数） |
| 7 | data/config無変更の確認 | ✅ `git status`でdata/・config/配下に変更なし |

---

## 6. SEO監査

| 項目 | 結果 |
|---|---|
| canonical | 変更なし（全ページ既存の値を維持） |
| sitemap.xml | diffゼロ（ページ増減が無いため） |
| robots.txt | diffゼロ |
| title/H1 | ranking.htmlのみ意図的に変更（「宅配食おすすめ比較ランキング」→「宅配食 比較一覧」）。他ページは既存を維持 |
| JSON-LD | 変更なし（`WebSite`型のみ、他タイプの混入なし） |
| 内部リンク | 目的別カード・診断ツールの「比較一覧で全件見る」リンクを含め、すべて実在パスへの参照であることを確認（4章の内部リンクチェック） |
| meta description | ranking.htmlのみ「順位付けはせず、確認できた情報のみを一覧にしています」を追記。他ページは変更なし |

---

## 7. データ整合性監査

- 検証カバレッジの表示値（confirmed 11／derived 2／pending 1／uncollected 19、計33）を、`templates.py`のロジックとは独立に**別途Pythonスクリプトで再実装して再計算**し、完全に一致することを確認した。
- 「全項目確認済み」バッジの対象が`chef-muten-tukuritoki`・`syokurakuzen`の2社のみであることを、同じ独立再実装で確認した。健康直球便（価格`derived`）が対象外であることを明示的に確認済み。
- 比較ページの価格差算出（食楽膳351円 vs 健康直球便578円 → 227円差）を手計算で検算し一致を確認。
- 出典リンク・確認日・source_idの対応関係は今回一切変更していない（Phase2〜4の既存ロジックをそのまま再利用したのみ）。

---

## 8. 差別化機能の動作確認

| 機能 | 確認内容 | 結果 |
|---|---|---|
| 検証カバレッジ | TOP・ranking・verification.htmlの3ページで同一の数値（11/33等）が表示されているか | ✅ 一致（共有ロジックのため） |
| 全項目確認済み判定 | CONFIRMEDのみを対象とし、DERIVED/PENDING/UNCOLLECTEDを誤って含めていないか | ✅ 独立再計算で確認（7章）。健康直球便（derived）を除外できている |
| 比較差分強調 | 価格が両社とも確認済み/算出値の場合のみ価格差を表示し、片方でも未確認なら非表示になるか | ✅ 3ペアで動作確認（5章）。target差分は共通項目のみの場合でも正しく「どちらでも当てはまる人」として表示される |

---

## 9. スコープ逸脱の有無

**逸脱なし。** `FINAL_REDESIGN_SPEC.md`のMUST MATCH/COPY BASELINE/DIFFERENTIATE以外の項目（DATA FIRST/DEFER/DO NOT BUILD）には一切着手していない。ranking.htmlの並び順・スコア・★評価・推薦エンジン・新規Theme・口コミ機能・sticky CTA・モバイルカード化は実装していない。

実装中に発見した軽微な改善余地は、その場で追加実装せず以下の通り本レポートに記録するに留めた。

- 目的別カードを最初`.card`の中に`.card`をネストする構成で実装したが、「デザイン方針：必要以上にカード化・装飾化しない」という仕様書の原則に照らして過剰と判断し、実装中に単一の外枠カード＋軽量ブロックへ修正した（スコープ内の是正として対応済み、追加のスコープ拡大ではない）。

---

## 10. 未解決事項

1. **モバイル実機確認ができていない**：本環境にはブラウザ描画確認の手段が無く、CSS定義（flexboxの折り返し・`.card`の`overflow-x:auto`等）の静的な確認に留まる。目的別カード・FAQ・結論カード等、新規追加した要素が実際のスマートフォン幅でどう見えるかは未検証。
2. **グローバルナビ文言（「おすすめ比較」）の統一可否**：`FINAL_REDESIGN_SPEC.md` 5.2節の通り、今回は意図的に対象外とした。ranking.htmlのページ内文言は「比較一覧」に統一されたが、サイト全体のナビゲーションラベルとの表記ゆれが残っている。
3. **診断ツールの「一致理由」表示の実ブラウザ動作**：JSロジックは構文検証・コードトレースで確認したが、実際のチェックボックス操作による動作確認は本環境では実施していない。

---

## 11. 次の判断事項

1. 上記「未解決事項」1・3について、実機またはブラウザ検証環境での確認を推奨する。
2. グローバルナビ文言の統一要否をユーザー側で判断する（未解決事項2）。
3. `FINAL_REDESIGN_SPEC.md`のDATA FIRST項目（ranking価格ソート・フィルタ、CTA文言の実額反映等）は、GA4のベースライン計測・データ充足の進捗を待って別途判断する。
4. 本リデザインの効果測定（目的別カードのクリック率、検証カバレッジ表示の閲覧・遷移率、比較ページの差分強調がCVに与える影響等）は、Phase4で導入したGA4のベースライン計測後に評価する。
5. commit/pushの指示を待つ。

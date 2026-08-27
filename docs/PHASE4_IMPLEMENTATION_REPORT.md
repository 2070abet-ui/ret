# 宅食図鑑 Phase4 実装報告（2026-08-27）

作成日: 2026-08-27
作成者: Claude Code
基準文書: `docs/PHASE4_FINAL_DECISION.md`（GO判定を受けた3項目のみを実装）
commit/push: **未実施**（指示により実施しない）

---

## 1. 実装した変更

### 1.1 GA4最小計測（`diagnosis_start` / `diagnosis_complete`のみ独自実装）

- **既存GA4設定の事前確認**: 実装前に`tools/sitegen`・生成済み`site/`をgrepし、`gtag`/`G-`測定ID/`dataLayer`/`googletagmanager`のいずれも存在しないことを確認済み（二重計測の懸念なし）。
- `config/site.json`に`ga4_measurement_id`キーを追加（空文字。ユーザーがGA4プロパティ作成後に値を入れる前提）。
- `tools/sitegen/data.py`に`GA4_MEASUREMENT_ID`定数を追加（`site.json`から読み込み、未設定時は空文字）。
- `tools/sitegen/templates.py`に`_ga4_block()`を追加し、`page_header()`から全ページ共通で出力。
  - 測定ID未設定の間は、外部スクリプト（googletagmanager.com）を**一切読み込まず**、`dataLayer`へpushするだけの安全な`gtag()`スタブのみを出力する（実際の送信は発生しない）。
  - 測定IDが設定されて初めて外部スクリプトを読み込み、`gtag('config', ...)`を発行する設計。
- `outbound_cta_click`・`internal_nav_click`は**独自実装しなかった**（`PHASE4_FINAL_DECISION.md` 1章の判断通り、GA4拡張計測機能の`outbound_click`／`page_view`パス探索で代替可能なため）。
- `diagnosis_start`: `tool/diagnosis.html`の目的・保存方法チェックボックスに`change`リスナーを追加し、初回操作でのみ1回発火（`_diagStarted`フラグで多重発火を防止）。
- `diagnosis_complete`: `runDiag()`内、`scored`計算後・結果描画前に追加。「条件未選択で診断ボタンを押した」早期returnケースでは発火しない位置に配置（実際に診断を実行した回数のみを計測）。パラメータは`goal_count`/`mealform_count`/`result_count`。

### 1.2 出典接続漏れの是正

事前に全11社×3フィールド（price/shipping/campaign）を機械的に再監査し、「確認済み/算出値なのに`source_id`が無い」セルを網羅的に洗い出した（想定していた2件に加え、同条件のもう1件を新たに発見）。

| サービス | フィールド | 追加した`source_id` | 根拠 |
|---|---|---|---|
| nosh | shipping | `nosh-shipping-202608` | `sources.json`に既存（nosh公式送料ページ、確認日2026-08-27） |
| shokutakubin | shipping | `shokutakubin-shop-202608` | `sources.json`に既存（食宅便通販サイト、確認日2026-08-27） |
| shokutakubin | price_plan | `shokutakubin-shop-202608` | **新規発見**。price_planの690円算出根拠も同一の出典ページに記載されており、shippingと同じ`source_id`を共有できる（chef-muten-tukuritokiで既に確立済みの「1出典から複数フィールドを確認した場合は共有してよい」というPhase2の原則を踏襲） |

いずれも`data/shipping.json`・`data/services.json`への`source_id`キー追加のみ（3行）。新規の一次情報収集・推測・データモデル拡張は無い。テンプレート側の変更も不要（既存の`source_link()`／`price_cell_html()`がそのまま機能した）。

**Rule of Threeとの関係**: `PHASE4_FINAL_DECISION.md` 3.1節の解釈明確化（「新規の一次情報収集を伴わない、既存確認済みデータへの出典接続はRule of Threeの対象外」）に従って実施した。

### 1.3 モバイル横スクロール案内

- CSS: 共通`<style>`に`.mobile-scroll-hint`クラスを追加（デスクトップでは非表示、640px以下でのみ表示）。既存の`overflow-x:auto`／`table{{min-width:480px}}`の仕組みはそのまま変更していない。
- `mobile_scroll_hint()`関数を追加し、以下5ページの幅広テーブル直前にのみ設置（対象を限定し、デザイン変更を広げていない）:
  - `ranking.html`
  - `verification.html`
  - `comparisons/*.html` ×3

サービス詳細ページ（2列×4行の基本情報テーブル）・トップ・キャンペーン一覧・診断ツール・記事・法務ページには追加していない（幅広の比較テーブルではないため対象外と判断）。

---

## 2. 実装しなかった項目

- `outbound_cta_click` / `internal_nav_click`（GA4拡張計測で代替可能と判断、1.1節）
- JSON-LD拡充、CTA文言最適化、ranking価格ソート、高齢者Theme、減塩/無添加/高タンパクTheme、口コミ機能、比較社数拡大、推薦エンジン、matching DSL、Theme汎用エンジン、UpdateLog基盤、複雑な計測基盤 — いずれも`PHASE4_FINAL_DECISION.md`の指示通り着手せず
- shipping/price残りの未確認セル（watami/mitsuboshi/wellness/fit-food-home/magokoro/yoshikei）、magokoro-careのcampaignエントリ新設、FIT FOOD HOME公式ドメイン確定 — いずれもデータ収集が前提のため今回は対象外（`PHASE4_FINAL_DECISION.md` 4章のB分類のまま）

---

## 3. テスト結果

| # | チェック内容 | 結果 |
|---|---|---|
| 1 | build成功 | ✅ 24ページ生成（ページ数の増減なし、想定通り） |
| 2 | 2回連続buildで冪等 | ✅ `diff -rq`で差分ゼロを確認 |
| 3 | JSON妥当性 | ✅ `config/site.json`・`data/services.json`・`data/shipping.json`とも有効なJSONであることを確認 |
| 4 | JS構文チェック | ✅ `tool/diagnosis.html`・`ranking.html`内の全`<script>`ブロックを抽出し`node --check`で構文エラー無しを確認 |
| 5 | GA4スタブの設置範囲 | ✅ `page_header()`を使う24ページ全てに設置。`404.html`・GSC確認用ファイルの2ページは元々`page_header()`を使わない独立ページのため対象外（既存仕様、今回の変更によるものではない） |
| 6 | GA4外部スクリプトの不発火 | ✅ 測定ID未設定のため`googletagmanager.com`への参照がsite全体に存在しないことを確認 |
| 7 | diagnosis_start/diagnosis_completeの発火条件 | ✅ コードトレースで確認：①`diagnosis_start`はチェックボックス初回操作でのみ1回発火（フラグガード）②`diagnosis_complete`は「未選択で診断ボタン」早期returnケースでは発火せず、実際にスコアリングが走った場合のみ発火 |
| 8 | 出典リンクとsources.jsonの対応 | ✅ 新規追加した2つの`source_id`（`nosh-shipping-202608`／`shokutakubin-shop-202608`）が`sources.json`に実在することを確認。全11社×3フィールドを再走査し、他に「確認済みなのにsource_idが無い」セル・「source_idがあるがsources.jsonに存在しない」セルが無いことを機械的に確認 |
| 9 | 未確認データへの出典リンク誤付与 | ✅ 今回の3件はいずれも既存のconfirmed/derivedステータスのセルのみが対象で、pending/uncollectedのセルには一切手を加えていない |
| 10 | ASP内部情報の漏洩 | ✅ `reward_yen`・`報酬`（サイト共通のPR開示文以外）・`program_id`・`a8mat`（アフィリエイトhref以外の文脈）のいずれも新規混入なし |
| 11 | canonical/sitemap/robots | ✅ 3者ともdiffゼロ（ページ増減・URL変更が無いため） |
| 12 | モバイル表示 | ✅ CSSレベルで確認（`.mobile-scroll-hint`が640px以下でのみ`display:block`になることをスタイル定義で確認）。**実機/実ブラウザでの目視確認は本環境では実施できていない**（4章に明記） |
| 13 | git diff全件確認 | ✅ 4章参照 |

---

## 4. 差分監査（git diff全件）

変更ファイル: `config/site.json`、`data/services.json`、`data/shipping.json`、`tools/sitegen/data.py`、`tools/sitegen/templates.py`、および上記コード変更に伴う`site/`配下24ページの再生成分。

- **config/site.json**: `ga4_measurement_id: ""`追加、コメント更新のみ。
- **data/services.json**: shokutakubinの`price_plan`に`source_id`追加のみ（1箇所）。
- **data/shipping.json**: nosh・shokutakubinの`shipping_rules`に`source_id`追加のみ（2箇所）。
- **tools/sitegen/data.py**: `GA4_MEASUREMENT_ID`定数追加のみ（+2行）。
- **tools/sitegen/templates.py**: `_ga4_block()`・`mobile_scroll_hint()`の追加、`page_header()`・`build_ranking_page()`・`build_comparison_page()`・`build_verification_dashboard()`・`build_diagnosis_tool()`への呼び出し追加。既存関数のロジック削除・置換は無し（純追加）。
- **site/配下**: 全24ページで①GA4スタブ`<script>`1行が`<head>`に追加 ②CSSに`.mobile-scroll-hint`定義が追加、の2点が共通差分。加えて、`ranking.html`・`verification.html`・比較ページ3本にモバイル案内文言1行、`tool/diagnosis.html`にGA4イベントコード、`services/nosh.html`・`services/shokutakubin.html`・`verification.html`に出典リンクが追加。**それ以外の意図しない差分は無い**（全ファイルのdiffを目視確認済み）。

---

## 5. 新たに発見した問題（スコープ外のため未対応、記録のみ）

指示通り、実装範囲を超える問題はその場で修正せず、ここに記録する。

1. **README.mdの公開URL記載とconfig/site.jsonの実URLの不一致**（Phase3の監査で既出、今回も未解消のまま）: README.mdは`https://takushokuzukan.workers.dev`と記載しているが、`config/site.json`・実際のcanonicalは`https://ret4853.2070abe.workers.dev`。ドキュメントの整合性の問題であり、サイトの技術的な破損ではない。
2. **モバイル実機確認の手段が本環境に無い**: `.mobile-scroll-hint`のCSSロジックは静的に確認したが、実際のスマートフォン/ブラウザでの見た目（横スクロールの挙動、案内文言の視認性）は未検証。次回、実機またはブラウザ検証ツールでの確認を推奨する。
3. **GA4測定IDが未設定のため、`diagnosis_start`/`diagnosis_complete`の実動作（実際にGoogleにデータが届くか）は未検証**: コードロジックの正しさはトレースで確認したが、測定IDが入るまでエンドツーエンドの動作確認はできない。ユーザーがGA4プロパティを作成し測定IDを設定した後、実ブラウザでのイベント発火確認（GA4のDebugViewの利用等）を推奨する。

---

## 6. Phase4完了判定

**完了。** `PHASE4_FINAL_DECISION.md`でGO判定を受けた3項目（GA4最小計測・出典接続漏れ修正・モバイル横スクロール案内）をすべて実装し、3章の回帰チェック13項目をすべて通過した。新機能・新規Theme・推薦エンジン等のスコープ外機能への越境は無い。

---

## 7. 次に実施すべきこと

1. **ユーザー側作業**: GA4プロパティを作成し、測定IDを`config/site.json`の`ga4_measurement_id`に設定して再ビルド・再デプロイする。
2. 設定後、ブラウザのGA4 DebugView等で`diagnosis_start`/`diagnosis_complete`が意図通り発火し、二重発火が無いことを実環境で確認する。
3. モバイル実機（またはブラウザの端末エミュレーション）で`.mobile-scroll-hint`の表示・横スクロール挙動を目視確認する。
4. 2〜3週間のベースライン計測期間を確保した後、`PHASE4_FINAL_DECISION.md` 6章のKPI（`outbound_click`のサービス別内訳、診断完了率、`/verification.html`の閲覧・遷移率、出典リンクのクリック率）を確認する。
5. データ品質優先順位（`PHASE4_FINAL_DECISION.md` 4章）に沿って、yoshikei価格・FIT FOOD HOME公式ドメイン確定のデータ収集を継続する（本Phaseのコード実装スコープには含めない）。
6. 5章に記録した3件のスコープ外事項（README.mdのURL不一致、モバイル実機確認、GA4エンドツーエンド確認）は、次回の監査または対応フェーズで扱う。

**commit/pushは行っていない。** 指示があり次第、次のステップに進む。

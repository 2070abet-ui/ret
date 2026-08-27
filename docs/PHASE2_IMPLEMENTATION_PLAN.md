# 宅食図鑑 PHASE2 IMPLEMENTATION PLAN（2026-08-27）

作成日: 2026-08-27
作成者: Claude Code（計画のみ。コード/data/*.json/config/*.json変更・サイト再生成・commit・push は一切行っていない）
基準文書: `docs/FINAL_PRODUCT_DESIGN.md`（2026-08-27 Phase2改訂版）。矛盾する場合はFINAL_PRODUCT_DESIGNを優先する。

FINAL_PRODUCT_DESIGN.mdの5〜7章・12章で確定した「Phase2は最大3項目」を、Phase1と同じ粒度の実装前監査に落とし込む。

---

## 1. Phase 2 Goal

**唯一検証済みの差別化（値単位の出典・確認日紐付け）を実装し、データが既に揃っているMUST MATCH項目（診断のmeal_form軸）を低コストで消化する。新規Theme・新規データ収集を要する機能・新規抽象化は一切作らない。**

---

## 2. Implementation Scope

FINAL_PRODUCT_DESIGN.md 12章のPhase2実装内容3項目は、精査の結果**実質2つのコード変更**に収斂する（値単位の出典リンクとサービス単位の出典表示は同一実装で同時に満たせるため）。

| # | 項目 | FINAL_PRODUCT_DESIGN上の分類 | 本Phaseでの扱い |
|---|---|---|---|
| 1 | 値単位（価格・送料・キャンペーン）の出典・確認日リンク表示 | DIFFERENTIATE（5章、唯一の真の差別化） | **実施** |
| 2 | サービス単位の出典表示（cachie.jp水準へのMUST MATCH） | MUST MATCH（4章#5） | **#1と実装を共有。追加のコードは無い** |
| 3 | 診断ツールへのmeal_form軸追加 | MUST MATCH（7章、データ完備） | **実施** |

以下はPhase2のコード実装スコープに含めない（12章の通り）:
- ranking.htmlの並び替え・絞り込みUI（price confirmed 6社以上になってから、DEFER）
- 高齢者Theme本体（9セット中5セル未確認、DATA FIRST）
- 診断のpriceフィルタ（confirmed 4/11社、DATA FIRST）
- 減塩/無添加/高タンパクTheme（恒久DO NOT BUILD）
- GA4等の計測基盤（並行導入は推奨するが差別化実装ではない）

---

## 3. Files to Change（次フェーズの実行タスク。今回は変更していない）

| ファイル | 変更種別 |
|---|---|
| `data/services.json` | A8承認5社のうち確認済みの`price_plan`/`first_time_campaign`に`source_id`キーを追加（後述4章の対象10件のみ） |
| `data/shipping.json` | 同5社のうち確認済みの行に`source_id`キーを追加 |
| `tools/sitegen/generators.py` | `sources`を`sources_by_id`辞書化し、`build_service_page`呼び出しに渡す1行変更。`meal_form`正規化関数を追加し診断データに渡す |
| `tools/sitegen/templates.py` | 出典リンクのヘルパー関数追加、`build_service_page`内の価格/キャンペーン/送料表示に出典リンクを追加、`build_diagnosis_tool`にmeal_formチェックボックスとフィルタロジックを追加 |

## 4. Files NOT to Change

- `tools/build.py` / `tools/sitegen/data.py`（読み込み対象ファイルは増えない。`data.load_data()`は既に`sources`を返しており、シグネチャ変更は不要）
- `config/*.json`（Phase2の対象外）
- `data/campaigns.json`（出典紐付けはservices.json側の`first_time_campaign`にのみ行う。Phase1で確認済みの通り、ranking.htmlの表示は既にcampaigns.jsonベースのため、campaign出典はサービス詳細ページ限定の表示とし、ranking.html側は変更しない＝2ファイル間の二重メンテを避ける）
- `data/menus.json`（栄養データは対象外）
- 高齢者Theme関連の新規ファイル（DEFER、9.3参照）
- `tools/watch.py`（監視ロジックは変更しない）

---

## 5. Data Changes（出典・確認日紐付けの対象棚卸し）

`data/sources.json`の既存エントリと、A8承認5社の各フィールドの現在の確認状態を突き合わせた結果、**紐付け可能なのは15マス中10マス**。未確認のマスにはリンクを追加しない（リンクできない出典を示せないため）。

| サービス | price_plan | shipping | first_time_campaign |
|---|---|---|---|
| シェフの無添つくりおき | ✅ `chef-muten-official`（2026-08-26） | ✅ `chef-muten-official`（同一ページで確認のため共用） | ✅ `chef-muten-official` |
| 食楽膳 | ✅ `syokurakuzen-official`（2026-08-26） | ✅ `syokurakuzen-guide-202608`（2026-08-27、送料専用ページ） | ✅ `syokurakuzen-official` |
| ヨシケイ | ❌ 未確認（`yoshikei-price-attempt-202608`は不成立の記録のみ） | ✅ `yoshikei-official-202608`（2026-08-27） | ❌ 未確認（requires_verification: true） |
| 健康直球便 | ✅ `kenko-chokkyokubin-price-202608`（2026-08-27） | ✅ `kenko-chokkyokubin-delivery-202608`（2026-08-27） | ✅ `kenko-chokkyokubin-official`（2026-08-26） |
| FIT FOOD HOME | ❌ 未確認 | ❌ 未確認 | ❌ 未確認（公式ドメイン自体が未確定） |

**方針**:
- 上記✅の10マスにのみ`source_id`を追加する。❌の5マスは何もしない（未確認のまま、リンクなし＝これ自体が「未収集」の正直な表示として機能する）。
- `source_id`の値は`data/sources.json`の`id`をそのまま参照する文字列。新しいテーブルは作らない。
- シェフの無添つくりおきは価格・送料・キャンペーンの3項目すべてが同一の`chef-muten-official`を指す。1つの出典ページから複数フィールドを確認した場合はそのまま同じIDを共有してよい（出典の水増しをしない）。

### 5.1 データ原則の遵守確認
- 推測で埋めない：ヨシケイ・FIT FOOD HOMEの未確認フィールドには`source_id`を付与しない。
- 既存の確認済みデータは変更しない：`source_id`追加は既存の`lowest_per_meal_yen`等の値そのものを一切変更しない、キーの追加のみ。
- A8承認情報・reward_yen等の内部管理情報は出典リンクの対象にしない（出典は「価格・送料・キャンペーン内容の一次情報」のみを指し、ASP報酬額のsource_urlとは別物）。`services.json`の`affiliate.source_url`フィールドとは混同しない。

---

## 6. UI Changes

| ページ | 変更 |
|---|---|
| サービス詳細ページ（`services/*.html`） | 「基本情報」表内の最安料金セル、「初回キャンペーン・お試し」カード、「解約・送料について」カードの各vstatusバッジの直後に、`source_id`が存在する場合のみ「出典を見る」リンクを追加 |
| 診断ツール（`tool/diagnosis.html`） | 「目的を選んでください」の上に「保存方法で絞り込む（任意）」チェックボックス（冷凍／冷蔵／日配）を追加 |
| ranking.html | **変更なし**（3章の理由により、campaign出典はcampaigns.json由来の表示と二重管理になるため対象外。バッジ表示は既にPhase1で実装済みのものを維持） |
| 比較ページ・キャンペーン一覧・トップページ | 変更なし |

見た目の大きな変更（新セクション追加）はサービス詳細ページの各カード内リンク追加のみ。レイアウト変更はしない。

---

## 7. 出典リンクの実装設計

### 7.1 ヘルパー関数（追加）

```python
def source_link(sources_by_id, source_id):
    """source_idに対応するsources.jsonエントリがあれば出典リンクを返す。
    無ければ空文字（リンクできない出典を示さない）。"""
    src = sources_by_id.get(source_id) if source_id else None
    if not src:
        return ""
    return (f' <a href="{esc(src["url"])}" target="_blank" rel="noopener nofollow" '
            f'style="font-size:12px;">出典を見る（確認日: {esc(src.get("confirmed_at",""))}）</a>')
```

`sources_by_id`は`generators.py`側で`{s["id"]: s for s in sources}`として1回だけ構築し、`build_service_page`に渡す（`shipping_by_id`と同じパターン）。

### 7.2 呼び出し箇所（既存コードへの追加、置換ではない）

- 最安料金セル: `{vstatus_badge(...)}{source_link(sources_by_id, service.get("price_plan", {}).get("source_id"))}`
- 初回キャンペーンの`<p>`: `{vstatus_badge(...)}{source_link(sources_by_id, service.get("first_time_campaign", {}).get("source_id"))}`
- `shipping_line()`: 引数に`sources_by_id`を追加し、confirmed/derived時のみ末尾にリンクを追加（uncollected時は追加しない＝出典が無いものにリンクを出さない）

### 7.3 表示されないケースの扱い
`source_id`が無い（＝5.節の❌の5マス、または他6社）場合は何も表示されない。バッジ（確認中/未収集）はPhase1のまま維持されるため、ユーザーには「バッジはあるが出典リンクが無い」状態が見える。これは意図した挙動であり、隠すべき欠陥ではない（凡例で「確認済み・算出値のみ出典を表示」と一言添えるかは実装時に判断、必須ではない）。

---

## 8. meal_form診断フィルタの実装設計

### 8.1 データの正規化（新規データ収集は不要）
`meal_form`は自由文（例:「冷凍（レンジで温めるだけ）」「冷凍 / 冷蔵」「日配（保冷ボックス）」）のため、正規化関数で3カテゴリに変換する。

```python
def meal_form_categories(meal_form_text):
    text = meal_form_text or ""
    cats = []
    if "冷凍" in text: cats.append("冷凍")
    if "冷蔵" in text: cats.append("冷蔵")
    if "日配" in text: cats.append("日配")
    return cats
```

現行11社での分布（確認済み）: 冷凍9社（食宅便は冷凍/冷蔵の両方でカウント）、冷蔵2社（食宅便・シェフの無添つくりおき）、日配1社（ヨシケイ）。全社が最低1カテゴリに分類され、"該当なし"は発生しない。

### 8.2 UI・ロジック
- 診断ツールの目的チェックボックスの上に「保存方法で絞り込む（任意）」を追加。チェックが無ければ従来通り全件対象（後方互換）。
- ロジック: `runDiag()`内で、まずmeal_formチェックが1つ以上あれば対象サービスを`meal_form_categories`との積集合が空でないものに絞り込み（AND条件のフィルタ）、その後に既存の目的タグスコアリング（OR条件のマッチング）を適用する。目的とmeal_formは別の性質の条件（前者は好み、後者は保存環境の制約）のため、混同しないよう分離する。
- `svc_data`（JS側に渡すJSON）に`meal_form_categories`を追加する（`tags`/`target`と並列の新規キー。既存キーは変更しない）。

### 8.3 やらないこと
- meal_formを目的タグ（`tags`/`target`）に混入させない（意味が異なるため）。
- 汎用フィルタフレームワーク化はしない。チェックボックス3つ＋配列の積集合判定のみ。

---

## 9. Regression tests

Phase1と同様、テストフレームワークは導入せず、`python tools/build.py`実行後の手動+簡易チェックリストとする。

| # | チェック内容 | 方法 |
|---|---|---|
| 1 | build成功、生成ページ数不変（23ページ、新規ページなし） | `build.py`標準出力を確認 |
| 2 | 出典リンクが対象10マスにのみ表示され、未確認5マスには表示されない | 5社の詳細ページを目視し、5.節の表と突合 |
| 3 | 出典リンクのURLが`sources.json`の該当`url`と一致する | grep等で該当リンクのhrefを抽出し照合 |
| 4 | 出典リンクに`reward_yen`等の内部管理情報が混入していない | P0再発防止。生成物をgrepし報酬額・ASP内部情報が新たに露出していないか確認 |
| 5 | meal_formフィルタが3カテゴリで正しく動作し、全11社がいずれか1つ以上のカテゴリに分類される | ブラウザ確認困難な場合は`meal_form_categories`のユニットレベル確認（各社のmeal_form文字列に対する出力を手計算と突合） |
| 6 | meal_formチェック無しの場合、既存の診断結果が変化しない（後方互換） | 目的のみでの診断結果がPhase1時点と同一であることを確認 |
| 7 | 他10社（非A8承認6社＋ヨシケイ・FIT FOOD HOMEの一部フィールド）の表示が変化していない | git diffで該当ページの差分が出典リンク追加以外に無いことを確認 |
| 8 | 冪等性（2回連続build後にdiffが変化しない） | Phase1と同じ確認手順 |

---

## 10. Completion criteria

1. A8承認5社のうち確認済みの10フィールドに`source_id`が追加され、対応する出典リンクがサービス詳細ページに表示されている
2. 未確認の5フィールド（ヨシケイの価格・キャンペーン、FIT FOOD HOMEの全3項目）にはリンクが表示されない
3. 診断ツールにmeal_formフィルタが追加され、既存の目的診断と組み合わせて動作する
4. 9章の回帰チェック8項目すべてがパスしている
5. ranking.html・campaigns.json・data/menus.jsonには一切変更が無い

---

## 11. Explicit non-goals（今回のPhaseから除外）

| 項目 | 理由 |
|---|---|
| 全11社・全フィールドへの出典紐付け拡張 | FINAL_PRODUCT_DESIGN 9章でA8承認5社の3フィールドに限定済み |
| ranking.htmlへの出典・並び替えUI追加 | campaigns.json二重管理を避けるため対象外（3章） |
| 高齢者Theme本体 | データ未充足（9セット中5セル）、DEFER |
| 減塩/無添角/高タンパクTheme | 恒久DO NOT BUILD（FINAL_PRODUCT_DESIGN 6章） |
| 診断のpriceフィルタ | confirmed価格4/11社で不足、DATA FIRST |
| `status`専用データキーの新設 | Phase1同様、既存フィールドからの導出で足りている（`source_id`は出典参照のみの追加で、確認状態そのものの再設計ではない） |
| データ変更履歴（バージョニング） | 調査済み4競合に実装なし。先回りしない（FINAL_PRODUCT_DESIGN 9.4） |
| GA4等の計測基盤導入 | Phase2の差別化実装と並行推奨だが、本プランのコード変更スコープには含めない |

---

## 12. 次Phaseへの移行条件

以下が揃った時点で、FINAL_PRODUCT_DESIGN.md 12章のPhase3（DATA FIRST項目の充足を踏まえた追加判断）に着手する。

1. 本Phaseの完了条件（10章）がすべて満たされている
2. shipping.json残5社・ヨシケイ/FIT FOOD HOMEの価格・高齢者Theme候補5セルのうち、いずれかで新規の一次情報確認が取れている（DATA FIRST項目の進捗）
3. GA4等の計測基盤が導入され、出典リンクのクリック率・meal_formフィルタ利用率の計測が開始されている
4. price confirmed済みサービスが6社以上になった時点で、ranking.htmlの並び替え/絞り込みUI（DEFER）の着手可否を再評価する

これらが無いままPhase3で高齢者Theme本体や新規Themeに着手しない。

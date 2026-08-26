# 宅食図鑑 PHASE1 IMPLEMENTATION PLAN（2026-08-27）

作成日: 2026-08-27
作成者: Claude Code（計画のみ。コード/data/*.json/config/*.json変更・サイト再生成・commit・push は一切行っていない）
基準文書: `docs/FINAL_PRODUCT_DESIGN.md`（矛盾する場合はFINAL_PRODUCT_DESIGNを優先）

本ドキュメントの目的は、設計をさらに広げることではなく、FINAL_PRODUCT_DESIGNで確定した「MUST MATCH → DIFFERENTIATE」の優先順位に沿って、**今、本当に作るべき最小単位**を確定すること。

再確認した現状（今回の監査で判明した事実。数値はすべて実ファイルから直接確認）:

| ファイル | 現状 |
|---|---|
| `config/watchlist.json` | 7エントリ（nosh/watami/mitsuboshi/wellness/shokutakubin/fitfood[disabled]/magokoro）。**A8提携承認済み4社（chef-muten-tukuritoki/syokurakuzen/yoshikei/kenko-chokkyokubin）が欠落** |
| `config/comparisons.json` | 2ペア（nosh vs mitsuboshi-farm, nosh vs watami-takushoku）。**3社とも`affiliate_links`上「未提携（ASP承認待ち）」**（mitsuboshi-farmは「掲載終了の可能性あり」の要再確認状態） |
| `config/affiliates.json` | A8承認済み5社: fit-food-home / chef-muten-tukuritoki / syokurakuzen / yoshikei / kenko-chokkyokubin |
| `data/services.json` price_plan | CONFIRMED 3/11（chef-muten:1,035円、syokurakuzen:351円、shokutakubin:690円[算出値]）。他8社null |
| `data/shipping.json` | 数値確定3社（chef-muten:990円、yoshikei:0円、kenko-chokkyokubin:0円）、変動額を文章で確認済み2社（nosh、syokurakuzen）、ブロッカー理由付きUNCOLLECTED5社（watami:403 Forbidden、mitsuboshi:JS描画で取得不可、wellness:記載箇所不明、fit-food-home:公式ドメイン未確定、magokoro:料金ページ未発見） |
| `data/campaigns.json` | `requires_verification:false`（=確認済み扱い）6件、`true`（=未確認）4件 |
| `tools/sitegen/templates.py` | `build_service_page`に関連サービスブロック無し。`shipping_line()`が既に「notesに"UNCOLLECTED"を含めば非表示」という状態判定ロジックを実装済み（これを7章のverification-status UIに転用可能） |
| テスト | リポジトリ内にテストコードは存在しない（`find`で確認済み） |

---

## 1. Phase 1 Goal

**「MUST MATCHのギャップを埋め、DIFFERENTIATEの土台（verification-status表示）を最小コストで敷く」。新規テーマ・新規診断軸・新規推薦ロジックは作らない。**

具体的には、以下の6項目のみを対象とする。テーマ拡張や汎用化は一切含まない。

---

## 2. Implementation Scope

| # | 項目 | FINAL_PRODUCT_DESIGN上の分類 | 本Phaseでの扱い |
|---|---|---|---|
| 1 | watchlist.json是正 | 内部運用（4章外・9章） | **実施** |
| 2 | comparisons.json再評価 | MUST MATCH（8章の指摘） | **実施（1ペア追加を提案、既存2ペアは維持）** |
| 3 | データ充足（価格・送料） | MUST MATCH（4章#2） | **実施（確認できる範囲のみ）** |
| 4 | 関連サービス | MUST MATCH（4章#8, 11章） | **実施** |
| 5 | フィールド単位verification表示 | DIFFERENTIATE（5章②） | **実施（最小実装）** |
| 6 | 高齢者Theme | DIFFERENTIATE（9章、条件付きGO） | **条件未達のため見送り（詳細9章参照）** |

---

## 3. Files to Change（次フェーズの実行タスク。今回は変更していない）

| ファイル | 変更種別 |
|---|---|
| `config/watchlist.json` | 4エントリ追加 |
| `config/comparisons.json` | 1ペア追加（既存2ペアは変更しない） |
| `data/services.json` | price_plan（対象3社のみ、確認できた場合）、必要なら`status`相当のキー追加は行わない（8.3で理由を説明） |
| `data/shipping.json` | shipping_fee/notes（対象社、確認できた場合のみ） |
| `tools/sitegen/templates.py` | `build_service_page`に関連サービスブロック追加、verification-statusバッジのヘルパー関数追加、`build_ranking_page`にバッジ表示追加 |
| `tools/sitegen/generators.py` | `build_service_page`呼び出しに`services`全体を渡す1行変更（関連サービス計算のため） |

## 4. Files NOT to Change

- `tools/build.py`（エントリポイントは変更不要）
- `tools/sitegen/data.py`（読み込み対象ファイルは増えない。追加キーも既存JSON構造の範囲内）
- `tools/watch.py`（監視ロジック自体は変更しない。対象リストのみ増える）
- `config/site.json` / `config/affiliates.json`（本Phaseでは変更対象外）
- `data/menus.json`（0件のまま。栄養DBは6章NO-GO/保留対象で本Phase対象外）
- 高齢者Theme関連の新規ファイル（テンプレート・生成コードとも新規作成しない。9章の判定により見送り）

---

## 5. Data Changes（3. データ充足の詳細監査）

### 5.1 対象と優先順位

| 優先度 | サービス | フィールド | 現状 | 一次情報での確認可否（判断材料） |
|---|---|---|---|---|
| 1 | yoshikei | price_plan | null（地域により異なる） | A8承認済み。ただし公式サイト自体が「プランは地域により異なる」と明記しており、**単一の「最安値」が存在しない可能性が高い**。shipping.jsonのnosh/syokurakuzenと同様、単一値ではなく文章記述（PENDING_VERIFICATIONまたは「地域差あり」の明記）で確定させる方針を検討 |
| 2 | kenko-chokkyokubin | price_plan | null（商品別価格は要確認） | A8承認済み。公式サイトに配送・支払いページがあり価格ページも存在する可能性が高い→確認を試みる価値が高い |
| 3 | fit-food-home | price_plan / shipping | null / UNCOLLECTED（公式ドメイン未確定） | A8承認済みだが**公式ドメイン自体が未確定**（fitfoodhome.jpはDNS不通と既に記録済み）。ドメイン確定が先決で、価格確認より前工程が必要 |
| 4 | watami-takushoku | shipping | UNCOLLECTED（403 Forbidden） | 機械取得不可の記録あり。再試行の価値は低い（規約上のbot対策の可能性）。**人力でのブラウザ確認が必要**なタスクとして残す（本Phaseでは実施しない） |
| 5 | mitsuboshi-farm | shipping | UNCOLLECTED（JS描画） | 同上。ASP掲載自体も「終了の可能性あり」の要再確認状態のため優先度を上げない |
| 6 | wellness-dining, magokoro-care | price/shipping | UNCOLLECTED | 非A8承認（wellness-diningは「案件存在を確認・要詳細確認」段階、magokoro-careも同様）のため優先度は最も低い |

### 5.2 方針
- **推測による穴埋めは禁止**。確認できないものはPENDING_VERIFICATION/UNCOLLECTEDのまま次フェーズへ持ち越す。
- yoshikeiのように「地域により異なり単一値が存在しない」場合、noshやsyokurakuzenの送料と同じ扱い（単一値を無理に作らずnotesに事実を記述）を価格にも適用する。**単一値への圧縮は誤誘導になるため行わない**（この方針は`data/shipping.json`の`_comment`に既に明記されている原則を価格にも一貫適用するだけであり、新しい方針の導入ではない）。
- fit-food-homeは公式ドメイン確認が前提条件。本Phaseのデータ充足作業では**着手順位を最下位に置く**（前工程が別途必要なため）。

### 5.3 完了条件
- yoshikei・kenko-chokkyokubinのいずれかでprice_plan.lowest_per_meal_yenがCONFIRMEDになる、**または**確認を試みた上で「地域差により単一値化不能」と判断され、その理由がnotesに記録される。
- 確認不能だった場合でも「試みた記録」（sources.jsonへのエントリ追加）を残す。何もせず放置しない。

---

## 6. UI Changes（概要。詳細は7・8章）

| ページ | 変更 |
|---|---|
| サービス詳細ページ（`services/*.html`） | ①末尾に関連サービスブロック追加 ②最安料金・送料・キャンペーンの値の隣にverification-statusバッジ追加 |
| ランキングページ（`ranking.html`） | 最安料金セルにverification-statusバッジ追加（列は増やさない。既存セル内に短いラベルを併記） |
| 比較ページ（`comparisons/*.html`） | 変更なし（本Phase対象外。ペア追加のみ） |
| 全ページ共通フッター | verification-statusバッジの凡例を1箇所追加 |

見た目の大きな変更（新セクション追加・レイアウト変更）は行わない。既存カード/テーブル構造に収める。

---

## 7. Related-service logic

### 7.1 アルゴリズム（汎用matching engineではなく単純な集合演算）

```
対象サービスの (tags ∪ target) を集合Aとする
他10社それぞれの (tags ∪ target) を集合Bとする
一致数 = |A ∩ B|
一致数 >= 2 の候補のみを対象とする
スコア降順に並べ、上位2〜3件を表示
同点の場合のタイブレーク:
  1. A8提携承認済みサービスを優先（config/affiliates.jsonのstatus参照）
  2. services.json記載順（先に定義されている方を優先）
一致数0〜1件しかない場合、ブロック自体を出力しない（空欄で「関連サービスがありません」とは表示しない）
```

新しいデータフィールドは不要。既存の`tags`/`target`のみを使う。ロジックはgenerators.py内で全サービス配列に対する事前計算として実装し、templates.pyの`build_service_page`にスコア済みの関連候補リストを渡す（テンプレート内でO(n²)計算をしない）。

### 7.2 妥当性の事前検証（実装前に机上で算出した一致数の例）

閾値2件・上位3件ルールが「根拠の弱い組み合わせを出さない」ことを保証できるか、代表的な3ケースで事前検証した（tags+targetの和集合による一致数）。

**高齢者クラスタ（syokurakuzen / kenko-chokkyokubin / magokoro-care / shokutakubin）**: 相互一致数3〜5件。例: syokurakuzen⇄kenko-chokkyokubin=4件（高齢者・塩分制限・健康志向・冷凍）、magokoro-care⇄kenko-chokkyokubin=4件（高齢者・健康志向・冷凍・やわらか食）。→ 閾値2を大きく上回り、根拠が明確。

**chef-muten-tukuritoki**: shokutakubin=3件（健康志向・時短・冷蔵）、syokurakuzen=2件（健康志向・惣菜）、yoshikei=2件（時短・家族）。タイブレーク（A8優先）により、上位3件は shokutakubin・syokurakuzen・yoshikei（syokurakuzen/yoshikeiはA8承認済みのため非承認のwatami等より優先）。

**nosh**: mitsuboshi-farm=5件（一人暮らし・ダイエット・糖質制限・低糖質・冷凍）、watami-takwashoku=4件（一人暮らし・時短・冷凍・管理栄養士監修）。→ 閾値を大きく上回り妥当。

いずれのケースも「タグが1個だけ偶然一致した無関係なサービス」が上位に出るリスクは無い（閾値2以上を要求しているため）。全11社×10社の総当たり結果は実装時にビルド出力で機械的に確認する（12章）。

### 7.3 CTA階層との整合（ranking.htmlとの関係）

`ranking.html`の各行には既に「公式サイトを確認」という直接CTAが存在する（比較検討ページとしての役割上、適切）。一方、**関連サービスブロックのリンク先は`/services/{id}.html`のみとし、アフィリエイトCTAを併記しない**。理由: 詳細ページ自身の主CTA（「公式サイトで料金・キャンペーンを確認」）を関連サービスブロックが弱めない（回遊優先→CTAは元のページ内で完結させる）ため。これはFINAL_PRODUCT_DESIGN 8.2の導線設計（Service Detail ⇄ 関連サービス → Comparison → Diagnosis → CTA）と整合する。

---

## 8. Verification-status UI

### 8.1 既存データ構造だけで導出可能か（結論: 一部可能、一部は導出の質が不安定）

| フィールド | 既存構造での導出可否 | 根拠 |
|---|---|---|
| `campaigns[].requires_verification` | **可能（変更不要）** | 既にboolean型で存在。`false`→確認済み、`true`→確認中、の2値で足りる（campaignsに「算出値」概念は不要） |
| `shipping_rules[].shipping_fee` + `notes` | **可能（変更不要）** | `shipping_fee`が数値→確認済み、`notes`に"UNCOLLECTED"を含む→未収集、両方null/文章のみ→「確認済み（変動あり）」の3値を導出可能。`templates.py`の`shipping_line()`が既に"UNCOLLECTED"文字列判定を実装済みで、同じ判定を流用できる |
| `services.json price_plan` | **部分的に可能（脆弱）** | `lowest_per_meal_yen`がnullかどうかは判定できるが、「確認済み」と「算出値(DERIVED)」を区別する情報は`plan_notes`の自由文中に限られる。現状すでにshokutakubinの`plan_notes`に「算出値（DERIVED）」、noshの`plan_notes`に「公式確認中（PENDING_VERIFICATION）」という**英語トークンを含む一文が実在**しており、これを部分文字列判定で拾うことは技術的には可能。ただし今後のデータ入力者がこの記法を維持する保証がない＝**長期的に壊れやすい** |

### 8.2 結論と実装方針

- **shipping/campaignsは既存構造のみで実装する**（データ変更不要、テンプレート側のロジック追加のみ）。
- **price_planは今回、文字列判定に依存する形で実装可能だが、既存の`plan_notes`記法（DERIVED/PENDING_VERIFICATION等の英語トークン埋め込み）に依存する**。これは新しいキーの追加ではなく、既存の書き方の慣習を機械可読ルールとして採用するだけであり、DB化・スキーマ拡張ではない。ただし壊れやすさをリスクとして明記する（13章）。
- 新しいテーブル・専用DBは作らない。ラベルは4種類の文字列（"確認済み" / "算出値" / "確認中" / "未収集"）を返す1つの純粋関数（例: `verification_badge(kind, value, notes)`）で足りる。

### 8.3 なぜ`status`専用キーを今回追加しないか
FINAL_PRODUCT_DESIGN 7.2は将来的に`status`専用キーへの構造化を推奨しているが、**今回のPhase1では追加しない**。理由: 現行の文字列判定だけでshipping/campaignsの2/3フィールドは確実に動作し、price_planも暫定的に動作するため、今すぐデータスキーマを変更する必要性がない（Rule of Three＝3箇所目の需要が明確になってから拡張する）。price_planの判定が壊れた場合（新規データが慣習に従わない場合）に初めて`status`キーの追加を検討する。

### 8.4 表示ラベルと凡例
バッジ文言: `確認済み` / `算出値` / `確認中` / `未収集`。全ページ共通フッター付近に1回だけ凡例（例: 「✅確認済み＝公式一次情報で確認 / 📐算出値＝一次情報から計算 / ⏳確認中＝情報はあるが裏付け不十分 / ❔未収集＝公式情報に未到達（理由は各ページに記載）」）を追加する。

### 8.5 重要なリスク（P0再発防止）
verification-statusバッジは`price_plan` / `shipping_rules` / `campaigns`の**表示用フィールドのみ**から導出し、`affiliate.campaigns[].reward_yen`等の内部管理フィールドを参照しない。UX監査で撤去したはずの内部報酬情報を、新しいバッジ機能経由で誤って再露出させないことを実装時のレビュー観点として明記する。

---

## 9. Senior-theme decision

### 9.1 3社×3軸の現状確認（今回の監査で判明）

| 軸 \ サービス | 食楽膳 | 健康直球便 | まごころケア食 |
|---|---|---|---|
| 個食対応 | **Yes**（tags「個食」、main_features「個食タイプの冷凍惣菜」で明記） | **未確認**（弁当形式のため実質個食の可能性は高いが、明記なし） | **未確認**（言及なし） |
| やわらか食対応 | **未確認**（tags/main_featuresに言及なし） | **Yes**（main_features「やわらかい食事の冷凍弁当」、tags「やわらか食」） | **未確認相当**（main_featuresに「やわらか食・ムース食などに対応」という記載はあるが、本サービスの他フィールドには一切「公式サイト確認済み」の注記が無く、Batch2で確立された確認済み表記の慣習（例:「（公式サイト2026-08-27確認）」）が付いていない。**確認済みとして扱えない**） |
| 塩分控えめ対応 | **Yes**（tags「塩分控えめ」、main_features「塩分控えめセット」） | **Yes**（tags「減塩」、main_features「減塩食」） | **未確認**（言及なし） |

**9セル中、確認済み(Yes)=4、未確認=5**。

### 9.2 判定

FINAL_PRODUCT_DESIGN 9章の公開条件は「まごころケア食の3軸該当有無が公式情報で確認できること」。現状、まごころケア食は3軸とも未確認（1軸はマーケティングコピーの言及があるのみで、本サイトの確認済み表記の慣習に従っていない）。

**結論: 条件は現時点で満たされていない。高齢者Themeは本Phaseで実装しない（コードも作らない）。**

理由:
1. テンプレート/生成コードだけを先に作っても、公開判断が下せない状態のコードは「使われるか分からない実装」に該当し、12章禁止事項（過剰設計の排除）の精神に反する。
2. 2社限定（食楽膳・健康直球便）の縮小版も、9セット中「健康直球便の個食対応」「食楽膳のやわらか食対応」の2セルが未確認のままであり、2社版であっても表を空欄なく埋められない。

### 9.3 次フェーズへの持ち越しタスク（データ収集のみ、Phase1のスコープには含めない）
- まごころケア食: 個食対応・やわらか食対応（正式確認）・塩分控えめ対応の3点を公式サイトで確認
- 食楽膳: やわらか食対応の有無を公式サイトで確認
- 健康直球便: 個食対応の有無を公式サイトで確認

上記5点が確認され次第（Yes/Noいずれでも可、確認できたことが条件）、高齢者Themeの実装をPhase2として起票する。

---

## 10. Comparison/CTA decision

### 10.1 既存2ペアの評価

| ペア | 現在のASP状態 | SEO実測 | 評価 |
|---|---|---|---|
| nosh vs mitsuboshi-farm | 両社とも「未提携（ASP承認待ち）」。mitsuboshi-farmはASP掲載自体が「終了の可能性あり」の要再確認 | `data/sources.json`に実測記録あり（「nosh 三ツ星ファーム 比較 どっち」で個人ブログが上位という記録） | **維持**。CVは現状ゼロだが、実測で個人サイトが上位を取れているSEO入口としての価値があり、両社ともASPプログラム自体は実在（提携申請すれば近い将来CV化可能）。除去する積極的理由がない |
| nosh vs watami-takushoku | 同上（未提携だがプログラムは実在） | 個別の実測記録はsources.jsonに無いが、両社とも大手ブランドで比較検索需要があると推定される（SEO_FLOW_RESEARCHの一般キーワード系評価より） | **維持**。ただし新規のSEO投資（記事追加等）はこのペアに対して行わない（6章で「一人暮らし/糖質制限」はCV先未提携としてC評価済みのテーマと重なるため） |

**非提携サービス同士の比較を残す合理性**: 両ペアとも「ASPプログラム自体は実在するが自分がまだ承認されていない」状態であり、「案件が存在しない」わけではない。将来提携が完了すれば即座にCV導線化できる。加えて、SEO実測で個人サイトが上位に入れる余地が確認されている数少ないクラスタ（3章）でもあるため、削除するとその実測済み優位性を放棄することになる。**削除しない**。

### 10.2 追加候補の評価

| 候補ペア | 一致タグ数 | 両社ASP状態 | 実測/根拠 | 採否 |
|---|---|---|---|---|
| syokurakuzen vs kenko-chokkyokubin | 4件（高齢者・塩分制限・健康志向・冷凍） | **両社ともA8承認済み** | SEO_FLOW_RESEARCHで「同一ターゲット層への代替CV先」として明記済み。SEO_CONTENT_FINAL_KW_SERP_AUDITの記事3/4が両社への相互内部リンクを計画済み | **採用を提案** |
| chef-muten-tukuritoki vs yoshikei | 2件（時短・家族） | 両社A8承認済み | 実測SERPでの比較検索需要の裏付けなし。meal_form自体が異なる（冷蔵惣菜 vs 日配食材宅配）ため、ユーザーが同列に比較検討する自然さに疑問 | **却下** |
| fit-food-home vs 他社 | 0〜1件（重複タグ薄い） | fit-food-homeのみA8承認 | ターゲット層（ダイエット/高タンパク）が他社と重ならない | **却下** |

### 10.3 結論（提案。config/comparisons.json自体は今回変更しない）
既存2ペアを維持し、`{"a": "syokurakuzen", "b": "kenko-chokkyokubin"}`を1件追加することを次フェーズの実行タスクとして提案する。根拠: ①両社ともA8承認済みで直接CVに繋がる ②実測に基づくターゲット層の重複が明確 ③9章で見送った高齢者Themeの代替として、比較ページ単体でも「高齢者・塩分」ニーズの受け皿になる（Theme非公開の間、比較ページがその役割を部分的に代替できる）。

### 10.4 CTA階層の再確認
`ranking.html`の各行CTA（「公式サイトを確認」）は比較検討ページの役割として適切であり変更不要。問題があったのは「関連サービス」等の**回遊用リンクが直接CTAと同列に並ぶこと**（7.3で対処済み）であり、ranking.html自体のCTA配置に問題はない。

---

## 11. Watchlist decision

### 11.1 11社との対応関係

| service_id | watchlist登録 | A8提携状態 |
|---|---|---|
| nosh | ○ | 未提携 |
| watami-takushoku | ○ | 未提携 |
| mitsuboshi-farm | ○ | 未提携（掲載終了可能性あり） |
| wellness-dining | ○ | 未提携 |
| shokutakubin | ○ | 未提携 |
| fit-food-home | △（disabled、url空） | **提携承認済み** |
| magokoro-care | ○ | 未提携 |
| chef-muten-tukuritoki | **✗未登録** | **提携承認済み** |
| syokurakuzen | **✗未登録** | **提携承認済み** |
| yoshikei | **✗未登録** | **提携承認済み** |
| kenko-chokkyokubin | **✗未登録** | **提携承認済み** |

**収益化対象5社のうち4社が監視対象から完全に漏れ、残り1社（fit-food-home）はURLが未確定で無効化されたままになっている**。これは設計判断ではなく単純な追加漏れであり、修正に議論の余地はない。

### 11.2 実施内容（次フェーズ）
- `chef-muten-tukuritoki` (`https://store.tavenal.com/tsukurioki/`)
- `syokurakuzen` (`https://shokurakuzen-sompocarefoods.com/`)
- `yoshikei` (`https://www.yoshikei.co.jp/`)
- `kenko-chokkyokubin` (`https://kenko-chokkyubin.com/`)

の4エントリを`targets`に追加する。`fit-food-home`は公式ドメインが未確定のため`disabled:true`を維持する（ドメイン確定後に別途対応）。

### 11.3 リスク
watch.pyは単純なページ全体ハッシュ＋正規表現シグナル抽出（`tools/watch.py`)であり、対象追加によるロジック変更は不要。ただし`chef-muten-tukuritoki`の公式URLがJavaScript描画に依存する場合、mitsuboshi-farmと同様に本文取得できない可能性がある。追加後、初回実行(`python tools/watch.py --dry-run`)で取得成否を確認する必要がある（次フェーズの完了条件に含める）。

---

## 12. Regression tests

リポジトリにテストフレームワークは存在しない（stdlibのみのビルド哲学、`tools/build.py`参照）。新規に pytest 等を導入することはRule of Threeに反するため行わない。代わりに、`python tools/build.py`実行後の**手動+簡易スクリプトチェックリスト**を次フェーズの完了条件に組み込む。

| # | チェック内容 | 方法 |
|---|---|---|
| 1 | 生成ページ数が想定通り（既存22 + 新規0、関連サービス/バッジはページ内追加のみでページ数は変わらない。比較ページのみ+1） | `build.py`の標準出力「生成完了: N ページ」を確認 |
| 2 | 内部管理情報（ASP報酬額）がHTMLに再露出していない | `site/services/*.html`と`site/ranking.html`を対象に、`reward_yen`相当の生の金額文字列が「報酬」「ASP」等の文脈で出力されていないか目視+grep確認（P0再発防止、8.5節） |
| 3 | 関連サービスブロックが一致数2未満のケースで非表示になっている | 全11社の詳細ページを生成し、一致数が最も少ないサービス（例: yoshikei、wellness-dining）で規定通りブロックが省略されるか確認 |
| 4 | verification-statusバッジが4種のラベルのみで構成され、null参照で例外を出さない | 全11社に対しビルドを実行しエラー無く完了することを確認（価格/送料未確認社でも`None`分岐が正しく処理されること） |
| 5 | 新規比較ページ（syokurakuzen vs kenko-chokkyokubin）が既存テンプレートで正しく生成される | `comp_pairs`に1行追加してビルド、`comparisons/syokurakuzen-vs-kenko-chokkyokubin.html`が生成されることを確認 |
| 6 | sitemap.xml・内部リンクが壊れていない | 生成後、`site/sitemap.xml`のURL数が増分と一致すること、関連サービスリンク先が実在するservice_idであることを確認 |
| 7 | watchlist追加後の初回取得確認 | `python tools/watch.py --dry-run`を実行し、追加4件が`[NEW]`または`[ERROR]`のどちらで終わるか記録（JS描画等で失敗する場合はshipping.json同様のUNCOLLECTED理由として記録） |

---

## 13. Completion criteria

Phase 1は以下すべてを満たした時点で完了とする。

1. `config/watchlist.json`にA8承認4社が追加され、`watch.py --dry-run`で取得可否が確認されている
2. `config/comparisons.json`の追加要否判断が確定している（採用する場合はペア追加、根拠は本ドキュメント10章を参照）
3. yoshikei・kenko-chokkyokubinのいずれかでprice_plan確認が試行され、結果（CONFIRMED or 確認不能の理由）が記録されている
4. 全11社の詳細ページに関連サービスブロックが実装され、7章のアルゴリズム通りに動作している（一致数2未満は非表示）
5. price_plan/shipping_rules/campaignsの表示箇所にverification-statusバッジが実装され、凡例が全ページに表示されている
6. 12章の回帰チェック7項目すべてがパスしている
7. 高齢者Themeは実装されていない（意図的な非対応であることが9章に記録されている）

---

## 14. Explicit non-goals（今回のPhaseから除外）

| 項目 | 理由 |
|---|---|
| 減塩Theme | FINAL_PRODUCT_DESIGN 6章NO-GO（5社横並びの塩分数値が未確立） |
| 無添加Theme | 同上（確認済みclaimが1社のみ） |
| 高タンパクTheme | 同上（SERP再検証未実施） |
| 高齢者Theme（本Phase） | 9章の通り、まごころケア食含む5セルが未確認のため見送り |
| 価格診断（priceフィルタ） | confirmed価格が3/11社のみで機能しない（design doc 10章） |
| 高度な推薦エンジン／matching_rule DSL | design doc 10章で恒久NO-GO |
| 汎用Themeエンジン | 対象テーマが1つも公開条件を満たしていない現状で汎用化する母数がない |
| UpdateLog正式基盤・毎週更新ページ | design doc 4章冒頭の設計思想（更新自体は差別化にならない）に基づき恒久的に作らない |
| 複雑な計測基盤（GA4以上のもの） | 本Phaseの対象外。GA4導入自体も本Phaseのスコープには含めない（データ充足・UI変更を優先） |
| `status`専用データキーの追加 | 8.3の通り、既存の文字列判定で当面は足りるため見送り（Rule of Three） |
| menus.json（栄養DB）へのデータ投入 | 減塩/高タンパクTheme同様、本Phase対象外 |
| price_planの単一値への強制圧縮（yoshikei等） | 誤誘導になるため行わない。地域差はshippingと同じ扱いで文章記述する |

---

## 15. 次Phaseへの移行条件

以下がすべて揃った時点で、FINAL_PRODUCT_DESIGN 14章のPhase2（DIFFERENTIATE本格実装）に着手する。

1. 本Phaseの完了条件（13章）がすべて満たされている
2. 9.3節の5点（まごころケア食3点＋食楽膳1点＋健康直球便1点）が公式情報で確認され、高齢者Themeの公開可否判断ができる状態になっている
3. verification-statusバッジのprice_plan判定（8.2節の文字列判定方式）が、新規データ入力時にも安定して機能しているか一度検証されている（不安定であれば`status`専用キーの追加をPhase2の最初のタスクとして起票する）
4. yoshikei/kenko-chokkyokubin/fit-food-homeの価格確認結果を踏まえ、diagnosis toolのpriceフィルタ導入可否（design doc 10章の保留条件＝confirmed価格6社以上）を再評価する

これらが未達のままPhase2の新規Theme・出典紐付けUIに着手しない。

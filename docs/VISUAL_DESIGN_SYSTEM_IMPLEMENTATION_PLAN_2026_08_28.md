# Visual Design System 実装計画（2026-08-28）

作成日: 2026-08-28
位置づけ: [[VISUAL_DESIGN_SYSTEM_AUDIT_2026_08_28.md]]（READ ONLY監査、P1〜P3で8項目を提案）を受けた実装計画。**本ドキュメントの作成自体がタスクであり、`tools/sitegen/templates.py`等へのコード変更はまだ行っていない。** 実装は本計画を参照する別セッション・別タスクで行う。

Explore agent 3件＋Plan agent1件による調査結果を、Read/Grepで直接ファイルを確認して検証済み。以下の重要事実は監査原文からの訂正・補強を含む。

## 監査原文からの訂正事項

- **循環import**: `generators.py:6`が`from sitegen import templates`のため、`templates.py`は`generators.py`を逆importできない。`meal_form_categories()`（現在`generators.py:14-26`）を`templates.py`へ移設する必要がある（純粋な関数移動、データ変更なし）。
- **詳細ページの主役アクセント**: `service_recommend_block()`（templates.py:1157-1170）は既に`<div class="card panel-accent">`＋`<ul class="feature-list">`で構成済み。監査原文が想定した「`.pros-highlight`の左罫線パターンを転用」は誤り（`.pros-highlight`は「良い点[0]」専用の別要素、templates.py:430,1235,1252で確認）。→ 詳細ページのメリハリは「主役を装飾する」のではなく「脇役カードを控えめにする」方向で実現する。

## 対象8項目

### P1（比較のしやすさに直結）

#### 1. 比較一覧：価格数字の縦位置を揃える
| 項目 | 内容 |
|---|---|
| 現在の実装箇所 | `_price_inline_html()`(templates.py:877-889)が生成する価格セル`<td>{price_cell}</td>`(1395行)。数字は`.price-figure`span(193行)。 |
| 変更内容 | ①`.price-figure`(193行)に`font-variant-numeric: tabular-nums;`追加。②1395行の`<td>`に`class="td-price"`付与。③CSS追加: `#ranking-table td.td-price { text-align:right; }`（ranking専用スコープ）。 |
| 変更しないもの | `_price_inline_html`/`_display_figure_html`/`price_figure_html`（モバイル）自体、価格ラベル・検証バッジ、列順、モバイルカード。 |
| UI仕様 | 上記CSS/マークアップ差分の通り。**限界**: basisによりラベル幅が異なるため、セル全体の`text-align:right`では数字だけの完全な桁揃えにはならない（読みやすさの向上に留まる）。 |
| PC/モバイル影響 | デスクトップ表のみ（`.ranking-desktop`は640px以下で非表示）。モバイルカードは別関数`price_figure_html`のため無影響。 |
| 実装順序 | P1の1番目。最も低リスクで他項目と独立。 |
| 検証方法 | `python tools/build.py`→`python tools/sitegen/validate.py`→Playwrightで`/ranking`をPC幅で開き価格列を確認。並び替え・フィルタの回帰がないことを確認。 |
| リスク・副作用 | 低。`.price-figure`はグローバル規則だが数字の字幅のみに影響。 |

#### 2. 比較一覧：sticky thead（条件付き実施）
| 項目 | 内容 |
|---|---|
| 現在の実装箇所 | `<table id="ranking-table">`(1462-1465行)は`<thead>/<tbody>`を持たない裸のtable。CSSに`sticky`は0件。 |
| 変更内容 | ヘッダー行を`<thead>`、`{rows}`を`<tbody>`で囲む。CSS追加: `#ranking-table thead th { position:sticky; top:0; z-index:1; background:var(--color-surface-alt); }`。 |
| 変更しないもの | 行のdata属性、列数・順序、並び替え/フィルタJSのロジック自体。 |
| UI仕様 | 上記の通り。既存トークン`--color-surface-alt`のみ使用、新色なし。 |
| PC/モバイル影響 | デスクトップのみ。 |
| 実装順序 | P1の3番目（最後）。1・3が先に完了していれば本項目が難航してもブロックしない。 |
| 検証方法 | Playwrightで実際にスクロールしヘッダー固定を目視確認。「表示価格が安い順」・保存方法フィルタの回帰テスト必須。 |
| リスク・副作用 | **要注意**: `.card`(117-125行)が`overflow-x:auto`を持ち、CSS仕様上`overflow-y`も暗黙に`auto`化されるため、`position:sticky`の基準（containing block）がビューポートではなく`.card`になり、**見た目上stickyが効かない可能性がある**。効かない場合は`<thead>/<tbody>`構造のみ残し`position:sticky`のCSSを外せばよい（後戻り不要、マークアップ整理としては無害）。並び替えJSの`reorderTo()`は`tr[data-mealform]`セレクタを使うが、ヘッダー行にはこの属性が無いため機能面は壊れない見込み。 |

#### 3. 比較ページ：「向いている人」を箇条書き化
| 項目 | 内容 |
|---|---|
| 現在の実装箇所 | `_comparison_target_diff_html()`(1594-1609)が`<p><strong>ラベル：</strong>・区切りの文章</p>`を最大3つ生成、`build_comparison_page()`の結論パネル(1635-1645)内に挿入。 |
| 変更内容 | 同関数内で`<li><strong>ラベル：</strong>・区切り</li>`を生成し`<ul class="feature-list">{items}</ul>`でラップ。 |
| 変更しないもの | 文言、only_a/only_b/common判定ロジック、結論パネル内の他要素（basis警告文・CTA）、パネルの位置。 |
| UI仕様 | `ul.feature-list li`は432行に既存（`margin-left:20px;font-size:14px`）、`service_recommend_block`でも同クラス使用中——**新規CSS不要**。 |
| PC/モバイル影響 | 分岐なし、両方同一。 |
| 実装順序 | P1の2番目。単一関数に閉じており独立。 |
| 検証方法 | `/comparisons/nosh-vs-watami-takushoku.html`等で箇条書き表示・文言・CTA数（6個、[[DIAGNOSIS_COMPARE_CTA_FUNNEL_AUDIT_2026_08_28.md]]で確認済み）に変化がないことを確認。 |
| リスク・副作用 | 極小。単一関数の内部変更のみ。 |

### P2（視覚的な起伏の追加）

#### 4. TOPヒーロー：大きな数字の追加
| 項目 | 内容 |
|---|---|
| 現在の実装箇所 | `build_index_page()`(1833-1936)のhero(1929-1936)はテキストのみ。`num_services`(1835行)・`coverage`(1854-1857行)は既にスコープ内。 |
| 変更内容 | hero内に`<div class="trust-stat"><span class="trust-figure">{num_services}</span><span class="trust-label">社の宅配食サービスを掲載</span></div>`を追加。 |
| 変更しないもの | `hero_lead`文言、`.hero-actions`のCTA、`trust_panel(compact=True)`本体。 |
| UI仕様 | `.trust-stat`/`.trust-figure`は既存クラス（288-290行）、モバイル用メディアクエリも既存（463行）——**新規CSS不要**。 |
| PC/モバイル影響 | 既存レスポンシブ規則を継承。375px幅でCTAと衝突しないことを目視確認要。 |
| 実装順序 | P2の2番目（項目5の後）。TOPページに閉じた独立変更。 |
| 検証方法 | `/index.html`をPC(1280px)・モバイル(375px)でスクリーンショットし、数字がファーストビューに収まりCTAを圧迫しないことを確認。 |
| リスク・副作用 | 極小。追加のみ、既存要素は不変。 |

#### 5. タグ：属性ごとの視覚的区別（保存方法 vs その他）
| 項目 | 内容 |
|---|---|
| 現在の実装箇所 | `.tag`は6箇所（templates.py:1236,1369,1621/1622,1875、およびJS内1806）でフラットな`service.get("tags", [])`をそのまま出力。`meal_form_categories()`は現在`generators.py:14-26`。`data/services.json`の`tags`には`meal_form`由来の文字列（例:"冷凍"）が実際に混在（データ変更は不要）。 |
| 変更内容 | ①`meal_form_categories()`を`generators.py`から`templates.py`へ移設し、`generators.py:139`の呼び出しを`templates.meal_form_categories(...)`に変更。②`templates.py`に`_tag_html(t)`ヘルパーを追加（`meal_form_categories(t)`が非空なら`tag tag-storage`、それ以外は従来の`tag`）。Python側5箇所を置換。③JS側1箇所(1806行)は`t.includes('冷凍')||t.includes('冷蔵')||t.includes('日配')`という等価ロジックで実装。④CSS追加: `.tag-storage { background:transparent; border:1px solid var(--color-border-strong); color:var(--color-text-muted); }`。 |
| 変更しないもの | タグの文言・データ、3件切り詰め(`[:3]`)ロジック、`PURPOSE_CATEGORIES`。 |
| UI仕様 | 上記CSSの通り。新色なし、既存トークンのみ。 |
| PC/モバイル影響 | `.tag`にレスポンシブ規則は無く、新modifierも同様（両幅で同一）。 |
| 実装順序 | **P2の1番目**（ラベル上はP2だが波及範囲が最大のため最初に安定させる）。**サブステップ化必須**: 5a（関数移設→build確認）→5b（TOP→比較一覧PC→比較一覧モバイル→詳細→比較ページ→診断結果の順に1箇所ずつ適用し都度build確認）。 |
| 検証方法 | 5b完了後`grep -rn "def meal_form_categories"`が`templates.py`内1件のみであることを確認。TOP/比較一覧(PC・モバイル)/詳細1件/比較ページ1件/診断結果1件をPlaywrightで目視し、冷凍/冷蔵/日配のみoutline調、他は従来の塗りピルであることを確認。 |
| リスク・副作用 | **8項目中最大**。呼び出し箇所6つ＋ファイル間の関数移設を伴うため取りこぼしが起きやすい。サブステップ化とgrep確認で対応する。 |

#### 6. 詳細ページ：主役ブロック（こんな方におすすめ）を際立たせる
| 項目 | 内容 |
|---|---|
| 現在の実装箇所 | `service_recommend_block()`(1157-1170)は既に`.card.panel-accent`。脇役カード: 基本情報(1262行)・初回キャンペーン・お試し(1274行)は共にプレーンな`.card`。 |
| 変更内容 | 脇役2枚（1262行・1274行）にのみ`class="card card-quiet"`を付与。CSS追加: `.card-quiet { box-shadow:none; background:transparent; border-color:var(--color-border); }`。 |
| 変更しないもの | `.card`本体（他の全ページに影響するため触らない）、料金カード(1255行)・解約送料(1281行)・特徴・良い点気になる点カードは対象外。`service_recommend_block`自体（既に`panel-accent`で区別済みのため手を加えない）。 |
| UI仕様 | 上記CSSの通り。既存トークン`--color-border`のみ使用。 |
| PC/モバイル影響 | `.card`にレスポンシブ規則は無く、両幅で同一。 |
| 実装順序 | P2の3番目（項目5・4の後、視覚言語の一貫性のため）。`build_service_page()`に閉じた独立変更。 |
| 検証方法 | 詳細ページ1件をPC・モバイルでスクリーンショットし、基本情報/キャンペーンカードが後退し、こんな方におすすめ/料金/特徴/良い点気になる点カードが従来通りであることを確認。 |
| リスク・副作用 | 低。`.card`本体は変更せず、2箇所のみに第2クラスを付与するため他ページへの波及なし。 |

### P3（軽微な仕上げ）

#### 7. 診断結果：「一致した条件」の軽い強調
| 項目 | 内容 |
|---|---|
| 現在の実装箇所 | JS内(1805,1813行)で`reason = matchedGoals.join('・')`を地の文表示。`matchedGoals`は1783行で算出。 |
| 変更内容 | `matchedGoals`各要素を個別の`<span class="tag">`にする。 |
| 変更しないもの | スコアリング・`TOP_N=3`(1791行)・カード構造・CTA。 |
| UI仕様 | 既存`.tag`クラスをそのまま使用（項目5実施済みなら`.tag-storage`区別も自動反映）。 |
| PC/モバイル影響 | なし、両方同一。 |
| 実装順序 | P3の2番目（項目8の後、同一関数内の編集の重複を避けるため）。 |
| 検証方法 | `/tool/diagnosis`で2条件以上選択し診断実行、一致条件がタグピル表示になることを確認。 |
| リスク・副作用 | 極小。単一JS箇所のみ。 |

#### 8. 診断導入文：期待値提示の追加
| 項目 | 内容 |
|---|---|
| 現在の実装箇所 | templates.py:1717の`<p>以下の条件を選ぶと、あなたに合いそうな宅配食サービスを表示します。</p>`直後（1719行）にチェックボックスカードが続く。 |
| 変更内容 | 1717行の直後に`<p class="price-meta">目的・保存方法を選ぶだけで、条件に近い上位3社をすぐに表示します。</p>`を追加。 |
| 変更しないもの | 既存の導入文、チェックボックス群、`runDiag()`ロジック。 |
| UI仕様 | 既存の`.price-meta`（控えめな小文字クラス）を流用、新規CSS不要。**文言注意**: 「3問で診断」的な言い回しは実態（複数選択チェックボックス＋即時マッチング）と合わないため使わず、`TOP_N=3`と整合する「上位3社を表示」という出力件数の説明にする。 |
| PC/モバイル影響 | なし、両方同一。 |
| 実装順序 | P3の1番目。単一の追記のみ。 |
| 検証方法 | `/tool/diagnosis`で新規行が1回だけ、正しい位置に表示されることを確認。 |
| リスク・副作用 | ほぼ無し。 |

## 実装順序（全体）

| Phase | 順序 | 項目 |
|---|---|---|
| P1 | 1→2→3 | 価格数字揃え → 比較ページ箇条書き化 → sticky thead（条件付き） |
| P2 | 5→4→6 | タグ区別（5a関数移設→5b適用） → TOPヒーロー数字 → 詳細ページ脇役カード |
| P3 | 8→7 | 診断導入文 → 診断結果タグ化 |

## Phase完了時の確認事項（安全に次へ進めるための基準）

**P1→P2に進む前**:
- `python tools/build.py`と`python tools/sitegen/validate.py`が成功。
- PC(1280px)で`/ranking`の価格列・（実施していれば）ヘッダーのsticky挙動を目視確認。
- モバイル(375px)で`/ranking`の`.ranking-mobile`カード表示に変化がないこと。
- 「表示価格が安い順」チェック・保存方法フィルタが従来通り機能する。
- `/comparisons/*.html`で箇条書き表示・CTA数（6個）に変化がないこと。
- sticky theadが目視で効いていない場合は、`<thead>/<tbody>`構造のみ残し`position:sticky`のCSSを外して次へ進んでよい（ブロッカーにしない）。

**P2→P3に進む前**:
- build/validate成功。
- `grep -rn "def meal_form_categories"`が`templates.py`内1件のみ。
- TOP／比較一覧(PC・モバイル)／詳細1件／比較ページ1件／診断結果1件で、冷凍/冷蔵/日配タグのみoutline調、他は従来の塗りピルで一貫していることを確認。
- TOP（PC・モバイル）で新しい数字がCTAと衝突しないこと。
- 詳細ページで基本情報/キャンペーンカードが後退し、他のカードは無変化であること。
- `git diff --stat data/ config/`が空（データ・スキーマ変更が無いこと）。

**全体完了時**:
- build/validate成功。
- `/tool/diagnosis`で導入文１回＋結果タグ化を確認。
- TOP・比較一覧・詳細1件・比較ページ1件・診断＋結果をPC/モバイル双方でPlaywright目視し、累積変更によるレイアウト崩れが無いこと。
- `git diff`が`tools/sitegen/templates.py`と`tools/sitegen/generators.py`のみに閉じていること。

## 制約の遵守確認

- 新しい色相・写真・★評価/王冠/メダル等のランキング装飾・リブランディングは含まない。
- `data/*.json`・`config/*.json`のスキーマ変更・新規データフィールドは含まない（項目5の`meal_form_categories()`移設はPythonコードの移動のみで、データファイルには一切触れない）。
- 導線・CTA・セクション順序の変更は含まない（[[DIAGNOSIS_COMPARE_CTA_FUNNEL_AUDIT_2026_08_28.md]]の凍結判定を維持）。
- 新規CSSクラスは`.td-price`（配置指定のみ）・`.tag-storage`・`.card-quiet`の3つに限定し、いずれも既存のカラートークン（`--color-border-strong`/`--color-border`/`--color-text-muted`/`--color-surface-alt`）のみを使用する。
- 既存の「表示価格が安い順」ソートJSが依存する`data-price`/`data-mealform`属性・`<tr>`/`.svc-card`の直接的な親子関係は変更しない。
- 本ドキュメントの作成時点でコード変更（`tools/sitegen/templates.py`・`generators.py`）は一切行っていない。実装は別セッション・別タスクで、本計画を参照して行う。

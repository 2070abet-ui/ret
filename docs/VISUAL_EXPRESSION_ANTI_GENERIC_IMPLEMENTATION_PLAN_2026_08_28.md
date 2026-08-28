# Visual Expression / Anti-Generic 実装計画（2026-08-28）

作成日: 2026-08-28
位置づけ: [[VISUAL_EXPRESSION_ANTI_GENERIC_AUDIT_2026_08_28.md]]（READ ONLY監査）を受けた実装計画。**本ドキュメントの作成自体がタスクであり、`tools/sitegen/templates.py`へのコード変更はまだ行っていない。** 実装は本計画を参照する別セッションで行う。

Explore agent 2件＋Plan agent1件による調査結果を、Read/Grepで直接ファイルを確認して検証済み（`tools/sitegen/templates.py`、2480行、[[VISUAL_DESIGN_SYSTEM_IMPLEMENTATION_PLAN_2026_08_28.md]]実装後の最新版）。行番号・現状コードはすべて実ファイルと一致することを確認済み。

## 監査ドキュメントの表現を1点訂正

監査が「画面幅いっぱいに敷いて」と表現した色帯パターンは、実際には`.purpose-section-top`のように**1200pxコンテナ内の色付き角丸ボックス**に過ぎず、真の画面端までの全幅（`header.site`と同じ）ではない。真の全幅ブリードには新規CSSユーティリティ（`100vw`+負マージン手法）が必要で、`100vw`がスクロールバー幅を含むブラウザでの横スクロール発生という既知の落とし穴がある。**本計画ではこのリスクを避け、`.trust-panel-compact`（既存の「箱を弱めた」パターン：影なし・枠線なし・地色に馴染ませる）を安全な前例として踏襲する方向を採用する**（真の全幅ブリードは行わない）。

## スコープの境界線（先に固定する）

「脱カード化・非対称化は本当に目立たせたい1〜2箇所だけ」という監査の制約を以下のように運用する。

- 脱カード化・非対称化の対象は実質2種類のみ:
  1. TOP「このサイトのこだわり」ブロック（項目1）
  2. キャンペーン訴求ブロック（項目3：TOP／項目3b：`/campaigns.html`）— 同一コンテンツ種別への統一表現として1つの意思決定の2箇所反映であり、「もう1箇所追加」ではない
- 見出し罫線（項目4・6）・数字の書体強調（項目2）・アイコン（項目5）は別カテゴリの装飾追加として扱い、各項目とも**明示した1箇所のみ**に限定する。
- 既存の脱カード化事例（`.trust-panel-compact`、`.purpose-section-top`）は変更しない。

## 実装項目一覧

| # | 項目 | 分類 | 対象関数 |
|---|---|---|---|
| 1 | 「このサイトのこだわり」の脱カード化 | P1 | `build_index_page`（2011-2018行） |
| 2 | Hero数値の書体コントラスト強化 | P1 | `build_index_page`（1982-1984行） |
| 3 | TOPキャンペーンブロックの非対称化＋色帯 | P2 | `build_index_page`（1889-1894, 2005-2009行） |
| 3b | `/campaigns.html`への同一処理の移植 | P2 | `build_campaigns_page`（1569-1602行） |
| 4 | 「主要サービス一覧」見出しの太罫線 | P2 | `build_index_page`（1995行） |
| 5 | 保存方法カテゴリの最小ラインアイコン | P3 | `_tag_html`（51-56行）＋診断JS（1852-1853行） |
| 6 | 「選び方のポイント」見出しの千鳥罫線 | P3 | `build_ranking_page`（1517行） |

---

## 項目1：「このサイトのこだわり」の脱カード化

| 項目 | 内容 |
|---|---|
| 対象ページ・コンポーネント | `build_index_page`（2011-2018行） |
| 現在の実装 | `<div class="card"><h2>このサイトのこだわり</h2><ul class="feature-list">...3項目...</ul></div>`。`.card`(143-152行)＝白背景＋枠線＋角丸＋影。サイト内の他ほぼ全ブロックと同一の視覚処理 |
| 具体的な変更方法 | 新規クラス`.section-flat`をこのdivのみに使用（`class="card"`→`class="section-flat"`）。CSS追加: `.section-flat { background:var(--color-surface-alt); border:none; border-radius:var(--radius-sm); box-shadow:none; padding:var(--space-4) var(--space-5); margin:var(--space-4) 0; } .section-flat h2 { margin-top:0; }` |
| 使用する既存トークン | `--color-surface-alt`, `--radius-sm`, `--space-4`, `--space-5`（新色なし） |
| PC/モバイル | 共通ルールでよい。追加メディアクエリ不要（`--space-*`のみで構成済み） |
| 視覚的な狙い | 相対的に重要度の低い補足訴求を影・枠線なしのフラット面にし、主要導線（サービス一覧・キャンペーン）の箱にまだ意味のあるコントラストを残す |
| やりすぎにならない制約 | `.section-flat`はこのブロック専用。既存の`.card-quiet`（詳細ページ脇役カード用）とは統合・転用しない |
| 回帰リスク | 低。単独ブロックのクラス置換＋新規CSS追加のみで他要素へ影響なし |
| 検証方法 | `python tools/build.py`後、`site/index.html`をPC(1280px)・モバイル(375px)で確認し、影・枠線が無いことと周囲ブロックとの余白衝突がないことを目視 |

## 項目2：Hero数値の書体コントラスト強化

| 項目 | 内容 |
|---|---|
| 対象ページ・コンポーネント | `build_index_page`（1982-1984行） |
| 現在の実装 | `<span class="trust-figure">{num_services}</span>`。**`.trust-figure`(333行、font-size:2rem)はHeroの数字と`trust_panel()`が生成する検証カバレッジ3指標（TOP/ranking.html/verification.html共有）の両方に使われる共有クラス**——直接拡大すると意図しない箇所まで影響する |
| 具体的な変更方法 | Hero側のみ`class="trust-figure"`→`class="hero-figure"`に**完全に置き換え**（二重付与しない）。CSS追加: `.hero-figure { font:var(--price-figure); font-size:2.75rem; line-height:1.05; letter-spacing:-0.01em; }`。640pxブレークポイント内に`.hero-figure { font-size:2rem; }`を追加 |
| 使用する既存トークン | `--price-figure`（新色なし） |
| PC/モバイル | PC 2.75rem→モバイル2rem。既存の`.trust-figure`向けモバイル上書き（507,512行）は無変更 |
| 視覚的な狙い | Heroの最重要数値を他ページ共有の統計数値から視覚的に切り離し、サイズ差で情報階層を明確化 |
| やりすぎにならない制約 | `.hero-figure`はHeroのこの1箇所のみ。`trust_panel()`の他数値サイズは変更しない |
| 回帰リスク | **要注意**: 実装者が誤って`.trust-figure`本体（333,355,507,512行）を直接編集すると、TOP/ranking.html/verification.htmlの検証カバレッジ数値まで巨大化する。**新規クラス追加方式を厳守し、`.trust-figure`本体には触れないこと** |
| 検証方法 | `site/index.html`のHero数字拡大を確認しつつ、`site/ranking.html`・`site/verification.html`の検証カバレッジ数値サイズが**変化していない**ことを並べて確認 |

## 項目3：TOPキャンペーンブロックの非対称化＋色帯

| 項目 | 内容 |
|---|---|
| 対象ページ・コンポーネント | `build_index_page`（ソート1889行、ループ1890-1894行、markup 2005-2009行） |
| 現在の実装 | `confirmed_first = sorted(campaigns, key=lambda c: c.get("requires_verification", True))`→`confirmed_first[:3]`を同一の`<li>`として`camp_items`に蓄積、`<div class="card panel-accent">`内に`<ul class="feature-list">`で描画。3件とも完全に同一markup |
| 具体的な変更方法 | `confirmed_first[0]`（安定ソートによりcampaigns.json記載順で同点処理）を大きな「PICK UP」枠、`confirmed_first[1:3]`を小さいリストとして非対称レイアウト化。<br>Python: `camp_big_html`を`confirmed_first[0]`から`<div class="campaign-pick-main"><p class="campaign-pick-label">PICK UP</p><p class="campaign-pick-name">{svc_name0}</p><p class="campaign-pick-value">{value_text0}</p><a class="text-link" href="/campaigns">条件を見る →</a></div>`として生成、`confirmed_first[1:3]`は従来通り`<li>`として`small_camp_items`に蓄積。<br>Markup: `<div class="campaign-pick"><h2>🎯 初回キャンペーン・お試し情報（最新）</h2><div class="campaign-pick-body">{camp_big_html}<ul class="feature-list campaign-pick-list">{small_camp_items}</ul></div><p>...すべて見る...</p></div>`。<br>CSS: `.campaign-pick { background:var(--color-primary-subtle); border:none; border-radius:var(--radius-md); box-shadow:none; padding:var(--space-5); margin:var(--space-3) 0; } .campaign-pick-body { display:flex; gap:var(--space-5); align-items:stretch; } .campaign-pick-main { flex:1 1 40%; background:var(--color-surface); border-radius:var(--radius-sm); padding:var(--space-4); display:flex; flex-direction:column; gap:4px; } .campaign-pick-label { font:var(--text-meta); color:var(--color-primary); font-weight:700; letter-spacing:.05em; margin:0; } .campaign-pick-name { font:var(--text-h3); margin:0; } .campaign-pick-value { font:var(--price-figure); margin:0; } .campaign-pick-list { flex:1 1 55%; margin:0; }` |
| 使用する既存トークン | `--color-primary-subtle`, `--color-surface`, `--radius-md/sm`, `--space-3〜5`, `--text-meta/h3`, `--price-figure`, `--color-primary`（新色なし） |
| PC/モバイル | PC横並び、640pxで`.campaign-pick-body { flex-direction:column; }`に切替 |
| 視覚的な狙い | 均質な3件リストから「確認済み優先という既存データに基づく1件の主役化」へ。単なる広告面積拡大ではなく情報の優先順位の可視化 |
| やりすぎにならない制約 | 非対称レイアウトはこのブロックのみ。「選び方のポイント」等の他の3項目リストには適用しない |
| 回帰リスク | `confirmed_first`が空の場合`camp_big_html`が空文字列になる可能性（実データでは想定外だが実装時にフォールバック要検討）。`.campaign-pick`は`.card`のoverflow-x:auto挙動から外れるが、テーブルを含まないため実害なし |
| 検証方法 | `site/index.html`でPICK UP枠が明確に大きく残り2件が小さいこと、モバイルで縦積みが自然なことを確認 |

## 項目3b：`/campaigns.html`への同一処理の移植

| 項目 | 内容 |
|---|---|
| 対象ページ・コンポーネント | `build_campaigns_page`（1569-1602行） |
| 現在の実装 | `for c in campaigns`という**無ソートの生ループ**、`confirmed_first`ロジックを全く使わない。全カードが同一`.card`＋4行テーブル |
| 具体的な変更方法 | TOPと**同一の**ソート式をこの関数内にも追加（共通ヘルパーへの切り出しはスコープ外、視覚表現のみに限定するため）: `confirmed_first = sorted(campaigns, key=lambda c: c.get("requires_verification", True))`。`enumerate(confirmed_first)`でループし、`i==0`のみ`wrapper_cls="campaign-pick-featured"`＋`<p class="campaign-pick-label">PICK UP</p>`を追加、それ以外は`wrapper_cls="card"`のまま。既存のsummary/table/CTA部分（1587-1588行）は無変更。<br>CSS追加: `.campaign-pick-featured { background:var(--color-primary-subtle); border:none; border-radius:var(--radius-md); box-shadow:none; padding:var(--space-5); margin:var(--space-3) 0; }`（`.campaign-pick-label`は項目3で追加済みのものを再利用） |
| 使用する既存トークン | `--color-primary-subtle`, `--radius-md`, `--space-3/5`（新色なし） |
| PC/モバイル | 縦積みカード構成のため横並び非対称は行わず「先頭1件のみ色帯＋ラベル」の縦方向強弱のみ。追加メディアクエリ不要 |
| 視覚的な狙い | `/campaigns.html`が単なる広告一覧に見えないよう、TOPと同じ「確認済み優先」ロジックの再利用でページ間の一貫性も生む |
| やりすぎにならない制約 | featured化は先頭1件のみ。2件目以降は`.card`のまま完全無変更 |
| 回帰リスク | TOPの1889行と同一のソート式を複製することになり、将来`requires_verification`の判定基準変更時に2箇所同時修正を忘れるリスク。**両関数に「TOPの`confirmed_first`と同一ロジック、変更時は両方見ること」という相互参照コメントを残すことを実装時に必須とする**。`campaigns`が空の場合の挙動は現状と同じ（新規リスクではない）。aff_link呼び出し（1587-1588行）は無変更のためアフィリエイト属性への影響なし |
| 検証方法 | `site/campaigns.html`で先頭カードのみ色帯＋PICK UPラベル、`campaigns.json`の全件が欠落なく表示されることを件数で確認 |

## 項目4：「主要サービス一覧」見出しの太罫線

| 項目 | 内容 |
|---|---|
| 対象ページ・コンポーネント | `build_index_page`（1995行） |
| 現在の実装 | `<h2>📊 主要サービス一覧</h2>`。`h2`(129行)・`.page-head`(279-281行)ともborder系ルールなし。`_CSS`全体で`border-bottom`は8箇所のみ、すべてナビ下線/テーブル行/リンク下線用途で見出し用途はゼロ（新規パターン確定・実ファイルで確認済み） |
| 具体的な変更方法 | 新規クラス`.heading-rule`をこの見出しのみに付与。CSS: `.heading-rule { display:inline-block; padding-bottom:var(--space-2); border-bottom:3px solid var(--color-border-strong); }` |
| 使用する既存トークン | `--color-border-strong`, `--space-2`（新色なし） |
| PC/モバイル | 共通でよい、追加調整不要 |
| 視覚的な狙い | 全`h2`が同一余白ルールのみで並ぶ単調さに「ここが本題」という区切りを1箇所作る |
| やりすぎにならない制約 | `.heading-rule`はこの1見出しのみ |
| 回帰リスク | 低。新規クラス追加のみ、既存`h2`ルール無変更 |
| 検証方法 | `site/index.html`で当該見出しのみ罫線があり他のh2には無いことを確認 |

## 項目5：保存方法カテゴリの最小ラインアイコン

| 項目 | 内容 |
|---|---|
| 対象ページ・コンポーネント | `_tag_html`（51-56行）＋診断JS（1852-1853行） |
| 現在の実装 | `_tag_html`は`tag`/`tag tag-storage`のクラスのみでアイコンなし。`.tag-storage`(214行)はテキストのみの輪郭バッジ。**例外**: 診断ツール結果表示（1852-1853行）はクライアントサイドJSで独自に`isStorageTag`判定を行っており、`_tag_html`を経由しない |
| 具体的な変更方法 | `_tag_html`を拡張し、保存方法カテゴリ該当時のみ最小限のインラインSVGを前置: `_STORAGE_ICONS = {"冷凍": "<svg class=\"tag-icon\" ...>", "冷蔵": "...", "日配": "..."}`、`_tag_html`内で`meal_form_categories(t)`が非空なら`_STORAGE_ICONS.get(cats[0], "")`を`<span class="tag tag-storage">`の前に挿入。CSS: `.tag-icon { width:11px; height:11px; margin-right:3px; vertical-align:-1px; stroke:currentColor; fill:none; stroke-width:1.4; stroke-linecap:round; }`（`stroke:currentColor`で`.tag-storage`の`--color-text-muted`を継承、新規色トークン不要。SVGパスは実装セッションで実ブラウザ確認しながら微調整） |
| 使用する既存トークン | 新規CSS変数なし（currentColor継承のみ） |
| PC/モバイル | 共通。ranking.htmlモバイルカードでタグ折り返しに影響しないか実装後に目視確認 |
| 視覚的な狙い | 保存方法という機能的に重要だが地味な情報に最小限のピクトグラムで識別性を持たせる。単色ラインのみでアイコン濫用を回避 |
| やりすぎにならない制約 | アイコンは`tag-storage`（冷凍/冷蔵/日配）のみ。他の特徴タグには追加しない |
| 回帰リスク | **診断ツール結果（1852-1853行）は`_tag_html`を通らないため、そのままではアイコンが付かずページ間で不一致になる**。対応方針を実装時に確定: (a) 同じSVGをJS側にも複製［推奨——「なぜここだけ違う」という新たな違和感を避けるため］、(b) スコープ外と明記し不一致を許容。`_tag_html`はranking表・TOPカード・サービス詳細で共有されており影響範囲が広いため、変更後は全呼び出し箇所を目視確認する |
| 検証方法 | `site/ranking.html`(PC表＋モバイルカード)・`site/index.html`(TOPカード)・任意のサービス詳細ページでアイコン表示を確認。診断ツール結果は確定した対応方針との整合を確認 |

## 項目6：「選び方のポイント」見出しの千鳥罫線

| 項目 | 内容 |
|---|---|
| 対象ページ・コンポーネント | `build_ranking_page`（1517行） |
| 現在の実装 | `<h2>選び方のポイント</h2>`。プレーンな`.card`内、罫線なし |
| 具体的な変更方法 | 新規クラス`.heading-staggered`をこの見出しのみに付与（項目4の直線罫線とは異なる質感）。CSS: `.heading-staggered { position:relative; display:inline-block; padding-bottom:10px; margin-bottom:var(--space-2); } .heading-staggered::after { content:""; position:absolute; left:0; bottom:0; width:40px; height:3px; background:var(--color-primary); border-radius:2px; } .heading-staggered::before { content:""; position:absolute; left:48px; bottom:2px; width:14px; height:2px; background:var(--color-border-strong); border-radius:1px; }` |
| 使用する既存トークン | `--color-primary`, `--color-border-strong`, `--space-2`（新色なし） |
| PC/モバイル | 共通、絶対値40px/14pxは375px幅でも問題ない想定。実装後に文字列との重なりを確認 |
| 視覚的な狙い | 項目4と異なる罫線表現を別の1箇所に置くことで単調さを避けつつ、サイト全体では2種類の罫線表現に留める（3種類目は作らない） |
| やりすぎにならない制約 | `.heading-staggered`はこの1見出しのみ。項目4の`.heading-rule`と併用しない。他のh2にも広げない |
| 回帰リスク | 低。新規クラス・疑似要素の追加のみ |
| 検証方法 | `site/ranking.html`で当該見出しのみ長短2本のオフセット罫線が表示され、他見出しに影響がないことを確認 |

---

## バナーについてのノート（項目3・3bの位置づけ）

- **サイズ非対称**: `confirmed_first[0]`のみ大きい枠、残りは小さい表示——単純な1件拡大ではなく情報階層を作る。
- **既存データの流用**: 新しいランキング指標・広告優先度は作らない。TOPで既に使われている「確認済み優先」ソートをそのまま再利用。
- **色帯であって影の強化ではない**: `.campaign-pick`/`.campaign-pick-featured`は`box-shadow:none`——既存の`.card`より影を**弱める**方向。
- **誠実な非緊急CTA**: 「条件を見る →」「すべてのキャンペーンを見る →」という既存の落ち着いた文言を維持。「今だけ」「残りわずか」等は追加しない。
- **既存の🎯絵文字（2006行）は現状維持**: 本計画は視覚的な箱・レイアウト変更が目的でありコピー編集はスコープ外。

## 実装手順：P1 → 検証 → P2 → 検証 → P3 → 最終検証

### Phase P1（項目1・2）
実装後 `python tools/build.py` を実行。

**P1→P2移行チェックリスト**:
- [ ] `site/index.html`で「このサイトのこだわり」に影・枠線が無いことを確認
- [ ] Hero数字が拡大され、`site/ranking.html`・`site/verification.html`の検証カバレッジ数値サイズが**変化していない**ことを確認（`.trust-figure`衝突なしの確認）
- [ ] PC(1280px)・モバイル(375px)双方で崩れがないこと
- [ ] `git diff`でCSS追加・markup変更が意図した箇所に限定されていること（`.card`/`.trust-figure`本体への意図しない変更が無いか）

### Phase P2（項目3・3b・4）
実装後 `python tools/build.py` を再実行。

**P2→P3移行チェックリスト**:
- [ ] `site/index.html`のキャンペーンブロックでPICK UP枠が明確に大きく、残り2件が小さいこと
- [ ] `site/campaigns.html`で先頭カードのみPICK UPラベル・色帯、2件目以降は従来通りの白カードであること
- [ ] `campaigns.json`の全件が`/campaigns.html`から欠落せず表示されていること（件数確認）
- [ ] TOP・campaigns.html双方でモバイル(375px)の縦積みが自然であること
- [ ] 「主要サービス一覧」見出しにのみ太罫線があり他のh2には無いこと
- [ ] funnel/CTA/ナビ/セクション順序（[[DIAGNOSIS_COMPARE_CTA_FUNNEL_AUDIT_2026_08_28.md]]で凍結済み）に変更が無いことをdiffで確認
- [ ] `site/ranking.html`のソート/フィルタJSが正常動作すること（本フェーズはranking.htmlのmarkupを変更していないため非退行のはずだが念のため確認）

### Phase P3（項目5・6）
実装時に項目5の診断ツールJS対応方針（(a)複製/(b)スコープ外明記）を確定。実装後 `python tools/build.py` を再実行。

**最終検証チェックリスト（サイト全体）**:
- [ ] build/validateがエラーなく完走
- [ ] 保存方法アイコンが`site/ranking.html`(PC表＋モバイル)・`site/index.html`(TOPカード)・任意のサービス詳細ページで一貫して表示
- [ ] 診断ツール結果のアイコン有無が確定方針と一致
- [ ] 「選び方のポイント」見出しの千鳥罫線が該当箇所のみ
- [ ] 脱カード化・非対称化された箇所が「このサイトのこだわり」「キャンペーンブロック(TOP＋campaigns.html)」の2種類のみであり、他セクションが従来の`.card`のままであること（境界線の最終監査）
- [ ] `_CSS`のdiffで新規`--color-*`宣言が増えていないこと
- [ ] PC(1280px)・モバイル(375px)でTOP・ranking・campaigns・サービス詳細1件をスクリーンショット比較し崩れがないこと
- [ ] `git diff --stat`が`tools/sitegen/templates.py`のみに収まっていること（`data/`・`config/`は無変更）

## 制約の遵守確認

- 新しい色相・写真・★評価/王冠/ランキング装飾・紫青グラデーション・ガラスモーフィズム・絵文字追加・不必要なアイコン濫用・新機能・全面リデザイン・リブランディングは含まない。
- 既存の`--radius-sm/md/lg`・`--shadow-sm/md`より強い丸み・影は追加しない（除去する方向のみ）。
- 新規CSSクラスは`.section-flat`・`.hero-figure`・`.campaign-pick`系（`-body`/`-main`/`-label`/`-name`/`-value`/`-list`/`-featured`）・`.heading-rule`・`.heading-staggered`・`.tag-icon`に限定し、いずれも既存カラートークンのみを使う。
- funnel/CTA/ナビ/セクション順序（[[DIAGNOSIS_COMPARE_CTA_FUNNEL_AUDIT_2026_08_28.md]]で凍結済み）は変更しない。
- `data/*.json`・`config/*.json`のスキーマ変更・新規データフィールドは含まない。
- 本ドキュメントの作成時点でコード変更（`tools/sitegen/templates.py`）は一切行っていない。実装は別セッションで、本計画を参照して行う。

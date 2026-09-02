---
name: article-writing-workflow
description: 宅食図鑑の記事作成依頼（「記事を書いて」「新しい記事を追加して」「◯◯についての記事作って」「既存記事を見直して」等）を受けたとき、追加の手順指示なしで自律実行するワークフロー。Context Audit → Topic & Keyword Research → Outline → Draft → Self-Review/Fact-Check → Wire-up → SEO/GEO Technical Review → Build & Validate → Browser Review → Report を実行し、docs/ARTICLE_WRITING_PRINCIPLES.mdに沿った記事をtools/sitegen/templates.pyのbuild_article_*関数として実装する。ranking/services等のUI変更・data/schema変更・アフィリエイトロジック変更は行わない。
---

# 記事作成ワークフロー（宅食図鑑）

「記事を書く／追加する／見直す」依頼を受けたら、このSkillを起動し、以下を自律実行する。**追加のワークフロー指示は求めない。**

## 最重要ルール

- **`docs/ARTICLE_WRITING_PRINCIPLES.md`（記事執筆原則・基準文書）を必ず読む。** 本サイトの記事コンテンツを恒久的に導く執筆基準であり、すべての記事作成・見直しはこの原則（結論先出し＋自己完結型構成、検証データの見せ方、タイトルルール、行動経済学の許可/禁止リスト、体験の誠実性、恒久禁止事項）に従う。
- 既存のプロジェクト方針・data/model・差別化要素・機能を勝手に変更しない。
- data/schema変更（`data/services.json`への`article_link`/`article_label`追加を含む）・アフィリエイトロジック変更・SEO構造（canonical/robots/sitemap）の変更を伴う場合は、実行前にユーザーへ確認する。
- 実在しない体験談・口コミ・数値を書かない。検証データ（公式一次情報）と主観的体験は明確に区別する（`ARTICLE_WRITING_PRINCIPLES.md` 8章）。
- 既存記事・既存ページ（ranking/services/comparisons）とテーマ・内容が重複する記事を作らない。

## リポジトリ前提（このプロジェクト固有）

- 静的サイト生成: `data/*.json` + `config/*.json`（単一情報源）→ `tools/sitegen/*.py` → `site/`（生成HTML・Git管理外）
- 記事コンテンツの実体は **`tools/sitegen/templates.py`** 内の `build_article_*` 関数（例: `build_article_chef_muten_kuchikomi(aff_links)`、`build_article_koreisha_takushoku(services, aff_links, sources_by_id=None)`）。1記事＝1関数。
- 記事の出力配線は **`tools/sitegen/generators.py`**：`(out_dir / "articles" / "<slug>.html").write_text(templates.build_article_X(...), encoding="utf-8")` → `pages.append("articles/<slug>.html")` の2行を追加する。
- 記事一覧への内部リンクは `templates.py` の **`ARTICLES_INDEX`**（リストに `(url, label)` タプルを追加）と `articles_index_block()`（TOP・ranking.htmlの両方から呼ばれる共通ブロック）。新規記事は必ずここに追加し、孤立ページ（被リンクなし）を作らない。
- サービス詳細ページから記事への被リンクは `data/services.json` 各サービスの `article_link`/`article_label` フィールド（任意）。新設・変更する場合はdata/schema変更にあたるため事前確認が必要。
- 記事内で使う共通関数（再利用する。重複実装しない）: `_pricing_of`, `_price_inline_html`, `pricing_detail_html`, `mobile_scroll_hint()`, `aff_link(aff_links, service_id, label=..., cls=...)`, `affiliate_disclosure_note()`, `vstatus_badge()`, `source_link()`, `esc()`。
- **`site/` は生成物。読まない・直接編集しない。** 変更反映は `python tools/build.py` で再生成する。
- 検証: リポジトリルートから `PYTHONPATH=tools python tools/sitegen/validate.py`（`PYTHONPATH`なしだと`ModuleNotFoundError: No module named 'sitegen'`になる。実行確認済み） / ビルド: リポジトリルートから `python tools/build.py`
- 記事執筆の基準: **`docs/ARTICLE_WRITING_PRINCIPLES.md`（必読）**。UI全般の基準は `docs/UI_DESIGN_PRINCIPLES.md`（記事以外のページが対象、本Skillの対象外）。docsの索引は `docs/README.md`。
- 検索は `git grep` を優先。`site/`, `__pycache__`, `data/snapshots/`, 巨大JSON, HISTORY docs を掘らない。

---

## Phase 1 — Context Audit（前提把握）

- Git状態（`git status` / `git log --oneline -5`）
- **`docs/ARTICLE_WRITING_PRINCIPLES.md` を全文読む**（記事タイプ分類・構成テンプレート・タイトルルール・行動経済学の許可/禁止・恒久禁止事項）
- 既存記事の一覧: `templates.py` の `ARTICLES_INDEX` とテンプレート内の `build_article_*` 関数を確認し、依頼テーマとの重複がないか確認
- `data/services.json` を読み、依頼テーマに該当するサービス数・タグ・データの厚み（価格confirmed件数等）を確認する。**データが薄いテーマ（該当サービスが1〜2社しかない等）は、書ける記事にならないため早期にユーザーへ報告しピボットを提案する**（過去の「無添加」→「高齢者向け」ピボットの教訓）。
- `data/campaigns.json` / `data/sources.json`（確認日・出典として使う一次情報）
- `config/affiliates.json`（既存のアフィリエイトリンク有無。新サービスへのリンクが必要な場合は事前確認）

## Phase 2 — Topic & Keyword Research（テーマ・キーワード選定）

依頼にテーマが明示されていない、または広すぎる場合に実施する。テーマが明確に指定されている場合は簡略化してよい。

- `docs/ARTICLE_WRITING_PRINCIPLES.md` 3章「今後の記事候補」を優先候補として参照する
- WebSearch等で競合・類似サイト（silver-choice.jp・マイベスト・宅食グルメ・宅食レポ等）の人気記事・ロングテールキーワードを調査する（`ARTICLE_WRITING_PRINCIPLES.md` 2章の記事タイプ分類に沿って評価する）
- 検索意図（informational / commercial investigation）を明確にし、記事タイプ（`ARTICLE_WRITING_PRINCIPLES.md` 2章のA〜H）を決定する
- 決定したテーマ・キーワード・記事タイプ・対象サービスをユーザーに簡潔に共有してから執筆に進む（大規模な新規記事の場合）

## Phase 3 — Outline（構成設計）

`ARTICLE_WRITING_PRINCIPLES.md` 4章の構成テンプレートに従ってアウトラインを作る。

1. 結論ブロック（H1直下、1〜3文で要旨）
2. 各H2セクションの一文結論（answer-first）
3. 比較表の配置箇所（該当する記事タイプの場合）
4. Q&Aブロック（末尾、想定質問をそのまま見出しに）
5. 目安文字数（`ARTICLE_WRITING_PRINCIPLES.md` 9章の記事タイプ別目安）
6. CTA配置（記事内の公式サイトCTA回数・配置。既存記事の`aff_link(..., cls="btn-primary"/"btn-secondary")`パターンに合わせる）

## Phase 4 — Draft（執筆・実装）

`templates.py` に `build_article_X(...)` 関数を新設する。

- 既存記事（`build_article_koreisha_takushoku`等）をパターンとして踏襲し、共通関数を再利用する（重複実装しない）
- 検証データの見せ方（`ARTICLE_WRITING_PRINCIPLES.md` 5章）: 確認日・出典を主要な数値の近くに明記、「当サイトが公式サイトで確認したところ」等の第三者確認の書き方
- タイトルルール（6章）: 鮮度表記（【◯年◯月最新】等）を使う場合は `LAST_VERIFIED_DATE` から動的算出する（**直書き禁止**。2026-09-02のUI監査で発見した鮮度ズレバグの再発防止）
- 行動経済学の許可リスト（7.1章）のみ使用し、禁止リスト（7.2章）・偽の緊急性・★評価等の恒久禁止事項（10章）に触れない
- 体験の誠実性（8章）: 実際に行っていない体験談を書かない
- `affiliate_disclosure_note()` を末尾に含める

## Phase 5 — Self-Review & Fact-Check（自己レビュー）

執筆直後に自分で確認する（編集者レビューに相当）。1回の通し読みで済ませず、**観点の異なる複数パスに分けて**確認する（混ぜて読むと事実誤りと文章表現の粗さを同時に見落としやすいため）。

1. **事実確認パス**（数値・出典）
   - 記事中の価格・送料・キャンペーン等の数値が `data/services.json` / `data/campaigns.json` / `data/sources.json` の値と一致しているか
   - 確認日・出典リンクが主要な数値に付いているか
2. **構成・一貫性パス**（章立て・整合性）
   - `ARTICLE_WRITING_PRINCIPLES.md` 11章のチェックリスト（8項目）を通す
   - 記事タイトル・見出しが実際の内容量・比較軸数と一致しているか（誇張がないか）
3. **文章パス**（表現・誠実性）
   - 捏造した体験談・口コミ・緊急性演出・根拠のない断定表現がないか
   - 冗長な言い回し・同じ主張の繰り返しがないか

## Phase 6 — Wire-up（配線）

1. `generators.py` に出力呼び出しを追加（`out_dir / "articles" / "<slug>.html"` への `write_text` と `pages.append(...)`）
2. `templates.py` の `ARTICLES_INDEX` に `(url, label)` を追加し、TOP・ranking.htmlからの内部リンクを確保する
3. 関連サービスへの逆リンクが必要な場合、`data/services.json` の該当サービスに `article_link`/`article_label` を追加する。**これはdata/schema変更にあたるため、事前にユーザーへ確認してから実施する。**

## Phase 7 — SEO / GEO Technical Review

- meta title・meta description（`page_header` に渡す `title`/`desc`）が記事内容と一致しているか、鮮度表記が動的算出になっているか
- 見出し階層（H1→H2→H3）が論理的か、キーワード詰め込みになっていないか
- 比較表・Q&Aブロックの構造（GEO対応：自己完結段落・結論先出し）が`ARTICLE_WRITING_PRINCIPLES.md` 4章の基準を満たしているか
- 内部リンク（`ARTICLES_INDEX`・関連サービスへのリンク・戻り導線）が機能しているか、孤立ページになっていないか
- 構造化データとの整合性: 記事ページが継承する `page_header` のJSON-LD（現状サイト全体で`WebSite`のみ）と、記事内の可視テキスト（タイトル・見出し・Q&A等）に矛盾がないか確認する。新たにArticle/FAQPage等のJSON-LDを追加する場合はtemplates.pyの構造変更にあたるため、事前にユーザーへ確認してから実施する（可視コンテンツと一致しない構造化データを書かない）

## Phase 8 — Build & Validate

- `python tools/build.py`（`site/` 再生成、生成ページ数・エラー有無を確認）
- `PYTHONPATH=tools python tools/sitegen/validate.py`（pricing schema等の整合性検証。リポジトリルートから実行し、`PYTHONPATH`を付けないと`ModuleNotFoundError`になる）
- エラーがあれば修正して再実行する

## Phase 9 — Browser Review

Playwright等のブラウザ操作環境が利用可能なら、実際のブラウザで確認する。ローカルサーバーで配信し、**desktopとmobileの両方**を確認する。

- 記事ページのfirst view・見出し階層・比較表の表示
- CTAボタンの表示崩れ（特に`.aff-note`を含む`btn-primary`/`btn-secondary`。折り返し崩れは過去に実際に発生した既知の不具合パターン）
- 内部リンク（`ARTICLES_INDEX`経由のTOP・ranking.htmlからの導線、関連サービスへのリンク）が実際に機能するか
- モバイルでの比較表の横スクロール・情報欠落の有無

**コードだけを見て「問題なし」と判断しない。**

## Phase 10 — Report

最後に簡潔に報告する。以下だけを出す。

1. 追加・変更した記事とその内容（テーマ・記事タイプ・対象サービス）
2. `ARTICLE_WRITING_PRINCIPLES.md` のどの基準をどう反映したか（構成テンプレート・検証データの見せ方・タイトルルール等）
3. 配線状況（`ARTICLES_INDEX`・`generators.py`・`data/services.json`の`article_link`変更有無）
4. build/validate結果
5. data/schema変更を伴う場合はその内容と承認状況
6. 追加で変更すべきでない事項（触らなかった範囲の明示）

---

## 自律判断ルール

依頼の規模に応じてフェーズを取捨する。

| 依頼の規模 | 実行フェーズ |
|---|---|
| 新規記事の追加（テーマ未指定） | 全Phase |
| 新規記事の追加（テーマ・キーワード指定済み） | Context Audit → Outline → Draft → Self-Review → Wire-up → SEO/GEO Review → Build/Validate → Browser Review → Report（Phase 2は簡略化） |
| 既存記事の文言・数値見直し（鮮度更新等） | Context Audit → Self-Review/Fact-Check → Build/Validate → Report |
| 既存記事の構成見直し（`ARTICLE_WRITING_PRINCIPLES.md`準拠チェック） | Context Audit → Outline見直し → Self-Review → SEO/GEO Review → Report |

## 絶対禁止

- data/schema変更（`data/*.json`・`config/*.json`）を事前確認なしに行う
- アフィリエイトロジック変更（`config/affiliates.json` のリンク等）
- SEO構造の不用意な変更（canonical・robots・sitemap・タイトル構造）
- `ranking`/`services`/`comparisons`/`diagnosis`等、記事以外のページUIを記事作成のついでに変更する
- 実在しない体験談・口コミ・数値の記載
- 偽の緊急性・残りわずか演出、根拠のない「おすすめNo.1」等の恒久禁止事項（`ARTICLE_WRITING_PRINCIPLES.md` 10章）
- 鮮度表記（【◯年◯月最新】等）の直書き（`LAST_VERIFIED_DATE`からの動的算出を必須とする）
- 既存記事・既存ページとテーマが重複する記事の量産
- 文字数を稼ぐための水増し・機械的な大量生成
- `site/`・`__pycache__`・build成果物・巨大JSONを大量に読み込む
- commit / push をユーザーの明示指示なしに行う

## Token / Context最適化

- このSkill自体を簡潔に保つ。
- 毎回リポジトリ全体を読まない。`docs/ARTICLE_WRITING_PRINCIPLES.md`・依頼テーマに関連するdata/services.jsonの該当サービスだけを読む。
- `site/`・`dist`・`build`・`coverage`・`cache`・`__pycache__`・`data/snapshots/`・生成物・巨大JSONは原則除外。
- 長大な既存docs（HISTORY分類）は毎回全文読まず、必要な箇所だけ`git grep`で検索する。
- 競合サイトの調査（Phase 2）が大規模になる場合は、forkまたはサブエージェントに委任し、本セッションのコンテキストを圧迫しない。

## 最終原則

目的は「記事数を増やすこと」ではなく、**`docs/ARTICLE_WRITING_PRINCIPLES.md`の基準を満たす記事を通じて、検索・AI引用・読者の意思決定のすべてに効く一次情報の強みを最大化すること**。

- 既存仕様（data/schema・アフィリエイトロジック）を変更する可能性がある場合、破壊的変更を実行せず、その点だけユーザーに確認する。
- commit / push はユーザーの明示指示があるまで行わない。

---
name: ui-design-workflow
description: 宅食図鑑のUI改善依頼（「UI改善して」「このページ再設計して」「フロント磨いて」「比較ページ見やすくして」「スマホUI直して」等）を受けたとき、追加の手順指示なしで自律実行するワークフロー。Context Audit → UX/Funnel Audit → Design → Implement → Baseline Polish → Accessibility → Guidelines QA → Browser Review → Final Verification → Report を実行し、購買意思決定ファネルとUI品質を最大化する。機能追加・data/model変更・差別化要素変更は行わない。
---

# UI自律改善ワークフロー（宅食図鑑）

「UIを改善する」依頼を受けたら、このSkillを起動し、以下を自律実行する。**追加のワークフロー指示は求めない。**

## 最重要ルール

- 既存のプロジェクト方針・data/model・差別化要素・機能を勝手に変更しない。
- 新機能追加・データ構造変更・ビジネスロジック変更・API仕様変更・アフィリエイトロジック変更・SEO構造の不用意な変更はUI改善の範囲外。
- 既存UIを「AIっぽい綺麗なUI」に置き換えるのではなく、**このサイト固有の購買意思決定ファネルを強化する**。
- 既存デザインの良い部分を理由なく破壊しない。必ず既存コードとUI設計方針を先に理解してから変更する。

## リポジトリ前提（このプロジェクト固有）

- 静的サイト生成: `data/*.json` + `config/*.json`（単一情報源）→ `tools/sitegen/*.py` → `site/`（生成HTML・Git管理外）
- フロントエンド本体は **`tools/sitegen/templates.py`**。HTMLテンプレートとデザインシステムCSS（`_CSS`）が同梱されている。
- **`site/` は生成物。読まない・直接編集しない。** 変更反映は `python tools/build.py` で再生成する。
- デザイントークンは `templates.py` の `_CSS` `:root` に定義済み（`--color-*`, `--space-*`, `--radius-*`, タイポグラフィ等）。理由なく変更・破壊しない。
- 検証: `python tools/sitegen/validate.py` / ビルド: `python tools/build.py`
- 現行UI仕様: `docs/FINAL_REDESIGN_SPEC.md`。docsの分類・索引は `docs/README.md`。
- `docs/UI_DESIGN_PRINCIPLES.md` が存在すれば必ず読む（無ければ現行仕様で代替）。
- 検索は `git grep` を優先。`site/`, `__pycache__`, `data/snapshots/`, 巨大JSON, HISTORY docs を掘らない。

## ファネル構造

TOP（`index.html`）→ 比較一覧（`ranking.html`）→ 詳細（`services/*.html`）→ 診断（`tool/diagnosis.html`）→ 比較（`comparisons/*.html`）→ CTA / 購買行動

---

## Phase 1 — Context Audit

対象の範囲を絞って確認する（リポジトリ全体は読まない）。

- Git状態（`git status` / `git log --oneline -5`）
- フロントエンド構成: `tools/sitegen/templates.py`（HTML+CSS）・`tools/sitegen/generators.py`（ページ生成）
- 対象ページ: どの生成関数が作るか（generators.py の `main()` 参照）
- 関連コンポーネント: `templates.py` 内の共通関数（`aff_link`, `price`, `trust_bar`, `card` 等）
- data/model: `data/*.json`・`config/*.json`（**読むだけ**・変更しない）
- 既存デザインシステム: `_CSS` の `:root` トークン
- responsive構造: `_CSS` 内の media query（640px等）
- 既存UIの共通パターン: カード・テーブル・`btn-primary`/`btn-secondary`・検証ステータスバッジ等
- 関連docs: `docs/UI_DESIGN_PRINCIPLES.md`（あれば必読）・現行UI仕様 `docs/FINAL_REDESIGN_SPEC.md` の必要箇所

不要な大量ファイル・生成物・`site/`・`node_modules`・build成果物は読み込まない。

## Phase 2 — UX / Funnel Audit

対象ページが購買意思決定ファネルのどこに位置するか判断する。

確認項目:

- このページの目的（ファネル上の役割）
- ユーザーが最初に理解すべき情報
- first view（最初の1画面）
- visual hierarchy / information density
- CTA hierarchy
- comparison clarity（比較の分かりやすさ）
- trust / credibility（検証状態・出典・運営者情報）
- mobile usability
- 次に進むべき行動（次のファネルステップ）

単なる装飾改善ではなく、**ユーザーの意思決定を助けるUI**になっているかを優先する。

## Phase 3 — Design Direction

`frontend-design` Skillが利用可能なら使用する。実装前に以下を整理する。

- Purpose（目的）
- Audience（対象ユーザー）
- Tone（トーン）
- Constraints（制約: 既存トークン・既存仕様・検証状態の意味は変えない）
- Differentiation（差別化要素）

既存サイトのブランド（primary `#E8552D` 等）・デザインとの一貫性を維持し、テンプレート的なAI UIを避ける。既存デザインの良い部分を理由なく壊さない。

## Phase 4 — Implement

設計後に実装する。編集対象は `tools/sitegen/templates.py`（または対象ページ生成関数）のみ。`site/` は触らない。

優先順位:

1. 情報階層
2. レイアウト
3. typography
4. spacing
5. card/component structure
6. CTA
7. responsive
8. interaction
9. decorative details

既存機能を壊さない。既存コンポーネント・共通関数を再利用する。同じUIパターンを複数ページで使う場合、重複実装を増やさない（共通CSS/共通関数へ集約）。実装後は `python tools/build.py` で `site/` を再生成して差分を確認する。

## Phase 5 — Baseline Polish

`baseline-ui` Skillが利用可能なら使用する。production qualityまで磨く。

- spacing / typography / alignment
- visual hierarchy
- card consistency
- CTA visibility
- responsive behavior
- interactive states
- mobile density

新しい機能や不要な装飾は追加しない。

## Phase 6 — Accessibility

`fixing-accessibility` Skillが利用可能なら使用する。確認項目:

- semantic HTML
- keyboard navigation / focus states
- labels
- button/link semantics
- aria
- contrast
- touch target（44px目安）
- mobile usability

UI設計を不必要に変更しない。

## Phase 7 — Guidelines QA

`web-design-guidelines` / `/web-interface-guidelines` が利用可能なら使用する。VercelのWeb Interface Guidelines等で監査し、問題を分類する。

- **P0: 致命的** → 必ず修正
- **P1: 修正推奨** → 原則修正
- **P2: 軽微** → 既存デザイン方針・費用対効果・変更リスクを考慮し、無理に修正せず報告のみでもよい

## Phase 8 — Browser Review

Playwright等のブラウザ操作環境が利用可能なら、実際のブラウザで確認する。`site/` をローカル配信して表示し、**desktopとmobileの両方**を確認。スクリーンショットを利用できる場合は必ず視覚確認する。

確認項目:

- first view / visual hierarchy
- CTA / information density
- spacing / typography / card consistency
- overflow / responsive breakage
- mobile usability
- page-to-page consistency
- funnel continuity（TOP→比較一覧→詳細→診断→比較→CTA の導線）

**コードだけを見て「問題なし」と判断しない。**

## Phase 9 — Final Verification

変更後に必ず確認する。

- `python tools/sitegen/validate.py`
- `python tools/build.py`（site/ 再生成、差分が意図通りか）
- console / runtime errors
- responsive errors
- broken links（内部リンク・生成されたURL）
- 意図しない機能変更（価格・キャンペーン・アフィリエイトリンク・データ表示が変わっていないか）

エラーがあれば修正して再確認する。

## Phase 10 — Report

最後に簡潔に報告する。以下だけを出す。

1. 変更内容
2. UX上の改善点
3. QA結果（P0/P1/P2の内訳）
4. 残したP2（理由とともに）
5. build/validate結果
6. 追加で変更すべきでない事項（触らなかった範囲の明示）

---

## 自律判断ルール

依頼の規模に応じてフェーズを取捨する。

| 依頼の規模 | 実行フェーズ |
|---|---|
| 新規ページ / 大規模UI変更 | 全Phase |
| 既存ページの小規模UI修正 | Context Audit → Implement → Baseline → Guidelines → 必要ならBrowser Review |
| CSS / spacing / typographyのみ | Baseline → Browser Review |
| animation追加 | Implementation → motion performance確認 → Browser Review |
| React component refactor（このプロジェクトには無し） | `composition-patterns` → `react-best-practices` → test/build |
| accessibility修正のみ | Accessibility → Guidelines → Browser Review |

## 絶対禁止

- 勝手な新機能追加
- data/model変更（`data/*.json`・`config/*.json`）
- 差別化要素変更・API仕様変更
- アフィリエイトロジック変更（`config/affiliates.json` のリンク等）
- SEO構造の不用意な変更（canonical・robots・sitemap・タイトル構造）
- 既存ページを理由なく全面別デザインにする
- 「モダンにする」だけを目的にした装飾追加
- 全ページ共通化を理由に個別ページの役割を消す
- P2問題を大量修正してscopeを膨らませる
- `site/`・`__pycache__`・build成果物・`node_modules`・巨大JSONを大量に読み込む
- 不要なファイルをコンテキストに投入する
- 問題がない部分まで変更する
- 作業途中で「さらに良くするための新機能」を思いついても勝手に追加しない

## Token / Context最適化

- このSkill自体を簡潔に保つ。
- 毎回リポジトリ全体を読まない。必要なページ・関連component・関連docsだけを読む。
- `site/`・`dist`・`build`・`coverage`・`cache`・`__pycache__`・`data/snapshots/`・生成物・巨大JSONは原則除外（`.gitignore` を確認）。
- 長大な既存docsは毎回全文読まず、必要な箇所だけ `git grep` で検索する。
- Skillに巨大な参考資料を直接埋め込まない。

## 最終原則

目的は「機能を増やすこと」ではなく、**現在のサイトの意思決定ファネルとUI品質を最大化すること**。

- 既存仕様を変更する可能性がある場合、破壊的変更を実行せず、その点だけユーザーに確認する。
- commit / push はユーザーの明示指示があるまで行わない。

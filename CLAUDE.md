# CLAUDE.md — 宅食図鑑 リポジトリ運用メモ（Claude Code用）

本ファイルは運用メモ。ユーザーの明示指示が最優先。

## 最初に読むもの（この順で）
1. README.md（プロジェクト概要）
2. docs/README.md（docsの軽量索引。ファイル名＋分類＋状態）
3. docs/FINAL_REDESIGN_SPEC.md（**現行UIのcanonical spec**。現状把握はこれで足りる）

## データフロー（最重要）
data/*.json + config/*.json（単一情報源）→ tools/sitegen/*.py（描画）→ site/（生成HTML）

## site/ は生成物
- site/ は tools/build.py の出力でGit管理外。**読まない・直接編集しない**。
- サイトの現状確認は data/*.json と tools/sitegen/templates.py を見るか、
  `python tools/build.py` を実行して site/ を再生成する。
- コード・データ検索は `git grep` を優先し、site/ 等の生成物を意図的に掘り込まない。

## docs/ の使い分け
- 現行UI: docs/FINAL_REDESIGN_SPEC.md（canonical）／プロダクト戦略: docs/FINAL_PRODUCT_DESIGN.md／UI原則: docs/UI_DESIGN_PRINCIPLES.md
- デプロイ: docs/DEPLOYMENT_GUIDE_2026_08.md
- 監査・実装計画・QA（docs/README.mdの「監査・計画・QA」節）は、**状態が「完了」のものは通常の現状把握で読まない**。必要時のみ索引の状態列（完了/未実施/見送り/進行中）で該当docを読む。HISTORYは原則読まない。

## 変更フロー（1変更につきdocは原則2本まで）
1. 現状spec（FINAL_REDESIGN_SPEC）を確認 → 2. 必要な調査のみ（索引で該当AUDITへ） → 3. 実装 → 4. 実機検証（build + validate + Playwright PC/モバイル） → 5. **spec更新（同一セッション内）**
- 監査または計画1本＋QA1本の最大2本に留め、監査→計画→QAの連鎖docを作らない。
- **実装完了時はFINAL_REDESIGN_SPEC.mdを同一セッションで最新化し、docs/README.mdの状態を「完了(commit)」に更新する。**

## 変更時のルール（探索とは分離）
- data/schema（data/*.json, config/*.json）は**勝手に変更しない**。変更は事前確認。
- production（サイト表示・デプロイ）に影響する変更は、まず現行仕様を確認してから実施。
- 変更後は `python tools/sitegen/validate.py`（または build 時の検証）を通し、
  `python tools/build.py` で site/ を再生成して差分を確認する。
- site/ を再trackしない・`.gitignore`を壊さない。
- commit / push はユーザーの明示指示があるまで行わない。

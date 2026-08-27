# CLAUDE.md — 宅食図鑑 リポジトリ運用メモ（Claude Code用）

本ファイルは運用メモ。ユーザーの明示指示が最優先。

## 最初に読むもの
1. README.md（プロジェクト概要）
2. docs/README.md（docsの索引。どこに何があるか）

## データフロー（最重要）
data/*.json + config/*.json（単一情報源）→ tools/sitegen/*.py（描画）→ site/（生成HTML）

## site/ は生成物
- site/ は tools/build.py の出力でGit管理外。**読まない・直接編集しない**。
- サイトの現状確認は data/*.json と tools/sitegen/templates.py を見るか、
  `python tools/build.py` を実行して site/ を再生成する。

## docs/ の使い分け
- 現行仕様: docs/FINAL_PRODUCT_DESIGN.md, docs/FINAL_REDESIGN_SPEC.md
- デプロイ: docs/DEPLOYMENT_GUIDE_2026_08.md
- docs/README.md の HISTORY（過去資料）・AUDIT（監査）は**参照が必要な時のみ**読む。
  デフォルトで全docsを横断しない。

## 変更時のルール（探索とは分離）
- data/schema（data/*.json, config/*.json）は**勝手に変更しない**。変更は事前確認。
- production（サイト表示・デプロイ）に影響する変更は、まず現行仕様を確認してから実施。
- 変更後は `python tools/sitegen/validate.py`（または build 時の検証）を通し、
  `python tools/build.py` で site/ を再生成して差分を確認する。
- commit / push はユーザーの明示指示があるまで行わない。

# Phase 2 設計書: Claude Code context最適化（CLAUDE.md / docs/README.md 設計案）

- 作成日: 2026-08-27
- 作成者: Claude Code（**READ ONLY 設計・監査**）
- 前提: Phase 1（site/生成物のGit追跡解除 + .gitignore追加）は commit `7f0bebe` で確定済み
- 本設計書の位置づけ: CLAUDE.md / docs/README.md を**実際に作成する前の設計案**。今回の実行範囲は本ファイルの作成まで

---

## 1. 現在のcontext流入構造

### 1.1 全体メトリクス（Phase 1適用後）

| 対象 | ファイル数 | サイズ/文字量 | Claude Codeへの影響 |
|---|---|---|---|
| Git tracked全体 | 43 | 778,288 B | repo map対象 |
| docs/ | 23 | 533,925文字 | **最大のテキスト塊**（HISTORYが大半） |
| data/ | 5 | ~87K文字 | 現状の正体（単一情報源） |
| tools/ | 6 | ~142K文字 | 生成・検証ロジック |
| config/ | 4 | ~8K文字 | アフィリエイト・監視設定 |
| README.md | 1 | 2.4KB | **起動時コンテキスト（唯一の常時読込）** |
| site/ | 28（on disk） | 736K文字 | **Phase 1で探索対象外化済み**（ignored・tracked外） |

### 1.2 現状のフロー

```
起動時: README.md（2.4KB）のみ自動読込。CLAUDE.md なし。
       ↓
探索時: repo map = 43ファイル。
       docs/ 23本（533K文字）に「現行仕様」「過去資料」「監査」が混在し、区別の索引がない
       → Claude Codeが docs を横断しやすい（22本中どれが現行か判別できない）
       ↓
data/config/tools は小さいため問題は小さいが、
「site/を見れば現状が分かる」時代（Phase 1前）から、
「data/*.jsonを見るべき」へ誘導する仕組みがない
```

### 1.3 問題の本質

- **「どこが現行か」の索引が存在しない**。Claude CodeはREADMEに書かれた一部docsと、探索で見つけたdocsを区別なく読み得る
- **site/（生成物）への誤探索を防ぐ明示的指示がない**（Phase 1でrepo mapからは消えたが、ユーザーが「サイトを見て」と言った時にHTMLを読む行動は残り得る）
- **過去資料を読むことが禁止されているわけではないが、優先順位が不明**

---

## 2. 現在のdocs分類（23本）

| 分類 | ファイル | 判断理由 |
|---|---|---|
| **CURRENT（現行状態・実装記録）** | `REDESIGN_IMPLEMENTATION_REPORT.md`, `PHASE4_IMPLEMENTATION_REPORT.md` | 実装済み内容の記録。現状のUI・機能を知る手掛かり |
| **SPEC（現行仕様）** | `FINAL_PRODUCT_DESIGN.md`, `FINAL_REDESIGN_SPEC.md`, `DEPLOYMENT_GUIDE_2026_08.md` | 現在の設計・運用仕様。**変更前に必ず参照すべき正本** |
| **GOVERNANCE（決定・ルール）** | `SITE_NAME_DOMAIN_DECISION_2026_08.md`, `PHASE4_FINAL_DECISION.md`, `DELIVERY_FOOD_AFFILIATE_NEXT_ACTION_2026_08.md` | サイト名・実装判断・収益計測設計・ロードマップ決定 |
| **AUDIT（監査・検証記録 / 参照時のみ）** | `DATA_VERIFICATION_AUDIT_20260827.md`, `REMAINING_8_ITEMS_AUDIT_20260827.md`, `REPOSITORY_CONTEXT_TOKEN_AUDIT.md` | governance上保持。特定監査の時のみ読む |
| **HISTORY（過去資料 / 原則読まない）** | `AFFILIATE_MARKET_ENTRY_RESEARCH_2026_08.md`, `AFFILIATE_MARKET_ENTRY_SHORTLIST_2026_08.md`, `SEO_FLOW_RESEARCH_2026_08.md`, `SEO_CONTENT_FINAL_KW_SERP_AUDIT_2026_08_26.md`, `SITE_UX_INTEREST_AUDIT_2026_08_26.md`, `PHASE1_IMPLEMENTATION_PLAN.md`, `PHASE2_IMPLEMENTATION_PLAN.md`, `PHASE3_IMPLEMENTATION_PLAN.md`, `PHASE3_COMPETITIVE_REAUDIT.md`, `PHASE4_COMPETITIVE_REAUDIT.md`, `REDESIGN_UI_SPEC.md`, `REDESIGN_COMPETITIVE_AUDIT.md` | 調査・計画・時点監査。FINAL系仕様・実装により置換/完了 |

**分類上の注意**
- `REDESIGN_UI_SPEC.md` は `FINAL_REDESIGN_SPEC.md` に統合された旧設計書 → HISTORY
- `REDESIGN_COMPETITIVE_AUDIT.md` は `FINAL_REDESIGN_SPEC.md` の基準文書だが、判断結果はFINAL側に反映 → HISTORY
- `SITE_UX_INTEREST_AUDIT` はリデザイン前の旧サイト監査 → 改善は実装済みのため HISTORY
- PHASE系（計画・時点監査）はすべて完了済み → HISTORY（将来「経緯を確認したい時」のみ参照）

---

## 3. Claude Codeの推奨読み順

```
1. README.md                        … プロジェクト概要（起動時に自動読込）
2. CLAUDE.md                        … 探索・変更ルール（Phase 2で新設、15〜30行）
3. docs/README.md                   … docsの索引（どこに何があるか）
4. docs/FINAL_PRODUCT_DESIGN.md     … 現行プロダクト設計（仕様の正本①）
   docs/FINAL_REDESIGN_SPEC.md      … 現行UI/UX設計（仕様の正本②）
5. data/*.json + config/*.json      … 現在の実データ（真の現状）
   tools/sitegen/*.py               … 生成ロジック（必要時）
6. docs/DEPLOYMENT_GUIDE_2026_08.md … デプロイ手順（必要時）
7. docs/README.md のAUDIT/HISTORY   … 特定目的がある時のみ参照
```

**「現在どうなっているか」は docs を横断せずとも、手順4・5で到達できる。**

---

## 4. CLAUDE.md 設計案

### 4.1 設計方針

- **15〜30行**に収める（常時contextに入るため、肥大化は逆効果）
- **探索ルールと変更ルールを分離**する
- 「tools/*は変更禁止」のような硬い禁止は**採用しない**。代わりに「data/schemaを勝手に変更しない」「production影響ある変更は事前確認」「現行仕様を確認してから変更」の3原則
- 詳細はdocs側へ逃がす（CLAUDE.mdには「どこを読めば分かるか」だけ書く）

### 4.2 記載項目

1. **最初に読むファイル**: README.md / CLAUDE.md / docs/README.md
2. **site/は生成物**: 読まない・直接編集しない・build.pyで再生成する
3. **data/のSingle Source of Truth**: 現状はdata/*.json + config/*.json が正体
4. **現行仕様の参照先**: FINAL_PRODUCT_DESIGN.md / FINAL_REDESIGN_SPEC.md
5. **過去docsを全探索しない**: docs/README.md の分類を尊重（HISTORYは必要時のみ）
6. **変更時の確認領域**: data/schemaは勝手に変更しない、production影響は事前確認、現行仕様を確認してから変更
7. **build/validationの標準手順**: validate.py → build.py
8. **重要禁止事項**: commit/pushは明示指示があるまで行わない

### 4.3 完成案（後述の付録A）

---

## 5. docs/README.md 設計案

### 5.1 設計方針

- **1ファイルでdocs全体の地図**を提供し、22本の横断を不要にする
- 分類: **CURRENT / SPEC / GOVERNANCE / AUDIT / HISTORY**（各1行要約）
- 「この分類はどこから来たか」を先頭に明記し、Claude Codeが誤ってHISTORYを正本扱いしないようにする
- docsを追加したら索引も更新する（運用ルールを文末に1行記載）

### 5.2 記載項目

1. 冒頭: 「現状を知るにはCURRENT/SPECだけ読めばよい。HISTORYは原則読まない」
2. 分類テーブル: 5分類 × 各ファイル + 1行要約
3. 運用注記: 新規docs追加時は分類と索引を更新すること

### 5.3 完成案（後述の付録B）

---

## 6. 現行仕様・現在状態のcanonical source

| 種類 | canonical source | 備考 |
|---|---|---|
| 現行プロダクト仕様 | `docs/FINAL_PRODUCT_DESIGN.md` | Phase2改訂版が最新 |
| 現行UI/UX仕様 | `docs/FINAL_REDESIGN_SPEC.md` | REDESIGN_UI_SPECの後継 |
| デプロイ手順 | `docs/DEPLOYMENT_GUIDE_2026_08.md` | Workers方式 |
| **現在のデータ（真の現状）** | `data/*.json`（services/campaigns/menus/shipping/sources） | 単一情報源 |
| アフィリエイト・監視設定 | `config/*.json`（affiliates/comparisons/site/watchlist） | 実設定 |
| 生成ロジック | `tools/sitegen/*.py` + `tools/build.py` | 表示の実体はここ |
| **現状のサイト表示** | （生成物 site/ は canonical ではない） | 確認時は build.py を実行 or data+template を読む |

**重要**: 「サイトを見れば現状が分かる」ではなく「data/*.json + templates.py を見れば現状が分かる」へ誘導する。

---

## 7. 過去docsの扱い

- **削除・移動・改名は今回しない**（Phase 2では禁止。将来の任意項目）
- 分類上はHISTORY（12本）とAUDIT（3本）として `docs/README.md` に明記し、「参照が必要な時のみ読む」対象にする
- 将来の任意改善（Phase 3候補）: `docs/history/` サブディレクトリへ物理移動 → Claude Codeの探索粒度をさらに下げる。ただし**現時点では実施しない**
- governance上、監査記録（AUDIT）は削除せず保持

---

## 8. 探索禁止 / 優先対象

### 8.1 優先対象（読みに行くべき）

| 対象 | 理由 |
|---|---|
| README.md / CLAUDE.md / docs/README.md | 入口・索引 |
| data/*.json / config/*.json | 現在の正体 |
| docs/FINAL_PRODUCT_DESIGN.md / FINAL_REDESIGN_SPEC.md | 現行仕様 |
| tools/sitegen/*.py | 生成ロジック（変更・調査時） |

### 8.2 デフォルトで読まない対象

| 対象 | 理由 |
|---|---|
| site/（生成物・Git管理外） | Phase 1で除外済み。読まずにdata+templateを見る |
| __pycache__ / *.pyc | バイナリキャッシュ |
| docs/HISTORY（12本） | 置換・完了済みの過去資料 |
| docs/AUDIT（3本） | 監査目的の時のみ |

### 8.3 変更時のルール（探索とは分離）

- data/schema（data/*.json, config/*.json）: **勝手に変更しない。変更は事前確認**
- tools/*: 変更自体は可能だが、現行仕様を確認し、validate.py→build.py で検証する
- production / サイト表示への影響: 事前に現行仕様（FINAL系）を確認してから実施

---

## 9. token/context削減効果

| 提案 | 優先度 | 分類 | 効果の見積もり |
|---|---|---|---|
| CLAUDE.md新設（15〜30行） | [HIGH] | **A**（直接効く） | 常時+0.5〜1K tokenの固定コスト。探索時のdocs横断・site/誤読を防ぐ効果が上回る |
| docs/README.md（索引） | [HIGH] | **A**（直接効く） | 読込時+1〜1.5K token。22本横断（数十万文字）を防止 |
| site/除外（Phase 1済み） | [HIGH] | **A**（直接効く） | 探索対象から736K文字を除去済み |
| HISTORY docsを読まない誘導 | [MEDIUM] | A（直接効く） | セッション毎に数万〜十数万tokenの節約（過去資料12本 約250KB相当） |
| AUDIT docsは参照時のみ | [MEDIUM] | A（直接効く） | 監査記録3本の誤読を防止 |
| README.md に docs/README.md へのリンク追加 | [MEDIUM] | B（探索効率） | 起動時の行き先が明確になる |
| 将来: docs/history/ への物理移動 | [LOW] | B（探索効率） | repo map上の粒度が下がる。**今回は実施しない** |
| CLAUDE.md肥大化（逆効果） | — | C（ほぼ無効/悪影響） | 長大なCLAUDE.mdは常時contextを圧迫。**回避** |

---

## 10. リスク

| リスク | 深刻度 | 対策 |
|---|---|---|
| CLAUDE.mdが古くなる・長大化 | 中 | 15〜30行に固定。詳細はdocs側へ。更新時はdiffを小さく |
| docs/README.mdの分類が古くなる | 中 | 「docs追加時は索引更新」を運用注記として明記 |
| 「読まない」指定で必要なHISTORYを見落とす | 低 | 「原則読まない・必要時のみ参照」とし、参照経路を残す |
| 変更ルールの硬直化で将来の実装変更を妨げる | 中 | 絶対禁止表現を避け「事前確認」「現行仕様を確認してから」で運用 |
| CLAUDE.mdがユーザー指示と競合する | 低 | CLAUDE.mdは「運用メモ」であり、ユーザー明示指示が最優先と明記 |
| 恒常的なcontext追加コスト | 低 | 固定+0.5〜1K tokenに対し、削減効果が数万token規模で上回る |

---

## 11. Phase 2実装手順（承認後）

> 本設計書では**実施しない**。承認後の手順は以下。

1. `CLAUDE.md` を新規作成（付録A・15〜30行）
2. `docs/README.md` を新規作成（付録B）
3. `README.md` の「ドキュメント」節に `docs/README.md` への案内を追記（任意・変更可否は要確認）
4. 確認: `git status` で追加2〜3ファイルのみ
5. commit / push（明示指示がある場合のみ）

---

## 12. 最小変更案

「これだけ実施すれば十分」の最小セット:

1. **[HIGH] `CLAUDE.md` 新設**（付録A・15〜30行）: 読み順・site/除外・canonical source・変更3原則
2. **[HIGH] `docs/README.md` 新設**（付録B）: CURRENT/SPEC/GOVERNANCE/AUDIT/HISTORY 分類 + 1行要約
3. **[MEDIUM] README.md の「ドキュメント」節へ docs/README.md への1行案内**（任意）

※ 上記のみで、docs横断・site誤読・過去資料の誤読がほぼ解消される。物理移動（docs/history/）は不要。

---

## 付録A: CLAUDE.md 完成案（今回の作成対象外・提案のみ）

```markdown
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
```

**行数: 24行**（15〜30行の範囲内）

---

## 付録B: docs/README.md 完成案（今回の作成対象外・提案のみ）

```markdown
# docs/ インデックス

docs/ は「現行仕様」「実装記録」「監査記録」「過去資料」に分類される。
**現状を知るには CURRENT と SPEC を読めばよい。HISTORY は原則読まない。**

## CURRENT（現行状態・実装記録）
| ファイル | 内容 |
|---|---|
| `REDESIGN_IMPLEMENTATION_REPORT.md` | 全面リデザイン実装報告（現行UI） |
| `PHASE4_IMPLEMENTATION_REPORT.md` | Phase4実装報告（GO判定3項目） |

## SPEC（現行仕様）
| ファイル | 内容 |
|---|---|
| `FINAL_PRODUCT_DESIGN.md` | 最終プロダクト設計（Phase2改訂版） |
| `FINAL_REDESIGN_SPEC.md` | 全面リデザイン最終設計書 |
| `DEPLOYMENT_GUIDE_2026_08.md` | デプロイ手順（Workers方式） |

## GOVERNANCE（決定・ルール）
| ファイル | 内容 |
|---|---|
| `SITE_NAME_DOMAIN_DECISION_2026_08.md` | サイト名・ドメイン決定 |
| `PHASE4_FINAL_DECISION.md` | Phase4最終実装判断・収益計測設計 |
| `DELIVERY_FOOD_AFFILIATE_NEXT_ACTION_2026_08.md` | 次の一手・ロードマップ |

## AUDIT（監査・検証記録 / 参照時のみ）
| ファイル | 内容 |
|---|---|
| `DATA_VERIFICATION_AUDIT_20260827.md` | 確認率改善の監査記録 |
| `REMAINING_8_ITEMS_AUDIT_20260827.md` | 残り8項目の確認可能性監査 |
| `REPOSITORY_CONTEXT_TOKEN_AUDIT.md` | context/token使用量監査 |

## HISTORY（過去資料 / 原則読まない）
- `AFFILIATE_MARKET_ENTRY_RESEARCH_2026_08.md` / `AFFILIATE_MARKET_ENTRY_SHORTLIST_2026_08.md` … 市場調査・ショートリスト
- `SEO_FLOW_RESEARCH_2026_08.md` / `SEO_CONTENT_FINAL_KW_SERP_AUDIT_2026_08_26.md` … SEO調査・記事選定
- `SITE_UX_INTEREST_AUDIT_2026_08_26.md` … リデザイン前のUX監査（改善済み）
- `PHASE1_IMPLEMENTATION_PLAN.md` / `PHASE2_IMPLEMENTATION_PLAN.md` / `PHASE3_IMPLEMENTATION_PLAN.md` … 実装計画（完了）
- `PHASE3_COMPETITIVE_REAUDIT.md` / `PHASE4_COMPETITIVE_REAUDIT.md` … 時点競合監査（完了）
- `REDESIGN_UI_SPEC.md` … UI設計（FINAL_REDESIGN_SPECに統合）
- `REDESIGN_COMPETITIVE_AUDIT.md` … 競合調査（FINAL_REDESIGN_SPECの基準文書）

## 運用注記
- 新規docsを追加したら、本ファイルに分類と1行要約を追加する。
- HISTORY/AUDIT は削除せず保持する（governance）。
```

---

## 最終判断

- **Phase 2の最小実施セットは「CLAUDE.md（24行）+ docs/README.md（索引）」の2ファイル**。これでdocs 22本の横断・site/誤読・HISTORY誤読を防げる。
- 物理移動（docs/history/）・README.md改修は**任意・将来判断**（今回は見送り）。
- 本設計書の作成をもってPhase 2設計は完了。**CLAUDE.md / docs/README.md はまだ作成していない**。

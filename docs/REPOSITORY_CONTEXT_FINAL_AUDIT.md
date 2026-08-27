# Repository Context 最適化 最終監査（Phase 4）

- 作成日: 2026-08-27
- 作成者: Claude Code（**READ ONLY 最終監査**）
- 位置づけ: Phase 1〜3完了後の「これ以上Repositoryを変更する価値があるのか」の最終判断
- 実施範囲: 監査と判定のみ。**本監査では一切の変更を行わない**

---

## 1. Phase 1〜3の実施結果

| Phase | commit | 実施内容 | 結果 |
|---|---|---|---|
| **1** | `7f0bebe` | site/生成物28ファイルのGit追跡解除 + .gitignore追加 | 探索対象から736,714文字を除外。build同一性をblobハッシュで確認 |
| **2** | `4f299d6` | CLAUDE.md（探索誘導・28行）、docs/README.md（5分類索引）、Phase2設計書 | docs横断の防止・読み順の最短化 |
| **3** | `3065289` | README→docs/README.md誘導、CLAUDE.md+git grep運用1行、索引更新、Phase3監査書 | 起動経路の仕上げ・grep運用の明文化 |

すべて**機能・data・schema・生成ロジックに無変更**で完了。push済み・作業ツリーclean。

---

## 2. 現在のRepository baseline

| 対象 | 値 |
|---|---|
| Git tracked | **47ファイル / 813,136 B** |
| docs/ | 26ファイル（5分類索引済み） |
| data/ | 5ファイル / 87,922 B（単一情報源） |
| tools/ | 6ファイル / 141,902 B（templates.py 111KB） |
| config/ | 4ファイル / 8,176 B |
| CLAUDE.md | 29行（探索誘導・git grep運用） |
| docs/README.md | 46行（5分類索引） |
| site/ | 28ファイル on disk・**tracked 0**・ignored |
| __pycache__ | 6ファイル 184KB on disk（ignore済み） |
| .git | 4.4MB / 32 commits |

---

## 3. 現在のcontext/token主要消費源

| 順位 | 対象 | 文字量 | 現状の制御 |
|---|---|---|---|
| 1 | **docs/HISTORY 12本** | 341,241（docsの64%） | docs/README.mdで「原則読まない」 |
| 2 | **site/ on disk 28本** | 736,714 | repo map/内蔵検索から除外済み（raw grepは残る） |
| 3 | **templates.py** | 111KB | 必要コード（読む価値あり） |
| 4 | docs/CURRENT+SPEC+GOVERNANCE 8本 | 141,334 | 必要（現行仕様・決定） |
| 5 | data/services.json | 56,726 | 必要（単一情報源） |
| 6 | __pycache__ | 184KB | ignore済み・探索対象外 |

---

## 4. Phase 1〜3による削減効果

| 指標 | Phase 1前 | 現在 | 削減 |
|---|---|---|---|
| Git tracked ファイル数 | 70 | 47 | -23（正味。site/-28 ＋ 新規docs/+5） |
| Git tracked サイズ | 1,486,583 B | 813,136 B | **-673,447 B（-45%）** |
| 探索対象のsite/文字量 | 736,714 | **0** | **-736,714文字（≈30〜45万token上限）** |
| docs探索方法 | 22本を区別なく横断 | 索引（5分類）で最短到達 | HISTORY誤読を防止 |

- 実測可能な効果は「tracked -45%」「site/の探索対象除外」。実際のtoken節約はセッション依存で数万〜十数万token規模と推定。
- 副作用（機能・data・生成ロジックへの影響）は**ゼロ**。

---

## 5. 残存する問題

| 問題 | 深刻度 | 備考 |
|---|---|---|
| HISTORY 12本がrepo内に残存（tracked） | 低 | 索引で「必要時のみ」に制御。視認ノイズのみ |
| raw grep時のsite/ヒット | 低 | CLAUDE.mdにgit grep優先を明記済み。内蔵検索は除外済み |
| templates.py 111KB | 低 | 必要コード。分割は機能リスク |
| 新規docs追加時の索引更新漏れリスク | 低 | docs/README.mdの運用注記で対応 |

**「大きなcontext削減が得られる未対応問題」は存在しない。**

---

## 6. 追加対策候補

| ID | 候補 | 内容 |
|---|---|---|
| A | docs/history/ への物理移動 | HISTORY 12本をサブディレクトリ化 |
| B | HISTORY 12本のuntrack+ignore | `git rm --cached` + .gitignore |
| C | 巨大HISTORY docsの要約化 | 過去資料の書き換え・圧縮 |
| D | templates.py 分割 | 生成ロジックの再構成 |
| E | __pycache__ 定期削除 | 運用上の掃除 |
| F | 新規.gitignore追加 | site/・cache系以外のignore追加 |

---

## 7. 各対策の費用対効果

| ID | 期待context効果 | コスト/リスク | 費用対効果 |
|---|---|---|---|
| A | **ほぼなし**（trackedのままならrepo mapサイズ不変。`ls docs/`の見た目のみ改善） | docs移動（governance影響・今回禁止） | **悪い** |
| B | 中（341K文字を探索対象から除外） | **governance違反リスク大**（監査・調査の履歴消失）。tracked履歴を失う | **悪い**（リスク過大） |
| C | 中〜大 | **過去資料の書き換え**・governance違反 | **悪い** |
| D | 小（読む必要は変わらない） | 生成ロジック変更・機能リスク大 | **悪い** |
| E | ほぼなし | 低（だが効果もほぼゼロ） | 中立 |
| F | ほぼなし（対応対象が残っていない） | 低 | 不要 |

---

## 8. HIGH/MEDIUM/LOW/NO-GO 判定

| 対策 | 判定 | 理由 |
|---|---|---|
| A: docs/history/移動 | **LOW** | 効果が「視認改善のみ」。governanceと要相談。実施する価値は限定的 |
| B: HISTORY untrack | **NO-GO** | 監査・調査の履歴消失リスク。token削減目的では許容できない |
| C: docs要約化 | **NO-GO** | 過去資料の書き換え。governance違反 |
| D: templates.py分割 | **NO-GO** | 機能・生成ロジック変更 |
| E: pycache掃除 | LOW | 効果ほぼゼロ・任意 |
| F: .gitignore追加 | **不要** | 対応対象が残っていない |

**HIGH/MEDIUM判定の追加対策は存在しない**（Phase 1〜3で完了済み）。

---

## 9. 最終推奨Repository構成

現在の構成が**最終形**として適切。

```
CLAUDE.md          … 探索誘導（29行・維持）
README.md          … 概要＋docs/README.mdへの誘導
docs/README.md     … 5分類索引（CURRENT/SPEC/GOVERNANCE/AUDIT/HISTORY）
docs/FINAL_*.md    … 現行仕様（canonical）
data/ config/ tools/ … 単一情報源・生成ロジック（変更禁止）
site/              … 生成物（Git管理外・build.pyで再生成）
```

推奨する変更: **なし**（現状維持）。

---

## 10. 今後の運用ルール

1. docsを探すときは**docs/README.md**を最初に見る（HISTORYは必要時のみ）
2. 検索は**`git grep`優先**（site/生成物を掘らない）
3. **data/*.json を価格等の正本**とし、site/生成HTMLを直接読まない
4. 新規docsを追加したら**docs/README.mdの索引に分類と1行要約を追加**
5. CLAUDE.mdは**30行以内**に維持（肥大化させない）
6. **site/を再trackしない**・`.gitignore`を壊さない
7. 現行仕様を確認してから変更（data/schemaは事前確認・production影響は要相談）
8. commit/pushは明示指示があるまで行わない

---

## 11. 「これ以上変更しない」項目

- `data/*.json` / `config/*.json`（pricing schema・affiliate含む）
- `tools/*`（templates.py含む生成・検証・監視ロジック）
- `site/` 生成ロジック・UI・schema
- **site/ のGit追跡状態**（tracked 0 を維持・再trackしない）
- `.gitignore`（現在の状態が最適）
- 既存docsの内容（HISTORY/AUDIT含む・書き換えない）
- CLAUDE.md・docs/README.md（編集は索引更新と30行内維持のみ）
- docsの物理移動・削除・改名・untrack

---

## 12. Repository Context最適化の最終判定

### 判定: **最適化は完了（これ以上のRepository変更は不要）**

- Phase 1〜3で、**探索対象の-45%（trackedサイズ）・site/ 736K文字の除外・docs索引化・探索誘導**を、機能・data・schema・生成ロジックに一切影響させずに達成した。
- 残る追加対策（A〜F）はすべて**LOW以下 or NO-GO**。特に「数%の削減のためにgovernanceや機能を犠牲にする」案はない。
- **「token削減を理由にRepositoryを変更する」段階は終了**。今後の価値は変更ではなく、**運用ルール（10章）の遵守**と、**新規docs追加時の索引更新**の継続にある。
- 本監査をもって Phase 1〜4 のContext最適化シリーズを完了とする。

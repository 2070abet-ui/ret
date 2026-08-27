# Phase 3 監査レポート: Repository Context / Token 最適化（追加監査）

- 作成日: 2026-08-27
- 作成者: Claude Code（**READ ONLY監査**）
- 前提: Phase 1（site/追跡解除+.gitignore）commit `7f0bebe` / Phase 2（CLAUDE.md+docs/README.md）commit `4f299d6` 済み
- 実施範囲: 監査と推奨案のみ。**本監査では一切の変更・削除・移動を行っていない**

---

## 1. 現状baseline（Phase 2完了時点）

| 対象 | ファイル数 | サイズ | 備考 |
|---|---|---|---|
| Git tracked 全体 | 46 | 799,900 B | |
| docs/ | 25 | ~534K文字 | 内HISTORY 12本=341K文字（64%） |
| data/ | 5 | 87,922 B | 単一情報源 |
| tools/（ソース） | 6 | 141,902 B | templates.py が111KB |
| config/ | 4 | 8,176 B | |
| CLAUDE.md | 1 | 28行 | 探索誘導（Phase 2） |
| docs/README.md | 1 | 44行 | 5分類索引（Phase 2） |
| site/（on disk） | 28 | 736,714 B | **repo map / 内蔵検索から除外済み** |
| __pycache__（on disk） | 6 | 184KB | ignore済み・tracked外 |
| .git 履歴 | 31 commits | 4.3MB | contextに無関係 |

---

## 2. token/context消費要因ランキング（Phase 3時点）

| 順位 | 要因 | 影響 | 分類 | 現状の緩和策 |
|---|---|---|---|---|
| 1 | **docs/HISTORY 12本（341K文字）** | 大 | A（読込・grep汚染） | docs/README.md索引＋CLAUDE.md「必要時のみ」 |
| 2 | **site/ HTML on disk（736K文字・28本）** | 中 | A（raw grep汚染） | repo map/内蔵検索からは除外済み。**raw grepは残る** |
| 3 | **templates.py（111KB・2,080行）** | 中 | B（必要コード） | 読む価値はある。分割はNO-GO |
| 4 | docs/CURRENT+SPEC+GOVERNANCE（141K文字） | 中 | B（必要） | 削減余地は小さい |
| 5 | data/services.json（56KB） | 低 | C（必要） | 単一情報源。変更禁止 |
| 6 | __pycache__（184KB） | 低 | C | ignore済み |
| 7 | .git履歴（4.3MB） | なし | C | contextに無関係 |

**結論**: Phase 1・2で**主要なcontext削減は達成済み**。追加で「大きな効果×安全」の対策はほぼ残っていない。

---

## 3. 巨大ファイル分析

| ファイル | サイズ | 種類 | 読む価値 | 判定 |
|---|---|---|---|---|
| tools/sitegen/templates.py | 111,975 B | Python | 高い（描画ロジックの実体） | **必要・変更禁止** |
| data/services.json | 56,726 B | JSON | 高い（価格等の正本） | **必要・変更禁止** |
| docs/AFFILIATE_MARKET_ENTRY_RESEARCH | 55,916 B | HISTORY | 低（市場調査・過去） | 索引で「原則読まない」 |
| docs/REDESIGN_UI_SPEC.md | 51,500 B | HISTORY | 低（FINAL_REDESIGN_SPECに統合） | 同上 |
| docs/SITE_UX_INTEREST_AUDIT | 36,061 B | HISTORY | 低（改善済み監査） | 同上 |
| docs/FINAL_PRODUCT_DESIGN.md | 33,242 B | **SPEC** | 高い（現行仕様） | **必要** |
| docs/REDESIGN_COMPETITIVE_AUDIT | 31,197 B | HISTORY | 低 | 索引で制御 |
| docs/PHASE1_IMPLEMENTATION_PLAN | 30,362 B | HISTORY | 低（完了） | 同上 |

- templates.py内訳: `_CSS`デザインシステムブロック（約330行）+ 各ページビルダー。**機能の塊なので分割はNO-GO**
- 巨大ファイルの大半はHISTORY docs → 索引＋読まない誘導で対処済み

---

## 4. 重複情報分析

| 重複の組 | 状況 | 判定 |
|---|---|---|
| data/*.json ⇔ templates.py | 価格・送料・キャンペーンは**dataが正本**、templatesは描画に使用 | **正常な依存関係**（重複ではない） |
| data/*.json ⇔ docs（HISTORY/AUDIT） | 過去の価格・確認状態がdocsに残存（例: DATA_VERIFICATION_AUDITにconfirmed 20件） | governance記録。**変更しない**。索引で「監査」と明示済み |
| site/ ⇔ data/*.json | site/はdataの完全展開 | **Phase 1で除外済み** |
| docs ⇔ docs | REDESIGN_UI_SPECがFINAL_REDESIGN_SPECに統合される等の重複 | HISTORY扱いで制御済み |

**結論**: 実質の重複は「docsの履歴情報」と「site/生成物」のみ。site/は除外済み、docsは索引で制御。**追加対応不要**。

---

## 5. docs分析

- **分類の妥当性**: Phase 2のCURRENT(2) / SPEC(3) / GOVERNANCE(3) / AUDIT(3) / HISTORY(12) は適切。
- **残余課題**:
  1. `docs/REPOSITORY_CONTEXT_PHASE2_PLAN.md`（実装済み設計書）と今回の`REPOSITORY_CONTEXT_PHASE3_AUDIT.md`が**docs/README.md索引に未登録**（索引の運用注記「新規docsは追加時索引更新」に従いPhase 4で追記推奨）
  2. `README.md` が **docs/README.md をまだ参照していない**（起動時: README→docs/README.md への導線が欠けている）
  3. HISTORYが同一ディレクトリ（docs/）に12本あり、`ls docs/`で見える。索引で探索は防げるが、**視認上のノイズ**は残る
- **巨大docsがcontextを圧迫する構造**: HISTORY/AUDITはCLAUDE.mdで「必要時のみ」と明示済み。追加で読ませない仕組みは不要

---

## 6. Git分析

| 項目 | 値 | 判定 |
|---|---|---|
| tracked ファイル数 | 46 | 正常 |
| tracked 総サイズ | 799,900 B | site/除外後は正常 |
| 最大tracked | templates.py 111KB | 必要コード |
| 不要なtracked生成物 | **なし** | site/・pyc・snapshot・log は全て除外/ignore済み |
| .gitignore対応済み | pyc, snapshot, log, site/生成物 | ほぼ完了 |
| Git履歴（4.3MB・31 commits） | contextに**実害なし** | 対応不要 |
| .gitignoreで対応可能な残り | なし（site/・cache系は対応済み） | — |

**結論**: Git側の対応余地はほぼ残っていない。「docs/HISTORYの物理移動＋ignore化」は**governance（tracked履歴保持）とのトレードオフ**があり、context効果も限定的（後述）→ Phase 4判断

---

## 7. grep/search汚染分析

検証（キーワード「価格」）:

| 検索方法 | ヒット数 | 内訳 |
|---|---|---|
| `git grep`（trackedのみ） | 31 files | data/config/docs（HISTORY docsも多数ヒット） |
| `grep -r`（on disk・ignore非考慮） | 55 files | **うち site/ HTML = 24 files** |

分析:
- **site/ HTML**: Claude Codeの**内蔵検索は.gitignoreを尊重**するため、通常の探索ではヒットしない。ただし**Bashの `grep -r` ではヒットし続ける**（site/はディスクに残存しているため）
- **HISTORY docs**: `git grep`でもdataと同様にヒットする。索引・CLAUDE.mdで「読まない」誘導は効くが、**検索ヒット自体は防げない**
- 対策（運用）: grepは `git grep` を基本にする、または `grep -r --exclude-dir=site` を使う。→ **CLAUDE.mdに1行追記が効果的だが、CLAUDE.md変更はPhase 3禁止のためPhase 4提案**

**結論**: 残る汚染は「raw grep時のsite/ヒット」と「HISTORY docsのキーワードヒット」。実害は限定的（内蔵検索は除外済み）。運用ガイダンス追加で対処可能。

---

## 8. Claude Code探索経路分析

```
起動時: README.md（自動読込）→ CLAUDE.md（探索誘導）→ docs/README.md（索引）
   ↓
目的別到達:
  現行仕様   → docs/FINAL_PRODUCT_DESIGN.md, docs/FINAL_REDESIGN_SPEC.md
  現状データ → data/*.json, config/*.json
  生成ロジック→ tools/sitegen/*.py
  デプロイ   → docs/DEPLOYMENT_GUIDE_2026_08.md
  監査/履歴  → docs/README.mdのAUDIT/HISTORY（必要時のみ）
```

- **改善済みの点**: site/除外、docs索引、HISTORY「必要時のみ」、変更3原則
- **残る経路上の課題**:
  1. README.mdがdocs/README.mdを指していない（起動時の入口が1段飛び）
  2. `ls docs/` でHISTORY 12本が並ぶ（視認ノイズ）
  3. raw grep時のsite/ヒット（運用ガイダンス未記載）

---

## 9. 対策候補

| ID | 候補 | 内容 |
|---|---|---|
| C1 | README.mdにdocs/README.md参照を追加 | 「ドキュメント」節を更新し、5分類索引へ誘導 |
| C2 | CLAUDE.mdにgrep運用1行追加 | 「検索はgit grep優先、site/は--exclude-dir対象」 |
| C3 | docs/HISTORYをdocs/history/へ物理移動 | `ls docs/`の視認ノイズ低減（Phase 4候補） |
| C4 | 巨大HISTORY docsの要約化・圧縮 | 過去資料の書き換え → **governance違反リスク** |
| C5 | templates.py分割 | 生成ロジック変更 → **機能リスク大** |
| C6 | __pycache__定期削除 | 運用上の小改善 |
| C7 | docs/README.md索引への追記 | PHASE2_PLAN・PHASE3_AUDITを分類追加 |
| C8 | README.mdのディレクトリ説明更新 | `docs/` の説明に「docs/README.md索引参照」を追記 |

---

## 10. 対策ごとの効果/リスク

| ID | 優先度 | 分類 | context効果 | リスク | 備考 |
|---|---|---|---|---|---|
| C1 | **MEDIUM** | **A**（直接） | 起動経路の最後の仕上げ。HISTORY誤探索の防止を補強 | 低（README文書変更のみ） | ただしREADME変更は要判断 |
| C7 | MEDIUM | A | 索引の完全性維持 | 極低 | 新規docsの索引反映 |
| C2 | MEDIUM | B（運用効率） | raw grep時のsite/ヒットを防ぐ | 低 | CLAUDE.md+1行 |
| C8 | LOW | B | ディレクトリ説明の正確化 | 低 | C1と同時実施が自然 |
| C3 | LOW | B（探索効率） | `ls docs/`の視認改善。**ただしrepo mapサイズは不変**（trackedのままなら） | 中（docs移動は今回禁止・governanceへの影響） | Phase 4判断 |
| C6 | LOW | C | ほぼなし | 低 | 任意 |
| C4 | **NO-GO** | — | — | 高（過去資料の書き換え・governance違反） | 実施しない |
| C5 | **NO-GO** | — | — | 高（生成ロジック・機能変更） | 実施しない |

---

## 11. 推奨Priority

| Priority | 対策 | 判断理由 |
|---|---|---|
| **HIGH** | （なし） | Phase 1・2で主要対策は完了。追加の「高効果×安全」は存在しない |
| **MEDIUM** | C1, C7 | README誘導の仕上げ・索引の完全性。安全 |
| **MEDIUM** | C2 | grep運用の明文化。低リスク |
| **LOW** | C8, C6 | 任意の改善 |
| **Phase 4へ** | C3 | docs/history/物理移動（要承認・governance検討） |
| **NO-GO** | C4, C5 | 過去資料書き換え・生成ロジック変更は禁止 |

---

## 12. 「変更しないもの」の明示

以下は**今回・今後も原則変更しない**:

- `data/*.json`（価格等のSingle Source of Truth・pricing schema）
- `config/*.json`（affiliate/CTA・監視・サイト設定）
- `tools/*`（生成・検証・監視ロジック。templates.py含む）
- `site/` 生成ロジック・UI・schema
- 既存docsの内容（HISTORY/AUDIT含む）・docs/README.md・CLAUDE.md
- `.gitignore`・deploy設定
- 削除・移動・改名・`git rm`

---

## 13. Phase 3実施案（実装する場合）

> 本監査では**実施しない**。承認後の最小案:

1. **[MEDIUM] README.md**: 「ドキュメント」節に docs/README.md（5分類索引）への参照を追加
2. **[MEDIUM] CLAUDE.md**: 「検索は `git grep` 優先・raw grep時は `--exclude-dir=site`」を1行追加
3. **[MEDIUM] docs/README.md**: 索引に `REPOSITORY_CONTEXT_PHASE2_PLAN.md` / `REPOSITORY_CONTEXT_PHASE3_AUDIT.md` を分類追記
4. 確認: `git diff --check` → commit → push（明示指示がある場合のみ）

※ この3項目はすべて**文書のみの変更**で、機能・data・生成ロジックに影響しない。

---

## 14. Phase 4へ持ち越す項目

| 項目 | 内容 | 判断材料 |
|---|---|---|
| C3: docs/HISTORY物理移動 | `docs/history/` サブディレクトリ化 | repo mapサイズは不変のため**context効果は限定的**。governance（tracked履歴）とのトレードオフを要判断。実質は「視認ノイズ低減」目的 |
| C3': docs/HISTORY untrack化 | `.gitignore` + `git rm --cached` | **governance違反リスク大**（監査・調査の履歴消失リスク）。推奨しない |
| C1/C2/C7 実装 | README・CLAUDE.md・docs索引の更新 | Phase 3実施案（上記13章）の承認待ち |
| grep運用の標準化 | `git grep` 優先・`--exclude-dir=site` | C2の一環 |

---

## 最終判断

- **Phase 1・2で「token/context削減の本丸」は完了している**（site/ 736K文字の探索対象除外＋docs索引＋探索誘導）。
- Phase 3の追加監査では、**「大きな効果×安全」な未実施対策は存在しない**ことを確認。
- 残るは**文書の仕上げ**（README誘導・grep運用明文化・索引追記）で、いずれも[MEDIUM]・文書のみ・低リスク。
- **C4（docs要約化）・C5（templates.py分割）はNO-GO**。token削減を理由に機能やgovernance記録を壊さない。
- 実施はご承認後。今回は**READ ONLYで停止**。

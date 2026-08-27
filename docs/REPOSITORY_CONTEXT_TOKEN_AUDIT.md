# リポジトリ Context / Token 使用量監査レポート

- 作成日: 2026-08-27
- 作成者: Claude Code（READ ONLY監査）
- 対象: 本リポジトリ（`C:\Users\2070a\ret` / branch `main`）
- 目的: Claude Codeのtoken/context使用量が過大になっている原因を特定し、機能・UI・data/model・pricing schema・生成ロジックを**一切変更せず**に安全に削減するための判断材料を提供する
- 実施範囲: **監査と推奨案のみ**。`.gitignore`変更・ファイル移動・削除・`git rm`・`commit`・`push`・docs再編・schema変更は行っていない

---

## 0. 監査方法

- ワーキングツリー全77ファイルを列挙し、ディレクトリ別・ファイル別サイズを計測
- `git ls-files` / `git status --ignored` / `.gitignore` / `.git/info/exclude` により tracked / untracked / ignored を判定
- `tools/build.py` / `tools/sitegen/generators.py` の実装を確認し、`site/` 配下が**全ファイル生成物**であることを確認
- `deploy.ps1` / `wrangler.toml` / `.github/workflows/` を確認し、全デプロイ経路で `site/` が再生成されることを確認
- 生成HTMLが `data/*.json` の内容を重複保持していることをgrepで確認

---

## 1. Executive Summary

### 1.1 全体像

| 項目 | 値 |
|---|---|
| ワーキングツリー合計 | 1.8MB / 77ファイル |
| Git管理ファイル数 | 70ファイル（tracked） |
| Gitリポジトリサイズ | 4.2MB（29 commits） |
| 作業ツリー状態 | clean（未commit・未pushなし） |
| CLAUDE.md | **存在しない**（起動時常時読込ファイルは README.md のみ） |

### 1.2 主要な原因（要約）

1. **`site/` の生成HTML（790KB / 736K文字 / 11,788行）がGit管理されている** → Claude Codeのrepo map・grep・探索対象になり、`data/*.json` + `tools/sitegen/templates.py` の内容を**そのまま重複**して読み込む。これが最大のcontext消費源。
2. **`docs/` に過去のフェーズ・調査ドキュメントが22本蓄積（544KB / 505K文字 / 5,732行）** → 最終仕様書（`FINAL_PRODUCT_DESIGN.md` / `FINAL_REDESIGN_SPEC.md`）に取って代わられた過去資料まで探索対象に残っている。
3. **同一情報の3重保持構造** → データは `data/*.json`（単一情報源）が正だが、同じ価格・キャンペーン・送料情報が `templates.py` と生成HTML `site/*.html` にも複製され、grep1回で同一情報が複数ヒットする。

### 1.3 最重要結論

- **`site/` 配下は `tools/build.py` が100%生成する成果物**であり、`data/*.json` + `config/*.json` + `tools/sitegen/*.py` から完全に再生成可能。
- さらに**全デプロイ経路**（`deploy.ps1` / Cloudflare Workers Builds Git連携 / 旧Pages workflow）が `python tools/build.py` を実行してから配信するため、**コミット済みHTMLはデプロイにも不要**。
- したがって `site/*.html` 等の生成物を **Git追跡から外し `.gitignore` に追加**（＝repo map / 検索対象から除外）することが、**最小変更で最大のcontext削減効果**を得られる唯一にして最強の策。
- 加えて、`docs/` の「現行仕様」と「履歴」をCLAUDE.md / インデックスで明示し、探索時に過去資料を読み飛ばせるようにする。

### 1.4 見積もりtoken負荷（参考）

日本語は1文字≈0.5〜1.0 token程度の密度のため、以下の概算（全量読込時の上限値）:

| 対象 | 文字数 | 概算token（全読時） |
|---|---|---|
| site/ 生成HTML | 736K | 約30〜45万 |
| docs/ 全Markdown | 505K | 約20〜30万 |
| tools/ ソース（pyc除く） | 141K | 約7〜10万 |
| data/ JSON | 87K | 約4〜6万 |
| config/ JSON | 8K | 約0.4万 |

※ Claude Codeは常に全量を読むわけではないが、「siteを確認」「noshの価格を調べる」「grepでキャンペーンを検索」などの操作が発生するたびに、上記の大きな塊がcontextに入り得る。

---

## 2. token/context使用量が多い原因ランキング

| 順位 | 原因 | 影響度 | 分類 | 対処 |
|---|---|---|---|---|
| 1 | **`site/` 生成HTMLがtracked**（790KB / 26HTML + robots/sitemap/google） | **非常大** | **A**（context削減に直接効く） | untrack + .gitignore |
| 2 | **docs/の過去資料・フェーズ計画の蓄積**（22本 / 544KB） | 大 | **A** | CLAUDE.md + インデックスで「現行仕様」を明示 |
| 3 | **同一情報の3重保持**（data JSON × templates.py × 生成HTML） | 大 | **A** | site/を探索対象から外すことで実質解消 |
| 4 | `tools/sitegen/templates.py` の巨大化（2,080行 / 111KB） | 中 | **B**（repoサイズには効く、contextは限定的） | 分割は生成ロジック変更になるため**現状維持** |
| 5 | `__pycache__` の .pyc（184KB on disk） | 小 | **B**（ただし既にignore済み・tracked外） | 現状維持 |
| 6 | `.git` 履歴 4.2MB | なし | **C**（contextに影響なし） | 対応不要 |

**補足**: ランキング1と2は「Claude Codeが実際にcontextへ取り込む量」に直結する。ランキング4〜6はGit repositoryサイズの話であり、context削減効果は限定的。

---

## 3. directory別の問題

### 3.1 `site/`（790KB / 28ファイル）—【最重要問題】

- 内訳: `*.html` 26本 + `robots.txt` + `sitemap.xml`（`googlef4d8b0b633188b1b.html` 含む）
- **全ファイルが `tools/build.py` の生成物**（`generators.py` のwrite処理を全件確認済み）
- 全HTML合計 **11,788行**。`ranking.html` 664行 / `verification.html` 473行 / `index.html` 509行など
- `data/services.json` の内容（価格・送料・キャンペーン・出典）を**HTML内に重複保持**していることを確認（例: `site/services/nosh.html` 内に「価格」12回「初回キャンペーン」8回「送料」18回）
- **Claude Codeが「サイトを見る」時は常にHTMLを読む**が、その内容の情報源は `data/*.json` 側にある
- → 修正を伴わずにsite/を読む必要があるケースはほぼない

### 3.2 `docs/`（544KB / 22ファイル / 5,732行）

- 市場調査・SEO調査・UI調査・フェーズ計画（PHASE1〜4）・競合再監査・最終仕様・監査記録が混在
- **現行仕様（current）**:
  - `FINAL_PRODUCT_DESIGN.md`（33KB）
  - `FINAL_REDESIGN_SPEC.md`（27KB）
- **履歴・調査資料（historical）**:
  - `PHASE1_IMPLEMENTATION_PLAN.md`（30KB）
  - `PHASE2_IMPLEMENTATION_PLAN.md`（15KB）
  - `PHASE3_IMPLEMENTATION_PLAN.md`（25KB）/ `PHASE3_COMPETITIVE_REAUDIT.md`（23KB）
  - `PHASE4_COMPETITIVE_REAUDIT.md`（24KB）/ `PHASE4_FINAL_DECISION.md`（21KB）/ `PHASE4_IMPLEMENTATION_REPORT.md`（12KB）
  - `REDESIGN_UI_SPEC.md`（51KB）※`FINAL_REDESIGN_SPEC.md`に統合済み
  - `REDESIGN_COMPETITIVE_AUDIT.md`（31KB）※`FINAL_REDESIGN_SPEC.md`の基準文書だが、現行仕様はFINAL側
  - `REDESIGN_IMPLEMENTATION_REPORT.md`（13KB）
  - `SEO_*` 2本、`AFFILIATE_MARKET_ENTRY_*` 2本、`SITE_UX_INTEREST_AUDIT`、`SITE_NAME_DOMAIN_DECISION`、`DELIVERY_FOOD_AFFILIATE_NEXT_ACTION` 等（各8〜56KB）
- **監査・governance記録**（research governance上は残すべき）:
  - `DATA_VERIFICATION_AUDIT_20260827.md`（8KB）
  - `REMAINING_8_ITEMS_AUDIT_20260827.md`（15KB）
- 問題は「どれが現行でどれが履歴か」の索引がなく、Claude Codeが探索時に全22本を横断し得る点

### 3.3 `data/`（100KB / 6JSON + snapshots/）

- **単一情報源（source of truth）**。`services.json`（56KB / 1,346行）が最大
- `snapshots/` は空ディレクトリ（`.gitignore` でignore済み・tracked外）→ 問題なし
- ここは**絶対に変更・ignoreしない**

### 3.4 `config/`（20KB / 4JSON）

- `affiliates.json` / `comparisons.json` / `site.json` / `watchlist.json`
- サイト生成・アフィリエイト・監視に必須 → **絶対に変更しない**

### 3.5 `tools/`（345KB / ソース7本 + pyc 6本）

- ソース: `build.py`(14行) / `watch.py`(228行) / `sitegen/data.py`(75行) / `sitegen/generators.py`(241行) / `sitegen/templates.py`(2,080行) / `sitegen/validate.py`(97行)
- `templates.py` が111KBで全ソースの約7割を占める
- `__pycache__/`（`.pyc` 合計184KB、`templates.cpython-314.pyc` だけで125KB）は **`.gitignore` 済み・tracked外** → Gitには影響なし
- Claude Codeのrepo mapはgitignoreを尊重するため、実害は限定的。ただし `find` / `ls` での一覧には現れる

### 3.6 ルート / その他

- `README.md`（2.4KB）: 起動時に毎回読まれる唯一のファイル。小さいので問題なし
- `deploy.ps1`（1.4KB）: `python tools/build.py` を実行してから deploy → site/はデプロイ時に再生成される
- `wrangler.toml`（0.8KB）: `./site` を静的配信。**デプロイ時はビルド後に配信**
- `.github/workflows/deploy-cloudflare.yml`（1.6KB）: **旧Pages方式の残骸**（ファイル冒頭コメントに「本番とは対象が異なる」「pushトリガー無効・手動のみ」と明記）。Git管理上は無害だが、存在意義は薄い
- `.claude/scheduled_tasks.lock` 等: `.git/info/exclude` で除外済み → 問題なし

---

## 4. 大容量・大量ファイル分析

### 4.1 上位ファイル（ワーキングツリー）

| 順位 | ファイル | サイズ | 分類 |
|---|---|---|---|
| 1 | `tools/sitegen/__pycache__/templates.cpython-314.pyc` | 125KB | ignore済み（触る必要なし） |
| 2 | `tools/sitegen/templates.py` | 111KB | **必要ソース**（変更禁止） |
| 3 | `site/ranking.html` | 61KB | **生成物** |
| 4 | `data/services.json` | 56KB | **単一情報源**（変更禁止） |
| 5 | `docs/AFFILIATE_MARKET_ENTRY_RESEARCH_2026_08.md` | 55KB | 履歴資料 |
| 6 | `docs/REDESIGN_UI_SPEC.md` | 51KB | 履歴資料（FINAL_REDESIGN_SPECに統合） |
| 7 | `site/verification.html` | 36KB | **生成物** |
| 8 | `docs/SITE_UX_INTEREST_AUDIT_2026_08_26.md` | 36KB | 履歴資料 |
| 9 | `site/articles/chef-muten-tukuritoki-kuchikomi.html` | 33KB | **生成物** |
| 10 | `site/index.html` | 33KB | **生成物** |

※ `site/` のHTML 26本は **31〜62KB × 26本 = 773KB** と、上位10件の過半数を占める。

### 4.2 大量の小ファイル

- 特に問題となる規模ではない（全77ファイル）
- ただし `site/` 内の26HTMLが「数は多いが中身は全部data JSONの複製」という構造は、**ファイル数 × 単体サイズ** の両面でcontextに効く

### 4.3 generated / cache / 一時ファイル

| 種別 | 場所 | サイズ | Git状態 | 対応 |
|---|---|---|---|---|
| 生成HTML | `site/*.html` ほか | 773KB | **tracked（問題）** | untrack + ignore推奨 |
| 生成XML/TXT | `site/sitemap.xml` / `robots.txt` | 数KB | tracked（問題） | untrack + ignore推奨 |
| GSC確認ファイル | `site/googlef4d8b0b633188b1b.html` | 数百B | tracked（問題） | untrack + ignore推奨 |
| .pyc | `tools/**/__pycache__/` | 184KB | ignore済み | 現状維持 |
| スナップショット | `data/snapshots/` | 0KB（空） | ignore済み | 現状維持 |
| ログ | `*.log` | なし | ignore済み | 現状維持 |

### 4.4 重複データ

- **3重保持構造**: 価格・送料・キャンペーン・出典情報が
  1. `data/*.json`（正本）
  2. `tools/sitegen/templates.py`（描画ロジック内に組込）
  3. `site/*.html`（生成物に展開）
  の3箇所に存在
- 特にHTMLは `data/*.json` の**丸ごと展開**であり、重複度が最も高い
- → `site/` を探索対象から外すだけで、Claude Codeから見える重複が解消される

---

## 5. Git tracked / untracked 分析

### 5.1 現状

- **tracked: 70ファイル / 1,486KB**
  - 内訳: `site/` 28ファイル（773KB / **全体の52%**）、`docs/` 22ファイル（544KB / 37%）、`tools/` 7ファイル（160KB）、`data/` 6ファイル（100KB）、`config/` 4ファイル（20KB）、その他 4ファイル
- **untracked: 0**（`git ls-files --others --exclude-standard` 空）
- **ignored**: `.claude/`（scheduled_tasks.lock等）、`tools/__pycache__/`、`tools/sitegen/__pycache__/`

### 5.2 判定

| 対象 | 判定 |
|---|---|
| `site/` 生成物 28ファイル | **trackedにする必要がない**（build.pyで再生成・デプロイ時にも再生成される） |
| `docs/` 22ファイル | tracked維持は妥当（governance）。ただし探索順序の誘導が必要 |
| `data/` / `config/` / `tools/` ソース | **必須tracked** |
| `.pyc` / `snapshots` / `.log` | 既にignore・tracked外で正常 |

### 5.3 巨大ファイルのGit管理

- 単体で巨大なバイナリ等はなし（最大でもテキスト111KB）。Gitサイズ4.2MBは正常
- **Gitサイズが原因ではない** → `.git` の縮小はcontext削減に効果なし

---

## 6. 現在の .gitignore 分析

### 6.1 現在の `.gitignore`（全文）

```
__pycache__/
*.pyc
data/snapshots/
*.log
.DS_Store
Thumbs.db
```

### 6.2 `.git/info/exclude` 追加分

```
**/.claude/scheduled_tasks.lock
**/.claude/scheduled_tasks.json
**/.claude/routines/.state/
**/.claude/worktrees/
**/.claude/checkpoints/
**/.claude/mailbox/
**/.claude/agent-registry.json
**/.claude/agent-memory-local
**/.claude/first-run
**/.claude/assistant-daemon-state.json
```

### 6.3 評価

| 現行ルール | 評価 |
|---|---|
| `__pycache__/` `*.pyc` | 正常（生成物を除外） |
| `data/snapshots/` | 正常（スナップショット除外） |
| `*.log` `.DS_Store` `Thumbs.db` | 正常 |
| `.claude/` 系（info/exclude） | 正常（Claude Codeのランタイム状態） |
| **`site/` 生成物の除外ルール** | **欠落（最大の問題）** |
| **`*.html` 等の一括除外** | **欠落（なし）** |

---

## 7. Claude Code contextへの影響

### 7.1 探索時に見えてしまうファイル

- `site/` 生成HTML 26本は repo map に載り、`ls site/` や `site/` 内を開く操作で**毎回736KB分の重複テキストが視野に入る**
- `docs/` 22本は横断的に見え、現行仕様と過去資料の区別がつかない
- `.pyc` はignore済みだが `find`/`ls` の一覧には現れる（実害は小）

### 7.2 grep / search対象になりやすいファイル

- 「価格」「キャンペーン」「送料」「nosh」等のキーワードgrepは
  `data/*.json`（正本）+ `templates.py`（ロジック）+ `site/*.html`（複製）に**同内容で複数ヒット**する
- 検索結果の該当行が大量に出るため、1回の検索でcontextを大量消費する

### 7.3 毎回読まれている可能性があるファイル

- `README.md`（2.4KB）: Claude Codeの起動時コンテキストに含まれる。**小さいので問題なし**
- CLAUDE.md: **存在しない** → 起動時コンテキストは現状軽い。追加は慎重に（下記12章）

### 7.4 CLAUDE.md等によって常時contextに入る情報

- 現状なし（CLAUDE.md未設置）
- **注意**: CLAUDE.mdを作ることは「常時contextを+1つ」増やすこと。最小限の内容（探索ガイダンスのみ）にしないと逆効果

### 7.5 巨大docsによる圧迫

- `docs/` 全505K文字。フェーズ計画・競合監査が現行仕様と並存しており、**正しい仕様を探すために関連する履歴まで読む**事態が発生し得る

### 7.6 generated outputによる重複

- `site/` HTMLが最大の重複源。`data/*.json` の完全展開であり、Claude Codeが「サイトの現状確認」をするたびにdata JSONとHTMLの両方を読む二重コストが発生

### 7.7 同じ情報の複数ファイル保持による重複

- data JSON ⇔ templates.py ⇔ site/ HTML の3重保持
- templates.py 内にHTML描画とデータ定義の両方が混在（分割はロジック変更になるため現状維持推奨）

### 7.8 session/contextとは無関係でGitサイズだけ大きいもの

- `.git` 4.2MB（29 commits）: contextに影響なし。対応不要
- `.pyc` 184KB on disk: context影響は小。ignore済み

---

## 8. 「ignore推奨」（安全にignoreできる）

| 対象 | 優先度 | 分類 | 根拠 |
|---|---|---|---|
| `site/*.html` | **[HIGH]** | **A** | build.pyの100%生成物。全デプロイ経路で再生成される |
| `site/robots.txt` `site/sitemap.xml` | [HIGH] | A | 同上（generators.pyが生成） |
| `site/googlef4d8b0b633188b1b.html` | [HIGH] | A | GSC確認ファイル（build.pyが生成） |
| `tools/**/__pycache__/` | 継続（既にignore済み） | B | 現状で正常 |
| `data/snapshots/` | 継続（既にignore済み） | B | 現状で正常 |
| `*.log` `.DS_Store` `Thumbs.db` | 継続（既にignore済み） | C | 現状で正常 |

※ `site/` をignoreする際は **「ディレクトリごとignore（`site/`）」ではなく「生成物パターン（`site/*.html` 等）でignore」** を推奨。ディレクトリごとignoreにすると将来手動配置するファイル（例: `site/favicon.ico` 等のバイナリ）が誤って無視される恐れがある。

---

## 9. 「tracked維持だが探索対象から外すべき」

- **前提**: Claude Codeのrepo mapは「git trackedファイル」を基本とするため、trackedを維持したまま検索対象から外す仕組みはGitignoreでは実現できない。よって以下は「tracked維持 + CLAUDE.md / インデックスで探索を誘導」の形で提案する。

| 対象 | 優先度 | 分類 | 方法 |
|---|---|---|---|
| docs/ の履歴資料（PHASE1〜4・UI_SPEC・競合監査・SEO調査等） | [MEDIUM] | A | CLAUDE.mdに「現行仕様はFINAL_PRODUCT_DESIGN.md / FINAL_REDESIGN_SPEC.md」と明記し、履歴docsを読まずに済ませる |
| docs/ の監査記録（DATA_VERIFICATION_AUDIT / REMAINING_8_ITEMS_AUDIT） | [MEDIUM] | A | governance上tracked維持。CLAUDE.mdで「必要時のみ読む」と明記 |
| `.github/workflows/deploy-cloudflare.yml` | [LOW] | C | 旧Pages残骸。1.6KBで害は小。削除は任意（本監査では変更しない） |

---

## 10. 「絶対に変更しない」

| 対象 | 理由 |
|---|---|
| `data/*.json`（services/campaigns/menus/shipping/sources） | 単一情報源（source of truth）。pricing schemaの中核 |
| `config/*.json`（affiliates/comparisons/site/watchlist） | サイト生成・アフィリエイト・監視に必須 |
| `tools/sitegen/*.py` / `tools/build.py` / `tools/watch.py` | 生成ロジック・検証ロジック。変更禁止 |
| `README.md` | リポジトリのエントリポイント |
| `wrangler.toml` / `deploy.ps1` | デプロイ設定・手順 |
| `site/` ディレクトリそのもの | デプロイ時の出力先。**ファイル削除ではなく「追跡解除」のみ**を検討対象にする |
| 監査・governance記録（docs内の監査ドキュメント） | research governance上必要 |

---

## 11. 推奨する .gitignore 変更案

```gitignore
# ---- 追加推奨（生成HTMLの追跡解除後） ----
# 生成物: tools/build.py の出力（data/*.json + config/*.json + tools/sitegen/*.py から再生成可能）
site/*.html
site/*/*.html
site/robots.txt
site/sitemap.xml
site/google*.html
```

- **適用手順の前提**: `.gitignore` に追加するだけでは「既にtrackedされているファイル」は対象外。**`git rm -r --cached site/`（追跡解除・ディスクには残す）** が必要。
- ただし本監査では実際の変更は行わない（実施手順は15章に記載）。
- 代替案（より保守的）: `site/*.html` をignoreせず、CLAUDE.mdで「site/を読むな」と明示する。効果は弱いがGitの状態を一切変えない。

---

## 12. 推奨する CLAUDE.md / context運用改善案

### 12.1 CLAUDE.md（新規作成・最小構成・15〜30行程度）

```markdown
# 宅食図鑑 リポジトリ運用メモ（Claude Code用）

## データフロー（最重要）
data/*.json（単一情報源）→ tools/sitegen/*.py（描画）→ site/（生成HTML）

## site/ は生成物
- site/ 配下は tools/build.py の出力。**読まないこと**。
- サイト内容の確認は data/*.json と tools/sitegen/templates.py を見るか、
  `python tools/build.py` を実行して site/ を再生成する。

## docs/ の使い分け
- 現行仕様: docs/FINAL_PRODUCT_DESIGN.md, docs/FINAL_REDESIGN_SPEC.md
- 履歴・調査（PHASE1〜4, REDESIGN_UI_SPEC, SEO/市場調査等）: 参照が必要な時のみ読む
- 監査記録: docs/DATA_VERIFICATION_AUDIT_20260827.md, docs/REMAINING_8_ITEMS_AUDIT_20260827.md

## 変更時のルール
- data/ と config/ は検証ロジック（tools/sitegen/validate.py）を通すこと
- 変更後は `python tools/build.py` で site/ を再生成し、差分を確認すること
```

### 12.2 docs/README.md（インデックス・任意）

- docs/ に目次ファイルを置き、各ドキュメントの「種別（現行/履歴/監査）」と「1行要約」を記載
- Claude Codeが最初にdocs/README.mdを見れば、全22本を横断せずに済む
- [MEDIUM] / A

### 12.3 注意（逆効果の防止）

- CLAUDE.mdは「常時contextに入る」ため、**長大化させない**（15〜30行が上限目安）
- `site/` のignoreをせずCLAUDE.mdだけで制御する場合は、grep/searchでsite/がヒットし続けるため、**効果は限定的**（本命はuntrack + ignore）

---

## 13. 実施した場合の期待効果

### 13.1 Phase 1（site/ untrack + ignore + CLAUDE.md 導入）

| 指標 | 現状 | 実施後 | 効果 |
|---|---|---|---|
| Claude Codeの探索対象（repo mapの文字量） | 約1.48M文字 | 約0.74M文字（site/ 分を除外） | **約50%削減** |
| grep「キャンペーン」等のヒット重複 | data + templates + site×26 | data + templates | **重複ヒット解消** |
| 「サイトを確認」時の読込量 | data JSON + 巨大HTML | data JSON + 必要ならbuild | **HTML読込を排除** |
| docs横断による誤読 | 22本を区別なく探索 | 現行2本 + 必要時のみ履歴 | **履歴の誤読を防止** |

### 13.2 定量的見積もり（全読時のtoken削減の上限）

- `site/` を探索対象から外す → **最大で約30〜45万token分の重複テキストがrepo map / 検索 / 読込から消える**
- docsの誘導 → セッション毎に**数万〜十数万token**の削減が見込める（過去資料を読み飛ばせるため）
- 実際のセッションでは「必要な分しか読まない」ため削減幅はセッション依存だが、**site/の除外だけでも探索コストの体感は大きく下がる**

---

## 14. リスク

| リスク | 深刻度 | 対策 |
|---|---|---|
| `site/` をuntrack後、新規クローン直後はHTMLが存在しない | 低 | デプロイは全経路で `python tools/build.py` を実行するため配信には影響しない。ローカルでも `python tools/build.py` で即復元 |
| Cloudflare側のビルド設定が将来変わり「コミット済みHTMLを直接配信」する方式に変わる | 低 | デプロイ設定（Build command）を変更しない限り発生しない。README/wrangler.tomlに明記済み |
| `git rm -r --cached site/` の操作ミスで `-f` 等を付けてディスクから削除してしまう | 中 | 手順を明文化し、必ず `--cached` を付ける。削除後の復元は `python tools/build.py` で可能 |
| CLAUDE.md を長大化させて逆にcontextが増える | 低 | 12.3に記載の通り15〜30行に制限 |
| 生成ロジック・dataを誤って変更する | 高（**禁止事項**） | 本監査では一切変更しない。実施時も `tools/` と `data/` には触れない |

---

## 15. 実施手順（将来実施する場合の推奨手順）

> ※ 本監査では**実行しない**。以下は承認後の実施手順案。

### Phase 1（最小変更・最大効果）

1. **`site/` の追跡解除**: `git rm -r --cached site/`
   （ファイルはディスクに残る。`ls site/` で全ファイルの存在を確認してから次の手順へ）
2. **`.gitignore` に生成物パターンを追加**:
   ```
   site/*.html
   site/*/*.html
   site/robots.txt
   site/sitemap.xml
   site/google*.html
   ```
3. **`.gitignore` が効いていることを確認**: `git status --ignored` で `!! site/...` が出ること
4. **`python tools/build.py` が正常に動作し site/ が再生成されることを確認**（gitの追跡から外れても生成に影響がないこと）
5. **CLAUDE.md を新規作成**（12.1の内容・15〜30行）
6. **確認**: `git status` で「site/の削除（staged） + .gitignore/CLAUDE.md追加」のみになっていること
7. **commit / push**（README・wrangler.toml・デプロイ設定に変更なし）

### Phase 2（任意・docs運用改善）

8. **docs/README.md のインデックス作成**（現行/履歴/監査の分類表）
9. CLAUDE.md の docs 誘導を微調整

### Phase 3（任意・保守的代替）

10. もし「コミット済みHTMLを残したい」場合は、untrackせずCLAUDE.mdの「site/を読まない」指示のみで運用（効果は弱い）

---

## 16. 最終判断

### 16.1 結論

- **Claude Codeのtoken/context使用量増大の主因は「Git管理された生成HTML `site/`（790KB）」と「docs/の履歴資料（544KB）」の2つ**であり、いずれも「機能・データ・生成ロジックを一切変えず」に探索対象から外せる。
- `site/` は全デプロイ経路で `python tools/build.py` により再生成されるため、**追跡解除してもデプロイ・サイト配信に影響しない**。
- `data/` / `config/` / `tools/` / pricing schema / 監査記録は**一切変更してはならない**。

### 16.2 推奨判断

| 項目 | 推奨 | 優先度 | 分類 |
|---|---|---|---|
| `site/` 生成物の untrack + ignore | **実施を強く推奨** | [HIGH] | A |
| CLAUDE.md 新設（探索ガイダンス） | 推奨 | [HIGH] | A |
| docs/README.md インデックス | 推奨（Phase 2） | [MEDIUM] | A |
| `.github/workflows/deploy-cloudflare.yml` の整理 | 任意 | [LOW] | C |
| `templates.py` 分割等のロジック変更 | **非推奨（機能変更になるため）** | — | — |
| `.git` 履歴の縮小 | 不要（contextに無関係） | — | C |

---

## Phase 1（最小変更で最大のcontext削減効果を得るための推奨セット）

> 「これだけやれば十分」の3〜10項目。全て[A]分類（Claude Codeのcontext削減に直接効く）。

1. **[HIGH][A] `site/` の生成物をGit追跡から外す**: `git rm -r --cached site/`（ディスクには残す）
2. **[HIGH][A] `.gitignore` に `site/*.html` / `site/*/*.html` / `site/robots.txt` / `site/sitemap.xml` / `site/google*.html` を追加**
3. **[HIGH][A] `git status --ignored` で `site/` が `!!`（ignore）になることを確認**
4. **[HIGH][A] `python tools/build.py` の再生成が正常に動作することを確認**（追跡解除後も生成に影響なし）
5. **[HIGH][A] CLAUDE.md を新規作成（15〜30行）**: 「site/は生成物で読まない」「現行仕様は FINAL_PRODUCT_DESIGN.md / FINAL_REDESIGN_SPEC.md」「data/・config/・tools/ は変更禁止」を明記
6. **[MEDIUM][A] docs/README.md インデックスを作成**（現行/履歴/監査の分類表 → 全docs横断を防止）
7. **[LOW][C] 旧Pages workflow（`.github/workflows/deploy-cloudflare.yml`）の扱いを検討**（1.6KB・手動のみ・害は小。削除は任意）
8. **[LOW][B] `__pycache__` の再生成は現状のignoreで維持**（変更不要・確認のみ）

**実施後の期待**: repo map / 探索対象の文字量が約半分になり、`site/` 由来の重複ヒットとHTML読込が消える。docsも「現行仕様」に誘導されるため、過去資料の誤読によるcontext消費が防がれる。

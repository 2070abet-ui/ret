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
| `UI_DESIGN_PRINCIPLES.md` | UI設計原則（意思決定支援型アフィリエイトサイトの設計基準。ui-design-workflow SkillがUI改善時に必読） |
| `SITE_NAME_DOMAIN_DECISION_2026_08.md` | サイト名・ドメイン決定 |
| `PHASE4_FINAL_DECISION.md` | Phase4最終実装判断・収益計測設計 |
| `DELIVERY_FOOD_AFFILIATE_NEXT_ACTION_2026_08.md` | 次の一手・ロードマップ |

## AUDIT（監査・検証記録 / 参照時のみ）
| ファイル | 内容 |
|---|---|
| `DATA_VERIFICATION_AUDIT_20260827.md` | 確認率改善の監査記録 |
| `REMAINING_8_ITEMS_AUDIT_20260827.md` | 残り8項目の確認可能性監査 |
| `REPOSITORY_CONTEXT_TOKEN_AUDIT.md` | context/token使用量監査 |
| `REPOSITORY_CONTEXT_PHASE2_PLAN.md` | context最適化Phase2設計書（実装済み） |
| `REPOSITORY_CONTEXT_PHASE3_AUDIT.md` | context最適化Phase3追加監査 |
| `URL_NORMALIZATION_AUDIT_2026_08_28.md` | 全32ページのURL正規化監査。canonical/sitemap（`.html`付き）が実サーバー（Cloudflare `html_handling=auto-trailing-slash`）では全ページ307リダイレクトすると判明、P1。推奨正規URLは拡張子なし、修正箇所を特定済み |
| `URL_NORMALIZATION_IMPLEMENTATION_2026_08_28.md` | 上記監査に基づく実装記録。canonical/sitemap/内部リンク/detail_url/比較URL生成を拡張子なしに統一（`templates.py`・`generators.py`のみ変更、data/config差分ゼロ）。build/validate/Playwright実画面確認まで完了、**デプロイは未実施** |
| `COMPETITOR_UX_FUNNEL_AUDIT_2026_08_28.md` | 宅食グルメ・マイベスト等4競合との実ブラウザ比較による購買意思決定ファネル監査。最重要所見は比較一覧の初回/通常価格が同一視覚重みで混在し誤読を招く問題（新規）。A/B/C分類・Top10問題・改善優先順位を提示。data/model・ランキング化は変更提案なし、未実装 |
| `PRICE_FAIRNESS_UI_FIX_FINAL_AUDIT_2026_08_28.md` | 上記監査に基づき`templates.py`のみで実装した価格公平性UI修正（初回/お試し価格の強調表示＋「表示価格が安い順」並び替え）のREAD ONLY最終監査。総合判定CONDITIONAL（実用上問題なし、軽微な残存リスクのみ）。凍結可と判定 |
| `VISUAL_DESIGN_SYSTEM_AUDIT_2026_08_28.md` | UIビジュアルデザイン（色・余白・タイポグラフィ・カード・情報密度）のREAD ONLY監査。kakaku.com/mybest.com/linear.app/oisix.comを実機調査し、写真が使えない制約下での代替案（大きな数字・線アイコン・色帯ゾーン）と、比較表の数字揃え・sticky thead・比較ページ結論の箇条書き化などをP1〜P3で提案。新色・写真・★評価は提案せず、デザインシステム標準を明文化 |
| `VISUAL_DESIGN_SYSTEM_IMPLEMENTATION_PLAN_2026_08_28.md` | 上記監査の8項目（P1〜P3）を実装計画に落とし込んだドキュメント。監査原文の誤り2件（`meal_form_categories()`の循環import制約、`.pros-highlight`誤用）を実ファイル確認で訂正。各項目に現状箇所・変更内容・変更しないもの・UI仕様・PC/モバイル影響・実装順序・検証方法・リスクを明記し、Phase完了時の確認事項を定義。**全8項目実装済み**（`tools/sitegen/templates.py`・`generators.py`、data/config差分ゼロ、PC/モバイルPlaywright確認済み） |
| `VISUAL_EXPRESSION_ANTI_GENERIC_AUDIT_2026_08_28.md` | 「AIっぽさ」を薄め人間が意図してデザインしたように見せるためのREAD ONLY監査（Layer3）。ほぼ日/GRAZA/スターバックス/Wirecutterを実機調査し、原因は「全セクションが同じ角丸カードで描かれる均質さ」と特定。脱カード化・タイポグラフィの強弱・非対称バナー等をP1〜P3で提案。新色・写真・★評価・過剰な角丸/影/絵文字/アイコン氾濫は導入せず、既存トークンのみで実現する方針 |
| `VISUAL_EXPRESSION_ANTI_GENERIC_IMPLEMENTATION_PLAN_2026_08_28.md` | 上記監査を実装計画に落とし込んだドキュメント。脱カード化・非対称化の対象を「このサイトのこだわり」「キャンペーンブロック(TOP＋campaigns.html)」の2種類のみに限定する境界線を明記。監査原文の「画面幅いっぱいの色帯」は実際には1200pxコンテナ内の角丸ボックスに過ぎないと訂正し、真の全幅ブリード（100vwの横スクロールリスク）は採用せず`.trust-panel-compact`型の安全な脱カード化を採用。**全7項目実装済み**（`tools/sitegen/templates.py`のみ、data/config差分ゼロ、PC/モバイルPlaywright確認済み） |

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

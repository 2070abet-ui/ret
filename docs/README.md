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

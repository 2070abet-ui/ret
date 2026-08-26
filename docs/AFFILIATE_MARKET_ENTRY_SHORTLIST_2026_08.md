# アフィリエイト参入ショートリスト（TOP10）— 実行用サマリー（2026年8月）

本ドキュメントは `docs/AFFILIATE_MARKET_ENTRY_RESEARCH_2026_08.md`（全24ジャンルの詳細調査）のTOP10を、着手判断・実行計画にすぐ使える形に再整理したものである。数値・出典の裏付けは調査本編を参照。

---

## TOP10 一覧（再掲）

| Rank | ジャンル | 総合点 | 初回CVの目安 | 参入時の最大の壁 |
|---|---|---|---|---|
| 1 | 宅配食/食品宅配 | 75.0 | 速い | 単発CV中心でLTV構築が課題 |
| 2 | ペット（ドッグフード） | 71.0 | 速い部類 | ペットフード安全法の表示義務、効能表現の逸脱リスク |
| 3 | 資格/スクール/オンライン教育 | 69.5 | やや遅い | 講座提供企業自身のオウンドメディアとの利益相反競合 |
| 4 | AI/SaaS（個人向け） | 68.5（実質60） | 中〜遅い | **本体サービスに公式ASP案件が存在しない**、AI検索代替リスク最大 |
| 5 | 格安SIM/通信 | 66.25 | 比較的速い | 大手比較メディアのコモディティ化、ブランドKWのリスティングNG規約 |
| 6 | 蓄電池・EV充電設備（補助金特化） | 66.0 | 中〜遅い | 自治体データの継続メンテナンスコストが高い |
| 7 | ガジェット | 66.0 | 比較的速い | 物販料率が低い（Amazon1.0〜1.5%） |
| 8 | サブスクリプション | 64.0 | 中 | **Netflix・Amazon Prime Videoは案件なし** |
| 9 | 婚活アプリ・結婚相談所 | 63.0 | 中 | デリケートなテーマゆえの表現配慮が必要 |
| 10 | オンライン家庭教師・個別指導塾 | 61.0 | 速い | 具体的単価が確認不能（要ASP登録後の確認） |

---

## 独自データDBスキーマ（TOP3の実装レベル定義）

### 1位: 宅配食/食品宅配 — `meal_kit_db`

```
Service       { service_id, name, operator, official_url }
Menu          { menu_id, service_id, menu_name, category, price_per_meal,
                calorie, salt_g, carb_g, protein_g, allergen_flags,
                last_checked_date }
Campaign      { campaign_id, service_id, campaign_name, discount_type,
                condition_text, valid_from, valid_to, source_url }
ShippingRule  { service_id, shipping_fee, min_order_count,
                cancellation_condition }
Review        { review_id, service_id, menu_id, taster(自分/読者),
                satisfaction_score, comment, photo_url, tasted_date }
Affiliate     { asp_name, service_id, reward_amount, cv_condition,
                approval_status_note, last_verified_date }
Keyword/Click/CV/Revenue { 通常のアクセス解析・成果テーブル }
```
**資産化のポイント**: `Review`（実食記録）と`Menu`の栄養素DBの掛け合わせが、単なる価格比較サイトにはない差別化軸になる。競合が模倣するには同じ手間（実際に取り寄せて食べる）をかける必要がある。

### 2位: ペット — `pet_food_db`

```
Product   { product_id, brand, product_name, target_breed_size,
            life_stage, protein_pct, fat_pct, fiber_pct,
            grain_free_flag, main_protein_source, country_of_origin,
            price_per_kg }
Campaign  { product_id, first_time_campaign, subscription_condition,
            valid_from, valid_to }
Review    { product_id, reviewer_type(自分の犬/読者投稿),
            breed, weight_kg, allergy_tag, feedback, fed_period_weeks }
Complaint { product_id, issue_type(下痢/食いつき不良等), reported_date,
            source }
Affiliate { asp_name, product_id, reward_amount, cv_condition,
            last_verified_date }
Keyword/Click/CV/Revenue
```
**資産化のポイント**: 犬種×体重×アレルギーの掛け合わせは検索需要が普遍的に続くため、`Product`+`Review`の蓄積がそのまま「診断ツール」のマスタデータになる。

### 6位: 蓄電池・EV充電設備 — `MunicipalitySubsidy`（長期moat型の核）

```
MunicipalitySubsidy {
  municipality_code, municipality_name, prefecture,
  target_equipment(蓄電池/EV充電器/V2H/太陽光),
  subsidy_amount, subsidy_rate, upper_limit,
  application_period_start, application_period_end,
  combinable_with_national_subsidy(bool),
  requirements_text, source_url, last_confirmed_date
}
Product      { product_id, category, maker, model, spec_json }
PriceQuote   { product_id, estimated_construction_cost, observed_date }
Affiliate    { asp_name, campaign_name, reward_amount, cv_condition }
Keyword/Click/CV/Revenue
```
**資産化のポイント**: 全国1,700超の自治体を横断的かつ最新状態で維持するサイトは現状少ない。`last_confirmed_date`を伴う継続更新そのものが模倣コストの高い参入障壁になる。Claude Codeによる定期クロール＋差分検知との相性が最も高いジャンル。

---

## 90日ロードマップ比較（A/B/C案）

| フェーズ | A案: 宅配食（速） | B案: ペット（バランス） | C案: 蓄電池補助金（moat） |
|---|---|---|---|
| Day 0-30 | ASP提携・実食レポート5-10本・サイト構築 | 成分DB初期構築(20-30商品)・ASP提携・記事5本 | 主要20自治体の補助金DB構築・記事10本 |
| Day 30-60 | ロングテール記事20本超・比較DB構築開始 | 診断ロジックβ版・記事20本・初回CV | 100自治体規模へDB拡大・診断ツールβ版 |
| Day 60-90 | CV数把握・診断ツールβ版・横展開検討 | 診断ツール正式公開・DB自動更新パイプライン | 全国自動更新パイプライン完成・初回CV・AI引用実績の確認 |
| 初期費用目安 | 3〜5万円（推測） | 5〜10万円（推測） | 5〜10万円（推測） |
| 想定初回CV時期 | 1〜3ヶ月（推測） | 数ヶ月規模（推測） | 半年規模の可能性（推測） |

いずれも金額・期間は本調査で確認できた単価・構造からの**推測**であり、確定値ではない。着手時にASP実アカウントで単価・承認条件を再確認すること。

---

## 着手前チェックリスト（共通）

1. 対象ジャンルの主要ASP（A8.net、もしもアフィリエイト、バリューコマース、afb、アクセストレード等）に実アカウント登録し、正確な単価・承認条件・キャンペーン有無を一次確認する。
2. 対象サイトのスクレイピング可否を利用規約・robots.txtで確認する（本調査では多くのジャンルで「確認不能」としている）。
3. YMYL・薬機法・景品表示法・食品表示法等、対象ジャンルの規制を再確認し、表現ルール（断定的効能表現の禁止等）をコンテンツガイドラインとして文書化する。
4. Claude Codeによる自動監視パイプライン（価格・キャンペーン・競合記事の差分検知）の対象URLリストを作成する。
5. 独自データDBの初期スキーマを確定し、最初の20〜30件を手動で収集して検証する。

---

## 11位以下で今回「次点」として記録しておく候補

- **カー用品**（61.0点、11位）: 車種別適合DBという組み合わせ爆発型のニッチ情報が模倣困難な資産になり得る。宅配食/ペット/蓄電池の次に検討する価値がある。
- **趣味/ホビー（プラモデル）**（60.0点、12位）: 作例・塗料実測データの模倣困難性は全ジャンル中トップクラスだが、物販単価の低さがネック。副業的な小規模運営に向く。

（全24ジャンルの詳細・確認不能事項・出典は調査本編 `docs/AFFILIATE_MARKET_ENTRY_RESEARCH_2026_08.md` を参照）

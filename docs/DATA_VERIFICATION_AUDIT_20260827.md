# 確認率改善 監査記録（2026-08-27）

## 目的
「公式確認中」が33項目中22項目と過多だった状態を、公式サイト直接確認により改善する。
推測・競合数値は採用せず、公式URLを直接閲覧して確認できた値のみconfirmedへ昇格する。

## 実施原則
- 公式サイトを直接確認した値のみ登録（推測・競合サイト数値は不採用）
- 確認できないものはconfirmedにしない（pending/derived維持）
- schema・status定義・UI・診断ロジック・評価軸は変更しない
- services.json と campaigns.json のキャンペーン状態を整合させる
- sources.json に出典URL・確認日を必ず対応させる

---

## 変更前後の33項目status比較

※statusはサイトの判定ロジック（`templates.py` の `_price_status`/`_shipping_status`/`_campaign_status`）に基づく実測値。キャンペーンは confirmed/uncollected の2値のみ（requires_verificationで導出）。

| 状態 | 変更前 | 変更後 | 差分 |
|---|---|---|---|
| confirmed | 11 | 25 | +14 |
| derived（算出値） | 2 | 1 | -1 |
| pending（確認中） | 1 | 3 | +2 |
| uncollected（未収集） | 19 | 4 | -15 |

確認率: **11/33（33%）→ 25/33（76%）**

### サービス×項目マトリクス（変更後・サイト実測）

| サービス | 価格 | 送料 | キャンペーン |
|---|---|---|---|
| nosh | pending（税込/税抜・食数対応が確定不能） | confirmed | confirmed |
| ワタミの宅食ダイレクト | pending（郵便番号依存で単一値化不可） | confirmed | confirmed |
| 三ツ星ファーム | confirmed 711円/食 | confirmed | confirmed |
| ウェルネスダイニング | confirmed 751円/食 | confirmed | confirmed |
| 食宅便 | derived 690円/食（全コース最安未確定） | confirmed | uncollected |
| FIT FOOD HOME | pending（アラカルト） | confirmed | uncollected |
| まごころケア食 | confirmed 398円/食 | confirmed | confirmed |
| シェフの無添つくりおき | confirmed | confirmed | confirmed |
| 食楽膳 | confirmed | confirmed | confirmed |
| ヨシケイ | uncollected（地域×コース依存・単一値化不能） | confirmed | uncollected |
| 健康直球便 | confirmed 578円/食 | confirmed | confirmed |

---

## confirmed化した値と根拠（公式URL・確認日）

### 三ツ星ファーム
- 価格: 711円/食（21食コース税込。7食927円・14食819円も確認）
  - 出典: https://mitsuboshifarm.jp/contents/?contents_id=mitsuboshi_plan（2026-08-27）
- 送料: 全国一律990円（税込）／北海道・沖縄・離島2,500円／14・21食は初回送料無料
  - 出典: 同上＋公式LP
- キャンペーン: 定期初回40%OFF（14食コース初回6,958円税込・送料無料・1食497円）
  - 出典: https://mitsuboshifarm.jp/lp/unrecog/13/campaign29/（2026-08-27）

### ウェルネスダイニング
- 価格: 751円/食（21食15,768円税込÷21。7食5,508円・14食10,854円も確認）
  - 出典: https://www.wellness-dining.com/kikubari/products/k110/（2026-08-27）
- 送料: お試し注文・お試し定期は送料無料。定期はずっと送料無料。北海道・沖縄は追加送料
  - 出典: 同上
- キャンペーン: お試し注文・初回送料無料／お試し定期8回すべて送料無料
  - 出典: 同上

### まごころケア食（公式ドメイン修正: magokoro-care.com → magokoro-care-shoku.com）
- 価格: 398円/食（2回目以降1食398円。初回14食2,660円=190円/食・66%OFF。21食お得便394円/食）
  - 出典: https://magokoro-care-shoku.com/（2026-08-27）
- 送料: 980円（税込）／沖縄県や離島は1,480円。全国宅配OK
  - 出典: https://magokoro-care-shoku.com/help/guide（2026-08-27）
- キャンペーン: 初回限定お得便（14食2,660円税込・1食190円・66%OFF）
  - 出典: https://magokoro-care-shoku.com/（2026-08-27）

### 健康直球便（derived → confirmed）
- 価格: 578円/食（カロリー・塩分調整食A/Bセット10食5,780円税込÷10。全5商品中最安を確認）
  - 出典: https://kenko-chokkyubin.com/（2026-08-27）※既存source_idを更新

### FIT FOOD HOME（公式ドメイン確定: store.tavenal.com）
- 送料: 都度購入990円（税込）／北海道550円・沖縄1,100円／定期購入は0円
  - 出典: https://store.tavenal.com/special-commercial（2026-08-27）

### ワタミの宅食ダイレクト（公式ドメイン修正: watami-takushoku.com → watami-takushoku.co.jp）
- 送料: お届け先（郵便番号）により異なり単一値化不可（確認済み事実として記録）
  - 出典: https://www.watami-takushoku.co.jp/（2026-08-27）
- キャンペーン: 2週間おためしセット（実質無料）・初回割引
  - 出典: https://www.watami-takushoku.co.jp/category/2week_trial（2026-08-27）

### nosh（キャンペーン整合性修正）
- キャンペーン: 初回購入時¥1,500 OFF（services.jsonのrequires_verificationをcampaigns.jsonと一致させFalseへ）
  - 出典: https://nosh.jp/package（2026-08-27）

---

## confirmed化しなかった項目と理由

| 項目 | 状態 | 理由 |
|---|---|---|
| nosh 価格 | pending維持 | 8/10/12食×通常/初回で複数価格があり、税込/税抜と食数の対応がJS描画のため完全確定できない。「最安492円/食」の宣伝コピーはプラン表と不一致のため不採用 |
| ワタミ 価格 | pending維持 | 通常価格は郵便番号入力により地域別で単一値化不可。「お試しセット399円/食」は公式サイトで直接確認できず不採用 |
| 食宅便 価格 | derived維持 | おまかせ7食690円/食が全コース（7/14/21/28食×5コース）中最安かを商品ページJSで完全確認できず |
| FIT FOOD HOME 価格 | pending維持 | アラカルト方式（税込653円〜2,891円/個）で単一の「1食あたり最安」が商品選択に依存し確定できない |
| ヨシケイ 価格 | uncollected維持 | 地域フランチャイズ×コース依存で単一値化不能（理由をnotesに明記） |
| 食宅便 キャンペーン | uncollected維持 | お試しプランの具体条件が確認できず（rv=Trueのためuncollected表示） |
| FIT FOOD HOME キャンペーン | uncollected維持 | お試しセットの存在は確認できるが具体価格・条件が未確定（rv=True） |
| ヨシケイ キャンペーン | uncollected維持 | 試食キャンペーンは地域別のため（rv=True） |

---

## URL修正一覧

| 対象 | 変更内容 |
|---|---|
| services.json ワタミ official_url | watami-takushoku.com → https://www.watami-takushoku.co.jp/ |
| services.json まごころ official_url | magokoro-care.com → https://magokoro-care-shoku.com/ |
| services.json FIT FOOD HOME official_url | （空）→ https://store.tavenal.com/ |
| affiliates.json ワタミ fallback | watami-takushoku.com → https://www.watami-takushoku.co.jp/ |
| affiliates.json まごころ fallback | magokoro-care.com → https://magokoro-care-shoku.com/ |
| affiliates.json FIT FOOD HOME fallback | （空）→ https://store.tavenal.com/ |
| campaigns.json ワタミ source_url | direct.watami-takushoku.com → https://www.watami-takushoku.co.jp/ |
| campaigns.json FIT FOOD HOME source_url | fitfoodhome.jp → https://store.tavenal.com/ |

※ 健康直球便のURL（kenko-chokkyubin.com）は既に正しいため変更なし。

---

## 残課題
- nosh/食宅便の価格は商品ページJSの完全な価格表取得ができればconfirmed化可能
- FIT FOOD HOME価格は「お試しセット」の具体価格が判明すればconfirmed化可能
- ワタミ通常価格は郵便番号を代表例入力して確認する方法が残る（要判断）

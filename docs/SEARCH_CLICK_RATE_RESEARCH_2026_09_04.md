# クリック数向上の方法 調査記録（2026-09-04）

作成日: 2026-09-04
作成者: Claude Code
範囲: **調査のみ（読み取り）**。Google公式ドキュメントの取得調査と、本番HTML・生成コードの読み取り確認。**コード/data/config変更・commit/push/deploy・GSC操作は行っていない**。
前提: `docs/GSC_STATUS_AND_STRATEGY_2026_09_04.md`（表示回数6・クリック0・平均順位38.2）の続き。

---

## 0. 先に結論

**クリック数 = 表示回数 × CTR × 掲載順位。現状（順位38.2＝4ページ目付近）ではクリックが起きる圏外のため、最大のレバーは「上位表示を増やす」ことであり、次が「検索結果での見え方（タイトル・スニペット・リッチリザルト）でCTRを上げる」。** Google公式はCTRを直接操作する方法は存在しないとし、順位はリクエストでは上がらない（質・被リンク・時間）と明言している。

- 今すぐできるコード/data変更として有望なのは、**露出中ページの`<title>`簡略化**と**Breadcrumb JSON-LD導入**（後者も表示はGoogle次第）。FAQリッチリザルトは**2026年5月に廃止済み**のため不採用。
- Product/Review（星）マークアップは**自己都合レビュー禁止等の制約があり、適用は慎重判断**（別途）。有料リンクはスパムポリシー違反で禁止。

## 1. 参照したGoogle公式一次情報
| 資料 | URL |
|---|---|
| Influencing your title links | https://developers.google.com/search/docs/appearance/title-link |
| SEO Starter Guide（Control your snippets） | https://developers.google.com/search/docs/fundamentals/seo-starter-guide |
| Get your website on Google | https://developers.google.com/search/docs/fundamentals/get-on-google |
| Ask Google to recrawl | https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl |
| Page indexing report | https://support.google.com/webmasters/answer/7440203 |
| Structured data 概要 | https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data |
| Product structured data | https://developers.google.com/search/docs/appearance/structured-data/product |
| Review snippet | https://developers.google.com/search/docs/appearance/structured-data/review-snippet |
| Breadcrumb | https://developers.google.com/search/docs/appearance/structured-data/breadcrumb |
| Sitelinks | https://developers.google.com/search/docs/appearance/sitelinks |
| FAQリッチリザルト廃止 | https://developers.google.com/search/updates#removing-faq-rich-result |

## 2. ルートA: 上位表示を増やす（クリック増の支配要因）
- 新サイトがクロールされインデックスされ順位が付き始めるまで**数週間〜**（公式）。表示6はこの進行中の正常な通過点。
- 順位は**indexリクエストでは上がらない**。決めるのはページの関連性・質・被リンク・サイトの信頼。
- 「他サイトからリンクされていない」ことは公式が**サイトを見つけられない最大の理由のひとつ**と明記。有料リンクは禁止。
- **実務**: 露出中の`/articles/chef-muten-tukuritoki-kuchikomi`・`/tool/diagnosis`を軸に、GSCでクエリ別順位の伸びを追い、記事層（独自価値のあるページ）を増やす。テンプレ量産ページ（services/comparisons）はGoogleが据え置くのも自然なので過度に追わない。

## 3. ルートB: 検索結果での見え方でCTRを上げる（公式の指針）

### 3.1 タイトルリンク（`<title>`）＝クリック判断の第一材料
- 説明的かつ簡潔に。「Home」等の曖昧語・キーワードスタッフィング・boilerplate（全ページ共通定型）を避ける
- ブランド名を入れる（後方）。長さ制限は無いが**端末幅で切り詰められる**
- Googleが自動で書き換えることがある（あくまで「指示」）
- **現状（本番確認）**: 記事は60字超で長く、モバイルで末尾が切られる可能性。クエリ語が先頭にある点は良い
  - 記事: `シェフの無添つくりおきの口コミ・評判を徹底検証！料金・送料・メニュー・「まずい？」まで【2026年8月】 | 宅食図鑑`
  - 診断: `宅配食 診断ツール｜自分に合うサービスを条件で探す | 宅食図鑑`（比較的良好）
- 構造: 全ページ `{title} | {SITE_NAME}`（`templates.py:1283`）→ **記事title側の冗長を減らすのが現実的**

### 3.2 スニペット（説明文）
- **スニペットはページ本文の実際の文章からGoogleが生成**。メタディスクリプションは採用されるときのみ
- → **検索クエリに直接答える文章をページ冒頭に置く**のが最も効く
- メタディスクリプションは「短く・そのページ固有・要点を含む」ものを
- 現状のmeta description（記事・診断とも）は質が良好。改善するなら「クエリ語＋具体的数字・分量」を先頭に

### 3.3 構造化データ（2026年時点で使えるものが限られる）
| 種類 | 扱い | このサイトへの示唆 |
|---|---|---|
| FAQPage | **廃止**（2026年5月公式削除） | **やらない** |
| Breadcrumb | 有効。URL行が置き換わり得る | **導入余地あり**（テンプレ1箇所） |
| Product snippet | 有効。購入できない編集レビューページ用 | 比較・口コミ記事で対象になり得る |
| Review snippet（星） | 自己都合レビュー禁止等の制約 | **適用は慎重判断**。安易な星マークアップは審査/スパムリスク |
| Article | ニュース系メイン | 優先しない |
| Sitelinks | 自動 | 若いサイトにはまだ出ない |

- リッチリザルトは**表示が保証されない**。導入後はRich Results Testで検証
- 現状はWebSite型JSON-LDのみ（`templates.py:1195`）

### 3.4 その他の表示要素
- URL: 拡張子なし正規URL化済み＝表示上も読みやすい（済）
- favicon: `/favicon.png` 実装済み（モバイル検索結果に表示）
- サイト名: `og:site_name`等で「宅食図鑑」表示（済）

## 4. このサイト固有の候補（→ `docs/CTR_IMPROVEMENT_PLAN_2026_09_04.md` で立案）
1. 露出中ページ（chef-muten記事）の`<title>`簡略化（クエリ一致を保ち冗長を削る）
2. Breadcrumb JSON-LDの導入（全ページ・テンプレ1箇所）
3. 記事冒頭段落の「クエリへの直接の答え」化（スニペット源の最適化）
4. GSCで「順位20位前後に到達したクエリ」を監視し、該当ページを逐次チューニング

## 5. やらないこと（判断メモ）
- FAQPage追加（廃止済み）
- 有料リンク（スパムポリシー違反）
- 同URLの過剰なindexリクエスト（再リクエストはクロールを早めない）
- Product/Reviewマークアップの無検証導入（自己都合レビュー禁止・affiliateサイトとしての審査リスク）

# GSC実データ監査＋検索流入ゼロ脱出の施策調査（2026-09-04）

作成日: 2026-09-04
作成者: Claude Code
範囲: **読み取り専用（A）＋外部調査（B）**。AはPlaywrightでログイン済みGoogle Search Console（アカウント: たな 2070abe@gmail.com）を直接閲覧し実データを取得した。**GSC上での設定変更・サイトマップ送信・インデックス登録リクエスト・「Test live URL」は一切実行していない**（step2の個別リクエスト実施前に記録として作成）。BはGoogle公式ドキュメントの取得調査のみ。コード/data/config変更・commit/push/deployは行っていない。
対象プロパティ: `https://ret4853.2070abe.workers.dev/`
前提: `docs/GSC_REDIRECT_ERROR_CAUSE_AUDIT_2026_08_31.md`（301化デプロイ済み）、`docs/GOOGLE_INDEX_REQUEST_LOG_2026_08_28.md`（追記2026-09-02）の続き。

---

## 0. 先に結論

**検索パフォーマンスが初めて「表示回数0」を脱出した（表示回数6、クリック0、平均掲載順位38.2）。** 表示ページ・クエリは既存のSEO仮説どおりで、**商標ロングテール（「シェフの無添つくりおき 口コミ」）と診断ページ・記事ページが最初の露出源**になっている。8/31の301化・sitemap再送信→9/2のGoogle再取得と時間的に整合する範囲で露出が発生し始めた。

- クリック0は「表示が無いから」ではなく「**掲載順位が平均38.2（4ページ目付近）で、クリックが発生する圏内（概ね1〜2ページ目）に入っていないから**」。新規サイトとして想定内。
- Pagesレポートの「Indexed 1 / Not indexed 32」は8/28時点の**古い集計**。ライブURL検査では**最低3ページ（`/`・`/tool/diagnosis`・記事）がindexed**を確認。
- 旧`.html`版のRedirect error 4件は301化デプロイ前のクロール残像で**再クロール待ち**。28件の「Discovered - currently not indexed」は**未クロール待ち**。いずれもエラーではなく時間待ち。

---

## 1. 検索パフォーマンス（期間: 3か月、GSC画面で直接確認、データは2026-09-01まで）

| 指標 | 値 | 前回（8/28時点） |
|---|---|---|
| 合計クリック数 | **0** | 0 |
| 合計表示回数 | **6** | **0** ← 初めて0以外 |
| 平均CTR | 0% | 0% |
| 平均掲載順位 | **38.2** | （順位なし） |

### 1.1 日別内訳
| 日 | 表示回数 |
|---|---|
| 2026-08-28 | 1 |
| 2026-08-29 | 0 |
| 2026-08-30 | 1 |
| 2026-08-31 | 2 |
| 2026-09-01 | 2 |

※9/2〜3はGSC集計ラグのため未反映の可能性（画面表示は「Last update: 数時間前」だがデータは9/1まで）。

### 1.2 クエリ別（表示されたもの）
| クエリ | クリック | 表示回数 |
|---|---|---|
| シェフの無添つくりおき 口コミ | 0 | 2 |
| site:workers.dev | 0 | 1 |

### 1.3 ページ別（表示されたもの）
| URL | クリック | 表示回数 |
|---|---|---|
| `/tool/diagnosis` | 0 | 3 |
| `/articles/chef-muten-tukuritoki-kuchikomi` | 0 | 3 |
| `/`（ルート） | 0 | 1 |

※クエリ別・ページ別の表示上の合計は総数6と±1〜2の差がある（GSCの表示上の集計特性）。数値は画面上の値をそのまま記録。

**解釈**: `docs/SEO_CONTENT_FINAL_KW_SERP_AUDIT_2026_08_26.md`で「個人サイトが実測SERP上位を取れる余地あり」と判定した商標ロングテールが、実際に最初の露出源になった。コンテンツ戦略の仮説が実データで支持された。

## 2. インデックス状況

### 2.1 Pagesレポート（※「Last update: 8/28/26」＝古い集計）
| 区分 | 件数 | 理由 |
|---|---|---|
| Indexed | **1** | – |
| Not indexed: Redirect error | **4** | 旧`.html`版URL（下表） |
| Not indexed: Discovered - currently not indexed | **28** | 発見済み・未クロール |

**Redirect error 4件（いずれも旧`.html`版・301化前のクロール）**:
| URL | 最終クロール |
|---|---|
| `/index.html` | 2026-08-29 |
| `/tool/diagnosis.html` | 2026-08-29 |
| `/ranking.html` | 2026-08-28 |
| `/articles/chef-muten-tukuritoki-kuchikomi.html` | 2026-08-28 |

Validation表示: Started（開始日 2026-09-01）。→ 8/31の301化デプロイ後にGoogleが追跡開始した状態。**次回クロールで解消される見込み**（`docs/GSC_REDIRECT_ERROR_CAUSE_AUDIT_2026_08_31.md` §7でライブテスト済み: 「URL is available to Google」）。

### 2.2 ライブURL検査（2026-09-04実施・読み取りのみ）
| URL | 結果 |
|---|---|
| `/articles/chef-muten-tukuritoki-kuchikomi` | ✅ **URL is on Google / Page is indexed** |
| `/tool/diagnosis`（正規URL） | ✅ **URL is on Google / Page is indexed** |
| `/tool/diagnosis.html`（旧） | ❌ Page is not indexed: **Redirect error**（最終クロール2026-08-29 = 301化前のまま。再クロール待ち） |

→ Pagesレポートの「Indexed 1」は古く、実態は**最低3正規URLがindexed**。Overviewの「HTTPS配信ページ数: 3」と一致。公式FAQにも「最近indexedされたページはPagesレポートに後から載る」とあり整合。

## 3. サイトマップ状況
| 項目 | 値 |
|---|---|
| URL | `/sitemap.xml` |
| Submitted | 2026-08-31 |
| **Last read** | **2026-09-02**（301化デプロイ後にGoogleが再取得済み） |
| Status | Success |
| Discovered pages | **35** |

## 4. エクスペリエンス
| 項目 | 値 |
|---|---|
| Core Web Vitals | モバイル・PCとも「データがありません」（フィールドデータ未蓄積） |
| HTTPS配信ページ数 | 3 |

---

## 5. 施策調査（B）: 検索流入ゼロから抜け出すために

### 5.1 参照したGoogle公式一次情報
| 資料 | URL |
|---|---|
| Get your website on Google | https://developers.google.com/search/docs/fundamentals/get-on-google |
| Ask Google to recrawl your URLs | https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl |
| Page indexing report（非インデックス理由） | https://support.google.com/webmasters/answer/7440203 |
| Site move（ドメイン移転） | https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes |

### 5.2 現状はGoogleの想定内（公式が明言する範囲）
- 「サイトが新しく、Googleがクロールする時間がまだ無い。**新サイトに気づくまで数週間かかりうる**」（get-on-google）
- 「クロールは**数日〜数週間**。インデックスは即時ではないし、**全ページがインデックスされる保証もない**」（ask-google-to-recrawl）
- 「**Discovered - currently not indexed** = 発見済みだが未クロール。Googleがクロールを後回しにした状態」（page-indexing-report）
- 個別リクエストは**同一URLへの再リクエストではクロールを早めない**。日次クォータも有限（ask-google-to-recrawl）

→ 28件の未クロール・現時点でindexed少数という状況は**異常ではなく、若いサイトの標準的な通過点**。表示回数が発生し始めた9/1時点で既に初期段階に入っている。

### 5.3 次に効くレバー（優先度順）
1. **時間 × コンテンツ追加の継続**: sitemapは9/2に自動再取得済み。新規記事の追加がGoogleの再取得→クロール予約を進める。記事5本・sitemap35ページはデータと整合。個別リクエストは新規・重要ページのみに限定（多用はクォータの無駄）。
2. **露出が出た記事ページを軸に順位向上**: 平均順位38.2は4ページ目付近。クリックが出る圏内（〜20位）へ上げるには、サイト内では**サービス詳細→記事への文脈リンク追加で記事ページにシグナルを集中**させる。
3. **被リンク**: 公式は「他サイトからリンクされていない」をサイトが見つけられない第1の理由に明記。**有料リンクはスパムポリシー違反**。現実的な獲得源は独自資産（無料診断ツール・独自データ記事）への自然リンク。短期で数は追わない。
4. **テンプレ量産ページを過度に追わない**: サービス詳細12・比較7は情報が似通うため「Discovered-not indexed」据え置きは自然な挙動。差別化された記事層に投資を集中（既存計画と一致）。
5. **ドメイン（中期的・今が最安）**: 現在は共有無料サブドメイン `ret4853.2070abe.workers.dev`。ブランド（宅食図鑑 / takushokuzukan.jp）がURLに現れず、クエリに「site:workers.dev」が出現＝Googleはホストを`workers.dev`配下として認識。**被リンク・評価シグナルが溜まる前＝今が移行コスト最小**。公式手順（全ページ301→新sitemap→Change of Address→リダイレクト最低1年維持）を把握済み。判断するなら露出本格化前が最適。
6. **測定リズム**: 毎日見ても変化は乏しい。**2〜4週間間隔**で①表示回数の増加（9/2以降分）②Pagesレポート更新（Indexed数）③旧`.html`Redirect error解消、を確認。

---

## 6. 次のアクション
- 本docは読み取り専用。GSC上の操作（例: `/services/chef-muten-tukuritoki` の個別インデックス登録リクエスト残1件）は実施時に別途記録する。
- 再確認時期の目安: 2026-09-07以降（sitemap再取得9/2→1〜2週間後の確認窓）。

---

## 7. 追記（2026-09-04）: 保留中リクエストの実行結果

本doc作成後、承認を得て`/services/chef-muten-tukuritoki`（正規URL）の個別「インデックス登録をリクエスト」を実行した。

- 検査結果: 未登録（**URL is unknown to Google**＝未クロール、最終クロールN/A）
- 実行結果: **リクエスト成功**（"Indexing requested"ダイアログ確認。リクエスト時にGSCがライブテストを自動実行→優先クロールキューへ追加）
- 詳細は`docs/GOOGLE_INDEX_REQUEST_LOG_2026_08_28.md` §6に記録。**これで既知の残タスクは全件完了**。
- 1〜2週間後（2026-09-07以降至近）に、本URLのクロール・indexed化と、§1の表示回数（9/2以降分）を再確認する。

# 宅食図鑑 無料公開ガイド（Cloudflare Pages / pages.dev）

作成日: 2026-08-26
目的: 独自ドメインなし・完全無料で本番公開し、ASP登録→流入→初回CVを最短で検証する。

---

## 1. 公開方針（決定事項）

- 独自ドメインは購入しない（takushokuzukan.jp も取得しない）
- Cloudflare Pages の無料プランを使用
- 公開URLは無料の `pages.dev` サブドメイン
- サイト名「宅食図鑑」は維持
- `site/` をCloudflare Pagesで静的ホスティング

## 2. Cloudflare Pages 無料プランの制限（2026年8月時点の公式情報）

| 項目 | 無料プラン | 本サイトの見込み |
|---|---|---|
| ビルド回数 | **500回/月** | 全く問題なし（週数回更新でも余裕） |
| ファイル数 | **20,000ファイル** | 現在14ファイル。1000ページ超でも余裕 |
| カスタムドメイン | 100個（無料で追加可だが今回は不使用） | 0個でOK |
| ビルドタイム | 20分/回でタイムアウト | 数秒で完了 |
| pages.dev サブドメイン | **無料で利用可能** | `takushokuzukan.pages.dev` を使用 |

出典: https://developers.cloudflare.com/pages/platform/limits/（2026-07-16更新を確認）

## 3. デプロイ方法（3択）

### 方法A: CloudflareネイティブのGitHub連携（推奨・最簡単・無料）

GitHub Actions不要。Cloudflareがリポジトリを直接監視し、pushのたびに自動ビルド・デプロイする。

**手順（1回だけ、約10分）:**

1. GitHubで新規リポジトリを作成（Publicが無料で簡単。PrivateでもPages連携は無料）
2. ローカルでリモート登録してpush:
   ```
   git remote add origin https://github.com/あなたのID/リポジトリ名.git
   git push -u origin main
   ```
3. Cloudflareに無料アカウント作成 → ダッシュボード → **Workers & Pages → Create → Pages → Connect to Git**
4. GitHub連携を許可 → 先ほどのリポジトリを選択
5. ビルド設定を入力:
   - **Framework preset**: （なし/Other）
   - **Build command**: `python tools/build.py`
   - **Build output directory**: `site`
   - 環境変数は不要（PythonはCloudflareのビルド環境に標準搭載）
6. 「Save and Deploy」
7. 完了後に発行されるURL: **`https://takushokuzukan.pages.dev`**（プロジェクト名がtakushokuzukanの場合）

以降、`git push` するだけで自動デプロイ。

### 方法B: Wrangler直接アップロード（Cloudflare連携不要・単発で手早く）

GitHubを使わず、ローカルから直接アップロードする方法。

1. Cloudflareに無料アカウント作成 → マイプロフィール → **APIトークン** → 「Cloudflare Pages: Edit」権限のトークンを作成
2. 環境変数を設定:
   ```
   setx CLOUDFLARE_API_TOKEN "作成したトークン"
   setx CLOUDFLARE_ACCOUNT_ID "アカウントID"
   ```
3. デプロイスクリプトを実行:
   ```
   .\deploy.ps1
   ```
   （内部で `python tools/build.py` → `npx wrangler pages deploy site --project-name=takushokuzukan` を実行）

### 方法C: GitHub Actions（`.github/workflows/deploy-cloudflare.yml`）

リポジトリのSettings → Secrets and variables → Actions に `CLOUDFLARE_API_TOKEN` と `CLOUDFLARE_ACCOUNT_ID` を設定すれば、pushのたびにGitHub Actionsからデプロイする。方法Aのほうがシンプルなため、方法Aを推奨。

## 4. 公開後の動作確認チェックリスト

公開URL（例: https://takushokuzukan.pages.dev）に対して以下を確認:

- [ ] トップページ `https://takushokuzukan.pages.dev/` → 200・タイトル表示
- [ ] 比較ページ `/comparisons/nosh-vs-mitsuboshi-farm.html`
- [ ] サービスページ `/services/nosh.html`
- [ ] 診断ツール `/tool/diagnosis.html` → JSが動作
- [ ] 法務ページ `/privacy.html` `/disclaimer.html` `/operator.html` `/contact.html` → 200
- [ ] `https://takushokuzukan.pages.dev/sitemap.xml` → XMLが返る
- [ ] `https://takushokuzukan.pages.dev/robots.txt` → 表示
- [ ] 存在しないURL（例 `/test.html`）→ カスタム404ページが表示
- [ ] HTTPS（`https://` で自動的に有効。無料）
- [ ] 各ページのcanonicalが `https://takushokuzukan.pages.dev/...` を指す

※内部リンク・外部リンクは本番ビルド前に監査済み（壊れた内部リンクなし、外部リンクはFIT FOOD HOMEのみ要確認扱い）。

## 4.5 法務ページ（ASP審査前の必須設定）

プライバシーポリシー・免責事項・運営者情報・お問い合わせページは実装済み（`/privacy.html` `/disclaimer.html` `/operator.html` `/contact.html`）。

**ASP審査前に必ず行うこと**: `config/site.json` の `operator` セクションに運営者名・メールアドレスを設定して再ビルドすること。

```json
{
  "name": "宅食図鑑",
  "url": "https://takushokuzukan.pages.dev",
  "operator": {
    "name": "あなたの名前（実名・ハンドル名）",
    "email": "お問い合わせ用メールアドレス",
    "note": "個人運営"
  }
}
```

未設定の間は「設定準備中です」と表示される。設定後に `python tools/build.py` で再生成する。

## 5. Google Search Console（無料）登録

公開URL確定後、Google Search Consoleに登録してインデックスを促進する。

1. https://search.google.com/search-console にアクセス
2. 「URLプレフィックス」で `https://takushokuzukan.pages.dev/` を登録
3. 所有権確認は「HTMLタグ」方式を選び、メタタグを取得
4. このメタタグを `tools/build.py` の `<head>` に組み込むか、`config/site.json` に `search_console_meta` を追加してビルド
5. 「サイトマップ」に `https://takushokuzukan.pages.dev/sitemap.xml` を送信

## 6. ASP登録と pages.dev URL の関係

### 調査結果の要点

**A8.net / afb / アクセストレードのいずれも、公式ヘルプで「pages.dev（無料サブドメイン）は登録不可」とは明記していない。** また「独自ドメインが必須」という明示的な公式ルールも確認できなかった。

各ASPのメディア審査は**人間によるコンテンツ審査**が主体であり、以下が判断基準になる（A8.net公式FAQ等で確認できる範囲）:

- サイトに実在する独自コンテンツがあるか
- プライバシーポリシー・運営者情報・問い合わせ手段があるか
- アダルト・出会い系等のNGジャンルでないか
- サイト名・URL・コンテンツの一貫性があるか

pages.devは「無料ブログ（WordPress.com・はてな等）」ではなく、**企業にも広く使われるプロフェッショナルな静的ホスティング**であるため、審査上は不利になりにくいと判断される。ただし**最終的な承認可否は各ASPの審査判断に依存する**ため、実際に登録して確認するのが唯一の確実な方法。

### 実践手順（推奨）

1. **A8.net**（無料登録）→ メディア登録でサイトURLに `https://takushokuzukan.pages.dev/` を入力して申請
   - 審査通過 → pages.devでOK（実証される）
   - 審査否認 → そのASPは独自ドメインが必要、と判断できる
2. **afb**（無料登録）→ 同様に申請
3. **アクセストレード**（無料登録）→ 同様に申請
4. 審査通過後に各ASPのプログラム提携（nosh・ワタミ・三ツ星ファーム等）を申請

### 独自ドメインが必要になる可能性のあるケース

- メディア審査で「ドメインの信頼性」を理由に否認された場合
- プログラム提携（広告主審査）で独自ドメインを要求された場合
- ※現時点でpages.devが原因で否認されると確定しているASPはない。実際に試して判断する。

### 注意

本調査ではASPのログイン後情報（正確な審査基準・報酬・承認条件）は確認できない。メディア登録・提携申請は実際の管理画面で行い、否認された場合はその理由を確認して対処すること。

---

## 7. 完全無料の確認

| 項目 | 費用 |
|---|---|
| Cloudflare Pages 無料プラン | 0円 |
| pages.dev サブドメイン | 0円 |
| GitHub（リポジトリ） | 0円 |
| Google Search Console | 0円 |
| ビルド・ホスティング | 0円（無料プランの範囲内） |
| 独自ドメイン | 購入しない |

課金が発生するのは「無料プランの制限を超えた場合」のみ（例: 500ビルド/月超過、有料プランへのアップグレード）。本サイトの規模では発生しない。

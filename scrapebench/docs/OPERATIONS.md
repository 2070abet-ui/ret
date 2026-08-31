# ScrapeBench 運用マニュアル（OPERATIONS.md）

公開URL: **https://scrapebench.2070abe.workers.dev**
デプロイ方式: Cloudflare Workers Static Assets（`wrangler.toml` + `src/worker.js`）

## データフロー

```
config/providers.json × config/scenarios.json
  → tools/bench.py（実測・SQLite保存・latest.json集計）
  → tools/build.py（静的HTML生成＋HTML検証）
  → npx wrangler deploy（Cloudflare Workers 公開）
```

- 生ログ: `data/benchmark.db`（SQLite・gitignore対象）
- 集計: `data/results/latest.json`（コミット対象・サイトビルドの入力）
- 生成物: `site/`（gitignore対象・デプロイ対象）

## 🛡️ APIクレジット保護ルール

各SaaS（Firecrawl, Apify等）のAPIクレジット消費を最小化するため、以下のルールを厳守すること。

1. **実計測スクリプト（tools/bench.py）の自動実行禁止**
   - UI/UX改修、テンプレート変更、ビルド（tools/build.py）、デプロイ作業等の日常開発において、実際のAPI計測スクリプトを自動実行しないこと。
   - テストや動作確認には、必ず既存の計測データ（data/results/latest.json または benchmark.db）を使用すること。

2. **実計測の実行タイミング**
   - 実際のAPIリクエストを伴う計測は、明示的に「実計測を実行してください」と指示があった場合のみ実行すること。

3. **実行前の想定消費確認**
   - 実計測の指示を受けた場合でも、実行前に「対象プロバイダー数 × シナリオ数 × リピート数 ＝ 合計想定クレジット数」を算出して提示し、確認を取ってから実行すること。

## 1. 実計測（APIキー運用）

### 1-1. APIキーを環境変数に設定

計測前に、計測したいプロバイダーのキーを設定する。**値はシークレット扱いとし、コミット・共有しないこと。**

| プロバイダー | 環境変数（config/providers.json の key_env） |
|---|---|
| Firecrawl | `FIRECRAWL_API_KEY` |
| Apify | `APIFY_API_TOKEN` ※（`APIFY_API_KEY` ではない点に注意） |
| ScrapingBee | `SCRAPINGBEE_API_KEY` |

PowerShell（そのセッションのみ有効）:

```powershell
$env:FIRECRAWL_API_KEY = "sk-..."
$env:APIFY_API_TOKEN = "apify_api_..."
$env:SCRAPINGBEE_API_KEY = "..."
```

永続化する場合（`setx` はターミナル再起動後に有効）:

```powershell
setx FIRECRAWL_API_KEY "sk-..."
```

### 1-2. 計測実行

```powershell
cd scrapebench
python tools/bench.py
```

- 全プロバイダー × 全シナリオ × repeat回を並列計測する。
- **`key_env` 未設定のプロバイダーは SKIP される**（残りは計測実行）。
- 結果は `data/benchmark.db` に追記され、最新セッションの集計が `data/results/latest.json` に出力される。

### 1-3. 計測対象の切り替え

- `config/providers.json` の `enabled` で計測対象を制御する（`false` は計測スキップ）。
- `httpbin-probe` はキー不要の**パイプライン検証用プローブ**であり、実プロバイダーではない。実運用では `enabled=false` のままにする。
- 新規プロバイダー追加時は、`config/providers.json` への追記に加えて、`tools/bench.py` の `CALLERS` にアダプタ関数を追加する必要がある。

## 2. サイト更新（ビルド）

```powershell
cd scrapebench
python tools/build.py
```

- `scrapebench/site/` に静的HTML一式（9ページ + sitemap.xml + robots.txt）を生成する。
- 生成時に**必須SEOメタタグ・タグバランスの検証**を自動実行。エラーがあればビルドが失敗する。

## 3. 本番デプロイ

```powershell
cd scrapebench
npx wrangler deploy --dry-run   # 任意: 設定・アセット検証のみ
npx wrangler deploy             # 本番反映
```

- ビルド→デプロイをまとめて実行する場合:

```powershell
cd scrapebench
python tools/build.py && npx wrangler deploy
```

- デプロイ後に公開URLで確認:

```powershell
curl -s https://scrapebench.2070abe.workers.dev/benchmarks/
```

## 4. 定期更新のサイクル（推奨）

計測は低頻度（週1回程度）かつ計測目的に限定する（利用規約・`robots.txt` に配慮）。

```powershell
cd scrapebench
python tools/bench.py            # 1. 実計測
python tools/build.py            # 2. サイト生成
npx wrangler deploy              # 3. 本番反映
git add data/results/latest.json # 4. 集計データをコミット（再現性のため）
git commit -m "bench(scrapebench): update benchmark results"
```

## 5. 備考

- Windowsコンソールで日本語が文字化けして見える場合は**表示のみの問題**（ファイル自体はUTF-8）。`chcp 65001` で改善する。
- `data/benchmark.db`・`site/`・`.wrangler/`・`__pycache__/` は gitignore 対象（コミットしない）。
- `data/results/latest.json` はコミット対象（サイトビルドの入力データのため）。
- サイトの canonical / sitemap / robots は `config/site.json` の `url` から自動生成される。URL変更時は同ファイルを更新して再ビルド・再デプロイすること。
# Cloudflare Pages へ直接アップロード（Windows PowerShell 用）
# 事前準備:
#   1. npm install -g wrangler  または  npx を使う
#   2. Cloudflareダッシュボード → マイプロフィール → APIトークン → 「Cloudflare Pages: Edit」権限のトークンを作成
#   3. このシェルを開く前に環境変数を設定:
#        setx CLOUDFLARE_API_TOKEN "作成したトークン"
#        setx CLOUDFLARE_ACCOUNT_ID "CloudflareアカウントID"
#      （設定後はターミナルを開き直すこと）
# 実行:
#   .\deploy.ps1

$ErrorActionPreference = "Stop"

Write-Host "==> サイトをビルド中..." -ForegroundColor Cyan
python tools\build.py
if ($LASTEXITCODE -ne 0) { throw "ビルドに失敗しました" }

if (-not $env:CLOUDFLARE_API_TOKEN) {
    Write-Host "エラー: CLOUDFLARE_API_TOKEN が設定されていません。" -ForegroundColor Red
    Write-Host "Cloudflareダッシュボード → マイプロフィール → APIトークン で作成し、setx CLOUDFLARE_API_TOKEN \"...\" を実行してください。" -ForegroundColor Yellow
    exit 1
}

Write-Host "==> Cloudflare Workers へデプロイ中（Static Assets方式）..." -ForegroundColor Cyan
npx wrangler deploy

Write-Host "==> 完了。公開URLを確認してください（通常は https://takushokuzukan.workers.dev）" -ForegroundColor Green

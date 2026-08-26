#!/usr/bin/env python3
"""
宅配食アフィリエイトサイト 静的サイト生成ツール（エントリポイント）
- data/*.json（構造化DB）からHTMLを生成する
- 依存ライブラリなし（Python標準ライブラリのみ）
- 使い方: python tools/build.py

実体は tools/sitegen/ 配下（data.py=データ読み込み / templates.py=ページ描画 / generators.py=生成の司令塔）。
生成先: site/
"""
from sitegen import generators

if __name__ == "__main__":
    generators.main()

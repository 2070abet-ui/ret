#!/usr/bin/env python3
"""
ScrapeBench 静的サイト生成ツール（エントリポイント）
- config/*.json + data/results/latest.json から HTML を生成する。
- 依存ライブラリなし（Python標準ライブラリのみ）。
- 使い方: python scrapebench/tools/build.py
生成先: scrapebench/site/
実体は tools/sitegen/ 配下（data.py=データ読み込み / templates.py=ページ描画 / generators.py=生成の司令塔 / validate.py=HTML検証）。
"""
from sitegen import generators

if __name__ == "__main__":
    generators.main()
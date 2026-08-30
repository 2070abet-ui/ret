"""
ScrapeBench 静的サイト生成 - データ読み込み層
config/*.json と data/results/latest.json（無ければ初期デフォルト）を読み込み、
描画用のデータ構造を作る。ページ描画は templates.py、生成の司令塔は generators.py。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "site"

# デフォルト値（config/site.json が読めない/未設定のときのフォールバック）
SITE_NAME = "ScrapeBench"
SITE_URL = "https://scrapebench.workers.dev"
SITE_DESC = "Real-world benchmarks for LLM-ready web scraping APIs. Success rate, latency, response size, and output quality measured across top providers."
LANG = "en"
OPERATOR = {"name": "", "email": "", "note": "Personal operator"}
GSC_META = ""

_site_config_path = CONFIG_DIR / "site.json"
if _site_config_path.exists():
    try:
        _cfg = json.loads(_site_config_path.read_text(encoding="utf-8"))
        SITE_NAME = _cfg.get("name", SITE_NAME)
        SITE_URL = _cfg.get("url", SITE_URL).rstrip("/")
        SITE_DESC = _cfg.get("description", SITE_DESC)
        LANG = _cfg.get("lang", LANG)
        OPERATOR = _cfg.get("operator", OPERATOR)
        GSC_META = _cfg.get("search_console_meta", "")
    except (json.JSONDecodeError, OSError):
        pass


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def load_providers():
    return load_json(CONFIG_DIR / "providers.json", {}).get("providers", [])


def load_scenarios():
    return load_json(CONFIG_DIR / "scenarios.json", {}).get("scenarios", [])


_DEFAULT_RESULTS = {
    "generated_at": "",
    "session_id": "",
    "summary": {"runs": 0, "succeeded": 0, "providers_measured": 0,
                "scenarios_measured": 0, "overall_success_rate": None},
    "results": [],
    "providers": [],
}


def load_results():
    """data/results/latest.json を読み込む。無ければ初期デフォルト（空）を返す。"""
    return load_json(DATA_DIR / "results" / "latest.json", _DEFAULT_RESULTS)


def load_benchmark_data():
    """描画用に providers / scenarios / results をまとめた構造を返す。
    cells は provider x scenario の組み合わせに result（無ければ None）を付けた一覧。"""
    providers = load_providers()
    scenarios = load_scenarios()
    results = load_results()
    result_map = {(r.get("provider_id"), r.get("scenario_id")): r for r in results.get("results", [])}
    provider_stats = {s.get("provider_id"): s for s in results.get("providers", [])}
    cells = []
    for p in providers:
        for s in scenarios:
            cells.append({
                "provider": p,
                "scenario": s,
                "result": result_map.get((p.get("id"), s.get("id"))),
            })
    return {
        "site": {"name": SITE_NAME, "url": SITE_URL, "desc": SITE_DESC, "lang": LANG},
        "providers": providers,
        "scenarios": scenarios,
        "summary": results.get("summary", {}),
        "generated_at": results.get("generated_at", ""),
        "cells": cells,
        "provider_stats": provider_stats,
        "has_data": bool(results.get("results")),
    }
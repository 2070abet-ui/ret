#!/usr/bin/env python3
"""
ScrapeBench 計測エンジン
- config/providers.json x config/scenarios.json を読み込み、各 Scraping API を実測する。
- 計測項目: 遅延時間（TTFB / 全体）、HTTPステータス、レスポンスサイズ、期待キーワード一致率。
- 生ログ: data/benchmark.db（SQLite runs テーブル）へ保存。
- 集計: 最新セッション分を data/results/latest.json へエクスポート。
- Python標準ライブラリのみ使用。APIキーは環境変数（providers.json の key_env）で渡す。
使い方: python scrapebench/tools/bench.py
"""
import json
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "benchmark.db"
RESULTS_PATH = DATA_DIR / "results" / "latest.json"

TIMEOUT = 60            # 1リクエストあたりのタイムアウト（秒）
POLITENESS_SLEEP = 0.5  # 同一プロバイダーへの連続呼び出し間隔（秒）

UA = "ScrapeBench/0.1 (+benchmark; low-frequency; purpose-limited measurement)"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _safe_decode(body):
    return body.decode("utf-8", errors="replace")


def _do_request(req):
    """urlopen を実行し (status, body, ttfb_ms, latency_ms) を返す。
    urlopen が返った時点（=ヘッダ受信完了）を TTFB とみなす。
    HTTP 4xx/5xx は例外にせず (status, body, None, None) として返す（ネットワーク異常は伝播）。"""
    t0 = time.perf_counter()
    try:
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        t_headers = time.perf_counter()
        body = resp.read()
        t_done = time.perf_counter()
        resp.close()
        return resp.status, body, (t_headers - t0) * 1000.0, (t_done - t0) * 1000.0
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, body, None, None


# ---------- プロバイダー別アダプタ ----------

def call_firecrawl(provider, scenario, api_key):
    api = provider["api"]
    payload = json.dumps({"url": scenario["target_url"], "formats": ["markdown"]}).encode("utf-8")
    req = urllib.request.Request(
        api["base_url"].rstrip("/") + "/scrape",
        data=payload, method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": UA})
    status, body, ttfb, lat = _do_request(req)
    text = _safe_decode(body)
    output = text
    try:
        output = (json.loads(text).get("data") or {}).get("markdown") or text
    except (json.JSONDecodeError, AttributeError):
        pass
    return {"http_status": status, "response_size_bytes": len(body), "output_text": output,
            "ttfb_ms": ttfb, "latency_ms": lat}


def call_apify(provider, scenario, api_key):
    api = provider["api"]
    url = api["base_url"].rstrip("/") + "/acts/apify~website-content-crawler/run-sync-get-dataset-items"
    url += "?" + urllib.parse.urlencode({"token": api_key})
    payload = json.dumps({"url": scenario["target_url"], "outputFormat": "markdown"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    status, body, ttfb, lat = _do_request(req)
    text = _safe_decode(body)
    output = text
    try:
        items = json.loads(text)
        if isinstance(items, list) and items:
            output = items[0].get("markdown") or items[0].get("text") or text
    except (json.JSONDecodeError, AttributeError):
        pass
    return {"http_status": status, "response_size_bytes": len(body), "output_text": output,
            "ttfb_ms": ttfb, "latency_ms": lat}


def call_scrapingbee(provider, scenario, api_key):
    api = provider["api"]
    query = urllib.parse.urlencode({"api_key": api_key, "url": scenario["target_url"], "render_js": "true"})
    req = urllib.request.Request(api["base_url"].rstrip("/") + "/?" + query,
                                 headers={"User-Agent": UA})
    status, body, ttfb, lat = _do_request(req)
    return {"http_status": status, "response_size_bytes": len(body), "output_text": _safe_decode(body),
            "ttfb_ms": ttfb, "latency_ms": lat}


def call_httpbin(provider, scenario, api_key):
    """キー不要のパイプライン検証用プローブ。
    target_url（httpbin.org 等の公開テストURL）へ直接 GET し、HTMLを返す。
    実プロバイダーの代替ではなく、計測パイプライン（実HTTP→SQLite→集計→サイト）全体の動作確認を目的とする。"""
    req = urllib.request.Request(scenario["target_url"], headers={"User-Agent": UA})
    status, body, ttfb, lat = _do_request(req)
    return {"http_status": status, "response_size_bytes": len(body), "output_text": _safe_decode(body),
            "ttfb_ms": ttfb, "latency_ms": lat}


CALLERS = {
    "firecrawl": call_firecrawl,
    "apify": call_apify,
    "scrapingbee": call_scrapingbee,
    "httpbin-probe": call_httpbin,
}


# ---------- SQLite ----------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            scenario_id TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            success INTEGER NOT NULL,
            http_status INTEGER,
            latency_ms INTEGER,
            ttfb_ms INTEGER,
            response_size_bytes INTEGER,
            output_chars INTEGER,
            keyword_match_count INTEGER,
            keyword_total INTEGER,
            match_ratio REAL,
            error TEXT,
            meta TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_session ON runs(session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_provider ON runs(provider_id)")
    conn.commit()
    return conn


def insert_runs(conn, runs):
    conn.executemany("""
        INSERT INTO runs (session_id, provider_id, scenario_id, started_at, completed_at,
                          success, http_status, latency_ms, ttfb_ms, response_size_bytes,
                          output_chars, keyword_match_count, keyword_total, match_ratio, error, meta)
        VALUES (:session_id, :provider_id, :scenario_id, :started_at, :completed_at,
                :success, :http_status, :latency_ms, :ttfb_ms, :response_size_bytes,
                :output_chars, :keyword_match_count, :keyword_total, :match_ratio, :error, :meta)
    """, runs)
    conn.commit()


# ---------- 計測 ----------

def run_provider(provider, scenarios, session_id):
    key_env = provider.get("key_env", "")
    api_key = os.environ.get(key_env, "") if key_env else ""
    if key_env and not api_key:
        print(f"  [SKIP] {provider['id']}: 環境変数 {key_env} が未設定のため計測をスキップ")
        return []
    caller = CALLERS.get(provider["id"])
    if not caller:
        print(f"  [SKIP] {provider['id']}: 未対応のプロバイダーアダプタ")
        return []
    runs = []
    for scenario in scenarios:
        sid = scenario.get("id", "?")
        repeat = int(scenario.get("repeat", 5))
        keywords = scenario.get("expect_contains", [])
        print(f"  [RUN ] {provider['id']} x {sid} ({repeat}回)")
        for _ in range(repeat):
            started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            row = {
                "session_id": session_id, "provider_id": provider["id"], "scenario_id": sid,
                "started_at": started_at, "completed_at": None,
                "success": 0, "http_status": None, "latency_ms": None, "ttfb_ms": None,
                "response_size_bytes": None, "output_chars": None,
                "keyword_match_count": 0, "keyword_total": len(keywords),
                "match_ratio": None, "error": None,
                "meta": json.dumps({"provider": provider["id"], "scenario": sid,
                                    "target_url": scenario.get("target_url", "")}),
            }
            try:
                result = caller(provider, scenario, api_key)
            except Exception as e:
                row["error"] = str(e)
                row["completed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                runs.append(row)
                print(f"      [ERR ] {provider['id']}x{sid}: {e}")
                time.sleep(POLITENESS_SLEEP)
                continue
            status = result["http_status"]
            success = 1 if status is not None and 200 <= status < 400 else 0
            output = result["output_text"]
            matched = sum(1 for kw in keywords if kw in output)
            total = len(keywords)
            row.update({
                "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "success": success, "http_status": status,
                "latency_ms": int(round(result["latency_ms"])) if result["latency_ms"] is not None else None,
                "ttfb_ms": int(round(result["ttfb_ms"])) if result["ttfb_ms"] is not None else None,
                "response_size_bytes": result["response_size_bytes"],
                "output_chars": len(output),
                "keyword_match_count": matched, "keyword_total": total,
                "match_ratio": (matched / total) if total else None,
                "error": None if success else f"http_status={status}",
            })
            runs.append(row)
            print(f"      [OK  ] status={status} latency={row['latency_ms']}ms match={matched}/{total}")
            time.sleep(POLITENESS_SLEEP)
    return runs


# ---------- 集計 ----------

def _pct(series):
    return (sum(series) / len(series)) if series else None


def _percentile(values, p):
    if not values:
        return None
    vs = sorted(values)
    k = (len(vs) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(vs) - 1)
    return vs[lo] if lo == hi else vs[lo] + (vs[hi] - vs[lo]) * (k - lo)


def aggregate_session(conn, session_id):
    rows = conn.execute(
        "SELECT * FROM runs WHERE session_id=? ORDER BY provider_id, scenario_id",
        (session_id,)).fetchall()
    cols = [d[0] for d in conn.execute("SELECT * FROM runs LIMIT 1").description]
    records = [dict(zip(cols, r)) for r in rows]

    by_key = {}
    for rec in records:
        by_key.setdefault((rec["provider_id"], rec["scenario_id"]), []).append(rec)

    results = []
    for (pid, sid), recs in by_key.items():
        lat = [r["latency_ms"] for r in recs if r["latency_ms"] is not None]
        ttfb = [r["ttfb_ms"] for r in recs if r["ttfb_ms"] is not None]
        sizes = [r["response_size_bytes"] for r in recs if r["response_size_bytes"] is not None]
        chars = [r["output_chars"] for r in recs if r["output_chars"] is not None]
        ratios = [r["match_ratio"] for r in recs if r["match_ratio"] is not None]
        succ = [r["success"] for r in recs]
        results.append({
            "provider_id": pid, "scenario_id": sid,
            "runs": len(recs),
            "success_rate": _pct(succ),
            "latency_p50_ms": _percentile(lat, 0.50),
            "latency_p95_ms": _percentile(lat, 0.95),
            "ttfb_p50_ms": _percentile(ttfb, 0.50),
            "avg_response_size_bytes": round(sum(sizes) / len(sizes)) if sizes else None,
            "avg_output_chars": round(sum(chars) / len(chars)) if chars else None,
            "avg_match_ratio": _pct(ratios),
            "errors": sum(1 for r in recs if not r["success"]),
            "cost_estimate_usd": None,  # 実効コスト算出は価格情報の統合後に実装予定
        })

    provider_rollup = {}
    for (pid, _sid), recs in by_key.items():
        provider_rollup.setdefault(pid, []).extend(recs)
    providers = []
    for pid, recs in provider_rollup.items():
        lat = [r["latency_ms"] for r in recs if r["latency_ms"] is not None]
        succ = [r["success"] for r in recs]
        ratios = [r["match_ratio"] for r in recs if r["match_ratio"] is not None]
        providers.append({
            "provider_id": pid,
            "runs": len(recs),
            "success_rate": _pct(succ),
            "latency_p50_ms": _percentile(lat, 0.50),
            "avg_match_ratio": _pct(ratios),
            "errors": sum(1 for r in recs if not r["success"]),
        })

    summary = {
        "runs": len(records),
        "succeeded": sum(1 for r in records if r["success"]),
        "providers_measured": len(provider_rollup),
        "scenarios_measured": len(by_key),
        "overall_success_rate": _pct([r["success"] for r in records]),
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session_id": session_id,
        "summary": summary,
        "results": results,
        "providers": providers,
    }


def export_results(payload):
    (DATA_DIR / "results").mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"集計出力: {RESULTS_PATH}")


def main():
    providers = [p for p in load_json(CONFIG_DIR / "providers.json")["providers"] if p.get("enabled", True)]
    scenarios = [s for s in load_json(CONFIG_DIR / "scenarios.json")["scenarios"] if s.get("enabled", True)]
    if not providers or not scenarios:
        print("providers または scenarios が空です")
        return 1

    session_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"=== ScrapeBench 計測 ({session_id}) ===")

    conn = init_db()
    all_runs = []
    with ThreadPoolExecutor(max_workers=min(len(providers), 4)) as ex:
        futs = [ex.submit(run_provider, p, scenarios, session_id) for p in providers]
        for fut in as_completed(futs):
            try:
                all_runs.extend(fut.result())
            except Exception as e:
                print(f"  [ERROR] プロバイダー実行失敗: {e}")

    insert_runs(conn, all_runs)
    if all_runs:
        export_results(aggregate_session(conn, session_id))
    else:
        print("有効な計測がありませんでした（latest.json は更新しません）")
    conn.close()

    print(f"\n=== 結果: 計測 {len(all_runs)} 行 / DB: {DB_PATH} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
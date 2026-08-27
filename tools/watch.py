#!/usr/bin/env python3
"""
宅配食アフィリエイト 定期監視ツール
- 公式サイトの価格・キャンペーン変更を検知する
- スナップショットを data/snapshots/ に保存し、前回との差分を報告する
- 使い方: python tools/watch.py  （または --dry-run）

注意: スクレイピングはサイトの利用規約を確認のうえ、低頻度（週1回程度）かつ
      ページの転載ではなく「変更検知」目的に限定すること。
"""
import hashlib
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
SNAP_DIR = ROOT / "data" / "snapshots"
HISTORY_FILE = SNAP_DIR / "history.json"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

# 価格・キャンペーンに関係する数字パターンの抽出用
PRICE_PATTERNS = [
    r"[0-9][0-9,]*\s*円",
    r"[0-9][0-9,]*\s*円/食",
    r"初回[^\s。]{0,30}",
    r"送料[^\s。]{0,20}",
    r"キャンペーン[^\s。]{0,40}",
    r"お試し[^\s。]{0,40}",
]

# 監視ターゲットID → サービスID（watchlist.jsonのtarget idからservices.jsonのpricingを引くため）
TARGET_SERVICE_MAP = {
    "nosh-official": "nosh",
    "watami-official": "watami-takushoku",
    "mitsuboshi-official": "mitsuboshi-farm",
    "wellness-official": "wellness-dining",
    "shokutakubin-official": "shokutakubin",
    "fitfood-official": "fit-food-home",
    "magokoro-official": "magokoro-care",
    "chef-muten-tukuritoki-official": "chef-muten-tukuritoki",
    "syokurakuzen-official": "syokurakuzen",
    "yoshikei-official": "yoshikei",
    "kenko-chokkyokubin-official": "kenko-chokkyokubin",
}


def load_pricing_map():
    """services.jsonから service_id -> pricing のマップを構築する。
    watch.pyが価格ポイント単位（basis/meal_count/id）で監視できるようにするための土台。
    JS描画などで取得不能な問題そのものはここでは解決しない（推測で埋めない）。"""
    path = ROOT / "data" / "services.json"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return {s["id"]: s.get("pricing") for s in data.get("services", []) if s.get("pricing")}


def price_point_signals(pricing):
    """pricingの全価格ポイントから監視対象の価格シグナル文字列（例: '612円'）を抽出する。
    値を持たないポイント（regional=true等）は除外する。"""
    signals = set()
    if not pricing:
        return signals
    for p in pricing.get("price_points", []):
        vals = [p.get("price_per_meal_yen"), p.get("min_per_meal_yen"),
                p.get("max_per_meal_yen"), p.get("total_yen")]
        for v in vals:
            if v is not None:
                signals.add(f"{v:,}円")
                signals.add(str(v))
    return signals


def missing_price_points(pricing, current_signals):
    """現在取得したページのシグナルに含まれていない（＝変わった可能性が高い）価格ポイントを
    価格ポイントidで返す。JS描画でそもそも数値が取得できない場合は全件ヒットしうるため、
    あくまで「変化の候補」として報告する（断定はしない）。"""
    missing = []
    if not pricing:
        return missing
    for p in pricing.get("price_points", []):
        vals = [p.get("price_per_meal_yen"), p.get("min_per_meal_yen"),
                p.get("max_per_meal_yen"), p.get("total_yen")]
        if not any(v is not None for v in vals):
            continue  # 値を持たないポイントは監視対象外
        present = any(v is not None and (f"{v:,}円" in current_signals or str(v) in current_signals) for v in vals)
        if not present:
            missing.append(p.get("id"))
    return missing


def load_watchlist():
    with open(CONFIG_DIR / "watchlist.json", encoding="utf-8") as f:
        return json.load(f)["targets"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()
        enc = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(enc, errors="replace")


def normalize(text):
    """本文抽出 + 正規化（ハッシュ比較のための前処理）"""
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_signals(text):
    """価格・キャンペーンに関するシグナルを抽出して返す"""
    signals = set()
    for pat in PRICE_PATTERNS:
        for m in re.findall(pat, text):
            s = m.strip()
            if len(s) <= 2:
                continue
            signals.add(s)
    return sorted(signals)


def main():
    dry_run = "--dry-run" in sys.argv
    targets = load_watchlist()
    SNAP_DIR.mkdir(parents=True, exist_ok=True)

    # Phase4: services.jsonのpricingを読み込み、監視対象ごとに価格ポイント単位で扱えるようにする
    pricing_map = load_pricing_map()

    history = {}
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, encoding="utf-8") as f:
            history = json.load(f)

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    changed = []
    errors = []

    print(f"=== 宅配食 定期監視 ({now_iso}) ===")
    for t in targets:
        if t.get("disabled") or not t.get("url"):
            continue
        tid = t["id"]
        url = t["url"]
        try:
            raw = fetch(url)
        except Exception as e:
            msg = f"  [ERROR] {tid} ({url}): {e}"
            print(msg)
            errors.append({"id": tid, "url": url, "error": str(e), "checked_at": now_iso})
            continue

        norm = normalize(raw)
        digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]
        signals = extract_signals(norm)
        prev = history.get(tid, {})

        # この監視対象に対応するpricing（価格ポイント単位の監視情報）
        svc_id = TARGET_SERVICE_MAP.get(tid, "")
        pricing = pricing_map.get(svc_id)
        pp_expected = price_point_signals(pricing)
        pp_missing = missing_price_points(pricing, set(signals)) if pricing else []

        status = "UNCHANGED"
        if not prev:
            status = "NEW"
        elif prev.get("digest") != digest:
            status = "CHANGED"

        if status == "CHANGED":
            # 変化したシグナルを報告
            prev_signals = set(prev.get("signals", []))
            new_signals = [s for s in signals if s not in prev_signals]
            removed = [s for s in prev_signals if s not in signals]
            print(f"  [CHANGED] {tid} ({url})")
            if new_signals:
                print(f"    追加されたシグナル: {new_signals[:10]}")
            if removed:
                print(f"    消えたシグナル: {removed[:10]}")
            if pp_missing:
                print(f"    価格ポイントの値が検出できず（価格変更またはJS取得不能の候補）: {pp_missing[:10]}")
            # 既知の価格ポイントに無い新しい価格シグナル（新価格の候補として報告のみ・断定しない）
            unknown_new = [s for s in new_signals if "円" in s and s not in pp_expected]
            if unknown_new:
                print(f"    既知の価格ポイントに無い新しい価格シグナル候補: {unknown_new[:10]}")
            changed.append({"id": tid, "url": url, "new_signals": new_signals[:20], "removed": removed[:20],
                            "price_points_missing": pp_missing[:20], "checked_at": now_iso})
        elif status == "NEW":
            print(f"  [NEW] {tid} ({url}) - 初回取得: シグナル {len(signals)}件")
            if pp_missing:
                print(f"    価格ポイントの値が検出できず（JS取得不能の可能性）: {pp_missing[:10]}")
            changed.append({"id": tid, "url": url, "new_signals": signals[:20], "removed": [],
                            "price_points_missing": pp_missing[:20], "checked_at": now_iso})
        else:
            print(f"  [OK] {tid} - 変更なし")

        history[tid] = {
            "digest": digest,
            "signals": signals[:50],
            "last_checked": now_iso,
            "status": status,
        }

        # サイト負荷を避けるための間隔
        time.sleep(2)

    if not dry_run:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"\n=== 結果: 変更 {len([c for c in changed if c['id']])} 件, エラー {len(errors)} 件 ===")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

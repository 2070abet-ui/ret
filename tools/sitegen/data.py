"""
宅食図鑑 静的サイト生成 - データ読み込み層
data/*.json・config/*.json の読み込みと、サイト全体設定（SITE_NAME/SITE_URL等）の解決のみを担当する。
ページ描画ロジックは templates.py、生成の司令塔は generators.py。
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"
OUT_DIR = ROOT / "site"

# サイト名・URLは config/site.json で管理する（Cloudflare Workers Static Assets 無料公開のため）
SITE_NAME = "宅食図鑑"
SITE_DESC = "宅配食・宅配弁当サービスの料金・初回キャンペーン情報を公式確認データで比較。最新のキャンペーン情報を毎週更新。"
_DEFAULT_URL = "https://takushokuzukan.pages.dev"
_site_config_path = CONFIG_DIR / "site.json"
SITE_URL = os.environ.get("SITE_URL", _DEFAULT_URL)
GSC_META = ""  # Google Search Console 所有権確認メタタグ
GA4_MEASUREMENT_ID = ""  # GA4測定ID（config/site.jsonで未設定の間はGA4タグ自体を出力しない）
GTM_CONTAINER_ID = ""  # Google Tag ManagerコンテナID（config/site.jsonで未設定の間はGTMスニペット自体を出力しない）
OPERATOR = {"name": "", "email": "", "note": "個人運営"}
if _site_config_path.exists():
    try:
        _site_config = json.loads(_site_config_path.read_text(encoding="utf-8"))
        SITE_URL = _site_config.get("url", SITE_URL)
        SITE_NAME = _site_config.get("name", SITE_NAME)
        GSC_META = _site_config.get("search_console_meta", "")
        GA4_MEASUREMENT_ID = _site_config.get("ga4_measurement_id", "")
        GTM_CONTAINER_ID = _site_config.get("gtm_container_id", "")
        OPERATOR = _site_config.get("operator", OPERATOR)
    except (json.JSONDecodeError, OSError):
        pass


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _compute_last_verified_date():
    """ページ単位の「最終更新」表示・sitemapのlastmodに使う日付。
    services/campaigns/shipping/sources各ファイルのupdated_at（YYYY-MM-DD文字列、
    辞書式比較がそのまま日付順になる）のうち最大値を返す。新規データフィールドの追加はしない。
    PHASE3_IMPLEMENTATION_PLAN.md 1.4節。"""
    dates = []
    for fname in ("services.json", "campaigns.json", "shipping.json", "sources.json"):
        try:
            d = load_json(DATA_DIR / fname)
        except (json.JSONDecodeError, OSError):
            continue
        ua = d.get("updated_at")
        if ua:
            dates.append(ua)
    return max(dates) if dates else ""


LAST_VERIFIED_DATE = _compute_last_verified_date()


def load_data():
    services = load_json(DATA_DIR / "services.json")["services"]
    campaigns = load_json(DATA_DIR / "campaigns.json")["campaigns"]
    shipping = load_json(DATA_DIR / "shipping.json")["shipping_rules"]
    sources = load_json(DATA_DIR / "sources.json")["sources"]
    aff_links = load_json(CONFIG_DIR / "affiliates.json")["affiliate_links"]
    return services, campaigns, shipping, sources, aff_links


def load_comparison_pairs():
    """比較ページのペア設定。従来 build.py にハードコードされていたリストを
    config/comparisons.json へ外出ししたもの。中身（ペアの組み合わせ）は変更していない。"""
    path = CONFIG_DIR / "comparisons.json"
    data = load_json(path)
    return [(p["a"], p["b"]) for p in data.get("pairs", [])]

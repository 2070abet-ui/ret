"""
宅食図鑑 静的サイト生成 - ページ描画層
data.py が読み込んだデータを受け取り、HTML文字列を組み立てる。
Batch1では既存ページの本文・タイトル・canonical・価格・キャンペーン内容は一切変更していない。
追加したのは共通ヘッダーへのOGP/favicon/基本JSON-LD、モバイル用テーブルCSSのみ。
"""
import base64
import json

from sitegen.data import SITE_NAME, SITE_DESC, SITE_URL, GSC_META, OPERATOR, LAST_VERIFIED_DATE, GA4_MEASUREMENT_ID


def esc(s):
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def yen(v):
    if v is None:
        return "公式確認中"
    return f"{v:,}円"


# ---------- フィールド単位の確認状態（verification status）----------
# 新しいstatus専用キーは追加しない。既存フィールド（lowest_per_meal_yen / shipping_fee /
# notes / requires_verification）だけから4状態を導出する（PHASE1_IMPLEMENTATION_PLAN.md 8章）。

_VSTATUS_LABEL = {
    "confirmed": "確認済み",
    "derived": "算出値",
    "pending": "確認中",
    "uncollected": "未収集",
}


def vstatus_badge(status):
    label = _VSTATUS_LABEL.get(status, "確認中")
    return f'<span class="vstatus vstatus-{status}">{esc(label)}</span>'


def mobile_scroll_hint():
    """横幅の広い比較テーブルの直前に置く、モバイルでの横スクロール案内。
    .mobile-scroll-hintはCSS側で640px以下でのみ表示される（デスクトップでは非表示）。
    PHASE4_FINAL_DECISION.md 3章・PHASE4_COMPETITIVE_REAUDIT.md 1章（silver-choice.jp実測）。"""
    return '<p class="mobile-scroll-hint">◀ 表がはみ出す場合は横にスクロールしてご覧ください ▶</p>'


def vstatus_legend(link_to_dashboard=True):
    link = ' <a href="/verification.html">→ 全社の確認状況を一覧で見る</a>' if link_to_dashboard else ""
    return (
        '<p style="font-size:12px;color:#666;margin-top:8px;">表示の見方：'
        f'{vstatus_badge("confirmed")}＝公式一次情報で確認／'
        f'{vstatus_badge("derived")}＝公式情報から計算／'
        f'{vstatus_badge("pending")}＝情報はあるが裏付け不十分／'
        f'{vstatus_badge("uncollected")}＝公式情報にまだ到達できていません{link}</p>'
    )


def _price_status(price_plan):
    """価格の確認状態。plan_notes中の既存の記法（DERIVED/PENDING_VERIFICATION）を
    機械可読な判定に使う（新規データキーの追加はしない）。"""
    if not price_plan:
        return "uncollected"
    notes = price_plan.get("plan_notes") or ""
    if price_plan.get("lowest_per_meal_yen") is not None:
        return "derived" if "DERIVED" in notes else "confirmed"
    return "pending" if "PENDING_VERIFICATION" in notes else "uncollected"


def _shipping_status(shipping_row):
    """送料の確認状態。shipping_fee/notesのみから導出。"""
    if not shipping_row:
        return "uncollected"
    notes = shipping_row.get("notes") or ""
    if shipping_row.get("shipping_fee") is not None:
        return "confirmed"
    if "UNCOLLECTED" in notes:
        return "uncollected"
    return "confirmed"  # 地域等により変動するが公式情報として文章で確認済み


def _campaign_status(first_time_campaign):
    """初回キャンペーンの確認状態。既存のrequires_verification(bool)をそのまま使う。"""
    if not first_time_campaign:
        return "uncollected"
    return "uncollected" if first_time_campaign.get("requires_verification", True) else "confirmed"


def source_link(sources_by_id, source_id):
    """source_idに対応するsources.jsonエントリがあれば出典リンクを返す。
    source_idが無い、またはsources.json側にエントリが見つからない場合は空文字
    （リンクできない出典を示さない。PHASE2_IMPLEMENTATION_PLAN.md 7章）。"""
    if not source_id or not sources_by_id:
        return ""
    src = sources_by_id.get(source_id)
    if not src:
        return ""
    return (f' <a href="{esc(src.get("url", ""))}" target="_blank" rel="noopener nofollow" '
            f'style="font-size:12px;">出典を見る（確認日: {esc(src.get("confirmed_at", ""))}）</a>')


def price_cell_html(price_plan, sources_by_id=None):
    """最安料金の表示（価格＋確認日/出典＋確認状態バッジ）を組み立てる。
    未確認（pending/uncollected）の値には確認日を出さない。出典リンクが既に確認日を
    含む場合は重複させず、出典が無い確認済み/算出値のみ最終確認日を単独表示する。
    build_service_pageと検証状況ダッシュボードで共有するロジック（新規データキーは追加しない）。
    PHASE3_IMPLEMENTATION_PLAN.md 1.2〜1.4節・3.2節。"""
    price_plan = price_plan or {}
    cheapest = price_plan.get("lowest_per_meal_yen")
    cheapest_html = (yen(cheapest) + "/食") if cheapest else "公式確認中"
    stat = _price_status(price_plan)
    src_link = source_link(sources_by_id, price_plan.get("source_id"))
    checked = price_plan.get("last_checked", "")
    if src_link:
        date_html = ""
    elif stat in ("confirmed", "derived") and checked:
        date_html = f"（{esc(checked)}時点）"
    else:
        date_html = ""
    return f"{cheapest_html}{date_html} {vstatus_badge(stat)}{src_link}"


def shipping_line(shipping_row, sources_by_id=None):
    """data/shipping.jsonの1行から送料の表示行を組み立てる。
    地域・食数・プランで変動し単一値にできないサービスは notes の事実記述をそのまま表示する
    （単一値への圧縮による誤誘導を避けるため）。
    notesに"UNCOLLECTED"を含む行（内部ブロッカーの理由等）は、その理由文自体は
    ユーザー向けに表示しないが、「未収集」であること自体は確認状態バッジで正直に示す。
    確認済み（変動ありを含む）の場合のみ、source_idがあれば出典リンクを付す。"""
    status = _shipping_status(shipping_row)
    badge = vstatus_badge(status)
    if status == "uncollected":
        return f'<p><strong>送料：</strong>{badge}（最新情報は公式サイトでご確認ください）</p>'
    fee = shipping_row.get("shipping_fee")
    notes = (shipping_row.get("notes") or "").strip()
    if fee is not None:
        fee_text = "送料無料" if fee == 0 else f"{yen(fee)}"
        text = f"{fee_text}（{notes}）" if notes else fee_text
    else:
        text = notes
    src = source_link(sources_by_id, shipping_row.get("source_id"))
    return f'<p><strong>送料：</strong>{esc(text)} {badge}{src}</p>'


# ---------- リンク生成 ----------

def aff_link(aff_links, service_id, label=None, cls="btn-primary"):
    """アフィリエイトリンク。actual_urlがあればそれ、なければ公式URLにフォールバック。
    両方ない場合は、壊れたリンクを出さず「要確認」表示にする。"""
    info = aff_links.get(service_id, {})
    actual = info.get("actual_url", "")
    fallback = info.get("fallback_url", "")
    url = actual or fallback
    target = info.get("asp", "")
    label = label or "公式サイトを見る"
    if not url:
        return f'<span class="btn-disabled" style="display:inline-block;background:#eee;color:#999;padding:8px 16px;border-radius:6px;font-size:13px;">公式サイト（公式確認中）</span>'
    note = ""
    if actual:
        note = f'<span class="aff-note">（{esc(target)}経由）</span>'
    return f'<a class="{cls}" href="{esc(url)}" rel="nofollow sponsored" target="_blank" rel="noopener">{esc(label)}{note}</a>'


# ---------- 共通メタ基盤（favicon / OGP / JSON-LD）----------

_FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="14" fill="#e8552d"/>'
    '<text x="32" y="44" font-size="32" font-family="sans-serif" font-weight="bold" '
    'text-anchor="middle" fill="#ffffff">宅</text></svg>'
)
FAVICON_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(_FAVICON_SVG.encode("utf-8")).decode("ascii")


def _meta_block(title, description, canonical_url):
    """OGP・Twitterカード・基本JSON-LD（WebSite）。既存のtitle/description/canonical値をそのまま利用するのみで、
    本文・見出し・価格表記等のコンテンツは一切変更しない。"""
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": SITE_URL,
        "description": SITE_DESC,
    }
    json_ld_script = json.dumps(json_ld, ensure_ascii=False)
    return f"""<link rel="icon" href="{FAVICON_DATA_URI}">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical_url)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary">
<script type="application/ld+json">{json_ld_script}</script>"""


# ---------- 共通テンプレート ----------

def _ga4_block():
    """GA4計測タグ。測定ID（config/site.jsonのga4_measurement_id）が未設定の間は
    外部スクリプトを読み込まず、dataLayerへのpushのみ行う安全なgtag()スタブだけを出力する。
    これによりdiagnosis_start/diagnosis_completeの呼び出しが、GA4未設定の状態でも
    gtag未定義エラーで壊れることなく（かつ二重計測にもならず）常に安全に動作する。
    測定IDが設定されて初めて実際にGoogleへ送信が始まる。PHASE4_FINAL_DECISION.md 1章。"""
    if not GA4_MEASUREMENT_ID:
        return ("<script>window.dataLayer=window.dataLayer||[];"
                "function gtag(){dataLayer.push(arguments);}</script>")
    gid = esc(GA4_MEASUREMENT_ID)
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
            f"gtag('js', new Date());gtag('config', '{gid}');</script>")


def page_header(title, description, canonical_path):
    canonical_url = f"{SITE_URL}/{canonical_path}"
    meta_block = _meta_block(title, description, canonical_url)
    ga4_block = _ga4_block()
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} | {SITE_NAME}</title>
<meta name="description" content="{esc(description)}">
{GSC_META}
<link rel="canonical" href="{canonical_url}">
{meta_block}
{ga4_block}
<style>
:root {{ --primary:#e8552d; --text:#222; --bg:#faf7f5; --card:#fff; --muted:#666; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:"Hiragino Kaku Gothic ProN","Meiryo",sans-serif; color:var(--text); background:var(--bg); line-height:1.7; }}
.container {{ max-width:1000px; margin:0 auto; padding:0 16px; }}
header.site {{ background:var(--primary); color:#fff; padding:16px 0; }}
header.site .container {{ display:flex; align-items:center; justify-content:space-between; }}
header.site a {{ color:#fff; text-decoration:none; }}
nav.main a {{ margin-right:16px; font-size:14px; }}
h1 {{ font-size:1.6rem; margin:24px 0 8px; }}
h2 {{ font-size:1.25rem; margin:24px 0 8px; }}
h3 {{ font-size:1.05rem; margin:16px 0 6px; }}
.card {{ background:var(--card); border-radius:8px; padding:16px; margin:12px 0; box-shadow:0 1px 3px rgba(0,0,0,.08); overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; background:var(--card); border-radius:8px; overflow:hidden; font-size:14px; }}
th, td {{ padding:10px 12px; text-align:left; border-bottom:1px solid #eee; vertical-align:top; }}
th {{ background:#f5ede8; font-weight:bold; }}
.btn-primary {{ display:inline-block; background:var(--primary); color:#fff; padding:10px 20px; border-radius:6px; text-decoration:none; font-weight:bold; }}
.btn-secondary {{ display:inline-block; background:#eee; color:#333; padding:8px 16px; border-radius:6px; text-decoration:none; font-weight:bold; }}
.tag {{ display:inline-block; background:#f5ede8; color:var(--primary); padding:2px 10px; border-radius:12px; font-size:12px; margin:2px; }}
.vstatus {{ display:inline-block; font-size:11px; padding:1px 8px; border-radius:10px; font-weight:bold; white-space:nowrap; }}
.vstatus-confirmed {{ background:#e6f4ea; color:#1e7e34; }}
.vstatus-derived {{ background:#e8f0fe; color:#1a56db; }}
.vstatus-pending {{ background:#fff4e5; color:#b45300; }}
.vstatus-uncollected {{ background:#f1f1f1; color:#777; }}
.aff-note {{ font-size:11px; opacity:.8; }}
.updated {{ color:var(--muted); font-size:12px; margin-top:24px; border-top:1px solid #ddd; padding-top:12px; }}
.pros-cons {{ display:flex; gap:16px; flex-wrap:wrap; }}
.pros-cons > div {{ flex:1; min-width:240px; }}
.pros li, .cons li {{ margin-left:20px; font-size:14px; }}
footer.site {{ text-align:center; padding:24px 16px; color:var(--muted); font-size:12px; margin-top:32px; }}
ul.feature-list li, ol.feature-list li {{ margin-left:20px; font-size:14px; }}
.mobile-scroll-hint {{ display:none; }}
@media (max-width:640px) {{
  table {{ min-width:480px; }}
  .mobile-scroll-hint {{ display:block; font-size:12px; color:var(--muted); margin:4px 0; }}
}}
</style>
</head>
<body>
<header class="site">
  <div class="container">
    <a href="/"><strong>{SITE_NAME}</strong></a>
    <nav class="main">
      <a href="/ranking.html">おすすめ比較</a>
      <a href="/campaigns.html">初回キャンペーン</a>
      <a href="/tool/diagnosis.html">診断ツール</a>
    </nav>
  </div>
</header>
<main class="container">
"""


def page_footer(updated_date, show_vstatus_legend=False):
    legend = vstatus_legend() if show_vstatus_legend else ""
    return f"""
<div class="updated">最終更新: {updated_date} ｜ 情報は確認時点のものであり、最新の価格・条件は必ず公式サイトをご確認ください。{legend}</div>
</main>
<footer class="site">
  <div class="container">
    <p>{SITE_NAME}は宅配食サービスの比較情報を提供するサイトです。各サービスの価格・キャンペーン情報は常に変動します。</p>
    <p>当サイトはアフィリエイト広告（PR）を含みます。リンク経由で購入すると当サイトに報酬が入ることがあります。</p>
    <nav class="footer-nav" style="margin-top:12px;font-size:13px;">
      <a href="/privacy.html" style="color:#eee;margin:0 8px;">プライバシーポリシー</a>｜
      <a href="/disclaimer.html" style="color:#eee;margin:0 8px;">免責事項</a>｜
      <a href="/operator.html" style="color:#eee;margin:0 8px;">運営者情報</a>｜
      <a href="/contact.html" style="color:#eee;margin:0 8px;">お問い合わせ</a>
    </nav>
  </div>
</footer>
</body>
</html>"""


# ---------- サービス詳細ページ ----------

def related_services_block(related):
    """関連サービスカード。tags+targetの一致数>=2件のサービスのみ渡される想定
    （計算はgenerators.pyのcompute_related()で事前に行う）。該当が無ければ何も出力しない。"""
    if not related:
        return ""
    items = "".join(
        f'<a class="btn-secondary" href="/services/{esc(r["id"])}.html">{esc(r["name"])}</a> '
        for r in related
    )
    return f"""
    <div class="card">
      <h2>関連サービス</h2>
      <p style="font-size:13px;color:#666;">共通する特徴・対象が多いサービスです。</p>
      <div style="margin-top:8px;">{items}</div>
    </div>"""


def comparison_links_block(comparison_links):
    """比較ページへのリンク。config/comparisons.jsonの既存ペアをそのまま表示するだけで、
    新規の比較ロジック・新規ページは作らない。該当が無ければ何も出力しない。
    PHASE3_IMPLEMENTATION_PLAN.md 1.4節（比較ページの内部リンク孤立の解消）。"""
    if not comparison_links:
        return ""
    items = "".join(
        f'<a class="btn-secondary" href="{esc(url)}" style="margin-right:8px;">{esc(partner_name)}と比較する →</a>'
        for partner_name, url in comparison_links
    )
    return f"""
    <div class="card">
      <h2>比較ページ</h2>
      <div style="margin-top:8px;">{items}</div>
    </div>"""


def build_service_page(service, aff_links, shipping_by_id=None, related=None, sources_by_id=None, comparison_links=None):
    s_id = service["id"]
    s_name = service["name"]
    shipping_html = shipping_line((shipping_by_id or {}).get(s_id), sources_by_id)
    related_html = related_services_block(related)
    comparison_html = comparison_links_block(comparison_links)

    # 関連記事リンク（サービスDBに article_link があれば表示）
    article_link_html = ""
    _art_link = service.get("article_link", "")
    if _art_link:
        _art_label = service.get("article_label", "関連記事を見る")
        article_link_html = f'<a class="btn-secondary" href="{esc(_art_link)}">{esc(_art_label)}</a> '

    # メニュー・栄養
    feature_list = "".join(f"<li>{esc(f)}</li>" for f in service.get("main_features", []))
    pros = "".join(f"<li>{esc(p)}</li>" for p in service.get("pros", []))
    cons = "".join(f"<li>{esc(c)}</li>" for c in service.get("cons", []))
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in service.get("tags", []))

    price_html = price_cell_html(service.get("price_plan", {}), sources_by_id)

    title = f"{s_name}の特徴・料金・初回キャンペーンを解説"
    desc = f"{s_name}の特徴・料金・初回キャンペーン・お試し情報をまとめました。{SITE_NAME}が公式サイトで最終確認した情報（2026年8月）に基づく内容です。"

    html = page_header(title, desc, f"services/{s_id}.html")
    html += f"""
    <h1>{esc(s_name)}</h1>
    <div>{tags}</div>

    <div class="card">
      <h2>基本情報</h2>
      <table>
        <tr><th>運営会社</th><td>{esc(service.get("operator", "公式確認中"))}</td></tr>
        <tr><th>形態</th><td>{esc(service.get("meal_type", ""))}（{esc(service.get("meal_form", ""))}）</td></tr>
        <tr><th>最安料金</th><td>{price_html}</td></tr>
        <tr><th>対象</th><td>{", ".join(service.get("target", []))}</td></tr>
      </table>
      <div style="margin-top:12px;">{aff_link(aff_links, s_id, label="公式サイトで料金・キャンペーンを確認")}</div>
    </div>

    <div class="card">
      <h2>特徴</h2>
      <ul class="feature-list">{feature_list}</ul>
    </div>

    <div class="card">
      <h2>良い点・気になる点</h2>
      <div class="pros-cons">
        <div><strong>良い点</strong><ul class="feature-list">{pros}</ul></div>
        <div><strong>気になる点</strong><ul class="feature-list">{cons}</ul></div>
      </div>
    </div>

    <div class="card">
      <h2>初回キャンペーン・お試し</h2>
      <p>{esc(service.get("first_time_campaign", {}).get("summary", "公式確認中"))} {vstatus_badge(_campaign_status(service.get("first_time_campaign", {})))}{source_link(sources_by_id, service.get("first_time_campaign", {}).get("source_id"))}</p>
      <p style="font-size:13px;color:#666;">{esc(service.get("first_time_campaign", {}).get("detail", ""))}</p>
      <div style="margin-top:12px;">{aff_link(aff_links, s_id, label="公式サイトでキャンペーンを確認", cls="btn-secondary")}</div>
    </div>

    <div class="card">
      <h2>解約・送料について</h2>
      {shipping_html}
      <p>{esc(service.get("cancellation_note", "公式確認中（公式サイトで確認してください）"))}</p>
    </div>
    {related_html}
    {comparison_html}
    <div style="margin-top:16px;">
      {article_link_html}
      <a class="btn-secondary" href="/ranking.html">← おすすめ比較一覧に戻る</a>
      <a class="btn-secondary" href="/campaigns.html">初回キャンペーン一覧を見る</a>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE, show_vstatus_legend=True)
    return html


# ---------- ランキングページ ----------

def comparison_pairs_block(comparison_pairs):
    """比較ページへのリンク一覧。config/comparisons.jsonの既存ペアをそのまま表示するだけで、
    新規の比較ロジック・新規ページは作らない。両社提携済みでないペアも参考情報として
    控えめなテキストリンクで載せる（CTAとしては扱わない）。
    PHASE3_IMPLEMENTATION_PLAN.md 1.4節（比較ページの内部リンク孤立の解消）。"""
    if not comparison_pairs:
        return ""
    items = "".join(
        f'<li><a href="{esc(url)}">{esc(a_name)} と {esc(b_name)} を比較する</a></li>'
        for a_name, b_name, url in comparison_pairs
    )
    return f"""
    <div class="card">
      <h2>個別の比較ページ</h2>
      <ul class="feature-list">{items}</ul>
    </div>"""


def build_ranking_page(services, campaigns, aff_links, comparison_pairs=None):
    # サービスID → 確認済みの初回キャンペーン特典（requires_verification=false のみ表示）
    # camp_txt/camp_badge は同じcampaigns.json（data/campaigns.json）を情報源として揃える
    # （services.json側のfirst_time_campaignは別データで鮮度がずれている場合があるため使わない）。
    confirmed_camp = {}
    any_camp_ids = set()
    for c in campaigns:
        any_camp_ids.add(c.get("service_id"))
        if not c.get("requires_verification", True):
            confirmed_camp[c.get("service_id")] = c.get("discount_type", "")

    rows = []
    for svc in services:
        cheapest = svc.get("price_plan", {}).get("lowest_per_meal_yen")
        cheapest_txt = (f"{yen(cheapest)}/食") if cheapest else "公式確認中"
        price_badge = vstatus_badge(_price_status(svc.get("price_plan", {})))
        camp_txt = confirmed_camp.get(svc["id"], "公式確認中")
        if svc["id"] in confirmed_camp:
            camp_status = "confirmed"
        elif svc["id"] in any_camp_ids:
            camp_status = "pending"
        else:
            camp_status = "uncollected"
        camp_badge = vstatus_badge(camp_status)
        tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in svc.get("tags", [])[:3])
        # 保存方法（冷凍/冷蔵/日配）。診断ツールと同じmeal_form_categories()の正規化結果を再利用する
        # （PHASE3_IMPLEMENTATION_PLAN.md 2章：新しいmatching engineやデータモデルは作らない）。
        mealform_cats = svc.get("meal_form_categories") or []
        mealform_txt = "・".join(mealform_cats) if mealform_cats else esc(svc.get("meal_form", "")) or "公式確認中"
        mealform_attr = esc(" ".join(mealform_cats))
        rows.append(f"""
        <tr data-mealform="{mealform_attr}">
          <td><a href="/services/{svc['id']}.html"><strong>{esc(svc['name'])}</strong></a><br>{tags}</td>
          <td>{cheapest_txt} {price_badge}</td>
          <td>{esc(camp_txt)} {camp_badge}</td>
          <td>{mealform_txt}</td>
          <td>{', '.join(svc.get('target', []))}</td>
          <td>
            <a class="btn-secondary" href="/services/{svc['id']}.html">詳しく見る</a>
            {aff_link(aff_links, svc['id'], label='公式サイトを確認', cls='btn-secondary')}
          </td>
        </tr>""")

    title = "宅配食おすすめ比較ランキング【2026年8月最新】"
    desc = "宅配食・宅配弁当サービスの最新比較。nosh、ワタミの宅食ダイレクト、三ツ星ファームなど主要サービスの料金・特徴・初回キャンペーンを一覧で比較。"

    html = page_header(title, desc, "ranking.html")
    html += f"""
    <h1>宅配食おすすめ比較ランキング【2026年8月最新】</h1>
    <p>主要宅配食サービスを比較しています。価格・キャンペーン情報は公式サイトで確認できたもののみ掲載し、未確認の項目は「公式確認中」と表示しています（{LAST_VERIFIED_DATE}時点）。</p>
    <div class="card">
      <h3 style="margin-top:0;">保存方法で絞り込む（任意）</h3>
      <div id="mealform-filter" class="checks">
        <label><input type="checkbox" value="冷凍" onchange="filterRankingByMealform()"> 冷凍</label>
        <label><input type="checkbox" value="冷蔵" onchange="filterRankingByMealform()"> 冷蔵</label>
        <label><input type="checkbox" value="日配" onchange="filterRankingByMealform()"> 日配</label>
      </div>
    </div>
    {mobile_scroll_hint()}
    <div class="card">
      <table id="ranking-table">
        <tr><th>サービス</th><th>最安料金</th><th>初回キャンペーン</th><th>保存方法</th><th>向いている人</th><th></th></tr>
        {''.join(rows)}
      </table>
    </div>
    <div class="card">
      <h2>選び方のポイント</h2>
      <ul class="feature-list">
        <li>「お試し価格で始めたい」→ 初回キャンペーンがお得なサービスを選ぶ</li>
        <li>「糖質制限をしたい」→ nosh・三ツ星ファームなど低糖質に強いサービス</li>
        <li>「栄養バランス重視」→ 管理栄養士監修のサービス</li>
      </ul>
      <p style="margin-top:12px;"><a class="btn-primary" href="/tool/diagnosis.html">自分に合うサービスを診断する →</a></p>
    </div>
    {comparison_pairs_block(comparison_pairs)}
    <p style="font-size:13px;color:#666;">※各サービスの詳細はサービス名リンクから。価格・キャンペーン情報は常に変動するため、最新情報は公式サイトをご確認ください。</p>
    <script>
    function filterRankingByMealform() {{
      const checked = [...document.querySelectorAll('#mealform-filter input:checked')].map(x => x.value);
      document.querySelectorAll('#ranking-table tr[data-mealform]').forEach(tr => {{
        const forms = (tr.dataset.mealform || '').split(' ').filter(Boolean);
        const show = checked.length === 0 || forms.some(f => checked.includes(f));
        tr.style.display = show ? '' : 'none';
      }});
    }}
    </script>
    """
    html += page_footer(LAST_VERIFIED_DATE, show_vstatus_legend=True)
    return html


# ---------- キャンペーン一覧ページ ----------

def build_campaigns_page(campaigns, services, aff_links):
    svc_by_id = {s["id"]: s for s in services}
    cards = []
    for c in campaigns:
        svc = svc_by_id.get(c.get("service_id"))
        svc_name = svc["name"] if svc else "公式確認中"
        svc_id = c.get("service_id", "")
        cards.append(f"""
        <div class="card">
          <h2>{esc(c['title'])}</h2>
          <p>{esc(c['summary'])}</p>
          <table>
            <tr><th>対象サービス</th><td>{esc(svc_name)}</td></tr>
            <tr><th>割引タイプ</th><td>{esc(c.get('discount_type', '公式確認中'))}</td></tr>
            <tr><th>条件</th><td>{esc(c.get('conditions', '公式確認中'))}</td></tr>
            <tr><th>最終確認</th><td>{esc(c.get('last_checked', ''))}</td></tr>
          </table>
          <div style="margin-top:12px;">
            <a class="btn-secondary" href="/services/{esc(svc_id)}.html">サービス詳細を見る</a>
            {aff_link(aff_links, c['service_id'], label='公式サイトでキャンペーンを確認', cls='btn-primary')}
          </div>
        </div>""")

    title = "宅配食 初回キャンペーン・お試し情報まとめ【2026年8月】"
    desc = "宅配食サービスの最新の初回キャンペーン・お試し価格情報を一覧で紹介。お得に宅配食を始めたい人向け。"

    html = page_header(title, desc, "campaigns.html")
    html += f"""
    <h1>宅配食 初回キャンペーン・お試し情報まとめ</h1>
    <p>各サービスの初回キャンペーン・お試し情報を毎週更新しています。最新の割引条件は必ず公式サイトでご確認ください。</p>
    {''.join(cards)}
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- 比較ページ ----------

def build_comparison_page(service_a, service_b, aff_links):
    a_id, b_id = service_a["id"], service_b["id"]
    a_name, b_name = service_a["name"], service_b["name"]

    a_cheapest = service_a.get("price_plan", {}).get("lowest_per_meal_yen")
    b_cheapest = service_b.get("price_plan", {}).get("lowest_per_meal_yen")
    a_price = (f"{yen(a_cheapest)}/食") if a_cheapest else "公式確認中"
    b_price = (f"{yen(b_cheapest)}/食") if b_cheapest else "公式確認中"

    a_tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in service_a.get("tags", []))
    b_tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in service_b.get("tags", []))

    title = f"{a_name}と{b_name}を徹底比較！どっちがおすすめ？【2026年】"
    desc = f"{a_name}と{b_name}を料金・特徴・初回キャンペーンで比較。一人暮らし・ダイエット・糖質制限など目的別におすすめを解説。"

    html = page_header(title, desc, f"comparisons/{a_id}-vs-{b_id}.html")
    html += f"""
    <h1>{esc(a_name)}と{esc(b_name)}を徹底比較</h1>
    <p>どちらにするか迷っている人向けに、料金・特徴・初回キャンペーンを比較します。（2026年8月時点の情報）</p>

    {mobile_scroll_hint()}
    <div class="card">
      <table>
        <tr><th></th><th>{esc(a_name)}</th><th>{esc(b_name)}</th></tr>
        <tr><td><strong>特徴</strong></td><td>{a_tags}</td><td>{b_tags}</td></tr>
        <tr><td><strong>最安料金</strong></td><td>{a_price}</td><td>{b_price}</td></tr>
        <tr><td><strong>向いている人</strong></td><td>{', '.join(service_a.get('target', []))}</td><td>{', '.join(service_b.get('target', []))}</td></tr>
        <tr><td><strong>料金・特徴を詳しく見る</strong></td><td><a class="btn-secondary" href="/services/{esc(a_id)}.html">{esc(a_name)}の詳細ページ</a></td><td><a class="btn-secondary" href="/services/{esc(b_id)}.html">{esc(b_name)}の詳細ページ</a></td></tr>
        <tr><td><strong>公式サイト</strong></td><td>{aff_link(aff_links, a_id, label='公式サイトを確認', cls='btn-secondary')}</td><td>{aff_link(aff_links, b_id, label='公式サイトを確認', cls='btn-secondary')}</td></tr>
      </table>
    </div>

    <div class="card">
      <h2>{esc(a_name)}のポイント</h2>
      <ul class="feature-list">{''.join(f'<li>{esc(p)}</li>' for p in service_a.get('pros', []))}</ul>
    </div>

    <div class="card">
      <h2>{esc(b_name)}のポイント</h2>
      <ul class="feature-list">{''.join(f'<li>{esc(p)}</li>' for p in service_b.get('pros', []))}</ul>
    </div>

    <div class="card">
      <h2>まとめ：どっちを選ぶべき？</h2>
      <p><strong>{esc(a_name)}が向いている人：</strong>{', '.join(service_a.get('target', []))}</p>
      <p><strong>{esc(b_name)}が向いている人：</strong>{', '.join(service_b.get('target', []))}</p>
      <p style="margin-top:12px;">どちらも初回キャンペーンがあります。まずはお試しで両方試して、自分に合う方を選ぶのがおすすめです。</p>
    </div>

    <div style="margin-top:16px;">
      <a class="btn-secondary" href="/services/{esc(a_id)}.html">{esc(a_name)}の詳細を見る</a>
      <a class="btn-secondary" href="/services/{esc(b_id)}.html">{esc(b_name)}の詳細を見る</a>
      <a class="btn-secondary" href="/campaigns.html">初回キャンペーン一覧を見る</a>
      <a class="btn-secondary" href="/tool/diagnosis.html">診断ツールで選ぶ</a>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- 診断ツール ----------

def build_diagnosis_tool(services, aff_links):
    # クライアントサイドで動作する条件検索ツール
    svc_data = []
    for svc in services:
        aff = aff_links.get(svc["id"], {})
        svc_data.append({
            "id": svc["id"],
            "name": svc["name"],
            "tags": svc.get("tags", []),
            "target": svc.get("target", []),
            "price": svc.get("price_plan", {}).get("lowest_per_meal_yen"),
            "meal_form_categories": svc.get("meal_form_categories", []),
            "url": svc.get("official_url", ""),
            "aff_url": aff.get("actual_url", ""),  # アフィリエイトリンク（あれば優先）
            "detail_url": f"/services/{svc['id']}.html",  # 当サイト内サービス詳細ページ
        })
    svc_json = json.dumps(svc_data, ensure_ascii=False)

    title = "宅配食 診断ツール｜自分に合うサービスを条件で探す"
    desc = "予算・目的・こだわりを選ぶだけで、あなたに合う宅配食サービスがわかる無料の診断ツール。"

    html = page_header(title, desc, "tool/diagnosis.html")
    html += f"""
    <h1>宅配食 診断ツール</h1>
    <p>以下の条件を選ぶと、あなたに合いそうな宅配食サービスを表示します。</p>

    <div class="card">
      <h3>目的を選んでください（複数可）</h3>
      <div id="goals" class="checks">
        <label><input type="checkbox" value="一人暮らし"> 一人暮らし</label>
        <label><input type="checkbox" value="ダイエット"> ダイエット</label>
        <label><input type="checkbox" value="糖質制限"> 糖質制限</label>
        <label><input type="checkbox" value="健康志向"> 健康志向</label>
        <label><input type="checkbox" value="時短"> 時短（手間を省きたい）</label>
        <label><input type="checkbox" value="高タンパク"> 高タンパク</label>
        <label><input type="checkbox" value="高齢者"> 親・高齢者の食事</label>
      </div>
      <h3 style="margin-top:16px;">保存方法で絞り込む（任意）</h3>
      <div id="mealforms" class="checks">
        <label><input type="checkbox" value="冷凍"> 冷凍</label>
        <label><input type="checkbox" value="冷蔵"> 冷蔵</label>
        <label><input type="checkbox" value="日配"> 日配</label>
      </div>
      <p style="margin-top:12px;"><button class="btn-primary" onclick="runDiag()">診断する</button></p>
    </div>

    <div id="result" class="card" style="display:none;"></div>

    <script>
    const SERVICES = {svc_json};
    // GA4計測（診断ツール専用。ページ遷移が無いGA4拡張計測ではカバーできないためこの2つのみ独自実装する。
    // PHASE4_FINAL_DECISION.md 1章）。診断開始は初回のチェック操作でのみ1回発火（多重発火防止）。
    let _diagStarted = false;
    document.querySelectorAll('#goals input, #mealforms input').forEach(el => {{
      el.addEventListener('change', () => {{
        if (!_diagStarted) {{ _diagStarted = true; gtag('event', 'diagnosis_start'); }}
      }});
    }});
    function runDiag() {{
      const goals = [...document.querySelectorAll('#goals input:checked')].map(x => x.value);
      const mealForms = [...document.querySelectorAll('#mealforms input:checked')].map(x => x.value);
      if (goals.length === 0 && mealForms.length === 0) {{
        document.getElementById('result').style.display = 'block';
        document.getElementById('result').innerHTML = '<p>目的または保存方法を1つ以上選んでください。</p>';
        return;
      }}
      // 保存方法（冷凍/冷蔵/日配）はAND条件の絞り込み。未選択なら全件を対象にする
      let candidates = SERVICES;
      if (mealForms.length > 0) {{
        candidates = candidates.filter(s => (s.meal_form_categories||[]).some(c => mealForms.includes(c)));
      }}
      // タグ or ターゲットとの一致数でスコアリング（目的が未選択なら絞り込みのみ行う）
      const scored = goals.length === 0
        ? candidates.map(s => ({{ ...s, score: 0 }}))
        : candidates.map(s => {{
            const pool = [...(s.tags||[]), ...(s.target||[])];
            let score = 0;
            for (const g of goals) {{ if (pool.includes(g)) score++; }}
            return {{ ...s, score }};
          }}).filter(s => s.score > 0).sort((a,b) => b.score - a.score);
      // 診断完了（「please select」の早期returnケースでは発火しない＝実際に診断を実行した回数のみ計測）
      gtag('event', 'diagnosis_complete', {{ goal_count: goals.length, mealform_count: mealForms.length, result_count: scored.length }});
      let html = '<h2>あなたにおすすめのサービス</h2>';
      if (scored.length === 0) {{
        html += '<p>条件に合うサービスがまだ登録されていません。近日中に追加予定です。</p>';
      }} else {{
        html += '<table><tr><th>サービス</th><th>特徴</th><th>詳細</th><th>公式サイト</th></tr>';
        for (const s of scored) {{
          const detail = `<a href="${{s.detail_url}}">詳しく見る</a>`;
          const url = s.aff_url || s.url || '';
          const rel = s.aff_url ? 'rel="nofollow sponsored"' : '';
          const label = s.aff_url ? '公式サイトを見る' : '公式サイト';
          const link = url ? `<a href="${{url}}" ${{rel}} target="_blank" rel="noopener">${{label}}</a>` : '<span style="color:#999">公式確認中</span>';
          html += `<tr><td><strong>${{s.name}}</strong></td><td>${{(s.tags||[]).join('・')}}</td><td>${{detail}}</td><td>${{link}}</td></tr>`;
        }}
        html += '</table>';
        html += '<p style="font-size:13px;color:#666;margin-top:12px;">※診断は簡易的なマッチングです。詳細は各サービスページをご確認ください。</p>';
      }}
      document.getElementById('result').style.display = 'block';
      document.getElementById('result').innerHTML = html;
    }}
    </script>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- トップページ ----------

def build_index_page(services, campaigns, aff_links):
    svc_by_id = {s["id"]: s for s in services}
    # キャンペーン一覧（最新3件）
    camp_items = ""
    for c in campaigns[:3]:
        svc_name = svc_by_id.get(c["service_id"], {}).get("name", "要確認")
        camp_items += f'<li><a href="/campaigns.html">{esc(svc_name)}：{esc(c["title"])}</a></li>'

    # サービス一覧カード
    svc_cards = ""
    for svc in services:
        svc_cards += f"""
        <div class="card" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
          <div>
            <a href="/services/{svc['id']}.html"><strong>{esc(svc['name'])}</strong></a>
            <div>{''.join(f'<span class="tag">{esc(t)}</span>' for t in svc.get('tags', [])[:3])}</div>
          </div>
          <div>{aff_link(aff_links, svc['id'], label='公式サイトを確認', cls='btn-secondary')}</div>
        </div>"""

    title = f"{SITE_NAME}｜宅配食の比較・初回キャンペーン情報"
    desc = SITE_DESC

    html = page_header(title, desc, "index.html")
    html += f"""
    <h1>宅配食を、データで選ぶ。</h1>
    <p>{SITE_NAME}は、宅配食・宅配弁当サービスの料金・初回キャンペーン情報を、公式サイトで最終確認したデータで比較するサイトです。最新のキャンペーン情報を毎週更新しています。</p>

    <div class="card" style="background:#fff8f0;">
      <h2>🎯 初回キャンペーン・お試し情報（最新）</h2>
      <ul class="feature-list">{camp_items or '<li>更新中</li>'}</ul>
      <p style="margin-top:8px;"><a class="btn-primary" href="/campaigns.html">すべてのキャンペーンを見る →</a></p>
    </div>

    <div class="card">
      <h2>📊 主要サービス一覧</h2>
      {svc_cards}
    </div>

    <div class="card">
      <h2>自分に合うサービスを探す</h2>
      <p>「一人暮らし」「糖質制限」「ダイエット」など、あなたの条件に合うサービスを診断します。</p>
      <p style="margin-top:8px;"><a class="btn-primary" href="/tool/diagnosis.html">診断ツールを開く →</a></p>
    </div>

    <div class="card">
      <h2>このサイトのこだわり</h2>
      <ul class="feature-list">
        <li><strong>鮮度</strong>：価格・キャンペーン情報を毎週更新し、最終確認日を明記</li>
        <li><strong>公式確認</strong>：公式サイトの情報を確認したもののみ掲載し、未確認の項目は「公式確認中」と明示</li>
        <li><strong>目的別</strong>：一人暮らし・ダイエット・糖質制限など目的で比較できる</li>
      </ul>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- 記事ページ：シェフの無添つくりおき 口コミ・評判 ----------

def build_article_chef_muten_kuchikomi(aff_links):
    """シェフの無添つくりおき 商標ロングテール記事（一次情報・公式サイト2026-08-26確認）"""
    title = "シェフの無添つくりおきの口コミ・評判を徹底検証！料金・送料・メニュー・「まずい？」まで【2026年8月】"
    desc = "シェフの無添つくりおきの料金（初回3,799円〜）・送料・メニュー・解約条件を公式情報で検証。「まずい？」の見方、口コミの確認方法、向いている人まで解説します。"
    html = page_header(title, desc, "articles/chef-muten-tukuritoki-kuchikomi.html")

    # A8 CTA（aff_link関数が actual_url を使用、rel=nofollow sponsored付き）
    cta = aff_link(aff_links, "chef-muten-tukuritoki", label="シェフの無添つくりおきを公式サイトで見る", cls="btn-primary")

    html += f"""
    <h1>シェフの無添つくりおきの口コミ・評判を徹底検証！料金・送料・メニュー・「まずい？」まで</h1>
    <p style="font-size:13px;color:#666;">最終確認日：2026年8月26日 ｜ 情報源：公式サイト（store.tavenal.com）・公式FAQ</p>

    <div class="card" style="background:#fff8f0;">
      <h2>結論：どんな人に向いている？</h2>
      <p>「シェフの無添つくりおき」は、<strong>添加物（保存料・化学調味料）を一切使わない無添加のお惣菜を、週替わりで届けてくれる冷蔵の惣菜宅配</strong>です。</p>
      <p>以下のような人に向いていると判断できます（公式情報に基づく）。</p>
      <ul class="feature-list">
        <li><strong>小さな子どもがいる家庭</strong>：無添加・やさしい味付けで、お子様に安心して食べさせたい人</li>
        <li><strong>毎日の献立・調理の時間を減らしたい人</strong>：レンジで温めるだけで食卓が完成</li>
        <li><strong>無添加にこだわりたい人</strong>：シェフ手作り・添加物不使用に特化</li>
      </ul>
      <p>一方、以下の人は合わない可能性があります。</p>
      <ul class="feature-list">
        <li><strong>一人暮らし</strong>：1セットが「大人2名+子ども」の家族向け想定で、量が多い（公式FAQで「一人暮らしには量が多い？」という質問がある）</li>
        <li><strong>メニューを自分で選びたい人</strong>：メニューはおまかせ・週替わりで指定不可</li>
        <li><strong>冷凍で長く保存したい人</strong>：冷蔵お届けで消費期限は4日</li>
      </ul>
      <div style="margin-top:12px;">{cta}</div>
    </div>

    <div class="card">
      <h2>シェフの無添つくりおきとは？（基本情報）</h2>
      <table>
        <tr><th>運営</th><td>株式会社タベナル（公式サイトより）</td></tr>
        <tr><th>サービス内容</th><td>一流シェフが化学調味料を一切使わず手作りするお惣菜を、週替わりで宅配</td></tr>
        <tr><th>特徴</th><td>添加物不使用（保存料・化学調味料不使用）／専属の管理栄養士が栄養設計を監修</td></tr>
        <tr><th>お届け形態</th><td>冷蔵状態でお届け（冷凍ではない）</td></tr>
        <tr><th>消費期限</th><td>お届けから4日間</td></tr>
        <tr><th>利用方法</th><td>毎週の定期購入。レンジで温めるだけ</td></tr>
        <tr><th>確認日</th><td>2026年8月26日（公式サイト）</td></tr>
      </table>
      <p style="font-size:13px;color:#666;">※同じ運営グループの「FIT FOOD HOME」会員はログインして注文可能と公式サイトに記載があります。</p>
    </div>

    <div class="card">
      <h2>料金プランを比較（公式情報）</h2>
      <table>
        <tr><th></th><th>食卓サポートプラン</th><th>食卓おまかせプラン</th></tr>
        <tr><td><strong>想定家族</strong></td><td>大人2名+お子様1名（幼児）</td><td>大人2名+お子様2名（小中学生）</td></tr>
        <tr><td><strong>想定日数</strong></td><td>夕食2回分</td><td>夕食3回分</td></tr>
        <tr><td><strong>メニュー数</strong></td><td>主菜2種+副菜3種（5個）</td><td>主菜3種（各2パック）+副菜6種（9個）</td></tr>
        <tr><td><strong>1個あたり内容量</strong></td><td>150〜300g程度</td><td>150〜600g程度</td></tr>
        <tr><td><strong>通常価格（2回目以降）</strong></td><td>5,173円（税込）+送料990円</td><td>13,607円（税込）+送料990円</td></tr>
        <tr><td><strong>初回限定価格</strong></td><td><strong>3,799円（税込・送料無料）</strong></td><td><strong>9,980円（税込・送料無料）</strong></td></tr>
      </table>
      <p style="font-size:13px;color:#666;">初回価格は「26%OFF」の限定価格で、ご契約者様1回目のご注文のみ適用（公式FAQより）。※価格は2026年8月26日時点の公式情報です。</p>
      <div style="margin-top:12px;">{cta}</div>
    </div>

    <div class="card">
      <h2>送料は？</h2>
      <ul class="feature-list">
        <li>通常（2回目以降）：<strong>1回あたり990円（税込）</strong></li>
        <li>初回：<strong>送料無料</strong>（初回限定価格に含まれる）</li>
      </ul>
      <p>送料が毎回かかる点は、費用を計算する際に注意が必要です。1回あたり990円を加味した上で、総額を比較しましょう。</p>
    </div>

    <div class="card">
      <h2>メニューと内容量（週替わり・指定不可）</h2>
      <p>メニューは<strong>週替わり</strong>で、お客様自身での指定はできません（公式FAQより）。栄養や食材のバランスを考慮した献立が届きます。</p>
      <ul class="feature-list">
        <li>主菜・副菜をバランスよく組み合わせた構成</li>
        <li>レンジで温めてお皿に盛り付けるだけでOK</li>
        <li>余った分は冷蔵保存（開封後）・一部メニューは冷凍保存も可能</li>
        <li>お弁当のおかずとしても活用できる</li>
      </ul>
    </div>

    <div class="card">
      <h2>「まずい？」の真相を考える（断定しない）</h2>
      <p>検索で「シェフの無添つくりおき まずい」と調べている方は、「本当に美味しいのか不安」という気持ちがあるはずです。</p>
      <p>当サイトは現時点で実際に試食した独自レビューは保有していません。そのため「美味しい」「まずい」と断定はしませんが、公式情報から判断材料を整理します。</p>
      <ul class="feature-list">
        <li>一流シェフが手作りしている（公式）</li>
        <li>無添加・やさしい味付けをコンセプトにしている（公式）</li>
        <li>味の感じ方は個人差が大きいため、<strong>初回限定価格（26%OFF・送料無料）で実際に試す</strong>のが確実</li>
      </ul>
      <p><strong>重要な注意点</strong>：無添加・やさしい味付けが「薄味」と感じる人もいれば「ちょうど良い」と感じる人もいます。また、冷蔵お届けのため冷凍タイプの宅配食とは食感・保存方法が異なります。</p>
    </div>

    <div class="card">
      <h2>口コミ・評判の見方（事実と評価の分離）</h2>
      <p>口コミ・評判を確認する際の注意点をまとめます。</p>
      <ul class="feature-list">
        <li><strong>確認できる事実</strong>：公式情報（料金・送料・メニュー構成・解約条件・消費期限）は上記の通り</li>
        <li><strong>人によって評価が分かれる点</strong>：味付けの好み、量の適正（家族構成による）、調理の手間感</li>
        <li><strong>特に確認したい点</strong>：家族構成に合った量か、週替わりメニューの好み、消費期限4日で食べ切れるか</li>
      </ul>
      <p style="font-size:13px;color:#666;">※当サイトは他サイトの口コミ文を転載していません。購入を検討する際は、公式サイトの情報と、ご自身の家族構成・食習慣に照らして判断してください。</p>
    </div>

    <div class="card">
      <h2>メリット・デメリット（公式情報から整理）</h2>
      <div class="pros-cons">
        <div>
          <strong>メリット</strong>
          <ul class="feature-list">
            <li>無添加（保存料・化学調味料不使用）で安心</li>
            <li>シェフ手作り・管理栄養士監修</li>
            <li>週替わりで飽きにくい</li>
            <li>レンジ調理のみで時短・後片付けが楽</li>
            <li>2回目以降はいつでも休止（解約）可能・違約金なし</li>
            <li>初回は26%OFF+送料無料で試せる</li>
          </ul>
        </div>
        <div>
          <strong>デメリット・注意点</strong>
          <ul class="feature-list">
            <li>メニュー指定不可（おまかせ・週替わり）</li>
            <li>冷蔵お届けのため消費期限が4日と短い</li>
            <li>毎回の送料990円がかかる</li>
            <li>家族向けの量で一人暮らしには多い可能性</li>
            <li>冷凍の宅配食と比べると長期保存には向かない</li>
          </ul>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>解約・スキップ・休止の条件（公式FAQより）</h2>
      <table>
        <tr><th>項目</th><th>内容</th></tr>
        <tr><td>初回お届け分</td><td>キャンセル不可（初回限定価格のため）</td></tr>
        <tr><td>2回目以降のスキップ</td><td>可能。お届けの6日前までに手続き（九州・島根・青森は7日前）</td></tr>
        <tr><td>休止（解約）</td><td>2回目以降はいつでも可能・違約金なし</td></tr>
        <tr><td>退会</td><td>定期休止手続き後、退会申請。完了まで約1週間</td></tr>
      </table>
      <p style="font-size:13px;color:#666;">初回はキャンセル不可・2回目以降はいつでも解約可能という点は、試しやすい一方で「初回分は必ず受け取る」必要がある点として押さえておきましょう。</p>
    </div>

    <div class="card" style="background:#fff8f0;">
      <h2>まとめ：自分に合うかどうかの判断基準</h2>
      <p>「シェフの無添つくりおき」は、<strong>無添加・手作りにこだわりたい家族向けの冷蔵惣菜宅配</strong>です。</p>
      <ul class="feature-list">
        <li>✅ 家族（特に小さな子ども）に無添加の食事を食べさせたい → 検討価値あり</li>
        <li>✅ 献立・調理の時短をしたい → 検討価値あり</li>
        <li>⚠️ 一人暮らしで量が少ない方が良い → 他の宅配食（nosh等）と比較を推奨</li>
        <li>⚠️ メニューを自分で選びたい → 不向き（おまかせ・週替わり）</li>
      </ul>
      <p>初回は26%OFF+送料無料（3,799円〜）で試せるため、「量・味・使い勝手」を実際に確認してから継続を判断するのがおすすめです。</p>
      <div style="margin-top:12px;">{cta}</div>
      <p style="font-size:12px;color:#999;margin-top:8px;">※当サイトはアフィリエイト広告（PR）を含みます。リンク経由で購入すると当サイトに報酬が入ることがあります。</p>
    </div>

    <div style="margin-top:16px;">
      <a class="btn-secondary" href="/services/chef-muten-tukuritoki.html">シェフの無添つくりおきの詳細ページを見る</a>
      <a class="btn-secondary" href="/ranking.html">宅配食の比較一覧を見る</a>
      <a class="btn-secondary" href="/campaigns.html">初回キャンペーン一覧を見る</a>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- 検証状況ダッシュボード ----------

def build_verification_dashboard(services, shipping_by_id, sources_by_id):
    """11社×価格・送料・キャンペーンの確認状況を1ページに集約するダッシュボード。
    data/sources.jsonは直接参照・列挙しない。既存の確認状態判定関数（_price_status/
    _shipping_status/_campaign_status）とprice_cell_html()/source_link()をそのまま
    再利用するだけで、ASP内部情報・報酬額・program_id等はいずれの関数からも出力されない
    （source_linkが返すのはurl/confirmed_atのみで、sources.jsonのnoteフィールドは
    一切参照しない）。新しいスコアリング・ランキング付けは行わない。
    PHASE3_IMPLEMENTATION_PLAN.md 3.2節。"""
    rows = []
    for svc in services:
        s_id = svc["id"]
        price_html = price_cell_html(svc.get("price_plan", {}), sources_by_id)
        shipping_row = (shipping_by_id or {}).get(s_id)
        ship_html = f"{vstatus_badge(_shipping_status(shipping_row))}{source_link(sources_by_id, (shipping_row or {}).get('source_id'))}"
        camp = svc.get("first_time_campaign", {})
        camp_html = f"{vstatus_badge(_campaign_status(camp))}{source_link(sources_by_id, camp.get('source_id'))}"
        rows.append(f"""
        <tr>
          <td><a href="/services/{s_id}.html"><strong>{esc(svc['name'])}</strong></a></td>
          <td>{price_html}</td>
          <td>{ship_html}</td>
          <td>{camp_html}</td>
        </tr>""")

    title = "全11社の価格・送料・キャンペーン確認状況一覧"
    desc = f"{SITE_NAME}が11社それぞれの価格・送料・初回キャンペーンをどこまで公式一次情報で確認できているかを一覧で開示します。確認済みの項目には出典と確認日を明記しています。"

    html = page_header(title, desc, "verification.html")
    html += f"""
    <h1>全11社の価格・送料・キャンペーン確認状況</h1>
    <p>各サービスの価格・送料・初回キャンペーンについて、公式一次情報でどこまで確認できているかを一覧にしています。確認済み・算出値の項目には出典リンクと確認日を付けています。未確認の項目には出典・確認日を表示していません（存在しない裏付けを示さないため）。</p>
    {vstatus_legend(link_to_dashboard=False)}
    {mobile_scroll_hint()}
    <div class="card">
      <table>
        <tr><th>サービス</th><th>価格</th><th>送料</th><th>初回キャンペーン</th></tr>
        {''.join(rows)}
      </table>
    </div>
    <p style="font-size:13px;color:#666;">※このページはスコアやランキングを付けるものではなく、当サイトが確認できている範囲をそのまま開示するものです。最新情報は必ず公式サイトでご確認ください。</p>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- 404ページ ----------

def build_404_page():
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ページが見つかりません | {SITE_NAME}</title>
<meta name="robots" content="noindex">
<link rel="icon" href="{FAVICON_DATA_URI}">
<style>
body {{ font-family:"Hiragino Kaku Gothic ProN","Meiryo",sans-serif; background:#faf7f5; color:#222; text-align:center; padding:60px 16px; }}
h1 {{ font-size:1.5rem; margin-bottom:16px; }}
p {{ margin-bottom:16px; color:#666; }}
a {{ color:#e8552d; }}
.footer {{ margin-top:48px; font-size:12px; color:#999; }}
</style>
</head>
<body>
<h1>ページが見つかりません（404）</h1>
<p>お探しのページは移動したか、存在しない可能性があります。</p>
<p><a href="/">ホームに戻る</a> ｜ <a href="/ranking.html">宅配食の比較一覧を見る</a> ｜ <a href="/campaigns.html">初回キャンペーンを見る</a></p>
<p class="footer">
<a href="/privacy.html" style="color:#999;margin:0 6px;">プライバシーポリシー</a>｜
<a href="/disclaimer.html" style="color:#999;margin:0 6px;">免責事項</a>｜
<a href="/operator.html" style="color:#999;margin:0 6px;">運営者情報</a>｜
<a href="/contact.html" style="color:#999;margin:0 6px;">お問い合わせ</a>
</p>
</body>
</html>"""


# ---------- 法務ページ（プライバシー・免責・運営者・お問い合わせ） ----------

def _operator_name():
    return OPERATOR.get("name", "").strip() or "（運営者名は設定準備中です）"


def _operator_email():
    return OPERATOR.get("email", "").strip()


def build_privacy_page():
    title = "プライバシーポリシー"
    desc = f"{SITE_NAME}（宅配食比較サイト）のプライバシーポリシー。個人情報の取り扱い、Cookie・アクセス解析、アフィリエイト広告について説明します。"
    html = page_header(title, desc, "privacy.html")
    html += f"""
    <h1>プライバシーポリシー</h1>
    <p>{SITE_NAME}（以下「当サイト」）は、個人情報の保護に関する法律および関連法令を遵守し、以下の方針に基づいて個人情報を適正に取り扱います。</p>

    <div class="card">
      <h2>1. 個人情報の収集について</h2>
      <p>当サイトは、現時点ではユーザー登録・入力フォームによる個人情報の収集は行っておりません。</p>
      <p>お問い合わせをいただいた際に、メールアドレスや氏名などの情報を送信いただく場合があります。これらの情報は、お問い合わせへの対応にのみ利用し、それ以外の目的には利用いたしません。</p>
    </div>

    <div class="card">
      <h2>2. Cookieについて</h2>
      <p>当サイトでは、以下の目的でCookieを使用する場合があります。</p>
      <ul class="feature-list">
        <li>アクセス解析（サイトの利用状況の把握）</li>
        <li>広告配信（訪問履歴に基づく広告の表示）</li>
        <li>アフィリエイトプログラムの成果判定</li>
      </ul>
      <p>Cookieには氏名・住所・電話番号などの個人を特定する情報は含まれません。Cookieの無効化は、お使いのブラウザの設定で行うことができます。</p>
    </div>

    <div class="card">
      <h2>3. アクセス解析について</h2>
      <p>当サイトでは、サイト改善のためにアクセス解析ツール（Google Analytics 等）を利用する場合があります。この際、Cookieを通じて、お使いのブラウザの種類・OS・アクセス日時・参照元などの情報が収集されることがありますが、これらの情報から個人を特定することはできません。</p>
      <p>Google Analyticsによるデータ収集を無効化したい場合は、Googleが提供するオプトアウトアドオンをご利用ください。</p>
    </div>

    <div class="card">
      <h2>4. アフィリエイト広告について</h2>
      <p>当サイトは、アフィリエイトプログラム（A8.net、afb、アクセストレード 等）に参加しています。記事内・ページ内のリンクから商品・サービスを購入された場合、当サイトに成果報酬が支払われることがあります。</p>
      <p>アフィリエイト広告の成果判定にはCookieが使用される場合がありますが、個人を特定する情報は収集されません。</p>
    </div>

    <div class="card">
      <h2>5. 個人情報の第三者提供について</h2>
      <p>当サイトは、法令に基づく場合を除き、ご提供いただいた個人情報を事前の同意なく第三者に提供いたしません。</p>
    </div>

    <div class="card">
      <h2>6. お問い合わせ</h2>
      <p>個人情報の取り扱いに関するお問い合わせは、<a href="/contact.html">お問い合わせページ</a>よりご連絡ください。</p>
    </div>

    <div class="card">
      <h2>7. ポリシーの変更</h2>
      <p>本ポリシーの内容は、法令の変更やサイトの運営方針に応じて予告なく変更する場合があります。変更後の内容は、本ページに掲載した時点で効力を生じるものとします。</p>
      <p>最終更新日: 2026-08-26</p>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


def build_disclaimer_page():
    title = "免責事項"
    desc = f"{SITE_NAME}（宅配食比較サイト）の免責事項。情報の正確性、アフィリエイト広告、リンク先サイトについての注意事項を説明します。"
    html = page_header(title, desc, "disclaimer.html")
    html += f"""
    <h1>免責事項</h1>

    <div class="card">
      <h2>1. 情報の正確性・最新性について</h2>
      <p>当サイトでは、宅配食サービスの価格・キャンペーン・送料・メニューなどの情報を、できる限り正確かつ最新の状態で提供するよう努めています。ただし、各サービスの情報は頻繁に変更されるため、当サイトの情報が必ずしも最新・正確であることを保証するものではありません。</p>
      <p><strong>実際の価格・条件・キャンペーン内容は、必ず各サービスの公式サイトでご確認ください。</strong></p>
    </div>

    <div class="card">
      <h2>2. アフィリエイト広告について</h2>
      <p>当サイトはアフィリエイト広告（PR）を含みます。記事内・ページ内のリンクから商品・サービスを購入・申し込んだ場合、当サイトに成果報酬が支払われることがあります。</p>
      <p>アフィリエイトリンクの有無にかかわらず、当サイトの記事・比較内容は中立性を保って作成するよう努めていますが、すべての情報が完全に中立的であることを保証するものではありません。</p>
    </div>

    <div class="card">
      <h2>3. 当サイトはサービス提供者ではありません</h2>
      <p>当サイトは、紹介する宅配食サービスの運営会社・提供者ではありません。商品・サービスの品質、配送、契約、解約などのトラブルについては、各サービスの公式窓口にお問い合わせください。</p>
    </div>

    <div class="card">
      <h2>4. 損害の責任について</h2>
      <p>当サイトの情報の利用によって生じたいかなる損害（直接損害・間接損害を問いません）についても、当サイトは一切の責任を負いかねます。情報の利用は利用者ご自身の判断と責任で行ってください。</p>
    </div>

    <div class="card">
      <h2>5. リンク先サイトについて</h2>
      <p>当サイトからリンクされている外部サイト（公式サイト・ASP・その他）の内容、および外部サイトで提供される情報・サービスについて、当サイトは責任を負いません。</p>
    </div>

    <div class="card">
      <h2>6. 情報の更新について</h2>
      <p>当サイトの情報は毎週更新することを目標としていますが、更新頻度や最終更新日時によって最新性は変動します。各ページに記載された最終更新日をご確認ください。</p>
      <p>最終更新日: 2026-08-26</p>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


def build_operator_page():
    title = "運営者情報"
    desc = f"{SITE_NAME}の運営者情報。サイトの運営目的、連絡先、各サービスとの関係性について説明します。"
    email = _operator_email()
    contact_html = f'<a href="mailto:{esc(email)}">{esc(email)}</a>' if email else "（お問い合わせメールアドレスは設定準備中です）"
    html = page_header(title, desc, "operator.html")
    html += f"""
    <h1>運営者情報</h1>

    <div class="card">
      <h2>運営者</h2>
      <table>
        <tr><th>運営者名</th><td>{esc(_operator_name())}</td></tr>
        <tr><th>運営形態</th><td>{esc(OPERATOR.get("note", "個人運営"))}</td></tr>
        <tr><th>お問い合わせ</th><td>{contact_html}</td></tr>
      </table>
    </div>

    <div class="card">
      <h2>サイトの目的</h2>
      <p>当サイトは、宅配食・宅配弁当サービスを検討されている方に向けて、各サービスの特徴・料金・初回キャンペーン情報を比較して提供することを目的としています。</p>
      <p>情報の鮮度を保つため、価格・キャンペーン情報は定期的に更新し、各ページに最終確認日を記載しています。</p>
    </div>

    <div class="card">
      <h2>各サービスとの関係性</h2>
      <p>当サイトは、紹介する各宅配食サービス（nosh、ワタミの宅食ダイレクト、三ツ星ファーム 等）の公式サイト・運営会社とは一切関係のない、独立した第三者の個人サイトです。</p>
      <p>当サイトはアフィリエイトプログラムに参加しており、リンク経由での購入により報酬を得る場合があります。</p>
    </div>

    <div class="card">
      <h2>免責</h2>
      <p>当サイトの情報は、正確性・最新性に努めていますが、その完全性を保証するものではありません。詳細は<a href="/disclaimer.html">免責事項</a>をご確認ください。</p>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


def build_contact_page():
    title = "お問い合わせ"
    desc = f"{SITE_NAME}へのお問い合わせ方法。誤情報のご指摘、削除依頼、その他のご連絡を受け付けています。"
    email = _operator_email()
    if email:
        contact_html = f'<p>以下のメールアドレスまでご連絡ください。</p><p style="font-size:1.1rem;"><a href="mailto:{esc(email)}">{esc(email)}</a></p>'
    else:
        contact_html = '<p>お問い合わせメールアドレスは設定準備中です。公開までしばらくお待ちください。</p>'
    html = page_header(title, desc, "contact.html")
    html += f"""
    <h1>お問い合わせ</h1>

    <div class="card">
      <h2>お問い合わせ方法</h2>
      {contact_html}
      <p style="font-size:13px;color:#666;">返信には数日かかる場合があります。あらかじめご了承ください。</p>
    </div>

    <div class="card">
      <h2>お問い合わせいただける内容</h2>
      <ul class="feature-list">
        <li>記事・情報の誤りについてのご指摘</li>
        <li>掲載情報の削除依頼（当サイトが独自に作成したコンテンツに限ります）</li>
        <li>サイトに関するご質問・ご意見</li>
      </ul>
    </div>

    <div class="card">
      <h2>ご注意</h2>
      <p>当サイトは各宅配食サービスの運営会社ではありません。サービス自体の注文・解約・配送に関するお問い合わせは、各サービスの公式窓口にお願いいたします。</p>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- sitemap / robots ----------

def build_sitemap(pages):
    urls = []
    for p in pages:
        urls.append(f"  <url>\n    <loc>{SITE_URL}/{p}</loc>\n    <lastmod>{LAST_VERIFIED_DATE}</lastmod>\n  </url>")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""


def build_robots():
    return f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml
"""

#!/usr/bin/env python3
"""
宅配食アフィリエイトサイト 静的サイト生成ツール
- data/*.json（構造化DB）からHTMLを生成する
- 依存ライブラリなし（Python標準ライブラリのみ）
- 使い方: python tools/build.py

生成先: site/
"""
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"
OUT_DIR = ROOT / "site"

# サイト名・URLは config/site.json で管理する（Cloudflare Pages 無料公開のため pages.dev を使用）
SITE_NAME = "宅食図鑑"
SITE_DESC = "宅配食・宅配弁当サービスを実データで比較。最新の初回キャンペーン・お試し情報を毎週更新。"
_DEFAULT_URL = "https://takushokuzukan.pages.dev"
_site_config_path = CONFIG_DIR / "site.json"
SITE_URL = os.environ.get("SITE_URL", _DEFAULT_URL)
GSC_META = ""  # Google Search Console 所有権確認メタタグ
OPERATOR = {"name": "", "email": "", "note": "個人運営"}
if _site_config_path.exists():
    try:
        _site_config = json.loads(_site_config_path.read_text(encoding="utf-8"))
        SITE_URL = _site_config.get("url", SITE_URL)
        SITE_NAME = _site_config.get("name", SITE_NAME)
        GSC_META = _site_config.get("search_console_meta", "")
        OPERATOR = _site_config.get("operator", OPERATOR)
    except (json.JSONDecodeError, OSError):
        pass


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_data():
    services = load_json(DATA_DIR / "services.json")["services"]
    campaigns = load_json(DATA_DIR / "campaigns.json")["campaigns"]
    shipping = load_json(DATA_DIR / "shipping.json")["shipping_rules"]
    sources = load_json(DATA_DIR / "sources.json")["sources"]
    aff_links = load_json(CONFIG_DIR / "affiliates.json")["affiliate_links"]
    return services, campaigns, shipping, sources, aff_links


def esc(s):
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def yen(v):
    if v is None:
        return "要確認"
    return f"{v:,}円"


def reward_display(campaign):
    """報酬表示。reward_text（歩合等）があればそれ、なければreward_yenを円表示。"""
    t = campaign.get("reward_text", "")
    if t:
        return t
    r = campaign.get("reward_yen")
    return yen(r) if r else "要確認"


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
        return f'<span class="btn-disabled" style="display:inline-block;background:#eee;color:#999;padding:8px 16px;border-radius:6px;font-size:13px;">公式サイト（要確認）</span>'
    note = ""
    if actual:
        note = f'<span class="aff-note">（{esc(target)}経由）</span>'
    return f'<a class="{cls}" href="{esc(url)}" rel="nofollow sponsored" target="_blank" rel="noopener">{esc(label)}{note}</a>'


# ---------- 共通テンプレート ----------

def page_header(title, description, canonical_path):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)} | {SITE_NAME}</title>
<meta name="description" content="{esc(description)}">
{GSC_META}
<link rel="canonical" href="{SITE_URL}/{canonical_path}">
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
.card {{ background:var(--card); border-radius:8px; padding:16px; margin:12px 0; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
table {{ width:100%; border-collapse:collapse; background:var(--card); border-radius:8px; overflow:hidden; font-size:14px; }}
th, td {{ padding:10px 12px; text-align:left; border-bottom:1px solid #eee; vertical-align:top; }}
th {{ background:#f5ede8; font-weight:bold; }}
.btn-primary {{ display:inline-block; background:var(--primary); color:#fff; padding:10px 20px; border-radius:6px; text-decoration:none; font-weight:bold; }}
.btn-secondary {{ display:inline-block; background:#eee; color:#333; padding:8px 16px; border-radius:6px; text-decoration:none; font-weight:bold; }}
.tag {{ display:inline-block; background:#f5ede8; color:var(--primary); padding:2px 10px; border-radius:12px; font-size:12px; margin:2px; }}
.aff-note {{ font-size:11px; opacity:.8; }}
.updated {{ color:var(--muted); font-size:12px; margin-top:24px; border-top:1px solid #ddd; padding-top:12px; }}
.pros-cons {{ display:flex; gap:16px; flex-wrap:wrap; }}
.pros-cons > div {{ flex:1; min-width:240px; }}
.pros li, .cons li {{ margin-left:20px; font-size:14px; }}
.reward-badge {{ display:inline-block; background:#fff3e0; border:1px solid #ffcc80; color:#e65100; padding:4px 12px; border-radius:6px; font-weight:bold; font-size:13px; }}
footer.site {{ text-align:center; padding:24px 16px; color:var(--muted); font-size:12px; margin-top:32px; }}
ul.feature-list li, ol.feature-list li {{ margin-left:20px; font-size:14px; }}
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


def page_footer(updated_date):
    return f"""
<div class="updated">最終更新: {updated_date} ｜ 情報は確認時点のものであり、最新の価格・条件は必ず公式サイトをご確認ください。</div>
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

def build_service_page(service, aff_links):
    s_id = service["id"]
    s_name = service["name"]
    aff = service.get("affiliate", {})
    aff_campaigns = aff.get("campaigns", [])

    # アフィリエイト報酬表示
    # 関連記事リンク（サービスDBに article_link があれば表示）
    article_link_html = ""
    _art_link = service.get("article_link", "")
    if _art_link:
        _art_label = service.get("article_label", "関連記事を見る")
        article_link_html = f'<a class="btn-secondary" href="{esc(_art_link)}">{esc(_art_label)}</a> '

    reward_html = ""
    if aff_campaigns:
        items = []
        for c in aff_campaigns:
            items.append(
                f'<tr><td>{esc(c.get("asp", ""))}</td><td>{reward_display(c)}</td>'
                f'<td>{esc(c.get("status", ""))}</td><td>{esc(c.get("cv_condition", ""))}</td></tr>'
            )
        reward_html = f"""
        <h2>アフィリエイト報酬（内部管理情報）</h2>
        <table>
          <tr><th>ASP</th><th>報酬</th><th>状態</th><th>成果条件</th></tr>
          {''.join(items)}
        </table>
        """

    # メニュー・栄養
    feature_list = "".join(f"<li>{esc(f)}</li>" for f in service.get("main_features", []))
    pros = "".join(f"<li>{esc(p)}</li>" for p in service.get("pros", []))
    cons = "".join(f"<li>{esc(c)}</li>" for c in service.get("cons", []))
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in service.get("tags", []))

    cheapest = service.get("price_plan", {}).get("lowest_per_meal_yen")
    cheapest_html = yen(cheapest) + "/食" if cheapest else "要確認"

    title = f"{s_name}の口コミ・評判・料金を徹底解説"
    desc = f"{s_name}の特徴・料金・初回キャンペーン・評判をまとめました。{SITE_NAME}の最新調査情報（2026年8月）に基づく内容です。"

    html = page_header(title, desc, f"services/{s_id}.html")
    html += f"""
    <h1>{esc(s_name)}</h1>
    <div>{tags}</div>

    <div class="card">
      <h2>基本情報</h2>
      <table>
        <tr><th>運営会社</th><td>{esc(service.get("operator", "要確認"))}</td></tr>
        <tr><th>形態</th><td>{esc(service.get("meal_type", ""))}（{esc(service.get("meal_form", ""))}）</td></tr>
        <tr><th>最安料金</th><td>{cheapest_html}（2026-08-26時点）</td></tr>
        <tr><th>対象</th><td>{", ".join(service.get("target", []))}</td></tr>
      </table>
      <div style="margin-top:12px;">{aff_link(aff_links, s_id)}</div>
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
      <p>{esc(service.get("first_time_campaign", {}).get("summary", "要確認"))}</p>
      <p style="font-size:13px;color:#666;">{esc(service.get("first_time_campaign", {}).get("detail", ""))}</p>
      <div style="margin-top:12px;">{aff_link(aff_links, s_id, label="公式サイトで最新情報を見る", cls="btn-secondary")}</div>
    </div>

    <div class="card">
      <h2>解約・送料について</h2>
      <p>{esc(service.get("cancellation_note", "要確認（公式サイトで確認してください）"))}</p>
    </div>

    {reward_html}

    <div style="margin-top:16px;">
      {article_link_html}
      <a class="btn-secondary" href="/ranking.html">← おすすめ比較一覧に戻る</a>
      <a class="btn-secondary" href="/campaigns.html">初回キャンペーン一覧を見る</a>
    </div>
    """
    html += page_footer("2026-08-26")
    return html


# ---------- ランキングページ ----------

def build_ranking_page(services, aff_links):
    rows = []
    for svc in services:
        aff = svc.get("affiliate", {}).get("campaigns", [])
        numerics = [c.get("reward_yen") for c in aff if c.get("reward_yen")]
        texts = [c.get("reward_text") for c in aff if c.get("reward_text")]
        if texts:
            reward_txt = texts[0]  # 歩合・範囲報酬はテキスト優先
        elif numerics:
            reward_txt = f"最大{yen(max(numerics))}"
        else:
            reward_txt = "要確認"
        cheapest = svc.get("price_plan", {}).get("lowest_per_meal_yen")
        cheapest_txt = f"{yen(cheapest)}/食" if cheapest else "要確認"
        tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in svc.get("tags", [])[:3])
        rows.append(f"""
        <tr>
          <td><a href="/services/{svc['id']}.html"><strong>{esc(svc['name'])}</strong></a><br>{tags}</td>
          <td>{cheapest_txt}</td>
          <td><span class="reward-badge">{reward_txt}</span></td>
          <td>{', '.join(svc.get('target', []))}</td>
          <td>{aff_link(aff_links, svc['id'], label='公式サイト', cls='btn-secondary')}</td>
        </tr>""")

    title = "宅配食おすすめ比較ランキング【2026年8月最新】"
    desc = "宅配食・宅配弁当サービスの最新比較。nosh、ワタミの宅食ダイレクト、三ツ星ファームなど主要サービスの料金・特徴・初回キャンペーンを一覧で比較。"

    html = page_header(title, desc, "ranking.html")
    html += f"""
    <h1>宅配食おすすめ比較ランキング【2026年8月最新】</h1>
    <p>主要宅配食サービスを最新データで比較しています。報酬表示はASP公開情報（2026-08-26時点）。</p>
    <div class="card">
      <table>
        <tr><th>サービス</th><th>最安料金</th><th>初回報酬目安</th><th>向いている人</th><th></th></tr>
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
    <p style="font-size:13px;color:#666;">※各サービスの詳細はサービス名リンクから。価格・キャンペーン情報は常に変動するため、最新情報は公式サイトをご確認ください。</p>
    """
    html += page_footer("2026-08-26")
    return html


# ---------- キャンペーン一覧ページ ----------

def build_campaigns_page(campaigns, services, aff_links):
    svc_by_id = {s["id"]: s for s in services}
    cards = []
    for c in campaigns:
        svc = svc_by_id.get(c.get("service_id"))
        svc_name = svc["name"] if svc else "要確認"
        reward_txt = reward_display(c.get("affiliate", {}))
        cards.append(f"""
        <div class="card">
          <h2>{esc(c['title'])}</h2>
          <p>{esc(c['summary'])}</p>
          <table>
            <tr><th>対象サービス</th><td>{esc(svc_name)}</td></tr>
            <tr><th>割引タイプ</th><td>{esc(c.get('discount_type', '要確認'))}</td></tr>
            <tr><th>条件</th><td>{esc(c.get('conditions', '要確認'))}</td></tr>
            <tr><th>成果報酬（ASP）</th><td>最大{reward_txt}（{esc(c.get('affiliate', {}).get('asp', ''))}）</td></tr>
            <tr><th>最終確認</th><td>{esc(c.get('last_checked', ''))}</td></tr>
          </table>
          <div style="margin-top:12px;">{aff_link(aff_links, c['service_id'], label='公式サイトでキャンペーンを確認', cls='btn-primary')}</div>
        </div>""")

    title = "宅配食 初回キャンペーン・お試し情報まとめ【2026年8月】"
    desc = "宅配食サービスの最新の初回キャンペーン・お試し価格情報を一覧で紹介。お得に宅配食を始めたい人向け。"

    html = page_header(title, desc, "campaigns.html")
    html += f"""
    <h1>宅配食 初回キャンペーン・お試し情報まとめ</h1>
    <p>各サービスの初回キャンペーン・お試し情報を毎週更新しています。最新の割引条件は必ず公式サイトでご確認ください。</p>
    {''.join(cards)}
    """
    html += page_footer("2026-08-26")
    return html


# ---------- 比較ページ ----------

def build_comparison_page(service_a, service_b, aff_links):
    a_id, b_id = service_a["id"], service_b["id"]
    a_name, b_name = service_a["name"], service_b["name"]

    a_cheapest = service_a.get("price_plan", {}).get("lowest_per_meal_yen")
    b_cheapest = service_b.get("price_plan", {}).get("lowest_per_meal_yen")
    a_price = f"{yen(a_cheapest)}/食" if a_cheapest else "要確認"
    b_price = f"{yen(b_cheapest)}/食" if b_cheapest else "要確認"

    a_tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in service_a.get("tags", []))
    b_tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in service_b.get("tags", []))

    title = f"{a_name}と{b_name}を徹底比較！どっちがおすすめ？【2026年】"
    desc = f"{a_name}と{b_name}を料金・特徴・初回キャンペーンで比較。一人暮らし・ダイエット・糖質制限など目的別におすすめを解説。"

    html = page_header(title, desc, f"comparisons/{a_id}-vs-{b_id}.html")
    html += f"""
    <h1>{esc(a_name)}と{esc(b_name)}を徹底比較</h1>
    <p>どちらにするか迷っている人向けに、料金・特徴・初回キャンペーンを比較します。（2026年8月時点の情報）</p>

    <div class="card">
      <table>
        <tr><th></th><th>{esc(a_name)}</th><th>{esc(b_name)}</th></tr>
        <tr><td><strong>特徴</strong></td><td>{a_tags}</td><td>{b_tags}</td></tr>
        <tr><td><strong>最安料金</strong></td><td>{a_price}</td><td>{b_price}</td></tr>
        <tr><td><strong>向いている人</strong></td><td>{', '.join(service_a.get('target', []))}</td><td>{', '.join(service_b.get('target', []))}</td></tr>
        <tr><td><strong>公式サイト</strong></td><td>{aff_link(aff_links, a_id, label='公式サイト', cls='btn-secondary')}</td><td>{aff_link(aff_links, b_id, label='公式サイト', cls='btn-secondary')}</td></tr>
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
      <a class="btn-secondary" href="/campaigns.html">初回キャンペーン一覧を見る</a>
      <a class="btn-secondary" href="/tool/diagnosis.html">診断ツールで選ぶ</a>
    </div>
    """
    html += page_footer("2026-08-26")
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
            "url": svc.get("official_url", ""),
            "aff_url": aff.get("actual_url", ""),  # アフィリエイトリンク（あれば優先）
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
      <p style="margin-top:12px;"><button class="btn-primary" onclick="runDiag()">診断する</button></p>
    </div>

    <div id="result" class="card" style="display:none;"></div>

    <script>
    const SERVICES = {svc_json};
    function runDiag() {{
      const goals = [...document.querySelectorAll('#goals input:checked')].map(x => x.value);
      if (goals.length === 0) {{
        document.getElementById('result').style.display = 'block';
        document.getElementById('result').innerHTML = '<p>目的を1つ以上選んでください。</p>';
        return;
      }}
      // タグ or ターゲットとの一致数でスコアリング
      const scored = SERVICES.map(s => {{
        const pool = [...(s.tags||[]), ...(s.target||[])];
        let score = 0;
        for (const g of goals) {{ if (pool.includes(g)) score++; }}
        return {{ ...s, score }};
      }}).filter(s => s.score > 0).sort((a,b) => b.score - a.score);
      let html = '<h2>あなたにおすすめのサービス</h2>';
      if (scored.length === 0) {{
        html += '<p>条件に合うサービスがまだ登録されていません。近日中に追加予定です。</p>';
      }} else {{
        html += '<table><tr><th>サービス</th><th>特徴</th><th>公式サイト</th></tr>';
        for (const s of scored) {{
          const url = s.aff_url || s.url || '';
          const rel = s.aff_url ? 'rel="nofollow sponsored"' : '';
          const label = s.aff_url ? '公式サイトを見る' : '公式サイト';
          const link = url ? `<a href="${{url}}" ${{rel}} target="_blank" rel="noopener">${{label}}</a>` : '<span style="color:#999">要確認</span>';
          html += `<tr><td><strong>${{s.name}}</strong></td><td>${{(s.tags||[]).join('・')}}</td><td>${{link}}</td></tr>`;
        }}
        html += '</table>';
        html += '<p style="font-size:13px;color:#666;margin-top:12px;">※診断は簡易的なマッチングです。詳細は各サービスページをご確認ください。</p>';
      }}
      document.getElementById('result').style.display = 'block';
      document.getElementById('result').innerHTML = html;
    }}
    </script>
    """
    html += page_footer("2026-08-26")
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
          <div>{aff_link(aff_links, svc['id'], label='公式サイト', cls='btn-secondary')}</div>
        </div>"""

    title = f"{SITE_NAME}｜宅配食の比較・初回キャンペーン情報"
    desc = SITE_DESC

    html = page_header(title, desc, "index.html")
    html += f"""
    <h1>宅配食を、データで選ぶ。</h1>
    <p>{SITE_NAME}は、宅配食・宅配弁当サービスの料金・栄養・初回キャンペーン情報を「実データ」で比較するサイトです。最新のキャンペーン情報を毎週更新しています。</p>

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
        <li><strong>実データ</strong>：AIが生成した記事ではなく、公式情報・実食をベースにしたデータ</li>
        <li><strong>目的別</strong>：一人暮らし・ダイエット・糖質制限など目的で比較できる</li>
      </ul>
    </div>
    """
    html += page_footer("2026-08-26")
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
    html += page_footer("2026-08-26")
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
    html += page_footer("2026-08-26")
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
    html += page_footer("2026-08-26")
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
    html += page_footer("2026-08-26")
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
    html += page_footer("2026-08-26")
    return html


# ---------- sitemap / robots ----------

def build_sitemap(pages):
    urls = []
    for p in pages:
        urls.append(f"  <url>\n    <loc>{SITE_URL}/{p}</loc>\n    <lastmod>2026-08-26</lastmod>\n  </url>")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""


def build_robots():
    return f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml
"""


# ---------- メイン ----------

def main():
    services, campaigns, shipping, sources, aff_links = load_data()

    # 出力先クリーン
    if OUT_DIR.exists():
        import shutil
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "services").mkdir(parents=True)
    (OUT_DIR / "comparisons").mkdir(parents=True)
    (OUT_DIR / "tool").mkdir(parents=True)

    pages = []

    # トップ
    (OUT_DIR / "index.html").write_text(build_index_page(services, campaigns, aff_links), encoding="utf-8")
    pages.append("index.html")

    # ランキング
    (OUT_DIR / "ranking.html").write_text(build_ranking_page(services, aff_links), encoding="utf-8")
    pages.append("ranking.html")

    # キャンペーン
    (OUT_DIR / "campaigns.html").write_text(build_campaigns_page(campaigns, services, aff_links), encoding="utf-8")
    pages.append("campaigns.html")

    # 診断ツール
    (OUT_DIR / "tool" / "diagnosis.html").write_text(build_diagnosis_tool(services, aff_links), encoding="utf-8")
    pages.append("tool/diagnosis.html")

    # 記事ページ（シェフの無添つくりおき 口コミ・評判）
    (OUT_DIR / "articles").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "articles" / "chef-muten-tukuritoki-kuchikomi.html").write_text(
        build_article_chef_muten_kuchikomi(aff_links), encoding="utf-8")
    pages.append("articles/chef-muten-tukuritoki-kuchikomi.html")

    # 法務ページ
    legal_pages = [
        ("privacy.html", build_privacy_page),
        ("disclaimer.html", build_disclaimer_page),
        ("operator.html", build_operator_page),
        ("contact.html", build_contact_page),
    ]
    for fname, fn in legal_pages:
        (OUT_DIR / fname).write_text(fn(), encoding="utf-8")
        pages.append(fname)

    # サービス個別ページ
    for svc in services:
        (OUT_DIR / "services" / f"{svc['id']}.html").write_text(build_service_page(svc, aff_links), encoding="utf-8")
        pages.append(f"services/{svc['id']}.html")

    # 比較ページ（主要な組み合わせを自動生成）
    comp_pairs = [
        ("nosh", "mitsuboshi-farm"),
        ("nosh", "watami-takushoku"),
    ]
    svc_by_id = {s["id"]: s for s in services}
    for a_id, b_id in comp_pairs:
        if a_id in svc_by_id and b_id in svc_by_id:
            (OUT_DIR / "comparisons" / f"{a_id}-vs-{b_id}.html").write_text(
                build_comparison_page(svc_by_id[a_id], svc_by_id[b_id], aff_links), encoding="utf-8")
            pages.append(f"comparisons/{a_id}-vs-{b_id}.html")

    # 404 / sitemap / robots
    (OUT_DIR / "404.html").write_text(build_404_page(), encoding="utf-8")
    (OUT_DIR / "sitemap.xml").write_text(build_sitemap(pages), encoding="utf-8")
    (OUT_DIR / "robots.txt").write_text(build_robots(), encoding="utf-8")

    print(f"生成完了: {len(pages)} ページ + sitemap.xml + robots.txt")
    print(f"出力先: {OUT_DIR}")


if __name__ == "__main__":
    main()

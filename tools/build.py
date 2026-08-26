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

# サイト名・ドメインは docs/SITE_NAME_DOMAIN_DECISION_2026_08.md で決定
SITE_NAME = "宅食図鑑"
SITE_DESC = "宅配食・宅配弁当サービスを実データで比較。最新の初回キャンペーン・お試し情報を毎週更新。"
SITE_URL = "https://takushokuzukan.jp"  # ドメイン取得後に確定（現在は予定ドメイン）


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


# ---------- リンク生成 ----------

def aff_link(aff_links, service_id, label=None, cls="btn-primary"):
    """アフィリエイトリンク。actual_urlがあればそれ、なければ公式URLにフォールバック。"""
    info = aff_links.get(service_id, {})
    actual = info.get("actual_url", "")
    fallback = info.get("fallback_url", "")
    url = actual or fallback
    target = info.get("asp", "")
    label = label or f"公式サイトを見る"
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
    reward_html = ""
    if aff_campaigns:
        items = []
        for c in aff_campaigns:
            items.append(
                f'<tr><td>{esc(c.get("asp", ""))}</td><td>{yen(c.get("reward_yen"))}</td>'
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
        max_reward = max([c.get("reward_yen") or 0 for c in aff]) if aff else None
        reward_txt = yen(max_reward) if max_reward else "要確認"
        cheapest = svc.get("price_plan", {}).get("lowest_per_meal_yen")
        cheapest_txt = f"{yen(cheapest)}/食" if cheapest else "要確認"
        tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in svc.get("tags", [])[:3])
        rows.append(f"""
        <tr>
          <td><a href="/services/{svc['id']}.html"><strong>{esc(svc['name'])}</strong></a><br>{tags}</td>
          <td>{cheapest_txt}</td>
          <td><span class="reward-badge">最大{reward_txt}</span></td>
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
        reward = c.get("affiliate", {}).get("reward_yen")
        reward_txt = yen(reward) if reward else "要確認"
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

def build_diagnosis_tool(services):
    # クライアントサイドで動作する条件検索ツール
    svc_data = []
    for svc in services:
        svc_data.append({
            "id": svc["id"],
            "name": svc["name"],
            "tags": svc.get("tags", []),
            "target": svc.get("target", []),
            "price": svc.get("price_plan", {}).get("lowest_per_meal_yen"),
            "url": svc.get("official_url", ""),
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
          html += `<tr><td><strong>${{s.name}}</strong></td><td>${{(s.tags||[]).join('・')}}</td><td><a href="${{s.url}}" target="_blank" rel="noopener">公式サイト</a></td></tr>`;
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
    (OUT_DIR / "tool" / "diagnosis.html").write_text(build_diagnosis_tool(services), encoding="utf-8")
    pages.append("tool/diagnosis.html")

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

    # sitemap / robots
    (OUT_DIR / "sitemap.xml").write_text(build_sitemap(pages), encoding="utf-8")
    (OUT_DIR / "robots.txt").write_text(build_robots(), encoding="utf-8")

    print(f"生成完了: {len(pages)} ページ + sitemap.xml + robots.txt")
    print(f"出力先: {OUT_DIR}")


if __name__ == "__main__":
    main()

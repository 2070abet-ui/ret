"""
ScrapeBench 静的サイト生成 - ページ描画層
data.py が用意したデータ構造を受け取り、HTML文字列を組み立てる。
セマンティックHTML5 + インラインCSS + レスポンシブ比較表 + SEO/OGP対応。
"""
import datetime as _dt
import html as _html
import json as _json
import urllib.parse as _up

from sitegen.data import SITE_NAME, SITE_URL, SITE_DESC, LANG, OPERATOR, GSC_META


def esc(s):
    if s is None:
        return ""
    return _html.escape(str(s), quote=True)


# ---------- favicon（インラインSVG data URI・B2対応）・JSON-LD（B3対応） ----------

_FAVICON_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<rect width='100' height='100' rx='20' fill='#1E6FD9'/>"
    "<rect x='22' y='54' width='12' height='26' rx='3' fill='white'/>"
    "<rect x='42' y='38' width='12' height='42' rx='3' fill='white'/>"
    "<rect x='62' y='24' width='12' height='56' rx='3' fill='white'/>"
    "</svg>")
FAVICON_HREF = "data:image/svg+xml," + _up.quote(_FAVICON_SVG, safe="")

_JSONLD = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "WebSite", "@id": f"{SITE_URL}/#website", "url": f"{SITE_URL}/",
         "name": SITE_NAME, "description": SITE_DESC},
        {"@type": "Organization", "@id": f"{SITE_URL}/#organization",
         "url": f"{SITE_URL}/", "name": SITE_NAME},
    ],
}


# ---------- デザイン（軽量・技術系サイト向け） ----------

_CSS = """\
:root {
  --bg:#F6F7F9; --surface:#FFFFFF; --text:#1B2430; --muted:#5B6470;
  --border:#E2E6EC; --accent:#1E6FD9; --accent-dark:#1557A6;
  --ok:#1E7E34; --ok-bg:#E6F4EA; --err:#B42318; --err-bg:#FEE4E2;
  --mono:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
  --font:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text);
  font:16px/1.7 var(--font); -webkit-text-size-adjust:100%; }
.site-header { background:var(--surface); border-bottom:1px solid var(--border);
  position:sticky; top:0; z-index:10; }
.nav { max-width:1080px; margin:0 auto; padding:12px 20px; display:flex;
  flex-wrap:wrap; align-items:center; gap:18px; }
.nav .brand { font-weight:700; color:var(--accent); text-decoration:none;
  font-size:1.05rem; margin-right:auto; }
.nav a:not(.brand) { color:var(--muted); text-decoration:none; font-size:0.95rem; }
.nav a:hover { color:var(--accent); }
main { max-width:1080px; margin:0 auto; padding:32px 20px 56px; }
.hero { padding:40px 0 16px; }
.hero h1 { font-size:2.2rem; line-height:1.25; margin:0 0 12px; }
.hero p { font-size:1.1rem; color:var(--muted); max-width:720px; margin:0 0 24px; }
.cta { display:flex; gap:12px; flex-wrap:wrap; }
.btn { display:inline-block; padding:10px 18px; border-radius:8px;
  text-decoration:none; font-weight:600; }
.btn-primary { background:var(--accent); color:#fff; }
.btn-primary:hover { background:var(--accent-dark); }
.btn-secondary { background:var(--surface); color:var(--accent); border:1px solid var(--border); }
h2 { font-size:1.35rem; margin:40px 0 12px; }
h3 { font-size:1.05rem; margin:24px 0 8px; }
p { margin:8px 0; }
.muted { color:var(--muted); font-size:0.85rem; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; }
.card { background:var(--surface); border:1px solid var(--border);
  border-radius:10px; padding:18px; }
.card h3 { margin-top:0; }
.stat-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
  gap:14px; margin:20px 0; }
.stat { background:var(--surface); border:1px solid var(--border);
  border-radius:10px; padding:14px 16px; }
.stat .num { font:700 1.6rem/1.2 var(--mono); color:var(--accent); }
.stat .lbl { font-size:0.82rem; color:var(--muted); margin-top:2px; }
.table-wrap { overflow-x:auto; background:var(--surface);
  border:1px solid var(--border); border-radius:10px; }
table { width:100%; border-collapse:collapse; min-width:760px; font-size:0.92rem; }
th, td { text-align:left; padding:10px 14px; border-bottom:1px solid var(--border);
  vertical-align:top; }
th { background:#F1F3F6; font-weight:600; white-space:nowrap; }
tr:last-child td { border-bottom:none; }
td.num, th.num { font-family:var(--mono); text-align:right; white-space:nowrap; }
.badge { display:inline-block; padding:2px 10px; border-radius:999px;
  font-size:0.8rem; font-weight:600; white-space:nowrap; }
.badge-ok { background:var(--ok-bg); color:var(--ok); }
.badge-err { background:var(--err-bg); color:var(--err); }
.badge-muted { background:#EEF0F3; color:var(--muted); }
.empty { background:var(--surface); border:1px dashed var(--border);
  border-radius:10px; padding:28px; color:var(--muted); }
code { font-family:var(--mono); background:#F1F3F6; padding:1px 6px;
  border-radius:4px; font-size:0.9em; }
ul, ol { padding-left:22px; }
.site-footer { border-top:1px solid var(--border); background:var(--surface);
  padding:24px 20px; }
.site-footer .inner { max-width:1080px; margin:0 auto; display:flex;
  flex-wrap:wrap; gap:10px 18px; justify-content:space-between;
  color:var(--muted); font-size:0.85rem; }
.site-footer a { color:var(--muted); text-decoration:none; }
.site-footer a:hover { color:var(--accent); }

/* C2: スキップリンク（キーボード利用者向け・フォーカス時のみ表示） */
.skip-link { position:absolute; left:-9999px; top:auto; width:1px; height:1px;
  overflow:hidden; }
.skip-link:focus { position:fixed; left:12px; top:12px; z-index:200; width:auto;
  height:auto; overflow:visible; background:var(--surface); color:var(--accent);
  padding:10px 16px; border-radius:6px; border:2px solid var(--accent); font-weight:600; }

/* C3: スクリーンリーダー専用（caption用） */
.visually-hidden { position:absolute; width:1px; height:1px; margin:-1px;
  padding:0; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; border:0; }

/* C1: ナビタップターゲット拡大（モバイルで高さ44px以上を確保） */
.nav a { padding:10px 8px; border-radius:6px; }

/* D2: カード内CTA行・小ボタン */
.cta-row { display:flex; gap:8px; flex-wrap:wrap; margin:12px 0 0; }
.btn-sm { padding:7px 12px; font-size:0.88rem; }

/* A1: テーブル1列目固定（モバイル横スクロール時もProvider名を可視化） */
.table-wrap { -webkit-overflow-scrolling:touch; }
th:first-child, td:first-child { position:sticky; left:0; background:var(--surface);
  box-shadow:1px 0 0 var(--border); z-index:1; }
thead th:first-child { background:#F1F3F6; z-index:2; }
"""


# ---------- レイアウト ----------

def _head(title, description, canonical, noindex=False):
    robots = "noindex, nofollow" if noindex else "index, follow"
    gsc = f'<meta name="google-site-verification" content="{esc(GSC_META)}">\n' if GSC_META else ""
    og_image = f"{SITE_URL}/og-image.png"
    twitter_card = "summary" if noindex else "summary_large_image"
    jsonld = '<script type="application/ld+json">' + _json.dumps(_JSONLD, ensure_ascii=False) + "</script>"
    return f"""<!DOCTYPE html>
<html lang="{esc(LANG)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<link rel="icon" href="{FAVICON_HREF}">
<meta name="robots" content="{robots}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og_image)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="{twitter_card}">
{gsc}{jsonld}<style>
{_CSS}</style>
</head>"""


def _nav():
    return f"""<header class="site-header">
<nav class="nav" aria-label="Main navigation">
<a class="brand" href="/">{esc(SITE_NAME)}</a>
<a href="/">Home</a>
<a href="/benchmarks/">Benchmarks</a>
<a href="/methodology/">Methodology</a>
<a href="/about/">About</a>
<a href="/contact/">Contact</a>
</nav>
</header>"""


def _footer():
    year = _dt.date.today().year
    op = OPERATOR.get("name") or SITE_NAME
    return f"""<footer class="site-footer">
<div class="inner">
<p>© {year} {esc(SITE_NAME)}. Operated by {esc(op)}.</p>
<nav aria-label="Legal">
<a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a> · <a href="/disclaimer/">Disclaimer</a>
</nav>
</div>
</footer>"""


def page(title, description, content_html, canonical, noindex=False):
    return (_head(title, description, canonical, noindex)
            + '\n<body>\n<a class="skip-link" href="#main">Skip to main content</a>\n'
            + _nav()
            + '\n<main id="main">\n' + content_html + "\n</main>\n"
            + _footer() + "\n</body>\n</html>\n")


# ---------- メトリクス表示ヘルパー ----------

def _ms(v):
    return "—" if v is None else f"{v:,.0f}"


def _pct(v):
    return "—" if v is None else f"{v * 100:.1f}%"


def _size(v):
    if v is None:
        return "—"
    if v >= 1024 * 1024:
        return f"{v / 1024 / 1024:.2f} MB"
    return f"{v / 1024:.1f} KB"


# ---------- ページビルダー ----------

def build_index_page(d):
    hero = f"""<section class="hero">
<h1>Real benchmarks for LLM-ready web scraping APIs.</h1>
<p>{esc(SITE_DESC)}</p>
<div class="cta">
<a class="btn btn-primary" href="/benchmarks/">View Benchmarks</a>
<a class="btn btn-secondary" href="/methodology/">Methodology</a>
</div>
</section>"""

    if d["has_data"]:
        s = d["summary"]
        stats = f"""<section class="stat-row">
<div class="stat"><div class="num">{s.get("runs", 0)}</div><div class="lbl">Total runs</div></div>
<div class="stat"><div class="num">{_pct(s.get("overall_success_rate"))}</div><div class="lbl">Overall success rate</div></div>
<div class="stat"><div class="num">{s.get("providers_measured", 0)}</div><div class="lbl">Providers measured</div></div>
<div class="stat"><div class="num">{s.get("scenarios_measured", 0)}</div><div class="lbl">Provider × scenario cells</div></div>
</section>"""
    else:
        stats = """<section class="empty">
No benchmark data yet. Run <code>python scrapebench/tools/bench.py</code> to collect measurements, then rebuild with <code>python scrapebench/tools/build.py</code>.
</section>"""

    pstats = d["provider_stats"]
    pcards = []
    for p in d["providers"]:
        pid = p.get("id", "")
        ps = pstats.get(pid)
        badge = '<span class="badge badge-ok">measured</span>' if ps else '<span class="badge badge-muted">pending</span>'
        link = f'<a href="{esc(p.get("official_url", "#"))}" rel="noopener noreferrer" target="_blank">{esc(p.get("name", pid))}</a>'
        detail = ""
        if ps:
            detail = f'<div class="stat"><div class="num">{_pct(ps.get("success_rate"))}</div><div class="lbl">success · p50 {_ms(ps.get("latency_p50_ms"))} ms</div></div>'
        notes = p.get("notes") or ""
        trial_url = p.get("trial_url")
        cta = ""
        if trial_url:
            cta = (f'<p class="cta-row"><a class="btn btn-primary btn-sm" href="{esc(trial_url)}" '
                   f'rel="noopener noreferrer" target="_blank">Try free trial</a> '
                   f'<a class="btn btn-secondary btn-sm" href="/benchmarks/{esc(pid)}/">Details</a></p>')
        pcards.append(f"""<article class="card">
<h3>{link}</h3>
<p>{badge}</p>
{detail}
<p class="muted">{esc(notes)}</p>
{cta}
</article>""")

    how = """<section>
<h2>How it works</h2>
<div class="cards">
<div class="card"><h3>1. Configure</h3><p>Providers and target scenarios are defined in <code>config/providers.json</code> and <code>config/scenarios.json</code>.</p></div>
<div class="card"><h3>2. Measure</h3><p><code>tools/bench.py</code> calls each provider API and records latency, status, size, and keyword-match quality into SQLite.</p></div>
<div class="card"><h3>3. Publish</h3><p><code>tools/build.py</code> turns the latest aggregated results into a static site served on Cloudflare.</p></div>
</div>
</section>"""

    providers_section = f'<section><h2>Providers</h2><div class="cards">{"".join(pcards)}</div></section>' if pcards else ""
    return page(
        f"{SITE_NAME} — Web Scraping API Latency & Success Rate Benchmarks",
        SITE_DESC,
        hero + stats + providers_section + how,
        f"{SITE_URL}/")


def build_benchmarks_page(d):
    if not d["has_data"]:
        content = """<h1>Benchmarks</h1>
<section class="empty">No measurements yet. Run <code>python scrapebench/tools/bench.py</code> after setting provider API keys, then rebuild.</section>"""
    else:
        rows = []
        for cell in d["cells"]:
            p, s, r = cell["provider"], cell["scenario"], cell["result"]
            pid = p.get("id", "")
            pname = f'<a href="/benchmarks/{esc(pid)}/">{esc(p.get("name", pid))}</a>'
            sname = esc(s.get("name", s.get("id")))
            turl = esc(s.get("target_url", ""))
            if r is None:
                rows.append(f"""<tr>
<td>{pname}</td><td>{sname}<br><code>{turl}</code></td>
<td class="num">—</td><td><span class="badge badge-muted">no data</span></td>
<td class="num">—</td><td class="num">—</td><td class="num">—</td><td class="num">—</td>
</tr>""")
                continue
            sr = r.get("success_rate")
            if sr is None:
                badge = '<span class="badge badge-muted">—</span>'
            elif sr >= 1.0:
                badge = f'<span class="badge badge-ok">{_pct(sr)}</span>'
            else:
                badge = f'<span class="badge badge-err">{_pct(sr)}</span>'
            rows.append(f"""<tr>
<td>{pname}</td><td>{sname}<br><code>{turl}</code></td>
<td class="num">{r.get("runs", "—")}</td>
<td>{badge}</td>
<td class="num">{_ms(r.get("latency_p50_ms"))}</td>
<td class="num">{_ms(r.get("latency_p95_ms"))}</td>
<td class="num">{_pct(r.get("avg_match_ratio"))}</td>
<td class="num">{_size(r.get("avg_response_size_bytes"))}</td>
</tr>""")
        gen = ""
        if d.get("generated_at"):
            gen = f'<p class="muted">Latest session: {esc(d["generated_at"])}. See <a href="/methodology/">methodology</a> for definitions.</p>'
        content = f"""<h1>Benchmarks</h1>
{gen}
<div class="table-wrap">
<table>
<caption class="visually-hidden">Provider by scenario benchmark results: success rate, p50/p95 latency, match ratio, and response size.</caption>
<thead>
<tr><th scope="col">Provider</th><th scope="col">Scenario</th><th scope="col" class="num">Runs</th><th scope="col">Success</th>
<th scope="col" class="num">p50 (ms)</th><th scope="col" class="num">p95 (ms)</th><th scope="col" class="num">Match (%)</th><th scope="col" class="num">Avg Size (KB)</th></tr>
</thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
</div>
<p class="muted">p50 / p95 are latency percentiles in milliseconds. Match (%) = expected keywords found in the extracted output. Avg Size (KB) = mean HTTP response body size.</p>"""
    return page(
        f"Benchmarks — Web Scraping API Latency & Success Rates | {SITE_NAME}",
        "Provider-by-provider benchmark results: success rate, p50/p95 latency, response size, and keyword-match quality for LLM web scraping APIs.",
        content, f"{SITE_URL}/benchmarks/")


def build_provider_page(d, provider):
    """プロバイダー詳細ページ（D1: 表のProvider名リンクの遷移先）。
    プロバイダー情報・CTA・そのプロバイダーのシナリオ別結果を表示する。"""
    pid = provider.get("id", "")
    name = provider.get("name", pid)
    rows = []
    for cell in d["cells"]:
        if cell["provider"].get("id") != pid:
            continue
        s = cell["scenario"]
        r = cell["result"]
        sname = esc(s.get("name", s.get("id")))
        turl = esc(s.get("target_url", ""))
        if r is None:
            rows.append(f"""<tr>
<td>{sname}<br><code>{turl}</code></td>
<td class="num">—</td><td><span class="badge badge-muted">no data</span></td>
<td class="num">—</td><td class="num">—</td><td class="num">—</td>
</tr>""")
            continue
        sr = r.get("success_rate")
        if sr is None:
            badge = '<span class="badge badge-muted">—</span>'
        elif sr >= 1.0:
            badge = f'<span class="badge badge-ok">{_pct(sr)}</span>'
        else:
            badge = f'<span class="badge badge-err">{_pct(sr)}</span>'
        rows.append(f"""<tr>
<td>{sname}<br><code>{turl}</code></td>
<td class="num">{r.get("runs", "—")}</td>
<td>{badge}</td>
<td class="num">{_ms(r.get("latency_p50_ms"))}</td>
<td class="num">{_ms(r.get("latency_p95_ms"))}</td>
<td class="num">{_pct(r.get("avg_match_ratio"))}</td>
</tr>""")

    official = provider.get("official_url", "#")
    trial_url = provider.get("trial_url")
    if trial_url:
        cta = (f'<p class="cta-row"><a class="btn btn-primary" href="{esc(trial_url)}" '
               f'rel="noopener noreferrer" target="_blank">Try free trial</a> '
               f'<a class="btn btn-secondary" href="{esc(official)}" rel="noopener noreferrer" target="_blank">Official site</a></p>')
    else:
        cta = (f'<p><a class="btn btn-secondary" href="{esc(official)}" '
               f'rel="noopener noreferrer" target="_blank">Official site</a></p>')

    content = f"""<h1>{esc(name)}</h1>
<p class="muted"><a href="/benchmarks/">← All benchmarks</a></p>
<p>{esc(provider.get("notes", ""))}</p>
{cta}
<h2>Results</h2>
<div class="table-wrap">
<table>
<caption class="visually-hidden">Benchmark results for {esc(name)} by scenario.</caption>
<thead>
<tr><th scope="col">Scenario</th><th scope="col" class="num">Runs</th><th scope="col">Success</th>
<th scope="col" class="num">p50 (ms)</th><th scope="col" class="num">p95 (ms)</th><th scope="col" class="num">Match (%)</th></tr>
</thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
</div>"""
    return page(
        f"{name} — Web Scraping API Benchmarks | {SITE_NAME}",
        f"Benchmark results for {name}: success rate, p50/p95 latency, and match ratio across web scraping API scenarios.",
        content, f"{SITE_URL}/benchmarks/{pid}/")


def build_methodology_page(d):
    content = """<h1>Methodology</h1>
<p>ScrapeBench measures LLM-oriented web scraping APIs under repeatable conditions. Results are point-in-time samples and do not constitute an official rating.</p>
<h2>Metrics</h2>
<ul>
<li><strong>Success rate</strong> — share of requests returning an HTTP status below 400.</li>
<li><strong>Latency (p50 / p95)</strong> — distribution of total request time, measured from request send to body fully received.</li>
<li><strong>TTFB</strong> — time to first response byte (headers received).</li>
<li><strong>Response size</strong> — bytes of the HTTP response body.</li>
<li><strong>Output quality (match ratio)</strong> — fraction of expected keywords (per scenario) present in the extracted text output.</li>
</ul>
<h2>Procedure</h2>
<ol>
<li>Each enabled provider is called for each enabled scenario, repeated <code>repeat</code> times (default 5).</li>
<li>Requests are sent with a 60-second timeout and a polite delay between calls.</li>
<li>Raw runs are stored in SQLite (<code>data/benchmark.db</code>); the latest session is aggregated into <code>data/results/latest.json</code>.</li>
</ol>
<h2>Fairness &amp; caveats</h2>
<ul>
<li>Results depend on network conditions, API region, plan tier, and time of day.</li>
<li>All providers are called with the same scenarios and identical target URLs for comparison.</li>
<li>Target pages are public test or documentation endpoints used at low frequency for measurement only, not for republication.</li>
</ul>
<h2>Transparency</h2>
<p>Scenario definitions and provider configuration are version-controlled in <code>config/</code>. The latest aggregation is published with its session timestamp.</p>"""
    return page(
        f"Methodology — How We Measure Web Scraping APIs | {SITE_NAME}",
        "How ScrapeBench measures web scraping APIs: metric definitions, procedure, fairness notes, and caveats.",
        content, f"{SITE_URL}/methodology/")


def build_about_page(d):
    op = OPERATOR
    email = op.get("email")
    email_html = (f'<p>Contact: <a href="mailto:{esc(email)}">{esc(email)}</a></p>'
                  if email else '<p>Operator contact will be published once configured in <code>config/site.json</code>.</p>')
    content = f"""<h1>About</h1>
<p>{esc(SITE_NAME)} is an independent benchmark site for LLM-oriented web scraping APIs. We run repeatable measurements across providers and publish the aggregated results as a static site.</p>
<h2>What we do</h2>
<ul>
<li>Run provider APIs against public test scenarios and record latency, success rate, size, and output quality.</li>
<li>Publish the latest aggregated results and the measurement methodology transparently.</li>
<li>Do not republish target page content; output is used for metric computation only.</li>
</ul>
{email_html}"""
    return page(
        f"About — {SITE_NAME}",
        "About ScrapeBench: an independent benchmark site for LLM-oriented web scraping APIs.",
        content, f"{SITE_URL}/about/")


def build_privacy_page(d):
    op = OPERATOR
    email = op.get("email") or "contact details published in config/site.json"
    content = f"""<h1>Privacy Policy</h1>
<p>This site is a static website served by Cloudflare. It does not maintain user accounts and does not collect personal information through forms.</p>
<h2>Data we process</h2>
<ul>
<li><strong>Benchmark data</strong> — aggregated measurement results derived from public API responses. Raw responses are stored locally for measurement purposes only.</li>
<li><strong>Web analytics</strong> — if analytics tags are enabled in the future (e.g., Google Tag Manager), standard page-view data may be collected.</li>
</ul>
<h2>Contact</h2>
<p>Privacy questions: {esc(email)}</p>"""
    return page(
        f"Privacy Policy — {SITE_NAME}",
        "Privacy policy for ScrapeBench.",
        content, f"{SITE_URL}/privacy/")


def build_terms_page(d):
    content = """<h1>Terms of Use</h1>
<p>By using this site you agree to the following terms.</p>
<h2>Use of benchmark results</h2>
<ul>
<li>Results are provided "as is", without warranty of any kind, and may change between measurement sessions.</li>
<li>They are point-in-time samples, not official vendor ratings.</li>
</ul>
<h2>Acceptable use</h2>
<ul>
<li>Do not republish our content in a way that misrepresents it as official vendor data.</li>
<li>Do not use the site to exceed fair use of the measured services.</li>
</ul>
<h2>Changes</h2>
<p>These terms may be updated; the date of the last update is indicated on this page.</p>"""
    return page(
        f"Terms of Use — {SITE_NAME}",
        "Terms of use for ScrapeBench.",
        content, f"{SITE_URL}/terms/")


def build_disclaimer_page(d):
    content = f"""<h1>Disclaimer</h1>
<p>{esc(SITE_NAME)} is an independent project and is not affiliated with, endorsed by, or sponsored by Firecrawl, Apify, ScrapingBee, or any other vendor mentioned on this site.</p>
<ul>
<li>All product names, logos, and brands are property of their respective owners.</li>
<li>Benchmark figures are measured by us at a specific time and under specific conditions; your results may differ.</li>
<li>No guarantee of accuracy or completeness is provided.</li>
</ul>"""
    return page(
        f"Disclaimer — {SITE_NAME}",
        "Disclaimer for ScrapeBench benchmark results and vendor references.",
        content, f"{SITE_URL}/disclaimer/")


def build_contact_page(d):
    op = OPERATOR
    email = op.get("email")
    email_html = (f'<p>Email: <a href="mailto:{esc(email)}">{esc(email)}</a></p>'
                  if email else '<p>Contact email will be published once configured in <code>config/site.json</code>.</p>')
    content = f"""<h1>Contact</h1>
<p>Questions, corrections, or feedback about the benchmark methodology?</p>
{email_html}
<p>Please allow time for a response.</p>"""
    return page(
        f"Contact — {SITE_NAME}",
        "Contact ScrapeBench with questions, corrections, or methodology feedback.",
        content, f"{SITE_URL}/contact/")


def build_404_page(d):
    content = """<h1>404 — Page not found</h1>
<p>The page you requested does not exist. Return to the <a href="/">home page</a> or browse <a href="/benchmarks/">benchmarks</a>.</p>"""
    return page(
        f"404 — {SITE_NAME}",
        "Page not found.",
        content, f"{SITE_URL}/404.html", noindex=True)


def build_sitemap(pages, d):
    base = SITE_URL.rstrip("/")
    locs = []
    for p in pages:
        if p == "index.html":
            locs.append(f"{base}/")
        elif p == "404.html":
            continue
        elif p.endswith("index.html"):
            locs.append(f"{base}/{p[:-len('index.html')]}")
        else:
            locs.append(f"{base}/{p}")
    urls = "\n".join(f"<url><loc>{esc(loc)}</loc></url>" for loc in locs)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + urls + "\n</urlset>\n")


def build_robots(d):
    base = SITE_URL.rstrip("/")
    return f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n"